"""
Orchestrator API endpoints.

- POST /sessions          - Create a session (optionally pre-routed)
- POST /chat              - Send a message
- POST /chat/stream       - Send a message with SSE streaming
- GET  /sessions/{id}/messages - Get session history
"""
import asyncio
import json
import logging
import time
from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.orchestrator.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    PromptResponse,
    SessionListResponse,
    SessionMessagesResponse,
    SessionSummary,
    SetPromptRequest,
    MessageItem,
)
from app.core.auth import User, agent_domain, current_user
from app.core.config import settings
from app.core.database import get_db
from app.services.agents.orchestrator_service import OrchestratorService
from app.services.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)

router = APIRouter()

orchestrator_service = OrchestratorService()


async def _check_owner(db: AsyncSession, session_id: str, user: User) -> None:
    """Sessions are private: the owner (or an administrator) only. 404 otherwise."""
    owner = await orchestrator_service.session_owner(db, session_id)
    if owner is None or (settings.auth_enabled and owner != user.username and not user.admin):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")


async def owned_session(session_id: str, user: User = Depends(current_user),
                        db: AsyncSession = Depends(get_db)) -> str:
    """Dependency for the /sessions/{session_id}/... routes."""
    await _check_owner(db, session_id, user)
    return session_id

# Keep idle SSE streams alive (cloud load balancers close connections idle for ~60s
# while the model generates or the guardrails hold the answer)
HEARTBEAT_SECONDS = 10


async def with_heartbeat(events: AsyncIterator[Dict[str, Any]]) -> AsyncIterator[Dict[str, Any]]:
    """Yield the events, plus {"type": "heartbeat"} whenever nothing came for HEARTBEAT_SECONDS."""
    start = time.time()
    iterator = events.__aiter__()
    pending = asyncio.ensure_future(iterator.__anext__())
    try:
        while True:
            done, _ = await asyncio.wait({pending}, timeout=HEARTBEAT_SECONDS)
            if not done:
                yield {"type": "heartbeat", "elapsed_ms": int((time.time() - start) * 1000)}
                continue
            try:
                event = pending.result()
            except StopAsyncIteration:
                return
            yield event
            pending = asyncio.ensure_future(iterator.__anext__())
    finally:
        if not pending.done():
            pending.cancel()


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Create a new chat session owned by the user (with an agent they may use)."""
    if settings.auth_enabled and request.agent_id:
        agent_def = AgentRegistry.get(request.agent_id)
        if agent_def and agent_domain(agent_def.a2a_url) not in user.domains:
            raise HTTPException(status_code=403, detail="Your profile has no access to this agent")
    try:
        result = await orchestrator_service.create_session(
            db=db,
            agent_id=request.agent_id,
            metadata={**(request.metadata or {}), "owner": user.username},
            locale=request.locale,
        )
        return CreateSessionResponse(**result)
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Send a message and get agent response."""
    await _check_owner(db, request.session_id, user)
    try:
        result = await orchestrator_service.process_message(
            db=db,
            session_id=request.session_id,
            message=request.message,
            user=user,
        )
        return ChatMessageResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def send_message_stream(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Send a message and stream the agent response via SSE."""
    await _check_owner(db, request.session_id, user)

    async def event_generator():
        try:
            async for event in with_heartbeat(orchestrator_service.process_message_stream(
                db=db,
                session_id=request.session_id,
                message=request.message,
                user=user,
            )):
                yield f"data: {json.dumps(event)}\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """List the user's chat sessions."""
    try:
        sessions = await orchestrator_service.list_sessions(
            db, owner=user.username if settings.auth_enabled else None)
        return SessionListResponse(
            sessions=[SessionSummary(**s) for s in sessions],
            total=len(sessions),
        )
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions")
async def delete_all_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Delete the user's chat sessions and their messages."""
    try:
        count = await orchestrator_service.delete_all_sessions(
            db, owner=user.username if settings.auth_enabled else None)
        return {"status": "deleted", "count": count}
    except Exception as e:
        logger.error(f"Error deleting all sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str = Depends(owned_session),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session and its messages."""
    try:
        await orchestrator_service.delete_session(db, session_id)
        return {"status": "deleted", "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/prompt", response_model=PromptResponse)
async def get_session_prompt(
    session_id: str = Depends(owned_session),
    db: AsyncSession = Depends(get_db),
):
    """Get the effective prompt for a session."""
    try:
        result = await orchestrator_service.get_session_prompt(db, session_id)
        return PromptResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sessions/{session_id}/prompt", response_model=PromptResponse)
async def set_session_prompt(
    request: SetPromptRequest,
    session_id: str = Depends(owned_session),
    db: AsyncSession = Depends(get_db),
):
    """Set a custom prompt for this session."""
    try:
        result = await orchestrator_service.set_session_prompt(
            db, session_id, request.custom_prompt
        )
        return PromptResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting session prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}/prompt", response_model=PromptResponse)
async def reset_session_prompt(
    session_id: str = Depends(owned_session),
    db: AsyncSession = Depends(get_db),
):
    """Reset to default prompt."""
    try:
        result = await orchestrator_service.reset_session_prompt(db, session_id)
        return PromptResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error resetting session prompt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages(
    session_id: str = Depends(owned_session),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages for a session."""
    try:
        messages = await orchestrator_service.get_session_messages(db, session_id)
        return SessionMessagesResponse(
            session_id=session_id,
            messages=[MessageItem(**m) for m in messages],
            total=len(messages),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
