"""
SQLAlchemy models for tenders (Appels d'Offres) and related entities.

Tender analysis use case - Go/No-Go decision support for public and private tenders.

Follows the same patterns as claim.py:
- Timezone-aware datetimes via utc_now()
- UUID primary keys
- pgvector embeddings (768 dimensions)
- JSON metadata columns
"""

import enum
from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
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

class TenderStatus(str, enum.Enum):
    """Tender processing status."""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    manual_review = "manual_review"
    pending_info = "pending_info"  # Waiting for additional information


class TenderDecisionType(str, enum.Enum):
    """Tender Go/No-Go decision types."""
    go = "go"
    no_go = "no_go"
    a_approfondir = "a_approfondir"


class TenderProcessingStep(str, enum.Enum):
    """Processing workflow steps for tenders."""
    ocr = "ocr"
    guardrails = "guardrails"
    rag_retrieval = "rag_retrieval"
    llm_decision = "llm_decision"
    final_review = "final_review"


# =============================================================================
# Models
# =============================================================================

class Tender(Base):
    """Tender (Appel d'Offres) model."""

    __tablename__ = "tenders"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_id = Column(String(255), nullable=False, index=True)  # e.g. "ENT-IDF"
    tender_number = Column(String(100), unique=True, nullable=False)
    tender_type = Column(String(100))  # marche_public / prive / conception_realisation
    document_path = Column(Text, nullable=False)
    status = Column(
        Enum(TenderStatus, native_enum=False),
        default=TenderStatus.pending,
        nullable=False,
        index=True,
    )
    submitted_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    processed_at = Column(DateTime(timezone=True))
    total_processing_time_ms = Column(Integer)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    tender_metadata = Column("metadata", JSON, default=dict)
    agent_logs = Column(JSON, default=list)  # HITL review logs and chat messages
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    documents = relationship(
        "TenderDocument", back_populates="tender", cascade="all, delete-orphan"
    )
    processing_logs = relationship(
        "TenderProcessingLog", back_populates="tender", cascade="all, delete-orphan"
    )
    decision = relationship(
        "TenderDecision", back_populates="tender", uselist=False, cascade="all, delete-orphan"
    )


class TenderDocument(Base):
    """Tender document (DCE pieces) with OCR results and embeddings."""

    __tablename__ = "tender_documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tender_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True
    )
    document_type = Column(String(100))  # dce / cctp / bpu / rc
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
    language = Column(String(10), default="fra")
    record_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationship
    tender = relationship("Tender", back_populates="documents")


class TenderDecision(Base):
    """Tender Go/No-Go decision with history of system and reviewer decisions."""

    __tablename__ = "tender_decisions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tender_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True
    )

    # Initial System Decision (automated)
    initial_decision = Column(Enum(TenderDecisionType, native_enum=False), nullable=False, index=True)
    initial_confidence = Column(Float)
    initial_reasoning = Column(Text)
    initial_decided_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    # Final Reviewer Decision (manual override)
    final_decision = Column(Enum(TenderDecisionType, native_enum=False), index=True)
    final_decision_by = Column(String(255))  # Reviewer ID
    final_decision_by_name = Column(String(255))  # Reviewer name
    final_decision_at = Column(DateTime(timezone=True))
    final_decision_notes = Column(Text)

    # Legacy field for backwards compatibility (maps to initial_decision)
    decision = Column(Enum(TenderDecisionType, native_enum=False), nullable=False, index=True)
    confidence = Column(Float)
    reasoning = Column(Text)

    # Supporting analysis
    risk_analysis = Column(JSON)
    similar_references = Column(JSON)
    historical_ao_analysis = Column(JSON)
    internal_capabilities = Column(JSON)

    # LLM Details
    llm_model = Column(String(100))

    # Review
    requires_manual_review = Column(Boolean, default=False)

    decided_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationship
    tender = relationship("Tender", back_populates="decision")


class TenderProcessingLog(Base):
    """Processing step execution log for tenders."""

    __tablename__ = "tender_processing_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tender_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True
    )
    step = Column(Enum(TenderProcessingStep, native_enum=False), nullable=False, index=True)
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
    tender = relationship("Tender", back_populates="processing_logs")


class CompanyReference(Base):
    """Past project references for company entities."""

    __tablename__ = "company_references"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    reference_number = Column(String(100), unique=True, nullable=False)
    project_name = Column(String(500), nullable=False)
    maitre_ouvrage = Column(String(255))
    nature_travaux = Column(String(255))
    montant = Column(Numeric(15, 2))
    date_debut = Column(Date)
    date_fin = Column(Date)
    region = Column(String(100))
    description = Column(Text)
    certifications_used = Column(JSON)
    key_metrics = Column(JSON)

    # Vector embedding for semantic search
    embedding = Column(Vector(768))

    # Status
    is_active = Column(Boolean, default=True, index=True)
    record_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class CompanyCapability(Base):
    """Company internal capabilities: certifications, equipment, teams."""

    __tablename__ = "company_capabilities"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    category = Column(String(100), nullable=False, index=True)  # certification / materiel / personnel
    name = Column(String(255), nullable=False)
    description = Column(Text)
    valid_until = Column(Date)
    region = Column(String(100))
    availability = Column(String(50))  # disponible / occupe / partiel
    details = Column(JSON)

    # Vector embedding for semantic search
    embedding = Column(Vector(768))

    # Status
    is_active = Column(Boolean, default=True, index=True)
    record_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class HistoricalTender(Base):
    """Historical won/lost tenders for trend analysis."""

    __tablename__ = "historical_tenders"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    ao_number = Column(String(100), unique=True, nullable=False)
    maitre_ouvrage = Column(String(255))
    nature_travaux = Column(String(255))
    montant_estime = Column(Numeric(15, 2))
    montant_propose = Column(Numeric(15, 2))
    resultat = Column(String(50))  # gagne / perdu / abandonne
    raison_resultat = Column(Text)
    date_soumission = Column(Date)
    criteres_attribution = Column(JSON)
    note_technique = Column(Float)
    note_prix = Column(Float)
    region = Column(String(100))
    description = Column(Text)

    # Vector embedding for semantic search
    embedding = Column(Vector(768))

    # Status
    is_active = Column(Boolean, default=True, index=True)
    record_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
