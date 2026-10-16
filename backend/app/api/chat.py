"""Chat API (app/services/chat).

    GET    /api/v1/chat/agents                           the agent profiles the user may talk to
    GET    /api/v1/chat/tool-display                     labels and colors of the MCP tools in the UI
    POST   /api/v1/chat/sessions                         new conversation       {agent_id?, locale}
    GET    /api/v1/chat/sessions                         the user's conversations
    DELETE /api/v1/chat/sessions                         delete them all
    GET    /api/v1/chat/sessions/<id>/messages           the messages of a conversation
    POST   /api/v1/chat/sessions/<id>/messages           send a message; the answer streams as server-sent events
    DELETE /api/v1/chat/sessions/<id>
    GET    /api/v1/chat/sessions/<id>/prompt             the prompt of the conversation's agent profile
    PUT    /api/v1/chat/sessions/<id>/prompt             override it for this conversation   {prompt}
    DELETE /api/v1/chat/sessions/<id>/prompt             back to the MLflow version

Conversations are private: a user lists and opens their own (an administrator can open any by its id).
"""
import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import get_profile, profiles_for_domains
from app.core.auth import User, current_user
from app.core.database import get_db
from app.models.conversation import ChatSession
from app.services.chat import prompts, sessions
from app.services.chat.config import tool_display
from app.services.chat.turn import chat_turn

router = APIRouter()

# A streamed answer can stay silent while the model thinks or the guardrails hold it: an event every
# HEARTBEAT_SECONDS keeps the connection open (cloud load balancers close it after ~60 s of silence)
HEARTBEAT_SECONDS = 10


class NewSession(BaseModel):
    agent_id: Optional[str] = None
    locale: str = "fr"


class Message(BaseModel):
    message: str


class Prompt(BaseModel):
    prompt: str


async def owned_session(session_id: str, user: User = Depends(current_user),
                        db: AsyncSession = Depends(get_db)) -> ChatSession:
    """The conversation, if it belongs to the user (404 otherwise, so other users' ids are not revealed)."""
    session = await sessions.get_session(db, session_id)
    if session is None or (sessions.owner_of(session) != user.username and not user.admin):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session


@router.get("/agents")
async def agents(user: User = Depends(current_user)):
    return [profile.to_api() for profile in profiles_for_domains(user.domains)]


@router.get("/tool-display")
async def tools_display():
    return tool_display()


@router.post("/sessions")
async def create_session(body: NewSession, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    profile = get_profile(body.agent_id)
    if body.agent_id and (profile is None or profile.domain not in user.domains):
        raise HTTPException(status_code=403, detail="Your profile has no access to this agent")
    return await sessions.create_session(db, user.username, body.agent_id, body.locale[:2])


@router.get("/sessions")
async def list_sessions(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    return await sessions.list_sessions(db, user.username)


@router.delete("/sessions")
async def delete_sessions(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    return {"deleted": await sessions.delete_sessions(db, user.username)}


@router.get("/sessions/{session_id}/messages")
async def messages(session: ChatSession = Depends(owned_session), db: AsyncSession = Depends(get_db)):
    return await sessions.session_messages(db, session)


@router.post("/sessions/{session_id}/messages")
async def send_message(body: Message, session: ChatSession = Depends(owned_session),
                       user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    async def stream():
        try:
            async for event in with_heartbeat(chat_turn(db, session, body.message, user)):
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.delete("/sessions/{session_id}")
async def delete_session(session: ChatSession = Depends(owned_session), db: AsyncSession = Depends(get_db)):
    await sessions.delete_session(db, session)
    return {"deleted": session.session_id}


@router.get("/sessions/{session_id}/prompt")
async def get_prompt(session: ChatSession = Depends(owned_session)):
    return await prompts.session_prompt(session)


@router.put("/sessions/{session_id}/prompt")
async def set_prompt(body: Prompt, session: ChatSession = Depends(owned_session), db: AsyncSession = Depends(get_db)):
    return await prompts.set_session_prompt(db, session, body.prompt)


@router.delete("/sessions/{session_id}/prompt")
async def reset_prompt(session: ChatSession = Depends(owned_session), db: AsyncSession = Depends(get_db)):
    return await prompts.set_session_prompt(db, session, None)


async def with_heartbeat(events: AsyncIterator[Dict[str, Any]]) -> AsyncIterator[Dict[str, Any]]:
    """The events, plus {"type": "heartbeat"} whenever nothing came for HEARTBEAT_SECONDS."""
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
