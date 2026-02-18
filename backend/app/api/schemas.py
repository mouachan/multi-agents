"""
Pydantic schemas for API requests and responses.

FIXES APPLIED:
- Replaced datetime.utcnow with timezone-aware datetime
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Helper for timezone-aware default
# =============================================================================

def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# =============================================================================
# Claims Schemas
# =============================================================================

class ClaimBase(BaseModel):
    user_id: str
    claim_number: str
    claim_type: Optional[str] = None
    document_path: str


class ClaimCreate(ClaimBase):
    pass


class ClaimUpdate(BaseModel):
    status: Optional[str] = None
    claim_metadata: Optional[Dict[str, Any]] = Field(
        default=None, serialization_alias="metadata"
    )


class ClaimResponse(ClaimBase):
    id: UUID
    status: str
    submitted_at: datetime
    processed_at: Optional[datetime] = None
    total_processing_time_ms: Optional[int] = None
    is_archived: bool = False
    claim_metadata: Dict[str, Any] = Field(
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


class ClaimListResponse(BaseModel):
    claims: List[ClaimResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# Processing Schemas
# =============================================================================

class ProcessClaimRequest(BaseModel):
    workflow_type: str = Field(
        default="standard",
        description="Workflow type: standard, expedited, manual_review"
    )
    skip_ocr: bool = False
    skip_guardrails: bool = False
    enable_rag: bool = True


class ProcessingStepLog(BaseModel):
    step_name: str
    agent_name: str
    status: str
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ProcessClaimResponse(BaseModel):
    claim_id: UUID
    status: str
    message: str
    processing_started_at: datetime


class ClaimStatusResponse(BaseModel):
    claim_id: UUID
    status: str
    current_step: Optional[str] = None
    progress_percentage: float
    processing_steps: List[ProcessingStepLog]
    estimated_completion_time: Optional[datetime] = None


class ClaimLogsResponse(BaseModel):
    claim_id: UUID
    logs: List[ProcessingStepLog]


# =============================================================================
# Decision Schemas
# =============================================================================

class ClaimDecisionResponse(BaseModel):
    id: UUID
    claim_id: UUID
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
    # Supporting data
    relevant_policies: Optional[Dict[str, Any]] = None
    similar_claims: Optional[Dict[str, Any]] = None
    user_contract_info: Optional[Dict[str, Any]] = None
    llm_model: Optional[str] = None
    requires_manual_review: bool
    decided_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Document Schemas
# =============================================================================

class DocumentUploadResponse(BaseModel):
    document_id: UUID
    file_path: str
    file_size_bytes: int
    mime_type: str
    uploaded_at: datetime


class DocumentResponse(BaseModel):
    id: UUID
    claim_id: UUID
    document_type: Optional[str] = None
    file_path: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    raw_ocr_text: Optional[str] = None
    raw_ocr_text_redacted: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    ocr_confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# User Schemas
# =============================================================================

class UserResponse(BaseModel):
    id: UUID
    user_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool
    created_at: datetime
    # PII redacted fields (returned by default)
    email_redacted: Optional[str] = None
    full_name_redacted: Optional[str] = None
    phone_number_redacted: Optional[str] = None
    date_of_birth_redacted: Optional[str] = None

    class Config:
        from_attributes = True


class UserContractResponse(BaseModel):
    id: UUID
    user_id: str
    contract_number: str
    contract_type: Optional[str] = None
    coverage_amount: Optional[float] = None
    premium_amount: Optional[float] = None
    is_active: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# Statistics Schemas
# =============================================================================

class ClaimStatistics(BaseModel):
    total_claims: int
    pending_claims: int
    processing_claims: int
    completed_claims: int
    failed_claims: int
    manual_review_claims: int
    average_processing_time_ms: Optional[float] = None


# =============================================================================
# HITL - Ask Agent Schemas
# =============================================================================

class AskAgentRequest(BaseModel):
    question: str = Field(..., description="Reviewer's question to the agent", min_length=1)
    reviewer_id: str = Field(..., description="Unique identifier for the reviewer")
    reviewer_name: str = Field(..., description="Display name of the reviewer")


class AskAgentResponse(BaseModel):
    success: bool
    claim_id: str
    question: str
    answer: str
    timestamp: datetime = Field(default_factory=utc_now)


# =============================================================================
# Guardrails Schemas
# =============================================================================

class GuardrailsDetectionResponse(BaseModel):
    """Schema for a single guardrails detection."""
    id: UUID
    detection_type: str  # EMAIL_ADDRESS, PHONE_NUMBER, etc.
    severity: Optional[str] = None
    action_taken: Optional[str] = None
    detected_at: datetime
    record_metadata: Optional[Dict[str, Any]] = None  # Contains source_step, detected_fields, etc.

    model_config = {"from_attributes": True}


class GuardrailsDetectionsListResponse(BaseModel):
    """Response for listing all detections for a claim."""
    claim_id: UUID
    detections: List[GuardrailsDetectionResponse]
    total: int


# =============================================================================
# Error Schemas
# =============================================================================

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)
