"""
A2A (Agent-to-Agent) Protocol Schemas.

Implements Google's A2A protocol for inter-agent communication.
Ref: https://google.github.io/A2A/
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# =============================================================================
# Agent Card (Discovery)
# =============================================================================

class AgentCapabilities(BaseModel):
    """Capabilities advertised by the agent."""
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


class Skill(BaseModel):
    """A skill that an agent can perform."""
    id: str
    name: str
    description: str
    tags: List[str] = []
    examples: List[str] = []


class AgentCard(BaseModel):
    """Agent Card for A2A discovery (/.well-known/agent.json)."""
    name: str
    url: str
    version: str = "1.0.0"
    description: str = ""
    capabilities: AgentCapabilities = AgentCapabilities()
    skills: List[Skill] = []
    defaultInputModes: List[str] = ["text/plain"]
    defaultOutputModes: List[str] = ["text/plain"]


# =============================================================================
# A2A Message Parts
# =============================================================================

class TextPart(BaseModel):
    """Text content part."""
    type: str = "text"
    text: str


class DataPart(BaseModel):
    """Structured data content part."""
    type: str = "data"
    data: Dict[str, Any]


Part = Union[TextPart, DataPart]


class A2AMessage(BaseModel):
    """A2A protocol message."""
    role: str  # "user" or "agent"
    parts: List[Part]


# =============================================================================
# A2A Task
# =============================================================================

class TaskStatus(BaseModel):
    """Status of an A2A task."""
    state: str  # "submitted", "working", "input-required", "completed", "failed", "canceled"
    message: Optional[A2AMessage] = None
    timestamp: Optional[str] = None


class Artifact(BaseModel):
    """Output artifact from a completed task."""
    name: Optional[str] = None
    description: Optional[str] = None
    parts: List[Part]
    index: int = 0


class Task(BaseModel):
    """A2A task representation."""
    id: str
    sessionId: Optional[str] = None
    status: TaskStatus
    artifacts: List[Artifact] = []
    history: List[A2AMessage] = []
    metadata: Dict[str, Any] = {}


# =============================================================================
# JSON-RPC 2.0 Request/Response
# =============================================================================

class TaskSendParams(BaseModel):
    """Parameters for tasks/send method."""
    id: str
    sessionId: Optional[str] = None
    message: A2AMessage
    acceptedOutputModes: List[str] = ["text/plain"]
    metadata: Dict[str, Any] = {}


class TaskGetParams(BaseModel):
    """Parameters for tasks/get method."""
    id: str
    historyLength: Optional[int] = None


class A2ARequest(BaseModel):
    """JSON-RPC 2.0 request for A2A protocol."""
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str
    params: Dict[str, Any] = {}


class A2ASuccessResponse(BaseModel):
    """JSON-RPC 2.0 success response."""
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Any


class A2AErrorResponse(BaseModel):
    """JSON-RPC 2.0 error response."""
    jsonrpc: str = "2.0"
    id: Union[str, int, None]
    error: Dict[str, Any]
