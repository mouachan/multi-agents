"""
Shared MCP transport wiring for all MCP servers.

Every server exposes, on the same port (8080):
  - /mcp     Streamable HTTP (stateless, JSON responses) — used by OGX, the
             MCP Gateway (Kuadrant) and the MCP lifecycle operator handshake
  - /sse     legacy SSE transport (+ /messages/) — kept for backward compatibility
  - /health  liveness/readiness probe
"""

import contextlib
from typing import Awaitable, Callable, Sequence

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute, Mount, Route


def create_mcp(name: str) -> FastMCP:
    """Create a FastMCP server suitable for running behind a gateway.

    DNS-rebinding protection is disabled explicitly: requests arrive with the
    Service name or the MCP Gateway internal hostname (e.g. claims-server.mcp-<ns>.local)
    as Host header, which FastMCP would otherwise reject (HTTP 421).
    """
    return FastMCP(
        name,
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )


def build_app(
    mcp: FastMCP,
    server_name: str,
    health_check: Callable[[Request], Awaitable[Response]],
    extra_routes: Sequence[BaseRoute] = (),
) -> Starlette:
    """Build the Starlette app serving /mcp, /sse and /health for a FastMCP server.

    extra_routes (e.g. the sandbox /policy) are matched before the SSE app mounted on /.
    """

    async def sse_options(request: Request) -> JSONResponse:
        return JSONResponse({
            "methods": ["GET", "POST", "OPTIONS"],
            "server_name": server_name,
            "transports": {"streamable_http": "/mcp", "sse": "/sse"},
            "capabilities": {"tools": True, "streaming": True},
        })

    # streamable_http_app() lazily creates mcp.session_manager, which must run
    # inside the parent app lifespan (mounted sub-app lifespans are not executed).
    streamable_routes = mcp.streamable_http_app().routes

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        async with mcp.session_manager.run():
            yield

    return Starlette(
        routes=[
            Route("/health", health_check),
            *extra_routes,
            *streamable_routes,
            Route("/sse", sse_options, methods=["OPTIONS"]),
            Route("/", sse_options, methods=["OPTIONS"]),
            Mount("/", app=mcp.sse_app()),
        ],
        lifespan=lifespan,
    )
