"""
Conversation models for orchestrator chat sessions and messages.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ChatSession(Base):
    """Chat session for orchestrator conversations."""

    __tablename__ = "chat_sessions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    agent_id = Column(String(50), index=True)
    status = Column(String(20), default="active", index=True)
    session_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    """Individual message in a chat session."""

    __tablename__ = "chat_messages"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    agent_id = Column(String(50))
    entity_id = Column(PG_UUID(as_uuid=True))
    entity_type = Column(String(50))
    suggested_actions = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
