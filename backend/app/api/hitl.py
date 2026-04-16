"""
Human-in-the-Loop (HITL) WebSocket API for real-time entity review.

Domain-agnostic: works for claims, tenders, and any future entity type
registered in AgentRegistry with HITL metadata.

WebSocket endpoints:
- /ws/review/{entity_type}/{entity_id}  - Join a review room for a specific entity

REST endpoints:
- POST /{entity_type}/{entity_id}/action     - Submit a review decision (approve/reject/comment)
- POST /{entity_type}/{entity_id}/ask-agent  - Ask agent a question (conversational HITL)
- GET  /{entity_type}/{entity_id}/messages   - Get review chat history
- GET  /active                               - Get list of active review sessions
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.api import schemas
from app.core.config import settings
from app.core.database import get_db
from app.services.agents.registry import AgentRegistry
from app.services.agent.reviewer import ReviewService
from app.services.agent.context_builder import ContextBuilder

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
review_service = ReviewService()
context_builder = ContextBuilder()


# =============================================================================
# Helpers
# =============================================================================

async def resolve_entity(entity_type: str, entity_id: UUID, db: AsyncSession):
    """Resolve an entity and its agent definition from the registry."""
    agent_def = AgentRegistry.get_by_entity_type(entity_type)
    if not agent_def or "hitl_model" not in agent_def.metadata:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")
    model = agent_def.metadata["hitl_model"]
    result = await db.execute(select(model).where(model.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_type.capitalize()} not found")
    return entity, agent_def


async def build_entity_context(entity, entity_type, entity_id, agent_def, db):
    """Build context dict from any entity via column introspection + OCR."""
    entity_data = {}
    for col in entity.__table__.columns:
        val = getattr(entity, col.name, None)
        if val is not None:
            entity_data[col.name] = str(val) if not isinstance(val, (str, int, float, bool)) else val

    # Load OCR from related document
    doc_model = agent_def.metadata["hitl_document_model"]
    fk = agent_def.metadata["hitl_fk_field"]
    doc_result = await db.execute(
        select(doc_model)
        .where(getattr(doc_model, fk) == entity_id)
        .order_by(doc_model.created_at.desc())
        .limit(1)
    )
    doc = doc_result.scalar_one_or_none()
    if doc:
        entity_data["ocr_data"] = context_builder.extract_ocr_context(
            {"raw_ocr_text": doc.raw_ocr_text, "structured_data": doc.structured_data}
        )

    return entity_data


# =============================================================================
# WebSocket Connection Manager
# =============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections for HITL review sessions.

    Features:
    - Multiple reviewers can join the same entity room
    - Presence tracking (who's currently reviewing)
    - Broadcast messages to all reviewers in a room
    """

    def __init__(self):
        # room_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> reviewer info
        self.reviewer_info: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, room_id: str, reviewer_id: str, reviewer_name: str):
        """Add a new reviewer to a review room."""
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()

        self.active_connections[room_id].add(websocket)
        self.reviewer_info[websocket] = {
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "room_id": room_id,
            "joined_at": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"Reviewer {reviewer_name} joined review room {room_id}")

        # Notify other reviewers
        await self.broadcast(room_id, {
            "type": "reviewer_joined",
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, exclude=websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a reviewer from their review room."""
        if websocket not in self.reviewer_info:
            return

        info = self.reviewer_info[websocket]
        room_id = info["room_id"]
        reviewer_name = info["reviewer_name"]

        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)

            # Clean up empty rooms
            if len(self.active_connections[room_id]) == 0:
                del self.active_connections[room_id]

        del self.reviewer_info[websocket]
        logger.info(f"Reviewer {reviewer_name} left review room {room_id}")

    async def broadcast(self, room_id: str, message: dict, exclude: WebSocket = None):
        """Send a message to all reviewers in a room."""
        if room_id not in self.active_connections:
            return

        message_json = json.dumps(message)

        dead_connections = set()
        for connection in self.active_connections[room_id]:
            if connection == exclude:
                continue

            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Failed to send message to reviewer: {e}")
                dead_connections.add(connection)

        for connection in dead_connections:
            self.disconnect(connection)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific reviewer."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    def get_reviewers(self, room_id: str) -> list:
        """Get list of active reviewers for a room."""
        if room_id not in self.active_connections:
            return []

        reviewers = []
        for ws in self.active_connections[room_id]:
            if ws in self.reviewer_info:
                info = self.reviewer_info[ws]
                reviewers.append({
                    "reviewer_id": info["reviewer_id"],
                    "reviewer_name": info["reviewer_name"],
                    "joined_at": info["joined_at"]
                })

        return reviewers


# Global connection manager
manager = ConnectionManager()


# =============================================================================
# Pydantic Models
# =============================================================================

class ReviewAction(BaseModel):
    """Review action submitted by a reviewer."""
    action: str  # "approve", "reject", "comment", "request_info"
    comment: str = ""
    reviewer_id: str
    reviewer_name: str


class ReviewMessage(BaseModel):
    """Chat message in review session."""
    message: str
    reviewer_id: str
    reviewer_name: str


# =============================================================================
# WebSocket Endpoint
# =============================================================================

@router.websocket("/ws/review/{entity_type}/{entity_id}")
async def websocket_review_endpoint(
    websocket: WebSocket,
    entity_type: str,
    entity_id: UUID,
    reviewer_id: str = "agent_001",
    reviewer_name: str = "Agent Smith"
):
    """
    WebSocket endpoint for real-time entity review.

    Query params:
    - reviewer_id: Unique identifier for the reviewer
    - reviewer_name: Display name for the reviewer

    Message types sent by server:
    - reviewer_joined: Another reviewer joined the room
    - reviewer_left: A reviewer left the room
    - chat_message: Someone sent a chat message
    - action_taken: Someone approved/rejected/commented
    - entity_updated: Entity status was updated

    Message types sent by client:
    - chat: Send a chat message
    - action: Submit a review action
    """
    room_id = f"{entity_type}:{entity_id}"

    await manager.connect(websocket, room_id, reviewer_id, reviewer_name)

    try:
        # Send initial state
        reviewers = manager.get_reviewers(room_id)
        await manager.send_personal(websocket, {
            "type": "connected",
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "active_reviewers": reviewers,
            "message": f"Connected to review room for {entity_type} {entity_id}"
        })

        # Listen for messages
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "chat":
                    await manager.broadcast(room_id, {
                        "type": "chat_message",
                        "reviewer_id": reviewer_id,
                        "reviewer_name": reviewer_name,
                        "message": message.get("message", ""),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                elif message_type == "action":
                    action = message.get("action")
                    comment = message.get("comment", "")

                    await manager.broadcast(room_id, {
                        "type": "action_taken",
                        "reviewer_id": reviewer_id,
                        "reviewer_name": reviewer_name,
                        "action": action,
                        "comment": comment,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, exclude=websocket)

                    await manager.send_personal(websocket, {
                        "type": "action_acknowledged",
                        "action": action,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                elif message_type == "ping":
                    await manager.send_personal(websocket, {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await manager.send_personal(websocket, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)

        await manager.broadcast(room_id, {
            "type": "reviewer_left",
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)


# =============================================================================
# REST Endpoints
# =============================================================================

@router.post("/{entity_type}/{entity_id}/action")
async def submit_review_action(
    entity_type: str,
    entity_id: UUID,
    action: ReviewAction,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a review action (approve/reject/comment).

    This endpoint is an alternative to WebSocket for submitting actions.
    It also broadcasts the action via WebSocket to active reviewers.
    """
    try:
        entity, agent_def = await resolve_entity(entity_type, entity_id, db)

        # Process action using review service
        updated_entity, updated_decision = await review_service.process_action(
            db=db,
            action=action.action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            reviewer_id=action.reviewer_id,
            reviewer_name=action.reviewer_name,
            comment=action.comment
        )

        room_id = f"{entity_type}:{entity_id}"

        # Broadcast action via WebSocket
        await manager.broadcast(room_id, {
            "type": "entity_updated",
            "entity_type": entity_type,
            "action": action.action,
            "reviewer_id": action.reviewer_id,
            "reviewer_name": action.reviewer_name,
            "comment": action.comment,
            "new_status": updated_entity.status.value if hasattr(updated_entity.status, 'value') else updated_entity.status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        logger.info(f"Review action '{action.action}' by {action.reviewer_name} on {entity_type} {entity_id}")

        return {
            "success": True,
            "entity_id": str(entity_id),
            "entity_type": entity_type,
            "action": action.action,
            "new_status": updated_entity.status.value if hasattr(updated_entity.status, 'value') else updated_entity.status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing review action: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_type}/{entity_id}/messages")
async def get_review_messages(
    entity_type: str,
    entity_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat/action history for an entity review session.

    Returns messages from agent_logs that are review-related.
    """
    entity, agent_def = await resolve_entity(entity_type, entity_id, db)

    # Extract review messages from agent_logs
    messages = []
    if entity.agent_logs:
        i = 0
        while i < len(entity.agent_logs):
            log = entity.agent_logs[i]

            # Group reviewer_question + agent_answer into qa_exchange
            if log.get("type") == "reviewer_question":
                answer_log = None
                if i + 1 < len(entity.agent_logs) and entity.agent_logs[i + 1].get("type") == "agent_answer":
                    answer_log = entity.agent_logs[i + 1]
                    i += 1

                messages.append({
                    "type": "qa_exchange",
                    "timestamp": log.get("timestamp"),
                    "reviewer_id": log.get("reviewer_id"),
                    "reviewer_name": log.get("reviewer_name"),
                    "message": log.get("message"),
                    "answer": answer_log.get("message") if answer_log else "No response received from agent."
                })
            elif log.get("type") in ["comment", "request_info"]:
                messages.append({
                    "timestamp": log.get("timestamp"),
                    "reviewer_id": log.get("reviewer_id"),
                    "reviewer_name": log.get("reviewer_name"),
                    "type": log.get("type"),
                    "message": log.get("message")
                })

            i += 1

    return {
        "entity_id": str(entity_id),
        "entity_type": entity_type,
        "messages": messages,
        "total": len(messages)
    }


@router.get("/active")
async def get_active_reviews():
    """
    Get list of active review sessions.

    Returns entities that currently have reviewers connected.
    """
    active_sessions = []

    for room_id, connections in manager.active_connections.items():
        if len(connections) > 0:
            reviewers = manager.get_reviewers(room_id)
            # Parse room_id "entity_type:entity_id"
            parts = room_id.split(":", 1)
            entity_type = parts[0] if len(parts) == 2 else "unknown"
            entity_id = parts[1] if len(parts) == 2 else room_id
            active_sessions.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "room_id": room_id,
                "reviewer_count": len(reviewers),
                "reviewers": reviewers
            })

    return {
        "active_sessions": active_sessions,
        "total": len(active_sessions)
    }


# =============================================================================
# Utility function for triggering HITL from processing pipelines
# =============================================================================

async def notify_manual_review_required(entity_type: str, entity_id: UUID, reason: str):
    """
    Notify all connected reviewers that an entity requires manual review.

    Call this from processing endpoints when decision = "manual_review" / "a_approfondir".
    """
    room_id = f"{entity_type}:{entity_id}"
    await manager.broadcast(room_id, {
        "type": "manual_review_required",
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    logger.info(f"Notified reviewers: Manual review required for {entity_type} {entity_id}")


# =============================================================================
# POST /{entity_type}/{entity_id}/ask-agent - Conversational HITL with Agent
# =============================================================================

@router.post("/{entity_type}/{entity_id}/ask-agent", response_model=schemas.AskAgentResponse)
async def ask_agent(
    entity_type: str,
    entity_id: UUID,
    request: schemas.AskAgentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask the LlamaStack agent a question about an entity in manual review.

    This enables conversational HITL where reviewers can ask for clarifications
    before making a decision. Each Q&A is logged in agent_logs for audit trail.

    Only available for entities in 'manual_review' or 'pending_info' status.
    """
    try:
        entity, agent_def = await resolve_entity(entity_type, entity_id, db)

        # Verify entity is in manual review
        status_val = entity.status.value if hasattr(entity.status, 'value') else entity.status
        if status_val not in ["manual_review", "pending_info"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot ask agent - {entity_type} status is '{status_val}'. Must be 'manual_review' or 'pending_info'."
            )

        logger.info(f"Reviewer {request.reviewer_name} asking agent about {entity_type} {entity_id}: {request.question}")

        # Build generic context via introspection
        entity_data = await build_entity_context(entity, entity_type, entity_id, agent_def, db)

        # Build review context
        context = context_builder.build_review_context(
            entity_type=entity_type,
            entity_id=str(entity_id),
            entity_data=entity_data
        )

        # Add reviewer question to context
        full_question = f"{context}\n\n**Reviewer Question:** {request.question}"

        # Create temporary agent and ask question
        answer = await review_service.ask_agent_standalone(
            question=full_question,
            agent_config={
                "model": settings.llamastack_default_model,
                "instructions": agent_def.instructions,
                "enable_session_persistence": False,
                "sampling_params": {
                    "strategy": {"type": "greedy"},
                    "max_tokens": 1024
                }
            }
        )

        logger.info(f"Agent response ({len(answer)} chars): {answer[:200]}...")

        # Save Q&A to agent_logs
        timestamp = datetime.now(timezone.utc)
        if not entity.agent_logs:
            entity.agent_logs = []

        entity.agent_logs.extend([
            {
                "type": "reviewer_question",
                "timestamp": timestamp.isoformat(),
                "reviewer_id": request.reviewer_id,
                "reviewer_name": request.reviewer_name,
                "message": request.question
            },
            {
                "type": "agent_answer",
                "timestamp": timestamp.isoformat(),
                "message": answer
            }
        ])
        flag_modified(entity, "agent_logs")
        await db.commit()

        logger.info(f"Saved Q&A to agent_logs for {entity_type} {entity_id}")

        room_id = f"{entity_type}:{entity_id}"

        # Broadcast Q&A via WebSocket
        await manager.broadcast(room_id, {
            "type": "qa_exchange",
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "question": request.question,
            "answer": answer,
            "reviewer_id": request.reviewer_id,
            "reviewer_name": request.reviewer_name,
            "timestamp": timestamp.isoformat()
        })

        return schemas.AskAgentResponse(
            success=True,
            entity_id=str(entity_id),
            entity_type=entity_type,
            question=request.question,
            answer=answer,
            timestamp=timestamp
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ask-agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
