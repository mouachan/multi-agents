"""How a tool of these servers is written.

    mcp = create_mcp("claims-server")

    @tool(mcp)
    async def get_claim(claim_id: str) -> dict:
        '''What the model reads to choose the tool and its arguments.'''
        claim = await fetch_one("SELECT ... WHERE claim_number = :number", number=claim_id)
        if claim is None:
            raise ToolError(f"Claim {claim_id} not found")
        return {"claim": claim}

The decorator registers the function as an MCP tool and turns its result into the JSON text the
agents read, with "success" and "processing_time_seconds" (shown in the processing timeline):
    {"success": true, ...the returned fields...}
    {"success": false, "error": "..."}    on ToolError (an expected refusal, e.g. unknown case), or on an
                                          unexpected failure (logged with its traceback)
A tool that fails half-way but has partial results returns them with "success": False and "error".
Before it leaves the server the result goes through personal_data.mask(): the model never reads the
names, e-mail addresses or phone numbers of the people in the records.
"""
import functools
import inspect
import json
import logging
import time
from typing import Any, Awaitable, Callable, Dict

from mcp.server.fastmcp import FastMCP

from .personal_data import mask

logger = logging.getLogger(__name__)


class ToolError(Exception):
    """A request the tool cannot serve; its message is returned to the model."""


def tool(mcp: FastMCP, *, personal_data: bool = True) -> Callable:
    """Register an async function returning a dict as a tool of `mcp` (see the module doc).

    personal_data=False: the result holds no personal data (e.g. a sandbox run), it is not masked.
    """
    def register(function: Callable[..., Awaitable[Dict[str, Any]]]):
        @functools.wraps(function)
        async def run(*args, **kwargs) -> str:
            started = time.monotonic()
            try:
                result = {"success": True, **(await function(*args, **kwargs))}
                if personal_data:
                    result = await mask(result)
            except ToolError as e:
                result = {"success": False, "error": str(e)}
            except Exception as e:
                logger.exception("Tool %s failed", function.__name__)
                result = {"success": False, "error": f"{type(e).__name__}: {e}"}
            result["processing_time_seconds"] = round(time.monotonic() - started, 2)
            return json.dumps(result, ensure_ascii=False, default=str)

        # the MCP schema is built from the signature: same parameters, a text result
        run.__signature__ = inspect.signature(function).replace(return_annotation=str)
        mcp.tool()(run)
        return function
    return register


def required(value: str, name: str) -> str:
    """A required text argument, stripped."""
    if not value or not value.strip():
        raise ToolError(f"{name} is required")
    return value.strip()
