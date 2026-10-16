"""Columns shared by the tables of every business domain.

Each domain has three tables, with the same columns plus a few of its own (database/init.sql):
    <cases>        the cases: claims, tenders, reclamations                       -> CaseColumns
    <documents>    their documents: OCR text and embedding (similarity search)    -> DocumentColumns
    <decisions>    the agent's decision, then the reviewer's final decision       -> DecisionColumns

A domain's models (app/models/claim.py, ...) combine these with their own columns, status and
decision types, and foreign key. The code shared by the domains (processing, decisions, review)
only uses the columns below.
"""
from datetime import datetime, timezone
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, BigInteger, Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CaseColumns:
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_path = Column(Text)            # the case PDF: OGX Files id, or a local path
    submitted_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    processed_at = Column(DateTime(timezone=True))
    total_processing_time_ms = Column(Integer)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    # Free-form JSON ("metadata" in the database; `metadata` is reserved by SQLAlchemy): processing
    # steps and usage of the last processing, ids of the document files, descriptions...
    meta = Column("metadata", JSON, default=dict)
    # Review journal: questions to the agent and their answers, reviewer decisions (app/services/review.py)
    agent_logs = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class DocumentColumns:
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_type = Column(String(100))
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(BigInteger)
    mime_type = Column(String(100))
    raw_ocr_text = Column(Text)
    structured_data = Column(JSON)
    ocr_confidence = Column(Float)
    ocr_processed_at = Column(DateTime(timezone=True))
    embedding = Column(Vector(768))          # similarity search of precedents (nomic-embed-text, 768 dims)
    page_count = Column(Integer)
    language = Column(String(10))
    record_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class DecisionColumns:
    """One row per processing. `initial_*` is what the agent decided; `final_*` is set when a reviewer
    decides; `decision` / `confidence` / `reasoning` are the current values shown to users."""
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    initial_confidence = Column(Float)
    initial_reasoning = Column(Text)
    initial_decided_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    final_decision_by = Column(String(255))        # OpenShift user name of the reviewer
    final_decision_by_name = Column(String(255))   # display name of the reviewer
    final_decision_at = Column(DateTime(timezone=True))
    final_decision_notes = Column(Text)            # the reviewer's justification
    confidence = Column(Float)
    reasoning = Column(Text)
    llm_model = Column(String(100))
    requires_manual_review = Column(Boolean, default=False)
    decided_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    # Evidence and review brief of the agent: reasons to review, points to check, bilingual texts
    decision_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
