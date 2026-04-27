"""
Pydantic schemas for Tender (Appels d'Offres) API requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.shared.schemas import DecisionResponseBase, ProcessingStepLog


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

class TenderDecisionResponse(DecisionResponseBase):
    tender_id: UUID
    # Supporting data (JSONB - can be dict or list)
    risk_analysis: Optional[Any] = None
    similar_references: Optional[Any] = None
    historical_ao_analysis: Optional[Any] = None
    internal_capabilities: Optional[Any] = None


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
    pending_info_tenders: int = 0
    average_processing_time_ms: Optional[float] = None
