"""Insurance claims (domain "claims", app/domains/claims.py): cases, documents, decisions, the
claimants, and the personal data found in a claim's documents."""
import enum
from uuid import uuid4

from sqlalchemy import JSON, Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.case import CaseColumns, DecisionColumns, DocumentColumns, utc_now


class ClaimStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"          # approved
    denied = "denied"
    failed = "failed"                # processing error: can be processed again
    manual_review = "manual_review"  # waiting for a reviewer
    pending_info = "pending_info"    # waiting for information from the claimant


class ClaimDecisionType(str, enum.Enum):
    approve = "approve"
    deny = "deny"
    manual_review = "manual_review"


class User(Base):
    """A policyholder (the claimant of a claim)."""
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)   # USR001
    email = Column(String(255))
    full_name = Column(String(255))
    date_of_birth = Column(Date)
    phone_number = Column(String(50))
    address = Column(JSON)


class Claim(CaseColumns, Base):
    __tablename__ = "claims"

    claim_number = Column(String(100), unique=True, nullable=False)
    claim_type = Column(String(100))       # Auto, Home, Medical, Life
    user_id = Column(String(255), nullable=False, index=True)
    status = Column(Enum(ClaimStatus, native_enum=False), default=ClaimStatus.pending, nullable=False, index=True)

    claimant = relationship(User, primaryjoin="foreign(Claim.user_id) == User.user_id",
                            viewonly=True, lazy="selectin")

    def api_extras(self) -> dict:
        """Added to the claim in the API (app/services/cases.py): the claimant's name."""
        return {"user_name": self.claimant.full_name if self.claimant else None}


class ClaimDocument(DocumentColumns, Base):
    __tablename__ = "claim_documents"

    claim_id = Column(PG_UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True)


class ClaimDecision(DecisionColumns, Base):
    __tablename__ = "claim_decisions"

    claim_id = Column(PG_UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True)
    initial_decision = Column(Enum(ClaimDecisionType, native_enum=False), nullable=False, index=True)
    final_decision = Column(Enum(ClaimDecisionType, native_enum=False), index=True)
    decision = Column(Enum(ClaimDecisionType, native_enum=False), nullable=False, index=True)


class GuardrailsDetection(Base):
    """Personal data found by NeMo Guardrails in a claim's documents (claim page, "PII" card)."""
    __tablename__ = "guardrails_detections"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    claim_id = Column(PG_UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True)
    detection_type = Column(String(100), nullable=False, index=True)   # "pii"
    severity = Column(String(20))
    action_taken = Column(String(50))
    text_span_start = Column(Integer)
    text_span_end = Column(Integer)
    redacted_text = Column(Text)
    detected_at = Column(DateTime(timezone=True), default=utc_now)
    record_metadata = Column("metadata", JSON, default=dict)          # entity type, masked text
    created_at = Column(DateTime(timezone=True), default=utc_now)
