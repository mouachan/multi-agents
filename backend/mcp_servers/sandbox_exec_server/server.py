"""
MCP Sandbox Exec Server - runs LLM-generated Python in an OpenShell sandbox.

Tool run_python(code, timeout_s): each call creates an OpenShell sandbox from the
code-sandbox image with the policy in SANDBOX_POLICY_FILE (no network, Landlock
filesystem rules), runs /usr/bin/python3.12 -c <code>, returns stdout/stderr/exit
code plus the policy denials observed in the output, then deletes the sandbox.

OpenShell (NVIDIA, Developer Preview in RHOAI 3.5) enforces the policy in the
kernel (Landlock, seccomp, network namespace + proxy); the gateway is reached over
mTLS with the client bundle mounted in OPENSHELL_TLS_DIR.
FastMCP server exposing Streamable HTTP (/mcp) and legacy SSE (/sse).
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

import yaml
from google.protobuf import json_format
from openshell import SandboxClient, TlsConfig
from openshell._proto import openshell_pb2
from starlette.responses import JSONResponse

from shared.mcp_app import build_app, create_mcp

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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


def _run_in_sandbox(code: str, timeout_s: int) -> Dict[str, Any]:
    spec = openshell_pb2.SandboxSpec()
    spec.template.image = SANDBOX_IMAGE
    json_format.ParseDict(_policy_dict(), spec.policy)
    name = f"run-python-{uuid.uuid4().hex[:8]}"
    start = time.time()
    with _client() as client:
        client.create(workspace=OPENSHELL_WORKSPACE, spec=spec, name=name,
                      labels={"app": "multi-agents", "tool": "run_python"})
        try:
            client.wait_ready(name, workspace=OPENSHELL_WORKSPACE, timeout_seconds=SANDBOX_READY_TIMEOUT)
            ready_ms = int((time.time() - start) * 1000)
            result = client.exec(name, [PYTHON, "-c", code], workspace=OPENSHELL_WORKSPACE,
                                 timeout_seconds=timeout_s, workdir="/sandbox")
        finally:
            try:
                client.delete(name, workspace=OPENSHELL_WORKSPACE, allow_missing=True)
            except Exception as e:
                logger.warning(f"Sandbox {name} not deleted: {e}")
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
            "ready_ms": ready_ms,
            "duration_ms": int((time.time() - start) * 1000),
        },
    }


# =============================================================================
# MCP Tools
# =============================================================================

@mcp.tool()
async def run_python(code: str, timeout_s: int = 20) -> str:
    """
    Execute Python code in an isolated OpenShell sandbox and return its output.

    Use it for exact computations (e.g. claim payout: amount minus deductible,
    capped by the policy limit). The sandbox has NO network access and can only
    write to /sandbox and /tmp; print() the results you need. Standard library
    and numpy are available.

    Args:
        code: Python source code to run with python3.12
        timeout_s: Maximum execution time in seconds (default 20)

    Returns:
        JSON with keys: success, exit_code, stdout, stderr, denials (policy denials
        observed: network / filesystem), sandbox (name, image, policy, timings)
    """
    if not code or not code.strip():
        return json.dumps({"success": False, "error": "code is required"})
    if not SANDBOX_IMAGE:
        return json.dumps({"success": False, "error": "SANDBOX_IMAGE is not configured"})

    timeout_s = max(1, min(int(timeout_s or 20), MAX_EXEC_TIMEOUT))
    logger.info(f"run_python: {len(code)} chars, timeout {timeout_s}s")
    try:
        result = await asyncio.to_thread(_run_in_sandbox, code, timeout_s)
        if result["denials"]:
            logger.warning(f"Sandbox policy denials: {result['denials']}")
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error(f"run_python failed: {e}", exc_info=True)
        return json.dumps({"success": False, "error": f"Sandbox execution failed: {e}"})


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
# Starlette App — /mcp (Streamable HTTP), /sse (legacy), /health
# =============================================================================

app = build_app(mcp, "sandbox-exec-server", health_check)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting MCP Sandbox Exec Server on {host}:{port}")
    logger.info(f"OpenShell gateway: {OPENSHELL_ENDPOINT} (workspace {OPENSHELL_WORKSPACE})")
    logger.info(f"Sandbox image: {SANDBOX_IMAGE}, policy: {SANDBOX_POLICY_FILE}")
    logger.info("Tools: run_python")

    uvicorn.run(app, host=host, port=port)
