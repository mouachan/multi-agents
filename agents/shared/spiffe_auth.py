"""SPIFFE workload identity for A2A calls (Zero Trust Workload Identity Manager / SPIRE).

No service mesh needed: the caller (backend) sends a JWT-SVID minted for the
audience "a2a:<agent-name>" as a Bearer token; this middleware validates it
against the local SPIRE agent (Workload API socket mounted by the SPIFFE CSI
driver) and checks the caller's SPIFFE ID path against an allow-list
(e.g. "/ns/multi-agents/sa/backend").

Enabled when SPIFFE_ENDPOINT_SOCKET is set. Public paths (agent card, health)
stay open so discovery and probes keep working.
"""
import asyncio
import json
import logging
import os
from contextvars import ContextVar
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

PUBLIC_PATHS = ("/.well-known/", "/health", "/docs", "/openapi.json")

# SPIFFE ID of the authenticated caller, visible to the executor (returned in the task metadata)
_caller: ContextVar[Optional[str]] = ContextVar("spiffe_caller", default=None)


def current_caller() -> Optional[str]:
    return _caller.get()


def enabled() -> bool:
    return bool(os.getenv("SPIFFE_ENDPOINT_SOCKET"))


class SpiffeJwtMiddleware:
    """Pure ASGI middleware (keeps A2A SSE streaming untouched)."""

    def __init__(self, app, audience: str, allowed_paths: Iterable[str]):
        from spiffe import WorkloadApiClient

        self.app = app
        self.audience = audience
        self.allowed = {p.strip() for p in allowed_paths if p.strip()}
        self.client = WorkloadApiClient()
        logger.info("SPIFFE JWT-SVID auth enabled (audience=%s, allowed=%s)", audience, sorted(self.allowed))

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or (
            scope["method"] == "GET" and scope["path"].startswith(PUBLIC_PATHS)
        ):
            return await self.app(scope, receive, send)

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        auth = headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return await _deny(send, 401, "missing JWT-SVID bearer token")
        try:
            svid = await asyncio.to_thread(self.client.validate_jwt_svid, auth[7:].strip(), self.audience)
        except Exception as e:
            logger.warning("Rejected JWT-SVID: %s", e)
            return await _deny(send, 401, "invalid JWT-SVID")

        caller = svid.spiffe_id
        if self.allowed and caller.path not in self.allowed:
            logger.warning("SPIFFE ID %s not allowed", caller)
            return await _deny(send, 403, f"caller {caller} not allowed")

        scope.setdefault("state", {})["spiffe_id"] = str(caller)
        _caller.set(str(caller))
        return await self.app(scope, receive, send)


async def _deny(send, status: int, message: str) -> None:
    body = json.dumps({"error": message}).encode()
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
    await send({"type": "http.response.body", "body": body})
