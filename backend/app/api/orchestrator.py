"""
Orchestrator API endpoints.

- POST /sessions          - Create a session (optionally pre-routed)
- POST /chat              - Send a message
- GET  /sessions/{id}/messages - Get session history
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.orchestrator_schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    SessionListResponse,
    SessionMessagesResponse,
    SessionSummary,
    MessageItem,
)
from app.core.database import get_db
from app.services.agents.orchestrator_service import OrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter()

orchestrator_service = OrchestratorService()


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    try:
        result = await orchestrator_service.create_session(
            db=db,
            agent_id=request.agent_id,
            metadata=request.metadata,
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
):
    """Send a message and get agent response."""
    try:
        result = await orchestrator_service.process_message(
            db=db,
            session_id=request.session_id,
            message=request.message,
            user_id=request.user_id,
        )
        return ChatMessageResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions."""
    try:
        sessions = await orchestrator_service.list_sessions(db)
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
):
    """Delete all chat sessions and their messages."""
    try:
        count = await orchestrator_service.delete_all_sessions(db)
        return {"status": "deleted", "count": count}
    except Exception as e:
        logger.error(f"Error deleting all sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
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


@router.get("/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages(
    session_id: str,
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
