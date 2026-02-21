"""
LlamaStack Responses API orchestrator.

Handles stateful multi-turn conversations via previous_response_id
with automatic MCP tool execution.
"""
import httpx
import json
import logging
import re
from typing import Dict, Any, List, Optional

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
