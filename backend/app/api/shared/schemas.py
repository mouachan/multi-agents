"""Schemas partagés entre tous les domaines."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class ProcessingStepLog(BaseModel):
    """Log d'étape de processing (utilisé par les 3 domaines)."""
    step_name: str
    agent_name: str
    status: str
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class DecisionResponseBase(BaseModel):
    """Champs communs à toutes les décisions (claims, tenders, reclamations)."""
    id: UUID
    initial_decision: str
    initial_confidence: Optional[float] = None
    initial_reasoning: Optional[str] = None
    initial_decided_at: Optional[datetime] = None
    final_decision: Optional[str] = None
    final_decision_by: Optional[str] = None
    final_decision_by_name: Optional[str] = None
    final_decision_at: Optional[datetime] = None
    final_decision_notes: Optional[str] = None
    decision: str
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    llm_model: Optional[str] = None
    requires_manual_review: bool
    decided_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}
