"""
LlamaStack Responses API orchestrator.

Handles stateful multi-turn conversations via previous_response_id
with automatic MCP tool execution.
"""
import httpx
import json
import logging
import re
from typing import AsyncGenerator, Dict, Any, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class ResponsesOrchestrator:
    """Orchestrate LLM interactions using Responses API with automatic tool execution."""

    @staticmethod
    def _default_mcp_servers() -> Dict[str, Any]:
        """Build MCP server configs from environment-driven settings."""
        return {
            "ocr-server": {
                "server_label": "ocr-server",
                "server_url": f"{settings.ocr_server_url}/sse"
            },
            "rag-server": {
                "server_label": "rag-server",
                "server_url": f"{settings.rag_server_url}/sse"
            },
            "claims-server": {
                "server_label": "claims-server",
                "server_url": f"{settings.claims_server_url}/sse"
            },
            "tenders-server": {
                "server_label": "tenders-server",
                "server_url": f"{settings.tenders_server_url}/sse"
            },
        }

    # Default tool-to-server mapping
    DEFAULT_TOOL_TO_SERVER = {
        # OCR server
        "ocr_document": "ocr-server",
        "ocr_health_check": "ocr-server",
        "list_supported_formats": "ocr-server",
        # RAG server (vector/semantic operations)
        "retrieve_user_info": "rag-server",
        "retrieve_similar_claims": "rag-server",
        "search_knowledge_base": "rag-server",
        "rag_health_check": "rag-server",
        "retrieve_similar_references": "rag-server",
        "retrieve_historical_tenders": "rag-server",
        "retrieve_capabilities": "rag-server",
        # Claims server (CRUD operations)
        "list_claims": "claims-server",
        "get_claim": "claims-server",
        "get_claim_documents": "claims-server",
        "analyze_claim": "claims-server",
        "get_claim_statistics": "claims-server",
        # Tenders server (CRUD operations)
        "list_tenders": "tenders-server",
        "get_tender": "tenders-server",
        "get_tender_documents": "tenders-server",
        "analyze_tender": "tenders-server",
        "get_tender_statistics": "tenders-server",
        # Decision persistence
        "save_claim_decision": "claims-server",
        "save_tender_decision": "tenders-server",
        # Embedding generation
        "generate_document_embedding": "rag-server",
    }

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 300.0,
        mcp_servers: Optional[Dict[str, Any]] = None,
        tool_to_server: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            base_url: LlamaStack endpoint URL
            timeout: Request timeout in seconds
            mcp_servers: Custom MCP server configurations (defaults to built-in servers)
            tool_to_server: Custom tool-to-server mapping (defaults to built-in mapping)
        """
        self.base_url = base_url or settings.llamastack_endpoint
        self.timeout = timeout
        self.model = settings.llamastack_default_model

        # MCP server configurations - configurable per agent
        self.mcp_servers = mcp_servers or self._default_mcp_servers()
        self._tool_to_server = tool_to_server or self.DEFAULT_TOOL_TO_SERVER.copy()

    def _build_mcp_tools(self, tools: List[str]) -> List[Dict[str, Any]]:
        """
        Build MCP tool configurations from tool names.

        Args:
            tools: List of tool names (e.g., ["ocr_document", "retrieve_user_info"])

        Returns:
            List of MCP tool configurations
        """
        # Group tools by server using configurable mapping
        servers_with_tools = {}
        for tool_name in tools:
            server = self._tool_to_server.get(tool_name)
            if not server:
                logger.warning(f"Unknown tool: {tool_name}")
                continue

            if server not in servers_with_tools:
                servers_with_tools[server] = []
            servers_with_tools[server].append(tool_name)

        # Build MCP tool configs
        mcp_tools = []
        for server, server_tools in servers_with_tools.items():
            config = self.mcp_servers[server].copy()
            config["type"] = "mcp"
            config["allowed_tools"] = server_tools
            mcp_tools.append(config)

        return mcp_tools

    async def process_with_agent(
        self,
        agent_config: Dict[str, Any],
        input_message: Any,  # Can be str or List[Dict]
        tools: Optional[List[str]] = None,
        max_infer_iters: int = 10,
        previous_response_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a task using the Responses API.

        When previous_response_id is provided, LlamaStack manages conversation
        context server-side — no need to send full history.

        Args:
            agent_config: Agent configuration with instructions
            input_message: New user message (str) or conversation (List[Dict])
            tools: Optional list of tools to enable
            max_infer_iters: Max tool-calling iterations
            previous_response_id: Chain from a previous response for multi-turn

        Returns:
            Agent response with output and response_id for chaining
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Build request payload
            payload = {
                "model": agent_config.get("model", self.model),
                "input": input_message,
                "stream": False,
                "store": True,
                "max_infer_iters": max_infer_iters,
                "max_tokens": settings.llamastack_max_tokens,
            }

            # Chain conversation via previous_response_id
            if previous_response_id:
                payload["previous_response_id"] = previous_response_id

            # Add instructions from agent_config
            if "instructions" in agent_config:
                payload["instructions"] = agent_config["instructions"]

            # Add tools if provided
            if tools:
                payload["tools"] = self._build_mcp_tools(tools)

            # Log
            has_chain = "chained" if previous_response_id else "new"
            logger.info(f"Calling Responses API with {len(tools or [])} tools, {has_chain} conversation")

            # Call Responses API
            response = await client.post(
                f"{self.base_url}/v1/responses",
                json=payload
            )

            response.raise_for_status()
            result = response.json()

            # Extract output
            output_items = result.get("output", [])

            # Collect ALL messages and tool calls
            all_message_texts = []
            tool_calls = []

            for item in output_items:
                if item.get("type") == "message":
                    # Extract text from each message
                    for content_item in item.get("content", []):
                        if content_item.get("type") == "output_text":
                            text = content_item.get("text", "")
                            if text.strip():
                                all_message_texts.append(text)
                elif item.get("type") == "mcp_call":
                    tool_calls.append({
                        "name": item.get("name"),
                        "server": item.get("server_label"),
                        "output": item.get("output"),
                        "error": item.get("error")
                    })

            # Concatenate all message texts to capture JSON from any turn
            output_text = "\n\n".join(all_message_texts)


            # Log each tool call for debugging
            for tc in tool_calls:
                status = "ERROR" if tc.get("error") else "OK"
                output_preview = ""
                if tc.get("output"):
                    output_preview = tc["output"][:200]
                elif tc.get("error"):
                    output_preview = tc["error"][:200]
                logger.info(f"Tool call: {tc.get('name')} [{tc.get('server')}] -> {status}: {output_preview}")

            logger.info(f"Response completed: tools_used={len(tool_calls)}, messages={len(all_message_texts)}")
            logger.info(f"Full output text ({len(output_text)} chars):\n{output_text[:2000]}")

            return {
                "response_id": result.get("id"),
                "output": output_text,
                "tool_calls": tool_calls,
                "usage": result.get("usage", {}),
            }

    async def process_with_agent_stream(
        self,
        agent_config: Dict[str, Any],
        input_message: Any,
        tools: Optional[List[str]] = None,
        max_infer_iters: int = 10,
        previous_response_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a task using the Responses API with SSE.

        Yields structured events:
        - {"type": "tool_call", "name": "...", "server": "..."}
        - {"type": "tool_result", "name": "...", "status": "completed"|"error"}
        - {"type": "text_delta", "delta": "..."}
        - {"type": "done", "response_id": "...", "usage": {...}, "tool_calls": [...], "output": "..."}
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": agent_config.get("model", self.model),
                "input": input_message,
                "stream": True,
                "store": True,
                "max_infer_iters": max_infer_iters,
                "max_tokens": settings.llamastack_max_tokens,
            }

            if previous_response_id:
                payload["previous_response_id"] = previous_response_id
            if "instructions" in agent_config:
                payload["instructions"] = agent_config["instructions"]
            if tools:
                payload["tools"] = self._build_mcp_tools(tools)

            has_chain = "chained" if previous_response_id else "new"
            logger.info(f"Streaming Responses API with {len(tools or [])} tools, {has_chain} conversation")

            # Accumulators for the final done event
            full_text = []
            tool_calls = []
            response_id = None
            usage = {}

            async with client.stream(
                "POST",
                f"{self.base_url}/v1/responses",
                json=payload,
            ) as response:
                response.raise_for_status()
                buffer = ""

                async for chunk in response.aiter_text():
                    buffer += chunk
                    # Process complete SSE lines
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        if not line or line.startswith(":"):
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                continue

                            try:
                                event = json.loads(data_str)
                            except json.JSONDecodeError:
                                continue

                            event_type = event.get("type", "")

                            # Response completed event
                            if event_type == "response.completed":
                                resp = event.get("response", {})
                                response_id = resp.get("id")
                                usage = resp.get("usage", {})
                                # Extract any remaining output from the completed response
                                for item in resp.get("output", []):
                                    if item.get("type") == "message":
                                        for ci in item.get("content", []):
                                            if ci.get("type") == "output_text":
                                                t = ci.get("text", "")
                                                if t.strip() and t not in full_text:
                                                    full_text.append(t)
                                    elif item.get("type") == "mcp_call":
                                        tc = {
                                            "name": item.get("name"),
                                            "server": item.get("server_label"),
                                            "output": item.get("output"),
                                            "error": item.get("error"),
                                        }
                                        if tc not in tool_calls:
                                            tool_calls.append(tc)
                                continue

                            # Helper: extract name/server from event or nested item
                            def _extract_mcp_info(ev: dict) -> tuple:
                                item = ev.get("item", {})
                                name = ev.get("name") or item.get("name", "")
                                server = ev.get("server_label") or item.get("server_label", "")
                                return name, server

                            # MCP tool call started (flat or nested format)
                            if event_type in (
                                "response.mcp_call.in_progress",
                                "response.mcp_call_in_progress",
                            ):
                                name, server = _extract_mcp_info(event)
                                if name:
                                    yield {"type": "tool_call", "name": name, "server": server}

                            # Output item added — detect mcp_call start
                            elif event_type == "response.output_item.added":
                                item = event.get("item", {})
                                if item.get("type") == "mcp_call":
                                    name = item.get("name", "")
                                    server = item.get("server_label", "")
                                    if name:
                                        yield {"type": "tool_call", "name": name, "server": server}

                            # Output item done — detect mcp_call completion
                            elif event_type == "response.output_item.done":
                                item = event.get("item", {})
                                if item.get("type") == "mcp_call":
                                    name = item.get("name", "")
                                    server = item.get("server_label", "")
                                    error = item.get("error")
                                    tc = {
                                        "name": name,
                                        "server": server,
                                        "output": item.get("output"),
                                        "error": error,
                                    }
                                    tool_calls.append(tc)
                                    status = "error" if error else "completed"
                                    yield {"type": "tool_result", "name": name, "status": status}

                            # MCP tool call completed (flat format)
                            elif event_type in (
                                "response.mcp_call.completed",
                                "response.mcp_call_completed",
                            ):
                                name, server = _extract_mcp_info(event)
                                error = event.get("error") or event.get("item", {}).get("error")
                                tc = {
                                    "name": name,
                                    "server": server,
                                    "output": event.get("output") or event.get("item", {}).get("output"),
                                    "error": error,
                                }
                                tool_calls.append(tc)
                                status = "error" if error else "completed"
                                yield {"type": "tool_result", "name": name, "status": status}

                            # Text output delta
                            elif event_type == "response.output_text.delta":
                                delta = event.get("delta", "")
                                if delta:
                                    full_text.append(delta)
                                    yield {"type": "text_delta", "delta": delta}

                            # Also handle content part deltas
                            elif event_type == "response.content_part.delta":
                                delta = event.get("delta", {})
                                if isinstance(delta, dict):
                                    text_val = delta.get("text", "")
                                else:
                                    text_val = str(delta)
                                if text_val:
                                    full_text.append(text_val)
                                    yield {"type": "text_delta", "delta": text_val}

            # Final done event
            output_text = "".join(full_text)
            logger.info(f"Stream completed: tools={len(tool_calls)}, text={len(output_text)} chars")

            yield {
                "type": "done",
                "response_id": response_id,
                "usage": usage,
                "tool_calls": tool_calls,
                "output": output_text,
            }
