"""
SQLAlchemy models for reclamations (courrier/colis) and related entities.

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

class ReclamationStatus(str, enum.Enum):
    """Reclamation processing status."""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    rejected = "rejected"
    manual_review = "manual_review"
    escalated = "escalated"


class ReclamationType(str, enum.Enum):
    """Reclamation types for courrier/colis."""
    colis_endommage = "colis_endommage"
    colis_perdu = "colis_perdu"
    non_livre = "non_livre"
    mauvaise_adresse = "mauvaise_adresse"
    vol_point_relais = "vol_point_relais"
    retard_livraison = "retard_livraison"


class ReclamationDecisionType(str, enum.Enum):
    """Reclamation decision types."""
    rembourser = "rembourser"
    reexpedier = "reexpedier"
    rejeter = "rejeter"
    escalader = "escalader"


class TrackingEventType(str, enum.Enum):
    """Tracking event types for courrier/colis."""
    prise_en_charge = "prise_en_charge"
    tri = "tri"
    en_cours_acheminement = "en_cours_acheminement"
    arrive_centre = "arrive_centre"
    en_livraison = "en_livraison"
    livre = "livre"
    avis_passage = "avis_passage"
    retour_expediteur = "retour_expediteur"
    incident = "incident"
    point_relais = "point_relais"


# =============================================================================
# Models
# =============================================================================

class Reclamation(Base):
    """Reclamation model."""

    __tablename__ = "reclamations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    numero_suivi = Column(String(100), nullable=False, index=True)
    reclamation_number = Column(String(100), unique=True, nullable=False)
    reclamation_type = Column(
        Enum(ReclamationType, native_enum=False),
        index=True,
    )
    client_nom = Column(String(255), nullable=False)
    client_email = Column(String(255), index=True)
    client_telephone = Column(String(50))
    description = Column(Text)
    valeur_declaree = Column(Numeric(10, 2))
    photo_path = Column(Text)
    document_path = Column(Text)
    status = Column(
        Enum(ReclamationStatus, native_enum=False),
        default=ReclamationStatus.pending,
        nullable=False,
        index=True,
    )
    submitted_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    processed_at = Column(DateTime(timezone=True))
    total_processing_time_ms = Column(Integer)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    reclamation_metadata = Column("metadata", JSON, default=dict)
    agent_logs = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    documents = relationship(
        "ReclamationDocument", back_populates="reclamation", cascade="all, delete-orphan"
    )
    processing_logs = relationship(
        "ReclamationProcessingLog", back_populates="reclamation", cascade="all, delete-orphan"
    )
    decision = relationship(
        "ReclamationDecision", back_populates="reclamation", uselist=False, cascade="all, delete-orphan"
    )


class ReclamationDocument(Base):
    """Reclamation document with OCR results and embeddings."""

    __tablename__ = "reclamation_documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    reclamation_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("reclamations.id"), nullable=False, index=True
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
    embedding = Column(Vector(768))

    # Metadata
    page_count = Column(Integer)
    language = Column(String(10), default="fra")
    record_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationship
    reclamation = relationship("Reclamation", back_populates="documents")


class ReclamationDecision(Base):
    """Reclamation processing decision."""

    __tablename__ = "reclamation_decisions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    reclamation_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("reclamations.id"), nullable=False, index=True
    )

    # Initial System Decision (automated)
    initial_decision = Column(Enum(ReclamationDecisionType, native_enum=False), index=True)
    initial_confidence = Column(Float)
    initial_reasoning = Column(Text)
    initial_decided_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    # Final Decision (manual override)
    final_decision = Column(Enum(ReclamationDecisionType, native_enum=False), index=True)
    final_decision_at = Column(DateTime(timezone=True))

    # Legacy field for backwards compatibility
    decision = Column(Enum(ReclamationDecisionType, native_enum=False), nullable=False, index=True)
    confidence = Column(Float)
    reasoning = Column(Text)

    # LLM Details
    llm_model = Column(String(100))

    # Review
    requires_manual_review = Column(Boolean, default=False)

    decided_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationship
    reclamation = relationship("Reclamation", back_populates="decision")


class ReclamationProcessingLog(Base):
    """Reclamation processing step execution log."""

    __tablename__ = "reclamation_processing_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    reclamation_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("reclamations.id"), nullable=False, index=True
    )
    step = Column(String(100), nullable=False, index=True)
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
    reclamation = relationship("Reclamation", back_populates="processing_logs")


class TrackingEvent(Base):
    """Tracking event for courrier/colis."""

    __tablename__ = "tracking_events"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    numero_suivi = Column(String(100), nullable=False, index=True)
    event_type = Column(
        Enum(TrackingEventType, native_enum=False),
        nullable=False,
        index=True,
    )
    event_date = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(255))
    detail = Column(Text)
    code_postal = Column(String(10))
    is_final = Column(Boolean, default=False)
    event_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class CourrierKnowledgeBase(Base):
    """Knowledge base articles for courrier/colis RAG."""

    __tablename__ = "courrier_knowledge_base"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), index=True)
    tags = Column(ARRAY(Text))

    # Vector embedding
    embedding = Column(Vector(768))

    # Status
    is_active = Column(Boolean, default=True, index=True)
    record_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
