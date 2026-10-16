"""BTP tenders (domain "tenders", app/domains/tenders.py): cases, documents, decisions.

The company references, tender history and capabilities searched by the agent are read by the
RAG MCP server (backend/mcp_servers/rag_server), not by the backend.
"""
import enum

from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.database import Base
from app.models.case import CaseColumns, DecisionColumns, DocumentColumns


class TenderStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"          # go: the company bids
    declined = "declined"            # no go
    failed = "failed"                # processing error: can be processed again
    manual_review = "manual_review"  # waiting for a reviewer
    pending_info = "pending_info"


class TenderDecisionType(str, enum.Enum):
    go = "go"
    no_go = "no_go"
    a_approfondir = "a_approfondir"   # needs a closer look by a human


class Tender(CaseColumns, Base):
    __tablename__ = "tenders"

    tender_number = Column(String(100), unique=True, nullable=False)
    tender_type = Column(String(100))     # marche_public / prive / conception_realisation
    entity_id = Column(String(255), index=True)   # the company's regional entity (ENT-IDF)
    status = Column(Enum(TenderStatus, native_enum=False), default=TenderStatus.pending, nullable=False, index=True)


class TenderDocument(DocumentColumns, Base):
    __tablename__ = "tender_documents"

    tender_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True)


class TenderDecision(DecisionColumns, Base):
    __tablename__ = "tender_decisions"

    tender_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False, index=True)
    initial_decision = Column(Enum(TenderDecisionType, native_enum=False), nullable=False, index=True)
    final_decision = Column(Enum(TenderDecisionType, native_enum=False), index=True)
    decision = Column(Enum(TenderDecisionType, native_enum=False), nullable=False, index=True)
