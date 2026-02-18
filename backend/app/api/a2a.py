"""
A2A (Agent-to-Agent) Protocol Endpoints.

Implements Google's A2A protocol for inter-agent communication:
- GET /.well-known/agent.json - Agent Card discovery
- POST /api/v1/a2a/{agent_id} - JSON-RPC 2.0 task handling
"""

import logging
import uuid
from typing import Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.agents.registry import AgentRegistry
from app.services.agent.responses_orchestrator import ResponsesOrchestrator
from .a2a_schemas import (
    AgentCard,
    AgentCapabilities,
    Skill,
    A2ARequest,
    A2AMessage,
    TextPart,
    Task,
    TaskStatus,
    Artifact,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory task store (for demo; production would use DB)
_tasks: Dict[str, Task] = {}

# Shared orchestrator instance
_orchestrator = None


def _get_orchestrator() -> ResponsesOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ResponsesOrchestrator()
    return _orchestrator


# =============================================================================
# Agent Card Discovery
# =============================================================================

@router.get("/.well-known/agent.json")
async def agent_card(request: Request):
    """Return the A2A Agent Card for service discovery."""
    agents = AgentRegistry.list_agents()

    skills = [
        Skill(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            tags=[agent.entity_type, agent.color],
            examples=[],
        )
        for agent in agents
    ]

    base_url = str(request.base_url).rstrip("/")

    card = AgentCard(
        name=settings.app_name,
        url=f"{base_url}{settings.api_v1_prefix}/a2a",
        version=settings.app_version,
        description="Multi-Agent AI Platform with Claims and Tenders agents",
        capabilities=AgentCapabilities(
            streaming=False,
            pushNotifications=False,
        ),
        skills=skills,
    )

    return card.model_dump()


# =============================================================================
# JSON-RPC 2.0 Task Endpoint
# =============================================================================

@router.post("/{agent_id}")
async def handle_a2a_request(agent_id: str, request: Request):
    """
    Handle A2A JSON-RPC 2.0 requests for a specific agent.

    Supported methods:
    - tasks/send: Send a task to the agent
    - tasks/get: Get task status and results
    """
    try:
        body = await request.json()
        rpc_request = A2ARequest(**body)
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
        }, status_code=400)

    # Validate agent exists
    agent_def = AgentRegistry.get(agent_id)
    if not agent_def:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_request.id,
            "error": {
                "code": -32602,
                "message": f"Unknown agent: {agent_id}. Available: {[a.id for a in AgentRegistry.list_agents()]}"
            }
        }, status_code=404)

    # Route to method handler
    if rpc_request.method == "tasks/send":
        return await _handle_task_send(rpc_request, agent_id, agent_def)
    elif rpc_request.method == "tasks/get":
        return await _handle_task_get(rpc_request)
    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_request.id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {rpc_request.method}. Supported: tasks/send, tasks/get"
            }
        })


async def _handle_task_send(rpc_request: A2ARequest, agent_id: str, agent_def) -> JSONResponse:
    """Handle tasks/send - execute a task with the specified agent."""
    params = rpc_request.params
    task_id = params.get("id", str(uuid.uuid4()))

    # Extract message text from parts
    message_parts = params.get("message", {}).get("parts", [])
    message_text = ""
    for part in message_parts:
        if part.get("type") == "text":
            message_text += part.get("text", "")

    if not message_text:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_request.id,
            "error": {"code": -32602, "message": "No text content in message"}
        })

    # Create task in "working" state
    task = Task(
        id=task_id,
        status=TaskStatus(state="working"),
        history=[A2AMessage(role="user", parts=[TextPart(text=message_text)])],
    )
    _tasks[task_id] = task

    try:
        # Call the LLM via Responses API with the agent's MCP tools
        orchestrator = _get_orchestrator()
        result = await orchestrator.process_with_agent(
            agent_config={
                "model": settings.llamastack_default_model,
                "instructions": agent_def.instructions,
            },
            input_message=message_text,
            tools=agent_def.tools,
        )

        output_text = result.get("output", "")
        tool_calls = result.get("tool_calls", [])

        # Build artifacts
        artifacts = [
            Artifact(
                parts=[TextPart(text=output_text)],
                index=0,
            )
        ]

        # Add tool call data as a data artifact if tools were used
        if tool_calls:
            from .a2a_schemas import DataPart
            artifacts.append(
                Artifact(
                    name="tool_calls",
                    description="MCP tool calls executed during processing",
                    parts=[DataPart(data={"tool_calls": tool_calls})],
                    index=1,
                )
            )

        # Update task to completed
        task.status = TaskStatus(state="completed")
        task.artifacts = artifacts
        task.history.append(
            A2AMessage(role="agent", parts=[TextPart(text=output_text)])
        )

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_request.id,
            "result": task.model_dump(),
        })

    except Exception as e:
        logger.error(f"A2A task failed: {e}", exc_info=True)

        task.status = TaskStatus(
            state="failed",
            message=A2AMessage(role="agent", parts=[TextPart(text=str(e))]),
        )

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_request.id,
            "result": task.model_dump(),
        })


async def _handle_task_get(rpc_request: A2ARequest) -> JSONResponse:
    """Handle tasks/get - retrieve task status."""
    task_id = rpc_request.params.get("id")

    if not task_id or task_id not in _tasks:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_request.id,
            "error": {"code": -32602, "message": f"Task not found: {task_id}"}
        })

    task = _tasks[task_id]

    # Apply history length limit if requested
    history_length = rpc_request.params.get("historyLength")
    task_data = task.model_dump()
    if history_length is not None:
        task_data["history"] = task_data["history"][-history_length:]

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": rpc_request.id,
        "result": task_data,
    })
