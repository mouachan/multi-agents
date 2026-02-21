"""Pydantic schemas for orchestrator API."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CreateSessionRequest(BaseModel):
    agent_id: Optional[str] = Field(None, description="Pre-route to a specific agent")
    locale: Optional[str] = Field("fr", description="User locale (fr or en)")
    metadata: Optional[Dict[str, Any]] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    id: str
    agent_id: Optional[str] = None
    status: str
    welcome_message: str


class ChatMessageRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., min_length=1, description="User message")
    user_id: Optional[str] = None


class SuggestedAction(BaseModel):
    label: str
    action: str
    params: Optional[Dict[str, Any]] = None


class ToolCallInfo(BaseModel):
    name: str
    status: str = "completed"
    server_label: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatMessageResponse(BaseModel):
    session_id: str
    intent: str
    agent_id: Optional[str] = None
    message: str
    suggested_actions: List[SuggestedAction] = []
    entity_reference: Optional[Dict[str, Any]] = None
    tool_calls: List[ToolCallInfo] = []
    token_usage: Optional[TokenUsage] = None
    model_id: Optional[str] = None


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    agent_id: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    suggested_actions: Optional[List[Dict[str, Any]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    token_usage: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: List[MessageItem]
    total: int


class SessionSummary(BaseModel):
    session_id: str
    agent_id: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_message: Optional[str] = None


class SessionListResponse(BaseModel):
    sessions: List[SessionSummary]
    total: int


class SetPromptRequest(BaseModel):
    custom_prompt: str = Field(..., min_length=10, description="Custom system prompt")


class PromptResponse(BaseModel):
    prompt: str
    is_custom: bool
    agent_id: Optional[str] = None
