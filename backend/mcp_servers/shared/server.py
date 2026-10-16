"""An MCP server of the platform: FastMCP tools served over HTTP on port 8080.

    /mcp     Streamable HTTP (stateless, JSON responses): OGX, the MCP Gateway, data-init
    /health  liveness and readiness probes (default: the database answers)

    mcp = create_mcp("claims-server")
    ... tools (shared/tools.py) ...
    if __name__ == "__main__":
        serve(mcp)
"""
import asyncio
import contextlib
import logging
import os
from typing import Awaitable, Callable, Optional, Sequence

import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute, Route

from .db import fetch_one, wait_for_database

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

HealthCheck = Callable[[Request], Awaitable[Response]]


def create_mcp(name: str) -> FastMCP:
    """A FastMCP server that answers behind a gateway: DNS-rebinding protection is off, as requests
    arrive with the Service name or the MCP Gateway host (claims-server.mcp-<ns>.local) as Host
    header, which FastMCP would otherwise refuse (HTTP 421)."""
    return FastMCP(name, stateless_http=True, json_response=True,
                   transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))


def app(mcp: FastMCP, health: Optional[HealthCheck] = None, routes: Sequence[BaseRoute] = ()) -> Starlette:
    """The HTTP application: /mcp, /health and the server's own routes (e.g. the sandbox /policy)."""
    async def database_health(request: Request) -> Response:
        try:
            await fetch_one("SELECT 1")
            return JSONResponse({"status": "healthy", "service": mcp.name})
        except Exception as e:
            return JSONResponse({"status": "unhealthy", "service": mcp.name, "error": str(e)[:200]}, status_code=503)

    # streamable_http_app() creates the session manager, which must run in this app's lifespan
    mcp_routes = mcp.streamable_http_app().routes

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette):
        async with mcp.session_manager.run():
            yield

    return Starlette(routes=[Route("/health", health or database_health), *routes, *mcp_routes], lifespan=lifespan)


def serve(mcp: FastMCP, health: Optional[HealthCheck] = None, routes: Sequence[BaseRoute] = (),
          database: bool = True) -> None:
    """Run the server on PORT (8080), once the database answers (database=False: no database)."""
    if database:
        wait_for_database()
    tools = sorted(t.name for t in asyncio.run(mcp.list_tools()))
    logger.info("%s: tools %s", mcp.name, ", ".join(tools))
    uvicorn.run(app(mcp, health, routes), host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
