"""
Pydantic schemas for Postal API requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.shared.schemas import ProcessingStepLog, utc_now


# =============================================================================
# Reclamation Schemas
# =============================================================================

class ReclamationBase(BaseModel):
    reclamation_number: str
    numero_suivi: str
    reclamation_type: Optional[str] = None
    client_nom: str
    client_email: Optional[str] = None
    client_telephone: Optional[str] = None
    description: Optional[str] = None
    document_path: Optional[str] = None


class ReclamationCreate(ReclamationBase):
    pass


class ReclamationUpdate(BaseModel):
    status: Optional[str] = None
    reclamation_metadata: Optional[Dict[str, Any]] = Field(
        default=None, serialization_alias="metadata"
    )


class ReclamationResponse(ReclamationBase):
    id: UUID
    status: str
    submitted_at: datetime
    processed_at: Optional[datetime] = None
    total_processing_time_ms: Optional[int] = None
    is_archived: bool = False
    valeur_declaree: Optional[float] = None
    reclamation_metadata: Dict[str, Any] = Field(
        default_factory=dict, serialization_alias="metadata"
    )
    agent_logs: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ReclamationListResponse(BaseModel):
    items: List[ReclamationResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# Processing Schemas
# =============================================================================

class ProcessReclamationRequest(BaseModel):
    workflow_type: str = Field(
        default="standard",
        description="Workflow type: standard, expedited, manual_review"
    )
    skip_ocr: bool = False
    enable_rag: bool = True


class ProcessReclamationResponse(BaseModel):
    reclamation_id: UUID
    status: str
    message: str
    processing_started_at: datetime


class ReclamationStatusResponse(BaseModel):
    reclamation_id: UUID
    status: str
    current_step: Optional[str] = None
    progress_percentage: float
    processing_steps: List[ProcessingStepLog]
    estimated_completion_time: Optional[datetime] = None


class ReclamationLogsResponse(BaseModel):
    reclamation_id: UUID
    logs: List[ProcessingStepLog]


# =============================================================================
# Decision Schemas
# =============================================================================

class ReclamationDecisionResponse(BaseModel):
    id: UUID
    reclamation_id: UUID
    decision: str
    confidence: float
    reasoning: str
    initial_decision: Optional[str] = None
    initial_confidence: Optional[float] = None
    initial_reasoning: Optional[str] = None
    llm_model: Optional[str] = None
    requires_manual_review: bool
    decided_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


# =============================================================================
# Statistics Schemas
# =============================================================================

class ReclamationStatisticsResponse(BaseModel):
    total: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    avg_processing_time_ms: Optional[float] = None


# =============================================================================
# Tracking Schemas
# =============================================================================

class TrackingEventResponse(BaseModel):
    id: UUID
    numero_suivi: str
    event_type: str
    event_date: datetime
    location: Optional[str] = None
    detail: Optional[str] = None
    code_postal: Optional[str] = None
    is_final: bool
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, validation_alias="event_metadata"
    )

    model_config = {"from_attributes": True, "populate_by_name": True}


# =============================================================================
# Error Schemas
# =============================================================================

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)
