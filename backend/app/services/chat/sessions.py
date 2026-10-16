"""Chat conversations: create, list, read, delete. Each conversation belongs to the user who
created it (metadata "owner"); the API (app/api/chat.py) only shows a user their own."""
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import get_profile
from app.models.conversation import ChatMessage, ChatSession
from app.services.chat.config import welcome_message


async def get_session(db: AsyncSession, session_id: str) -> Optional[ChatSession]:
    return (await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))).scalar_one_or_none()


def owner_of(session: ChatSession) -> str:
    """The user who created the conversation ("" for conversations created before authentication)."""
    return (session.session_metadata or {}).get("owner", "")


async def create_session(db: AsyncSession, owner: str, profile_id: Optional[str], language: str) -> Dict[str, Any]:
    """A new conversation, optionally started with an agent profile, with its welcome message."""
    session = ChatSession(session_id=f"session_{uuid.uuid4().hex[:12]}", agent_id=profile_id,
                          status="active", session_metadata={"owner": owner})
    db.add(session)
    await db.flush()
    welcome = welcome_message(get_profile(profile_id), language)
    db.add(ChatMessage(session_id=session.id, role="assistant", content=welcome, agent_id="orchestrator"))
    await db.commit()
    return {"session_id": session.session_id, "agent_id": profile_id, "welcome_message": welcome}


async def list_sessions(db: AsyncSession, owner: Optional[str], limit: int = 50) -> List[Dict[str, Any]]:
    """The most recent conversations (of `owner`; all when None), with their last message."""
    query = select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit)
    if owner is not None:
        query = query.where(ChatSession.session_metadata["owner"].astext == owner)
    sessions = (await db.execute(query)).scalars().all()
    listed = []
    for session in sessions:
        last = (await db.execute(
            select(ChatMessage.content).where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.desc()).limit(1)
        )).scalar_one_or_none()
        listed.append({"session_id": session.session_id, "agent_id": session.agent_id,
                       "created_at": session.created_at, "updated_at": session.updated_at,
                       "last_message": (last or "")[:80]})
    return listed


async def session_messages(db: AsyncSession, session: ChatSession) -> List[Dict[str, Any]]:
    messages = (await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at)
    )).scalars().all()
    return [{"id": str(m.id), "role": m.role, "content": m.content, "agent_id": m.agent_id,
             "suggested_actions": m.suggested_actions, "tool_calls": m.tool_calls,
             "token_usage": m.token_usage, "model_id": m.model_id, "saved_trace": m.trace,
             "created_at": m.created_at} for m in messages]


async def delete_session(db: AsyncSession, session: ChatSession) -> None:
    await db.delete(session)
    await db.commit()


async def delete_sessions(db: AsyncSession, owner: Optional[str]) -> int:
    """Delete the conversations of `owner` (all when None); returns how many."""
    ids = select(ChatSession.id)
    if owner is not None:
        ids = ids.where(ChatSession.session_metadata["owner"].astext == owner)
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(ids)))
    result = await db.execute(delete(ChatSession).where(ChatSession.id.in_(ids)))
    await db.commit()
    return result.rowcount
