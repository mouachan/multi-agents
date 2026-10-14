"""SPIFFE JWT-SVIDs for calls to the A2A agents (Zero Trust Workload Identity Manager).

Active when SPIFFE_ENDPOINT_SOCKET is set (SPIFFE CSI driver mount). For a call to
http://claims-agent.<ns>.svc..., the audience is "a2a:claims-agent"; tokens are
cached until shortly before expiry (SPIRE default JWT-SVID TTL: 5 minutes).
"""
import asyncio
import logging
import os
import time
from typing import Dict, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

_source = None
_cache: Dict[str, Tuple[str, float]] = {}
_lock = asyncio.Lock()


def enabled() -> bool:
    return bool(os.getenv("SPIFFE_ENDPOINT_SOCKET"))


def _get_source():
    global _source
    if _source is None:
        from spiffe import JwtSource
        _source = JwtSource(timeout_in_seconds=10)
        logger.info("SPIFFE JwtSource connected to %s", os.getenv("SPIFFE_ENDPOINT_SOCKET"))
    return _source


async def token_for(audience: str) -> Optional[str]:
    cached = _cache.get(audience)
    if cached and cached[1] - time.time() > 60:
        return cached[0]
    async with _lock:
        source = await asyncio.to_thread(_get_source)
        svid = await asyncio.to_thread(source.fetch_svid, {audience})
        _cache[audience] = (svid.token, float(svid.expiry))
        return svid.token


async def add_a2a_auth(request: httpx.Request) -> None:
    """httpx request hook: Bearer JWT-SVID with audience derived from the agent host."""
    if not enabled():
        return
    agent = request.url.host.split(".")[0]
    if not agent.endswith("-agent"):
        return
    try:
        request.headers["Authorization"] = f"Bearer {await token_for(f'a2a:{agent}')}"
    except Exception as e:
        logger.error("Could not fetch JWT-SVID for %s: %s", agent, e)
