"""OpenShell sandbox: the policy applied to the agents' code interpreter (run_python) and
fixed isolation scenarios, served by the sandbox MCP server (SANDBOX_SERVER_URL)."""
import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


async def _call(method: str, path: str, timeout: float) -> Dict[str, Any]:
    if not settings.sandbox_server_url:
        raise HTTPException(status_code=503, detail="The OpenShell sandbox is not deployed (mcp.sandbox.enabled)")
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(method, f"{settings.sandbox_server_url.rstrip('/')}{path}")
    except httpx.HTTPError as e:
        logger.warning("Sandbox server unreachable: %s", e)
        raise HTTPException(status_code=502, detail=f"Sandbox server unreachable: {type(e).__name__}")
    if resp.status_code >= 400:
        detail = resp.json().get("error", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)
    return resp.json()


@router.get("/policy")
async def get_policy() -> Dict[str, Any]:
    """Policy in force (filesystem, Landlock, process, network) and gateway status."""
    info = await _call("GET", "/policy", 10)
    health = await _call("GET", "/health", 10)
    info["openshell"] = health.get("openshell", {})
    return info


@router.post("/demo/{scenario}")
async def run_demo(scenario: str) -> Dict[str, Any]:
    """Run a fixed isolation scenario (compute, identity, network, write_system, read_outside)."""
    return await _call("POST", f"/demo/{scenario}", 120)
