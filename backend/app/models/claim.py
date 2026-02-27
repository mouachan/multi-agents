"""
SQLAlchemy models for claims and related entities.

FIXES APPLIED:
- Replaced datetime.utcnow with datetime.now(timezone.utc)
- Using timezone-aware datetimes throughout
"""

import enum
from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# =============================================================================
# Helper function for timezone-aware timestamps
# =============================================================================

def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# =============================================================================
# Enums
# =============================================================================

class ClaimStatus(str, enum.Enum):
    """Claim processing status."""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    denied = "denied"
    failed = "failed"
    manual_review = "manual_review"
    pending_info = "pending_info"  # Waiting for additional information from claimant


class ProcessingStep(str, enum.Enum):
    """Processing workflow steps."""
    ocr = "ocr"
    guardrails = "guardrails"
    rag_retrieval = "rag_retrieval"
    llm_decision = "llm_decision"
    final_review = "final_review"


class DecisionType(str, enum.Enum):
    """Claim decision types."""
    approve = "approve"
    deny = "deny"
    manual_review = "manual_review"


# =============================================================================
# Models
# =============================================================================

class Claim(Base):
    """Claim model."""

    __tablename__ = "claims"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    claim_number = Column(String(100), unique=True, nullable=False)
    claim_type = Column(String(100))
    document_path = Column(Text, nullable=False)
    status = Column(
        Enum(ClaimStatus, native_enum=False),
        default=ClaimStatus.pending,
        nullable=False,
        index=True,
    )
    submitted_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    processed_at = Column(DateTime(timezone=True))
    total_processing_time_ms = Column(Integer)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    claim_metadata = Column("metadata", JSON, default=dict)
    agent_logs = Column(JSON, default=list)  # HITL review logs and chat messages
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    documents = relationship(
        "ClaimDocument", back_populates="claim", cascade="all, delete-orphan"
    )
    processing_logs = relationship(
        "ProcessingLog", back_populates="claim", cascade="all, delete-orphan"
    )
    guardrails_detections = relationship(
        "GuardrailsDetection", back_populates="claim", cascade="all, delete-orphan"
    )
    decision = relationship(
        "ClaimDecision", back_populates="claim", uselist=False, cascade="all, delete-orphan"
    )


class ClaimDocument(Base):
    """Claim document with OCR results and embeddings."""

    __tablename__ = "claim_documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    claim_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True
    )
    document_type = Column(String(100))
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(BigInteger)
    mime_type = Column(String(100))

    # OCR Results
    raw_ocr_text = Column(Text)
    raw_ocr_text_redacted = Column(Text)
    structured_data = Column(JSON)
    ocr_confidence = Column(Float)
    ocr_processed_at = Column(DateTime(timezone=True))

    # Vector embedding for semantic search
    embedding = Column(Vector(768))  # 768 dimensions for all-mpnet-base-v2

    # Metadata
    page_count = Column(Integer)
    language = Column(String(10), default="eng")
    record_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationship
    claim = relationship("Claim", back_populates="documents")


class UserContract(Base):
    """User insurance contract with embeddings."""

    __tablename__ = "user_contracts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    contract_number = Column(String(100), unique=True, nullable=False)
    contract_type = Column(String(100))

    # Contract details
    start_date = Column(Date)
    end_date = Column(Date)
    coverage_amount = Column(Numeric(15, 2))
    premium_amount = Column(Numeric(15, 2))
    payment_frequency = Column(String(50))

    # Contract content
    full_text = Column(Text)
    key_terms = Column(JSON)
    coverage_details = Column(JSON)
    exclusions = Column(JSON)

    # Vector embedding
    embedding = Column(Vector(768))

    # Status
    is_active = Column(Boolean, default=True, index=True)
    record_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class ProcessingLog(Base):
    """Processing step execution log."""

    __tablename__ = "processing_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    claim_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True
    )
    step = Column(Enum(ProcessingStep, native_enum=False), nullable=False, index=True)
    agent_name = Column(String(100))

    # Execution details
    started_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    status = Column(String(50))

    # Input/Output
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)

    # Metrics
    confidence_score = Column(Float)
    tokens_used = Column(Integer)

    record_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationship
    claim = relationship("Claim", back_populates="processing_logs")


class GuardrailsDetection(Base):
    """Guardrails PII/sensitive data detection."""

    __tablename__ = "guardrails_detections"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    claim_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True
    )
    detection_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), index=True)

    # Detection details (DO NOT store actual PII)
    original_text = Column(Text)  # For audit only
    redacted_text = Column(Text)
    text_span_start = Column(Integer)
    text_span_end = Column(Integer)

    # Action taken
    action_taken = Column(String(50))
    detected_at = Column(DateTime(timezone=True), default=utc_now)

    record_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationship
    claim = relationship("Claim", back_populates="guardrails_detections")


class ClaimDecision(Base):
    """Claim processing decision with history of system and reviewer decisions."""

    __tablename__ = "claim_decisions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    claim_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True
    )

    # Initial System Decision (automated)
    initial_decision = Column(Enum(DecisionType, native_enum=False), nullable=False, index=True)
    initial_confidence = Column(Float)
    initial_reasoning = Column(Text)
    initial_decided_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    # Final Reviewer Decision (manual override)
    final_decision = Column(Enum(DecisionType, native_enum=False), index=True)
    final_decision_by = Column(String(255))  # Reviewer ID
    final_decision_by_name = Column(String(255))  # Reviewer name
    final_decision_at = Column(DateTime(timezone=True))
    final_decision_notes = Column(Text)

    # Legacy field for backwards compatibility (maps to initial_decision)
    decision = Column(Enum(DecisionType, native_enum=False), nullable=False, index=True)
    confidence = Column(Float)
    reasoning = Column(Text)
    reasoning_redacted = Column(Text)

    # Supporting evidence
    relevant_policies = Column(JSON)
    similar_claims = Column(JSON)
    user_contract_info = Column(JSON)

    # LLM Details
    llm_model = Column(String(100))
    llm_prompt = Column(Text)
    llm_response = Column(Text)

    # Review
    requires_manual_review = Column(Boolean, default=False)
    manual_review_notes = Column(Text)
    reviewed_by = Column(String(255))
    reviewed_at = Column(DateTime(timezone=True))

    decided_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationship
    claim = relationship("Claim", back_populates="decision")


class KnowledgeBase(Base):
    """Knowledge base articles for RAG."""

    __tablename__ = "knowledge_base"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), index=True)
    tags = Column(ARRAY(Text))

    # Vector embedding
    embedding = Column(Vector(768))

    # Versioning
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)
    effective_date = Column(Date)
    expiry_date = Column(Date)

    # Metadata
    source = Column(String(255))
    author = Column(String(255))
    last_reviewed = Column(Date)
    record_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), index=True)
    full_name = Column(String(255))
    date_of_birth = Column(Date)
    phone_number = Column(String(50))
    address = Column(JSON)

    # PII redacted versions
    email_redacted = Column(String(255))
    full_name_redacted = Column(String(255))
    phone_number_redacted = Column(String(50))
    date_of_birth_redacted = Column(String(20))
    address_redacted = Column(JSON)

    # Account status
    is_active = Column(Boolean, default=True, index=True)
    account_created_at = Column(DateTime(timezone=True), default=utc_now)
    last_login_at = Column(DateTime(timezone=True))

    record_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
