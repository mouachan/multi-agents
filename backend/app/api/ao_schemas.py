"""
Pydantic schemas for Tender (Appels d'Offres) API requests and responses.

Follows the same patterns as schemas.py for consistency.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.schemas import ProcessingStepLog


# =============================================================================
# Tender Schemas
# =============================================================================

class TenderBase(BaseModel):
    entity_id: str
    tender_number: str
    tender_type: Optional[str] = None
    document_path: str


class TenderCreate(TenderBase):
    pass


class TenderResponse(TenderBase):
    id: UUID
    status: str
    submitted_at: datetime
    processed_at: Optional[datetime] = None
    total_processing_time_ms: Optional[int] = None
    is_archived: bool = False
    tender_metadata: Dict[str, Any] = Field(
        default_factory=dict, serialization_alias="metadata"
    )
    agent_logs: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="HITL review logs and chat messages"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class TenderListResponse(BaseModel):
    tenders: List[TenderResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# Processing Schemas
# =============================================================================

class ProcessTenderRequest(BaseModel):
    workflow_type: str = Field(
        default="standard",
        description="Workflow type: standard, expedited, manual_review"
    )
    skip_ocr: bool = False
    enable_rag: bool = True


class ProcessTenderResponse(BaseModel):
    tender_id: UUID
    status: str
    message: str
    processing_started_at: datetime


class TenderStatusResponse(BaseModel):
    tender_id: UUID
    status: str
    current_step: Optional[str] = None
    progress_percentage: float
    processing_steps: List[ProcessingStepLog]
    estimated_completion_time: Optional[datetime] = None


class TenderLogsResponse(BaseModel):
    tender_id: UUID
    logs: List[ProcessingStepLog]


# =============================================================================
# Decision Schemas
# =============================================================================

class TenderDecisionResponse(BaseModel):
    id: UUID
    tender_id: UUID
    # Initial system decision
    initial_decision: str
    initial_confidence: Optional[float] = None
    initial_reasoning: Optional[str] = None
    initial_decided_at: Optional[datetime] = None
    # Final reviewer decision
    final_decision: Optional[str] = None
    final_decision_by: Optional[str] = None
    final_decision_by_name: Optional[str] = None
    final_decision_at: Optional[datetime] = None
    final_decision_notes: Optional[str] = None
    # Legacy fields for backwards compatibility
    decision: str
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    # Supporting data (JSONB - can be dict or list)
    risk_analysis: Optional[Any] = None
    similar_references: Optional[Any] = None
    historical_ao_analysis: Optional[Any] = None
    internal_capabilities: Optional[Any] = None
    llm_model: Optional[str] = None
    requires_manual_review: bool
    decided_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Statistics Schemas
# =============================================================================

class TenderStatistics(BaseModel):
    total_tenders: int
    pending_tenders: int
    processing_tenders: int
    completed_tenders: int
    failed_tenders: int
    manual_review_tenders: int
    average_processing_time_ms: Optional[float] = None
