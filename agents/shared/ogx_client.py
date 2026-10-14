"""OGX Responses API client (RHOAI 3.5 — formerly LlamaStack, same HTTP API).

Streams /v1/responses with MCP tools and normalizes the SSE events into:
    {"type": "tool_call",   "name", "server"}
    {"type": "tool_result", "name", "server", "status", "output", "error"}
    {"type": "text_delta",  "delta"}
    {"type": "done", "output", "tool_calls", "response_id", "model", "usage"}
"""
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

TOOL_TO_SERVER = {
    "ocr_document": "ocr-server",
    "ocr_health_check": "ocr-server",
    "list_supported_formats": "ocr-server",
    "retrieve_user_info": "rag-server",
    "retrieve_similar_claims": "rag-server",
    "search_knowledge_base": "rag-server",
    "retrieve_similar_references": "rag-server",
    "retrieve_historical_tenders": "rag-server",
    "retrieve_capabilities": "rag-server",
    "search_courrier_knowledge": "rag-server",
    "retrieve_similar_reclamations": "rag-server",
    "list_claims": "claims-server",
    "get_claim": "claims-server",
    "get_claim_documents": "claims-server",
    "get_claim_statistics": "claims-server",
    "save_claim_decision": "claims-server",
    "list_tenders": "tenders-server",
    "get_tender": "tenders-server",
    "get_tender_documents": "tenders-server",
    "get_tender_statistics": "tenders-server",
    "save_tender_decision": "tenders-server",
    "list_reclamations": "postal-server",
    "get_reclamation": "postal-server",
    "get_reclamation_documents": "postal-server",
    "get_reclamation_statistics": "postal-server",
    "analyze_reclamation": "postal-server",
    "save_reclamation_decision": "postal-server",
    "get_tracking": "tracking-server",
    "search_tracking": "tracking-server",
}


class OGXClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 300.0,
        mcp_gateway_url: str = "",
        mcp_server_url_template: str = "http://{server}:8080/mcp",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.mcp_gateway_url = mcp_gateway_url
        self.mcp_server_url_template = mcp_server_url_template

    def build_mcp_tools(self, tools: List[str]) -> List[Dict[str, Any]]:
        if not tools:
            return []
        if self.mcp_gateway_url:
            # One MCP endpoint aggregating every server (Kuadrant MCP Gateway, no tool prefix)
            return [{
                "type": "mcp",
                "server_label": "mcp-gateway",
                "server_url": self.mcp_gateway_url,
                "allowed_tools": sorted(tools),
                "require_approval": "never",
            }]

        servers: Dict[str, set] = {}
        for tool in tools:
            server = TOOL_TO_SERVER.get(tool)
            if server:
                servers.setdefault(server, set()).add(tool)
            else:
                logger.warning("Unknown tool '%s' — skipped", tool)
        return [
            {
                "type": "mcp",
                "server_label": server,
                "server_url": self.mcp_server_url_template.format(server=server),
                "allowed_tools": sorted(names),
                "require_approval": "never",
            }
            for server, names in servers.items()
        ]

    async def stream(
        self,
        model: str,
        instructions: str,
        input_message: str,
        tools: List[str],
        max_tokens: int = 4096,
        previous_response_id: Optional[str] = None,
        tool_choice: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        payload: Dict[str, Any] = {
            "model": model,
            "input": input_message,
            "instructions": instructions,
            "stream": True,
            "store": True,
            "max_output_tokens": max_tokens,
            "tools": self.build_mcp_tools(tools),
        }
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        if tool_choice and payload["tools"]:
            payload["tool_choice"] = tool_choice

        full_text: List[str] = []
        tool_calls: List[Dict[str, Any]] = []
        seen_calls: set = set()
        response: Dict[str, Any] = {}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", f"{self.base_url}/v1/responses", json=payload) as resp:
                if resp.status_code >= 400:
                    body = (await resp.aread()).decode(errors="replace")
                    raise RuntimeError(f"OGX /v1/responses {resp.status_code}: {body[:500]}")

                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    etype = event.get("type", "")
                    item = event.get("item") or {}

                    if etype == "response.output_text.delta":
                        delta = event.get("delta", "")
                        if delta:
                            full_text.append(delta)
                            yield {"type": "text_delta", "delta": delta}

                    elif etype == "response.output_item.added" and item.get("type") == "mcp_call":
                        yield {"type": "tool_call", "name": item.get("name", ""),
                               "server": item.get("server_label", "")}

                    elif etype == "response.output_item.done" and item.get("type") == "mcp_call":
                        tc = self._tool_call(item)
                        seen_calls.add(item.get("id") or tc["name"])
                        tool_calls.append(tc)
                        yield {"type": "tool_result", **tc,
                               "status": "error" if tc["error"] else "completed"}

                    elif etype in ("response.completed", "response.incomplete", "response.failed"):
                        response = event.get("response", {}) or {}
                        if etype == "response.failed":
                            err = response.get("error") or {}
                            raise RuntimeError(f"OGX response failed: {err.get('message', err)}")

        # Fallback: collect anything the delta stream did not carry
        for out in response.get("output", []):
            if out.get("type") == "mcp_call" and (out.get("id") or out.get("name")) not in seen_calls:
                tool_calls.append(self._tool_call(out))
            elif out.get("type") == "message" and not full_text:
                for content in out.get("content", []):
                    if content.get("type") == "output_text" and content.get("text"):
                        full_text.append(content["text"])

        yield {
            "type": "done",
            "output": "".join(full_text),
            "tool_calls": tool_calls,
            "response_id": response.get("id"),
            "model": response.get("model", model),
            "usage": response.get("usage") or {},
        }

    @staticmethod
    def _tool_call(item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "name": item.get("name", ""),
            "server": item.get("server_label", ""),
            "arguments": item.get("arguments", ""),
            "output": item.get("output", ""),
            "error": item.get("error"),
        }
