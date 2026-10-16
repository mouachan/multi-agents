"""
MCP Sandbox Exec Server - runs LLM-generated Python in an OpenShell sandbox.

Tool run_python(code, timeout_s): runs /usr/bin/python3.12 -c <code> in an OpenShell
sandbox from the code-sandbox image with the policy in SANDBOX_POLICY_FILE (no
network, Landlock filesystem rules) and returns stdout/stderr/exit code plus the
policy denials observed in the output.

Creating a sandbox takes ~30 s (pod + volume), so one warm sandbox is created at
startup and reused (SANDBOX_REUSE=true): calls are serialized, /sandbox and /tmp are
wiped before each run, and the sandbox is recreated if it disappears. At startup the
sandboxes left by previous pods are deleted (the server runs as a single replica). The policy is
enforced by the kernel on every run either way. SANDBOX_REUSE=false gives one
throw-away sandbox per call.

OpenShell (NVIDIA, Developer Preview in RHOAI 3.5) enforces the policy in the
kernel (Landlock, seccomp, network namespace + proxy); the gateway is reached over
mTLS with the client bundle mounted in OPENSHELL_TLS_DIR.
Besides /mcp it serves the backend's sandbox page: /policy (the policy in force) and /demo/{scenario}
(fixed isolation scenarios).
"""

import asyncio
import logging
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

import yaml
from google.protobuf import json_format
from openshell import SandboxClient, TlsConfig
from openshell._proto import openshell_pb2
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from shared.server import create_mcp, serve
from shared.tools import ToolError, tool

logger = logging.getLogger(__name__)

OPENSHELL_ENDPOINT = os.getenv("OPENSHELL_ENDPOINT", "openshell.openshell.svc:8080")
OPENSHELL_TLS_DIR = os.getenv("OPENSHELL_TLS_DIR", "/etc/openshell/mtls")
OPENSHELL_BEARER_TOKEN = os.getenv("OPENSHELL_BEARER_TOKEN", "")
OPENSHELL_WORKSPACE = os.getenv("OPENSHELL_WORKSPACE", "default")
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "")
SANDBOX_POLICY_FILE = os.getenv("SANDBOX_POLICY_FILE", "/etc/openshell/policy/code-sandbox-policy.yaml")
SANDBOX_READY_TIMEOUT = float(os.getenv("SANDBOX_READY_TIMEOUT", "120"))
MAX_EXEC_TIMEOUT = int(os.getenv("SANDBOX_MAX_EXEC_TIMEOUT", "60"))
MAX_OUTPUT_CHARS = 8000
SANDBOX_REUSE = os.getenv("SANDBOX_REUSE", "true").lower() == "true"
SANDBOX_LABELS = {"app": "multi-agents", "tool": "run_python"}
LABEL_SELECTOR = ",".join(f"{k}={v}" for k, v in SANDBOX_LABELS.items())
PREWARM_ATTEMPTS = 20
PREWARM_INTERVAL = 15  # seconds; after a cluster restart the gateway may not resolve yet
CLEANUP = "import shutil,os\nfor d in ('/sandbox','/tmp'):\n    for e in os.listdir(d):\n        p=os.path.join(d,e)\n        shutil.rmtree(p,True) if os.path.isdir(p) and not os.path.islink(p) else os.remove(p)"
PYTHON = "/usr/bin/python3.12"  # exact binary allowed by the policy

# Denials surfaced in the sandbox output (the authoritative OCSF events are in the
# OpenShell supervisor / gateway logs)
NETWORK_DENIAL = re.compile(
    r"(Network is unreachable|Connection refused|Name or service not known|"
    r"Temporary failure in name resolution|nodename nor servname|urlopen error|"
    r"Operation not permitted.*(socket|connect)|403 Forbidden)", re.IGNORECASE)
FILE_DENIAL = re.compile(r"(Permission denied|\[Errno 13\]|Read-only file system|\[Errno 30\])")

mcp = create_mcp("sandbox-exec-server")


def _policy_dict() -> Dict[str, Any]:
    """Policy file (OpenShell YAML schema) -> SandboxPolicy message fields."""
    with open(SANDBOX_POLICY_FILE) as f:
        doc = yaml.safe_load(f) or {}
    return {
        "version": doc.get("version", 1),
        "filesystem": doc.get("filesystem_policy", {}),
        "landlock": doc.get("landlock", {}),
        "process": doc.get("process", {}),
        "network_policies": doc.get("network_policies") or {},
    }


def _client() -> SandboxClient:
    tls_dir = Path(OPENSHELL_TLS_DIR)
    tls = TlsConfig(ca_path=tls_dir / "ca.crt", cert_path=tls_dir / "tls.crt", key_path=tls_dir / "tls.key")
    return SandboxClient(OPENSHELL_ENDPOINT, tls=tls, bearer_token=OPENSHELL_BEARER_TOKEN or None)


def _denials(stderr: str, stdout: str) -> List[Dict[str, str]]:
    found = []
    for line in (stderr + "\n" + stdout).splitlines():
        if NETWORK_DENIAL.search(line):
            found.append({"type": "network", "verdict": "DENIED", "detail": line.strip()[:300]})
        elif FILE_DENIAL.search(line):
            found.append({"type": "filesystem", "verdict": "DENIED", "detail": line.strip()[:300]})
    return found[:10]


def _spec() -> openshell_pb2.SandboxSpec:
    spec = openshell_pb2.SandboxSpec()
    spec.template.image = SANDBOX_IMAGE
    json_format.ParseDict(_policy_dict(), spec.policy)
    return spec


def _create(client: SandboxClient) -> str:
    name = f"run-python-{uuid.uuid4().hex[:8]}"
    client.create(workspace=OPENSHELL_WORKSPACE, spec=_spec(), name=name, labels=SANDBOX_LABELS)
    client.wait_ready(name, workspace=OPENSHELL_WORKSPACE, timeout_seconds=SANDBOX_READY_TIMEOUT)
    return name


def _delete(client: SandboxClient, name: str) -> None:
    try:
        client.delete(name, workspace=OPENSHELL_WORKSPACE, allow_missing=True)
    except Exception as e:
        logger.warning(f"Sandbox {name} not deleted: {e}")


def _delete_orphans(client: SandboxClient) -> None:
    """Delete the run_python sandboxes left by previous server pods (one replica)."""
    for ref in client.list_all(workspace=OPENSHELL_WORKSPACE, label_selector=LABEL_SELECTOR):
        logger.info(f"Deleting orphan sandbox {ref.name}")
        _delete(client, ref.name)


class WarmSandbox:
    """One reusable sandbox; recreated when an exec fails because it is gone."""

    def __init__(self) -> None:
        self.name = ""
        self.lock = threading.Lock()  # one run at a time in the shared sandbox

    def prewarm(self) -> None:
        for attempt in range(1, PREWARM_ATTEMPTS + 1):
            try:
                with self.lock, _client() as client:
                    _delete_orphans(client)
                    self.ensure(client)
                return
            except Exception as e:
                logger.warning(f"Sandbox pre-warm attempt {attempt}/{PREWARM_ATTEMPTS} failed: {e}")
                time.sleep(PREWARM_INTERVAL)
        logger.warning("Sandbox pre-warm gave up: the first run_python call creates the sandbox")

    def ensure(self, client: SandboxClient) -> int:
        """Create the sandbox if needed; returns the time spent waiting for it (ms)."""
        if self.name:
            return 0
        start = time.time()
        self.name = _create(client)
        logger.info(f"Warm sandbox {self.name} ready in {time.time() - start:.1f}s")
        return int((time.time() - start) * 1000)

    def run(self, client: SandboxClient, code: str, timeout_s: int):
        with self.lock:
            return self._run(client, code, timeout_s)

    def _run(self, client: SandboxClient, code: str, timeout_s: int):
        ready_ms = self.ensure(client)
        try:
            client.exec(self.name, [PYTHON, "-c", CLEANUP], workspace=OPENSHELL_WORKSPACE,
                        timeout_seconds=15, workdir="/sandbox")
        except Exception as e:
            logger.warning(f"Warm sandbox {self.name} unusable ({e}), recreating")
            _delete(client, self.name)
            self.name = ""
            ready_ms += self.ensure(client)
        result = client.exec(self.name, [PYTHON, "-c", code], workspace=OPENSHELL_WORKSPACE,
                             timeout_seconds=timeout_s, workdir="/sandbox")
        return self.name, ready_ms, result


_warm = WarmSandbox()


def _run_in_sandbox(code: str, timeout_s: int) -> Dict[str, Any]:
    start = time.time()
    with _client() as client:
        if SANDBOX_REUSE:
            name, ready_ms, result = _warm.run(client, code, timeout_s)
        else:
            name = _create(client)
            ready_ms = int((time.time() - start) * 1000)
            try:
                result = client.exec(name, [PYTHON, "-c", code], workspace=OPENSHELL_WORKSPACE,
                                     timeout_seconds=timeout_s, workdir="/sandbox")
            finally:
                _delete(client, name)
    return {
        "success": result.exit_code == 0,
        "exit_code": result.exit_code,
        "stdout": result.stdout[-MAX_OUTPUT_CHARS:],
        "stderr": result.stderr[-MAX_OUTPUT_CHARS:],
        "denials": _denials(result.stderr, result.stdout),
        "sandbox": {
            "name": name,
            "image": SANDBOX_IMAGE,
            "policy": "network deny-all, Landlock (rw: /sandbox, /tmp)",
            "reused": SANDBOX_REUSE and ready_ms == 0,
            "ready_ms": ready_ms,
            "duration_ms": int((time.time() - start) * 1000),
        },
    }


# =============================================================================
# MCP Tools
# =============================================================================

@tool(mcp, personal_data=False)
async def run_python(code: str, timeout_s: int = 20) -> Dict[str, Any]:
    """
    Execute Python code in an isolated OpenShell sandbox and return its output.

    Use it for exact computations (e.g. claim payout: amount minus deductible,
    capped by the policy limit). The sandbox has NO network access and can only
    write to /sandbox and /tmp; print() the results you need. Standard library
    and numpy are available. Write the code on one line, statements separated by
    "; " and strings in single quotes, e.g. "a=6200.0; b=350.0; print('payout:', a-b)".

    Args:
        code: Python source code to run with python3.12
        timeout_s: Maximum execution time in seconds (default 20)

    Returns:
        JSON with keys: success, exit_code, stdout, stderr, denials (policy denials
        observed: network / filesystem), sandbox (name, image, policy, timings)
    """
    if not code or not code.strip():
        raise ToolError("code is required")
    if not SANDBOX_IMAGE:
        raise ToolError("SANDBOX_IMAGE is not configured")

    timeout_s = max(1, min(int(timeout_s or 20), MAX_EXEC_TIMEOUT))
    logger.info(f"run_python: {len(code)} chars, timeout {timeout_s}s")
    result = await asyncio.to_thread(_run_in_sandbox, code, timeout_s)
    if result["denials"]:
        logger.warning(f"Sandbox policy denials: {result['denials']}")
    return result


# =============================================================================
# Health Check
# =============================================================================

async def health_check(request):
    """The server is healthy without the gateway; the gateway status is reported."""
    try:
        def _health():
            with _client() as client:
                return client.health().version
        version = await asyncio.wait_for(asyncio.to_thread(_health), timeout=5)
        gateway = {"status": "connected", "endpoint": OPENSHELL_ENDPOINT, "version": version}
    except Exception as e:
        gateway = {"status": "unavailable", "endpoint": OPENSHELL_ENDPOINT, "error": str(e)[:200]}
    return JSONResponse({"status": "healthy", "service": "sandbox-exec-server", "openshell": gateway})


# =============================================================================
# Demonstration endpoints (used by the backend /api/v1/sandbox): the policy in force and
# fixed isolation scenarios. No arbitrary code is accepted here.
# =============================================================================

DEMO_SCENARIOS: Dict[str, Dict[str, str]] = {
    "compute": {
        "expect": "allowed",
        "code": ("claimed, deductible, ceiling = 12500.0, 350.0, 10000.0\n"
                 "payout = min(max(claimed - deductible, 0), ceiling)\n"
                 "print(f'claimed={claimed} deductible={deductible} ceiling={ceiling}')\n"
                 "print(f'payout={payout}')"),
    },
    "identity": {
        "expect": "allowed",
        "code": "import os\nprint('uid:', os.getuid(), 'gid:', os.getgid(), '| root:', os.getuid() == 0)",
    },
    "network": {
        "expect": "denied",
        "code": "import urllib.request\nurllib.request.urlopen('https://example.com', timeout=5)",
    },
    "write_system": {
        "expect": "denied",
        "code": "open('/etc/hacked', 'w').write('x')",
    },
    "read_outside": {
        "expect": "denied",
        "code": "import os\nprint(os.listdir('/var'))",
    },
}


def _policy_info() -> Dict[str, Any]:
    with open(SANDBOX_POLICY_FILE) as f:
        text = f.read()
    return {
        "policy": yaml.safe_load(text) or {},
        "policy_yaml": text,
        "image": SANDBOX_IMAGE,
        "gateway": OPENSHELL_ENDPOINT,
        "workspace": OPENSHELL_WORKSPACE,
        "python": PYTHON,
        "reuse": SANDBOX_REUSE,
        "warm_sandbox": _warm.name or None,
        "max_exec_timeout_s": MAX_EXEC_TIMEOUT,
    }


async def policy(request: Request) -> JSONResponse:
    try:
        return JSONResponse(_policy_info())
    except Exception as e:
        return JSONResponse({"error": f"Policy not readable: {e}"}, status_code=500)


async def demo(request: Request) -> JSONResponse:
    name = request.path_params["scenario"]
    scenario = DEMO_SCENARIOS.get(name)
    if not scenario:
        return JSONResponse({"error": f"Unknown scenario {name}", "scenarios": list(DEMO_SCENARIOS)},
                            status_code=404)
    if not SANDBOX_IMAGE:
        return JSONResponse({"error": "SANDBOX_IMAGE is not configured"}, status_code=503)
    try:
        result = await asyncio.to_thread(_run_in_sandbox, scenario["code"], 20)
    except Exception as e:
        logger.error(f"Demo {name} failed: {e}", exc_info=True)
        return JSONResponse({"error": f"Sandbox execution failed: {e}"}, status_code=502)
    return JSONResponse({"scenario": name, "expect": scenario["expect"], "code": scenario["code"], **result})


if __name__ == "__main__":
    logger.info(f"OpenShell gateway: {OPENSHELL_ENDPOINT} (workspace {OPENSHELL_WORKSPACE})")
    logger.info(f"Sandbox image: {SANDBOX_IMAGE}, policy: {SANDBOX_POLICY_FILE}")
    if SANDBOX_REUSE and SANDBOX_IMAGE:
        threading.Thread(target=_warm.prewarm, name="sandbox-prewarm", daemon=True).start()
    serve(mcp, health=health_check, database=False, routes=[
        Route("/policy", policy, methods=["GET"]),
        Route("/demo/{scenario}", demo, methods=["POST"]),
    ])
