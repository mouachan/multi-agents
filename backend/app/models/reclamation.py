"""Postal complaints (domain "postal", app/domains/postal.py): cases, documents, decisions, and the
tracking events of the parcels. Business values are French, as in the database."""
import enum
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.core.database import Base
from app.models.case import CaseColumns, DecisionColumns, DocumentColumns, utc_now


class ReclamationStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"          # refunded or re-shipped
    rejected = "rejected"
    manual_review = "manual_review"
    escalated = "escalated"          # waiting for a reviewer
    failed = "failed"                # processing error: can be processed again


class ReclamationType(str, enum.Enum):
    colis_endommage = "colis_endommage"     # damaged parcel
    colis_perdu = "colis_perdu"             # lost parcel
    non_livre = "non_livre"                 # not delivered
    mauvaise_adresse = "mauvaise_adresse"   # wrong address
    vol_point_relais = "vol_point_relais"   # stolen at the pick-up point
    retard_livraison = "retard_livraison"   # late delivery


class ReclamationDecisionType(str, enum.Enum):
    rembourser = "rembourser"   # refund
    reexpedier = "reexpedier"   # re-ship
    rejeter = "rejeter"         # reject
    escalader = "escalader"     # escalate to a human


class TrackingEventType(str, enum.Enum):
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


class Reclamation(CaseColumns, Base):
    __tablename__ = "reclamations"

    reclamation_number = Column(String(100), unique=True, nullable=False)
    reclamation_type = Column(Enum(ReclamationType, native_enum=False), nullable=False)
    numero_suivi = Column(String(100), nullable=False, index=True)    # tracking number of the parcel
    client_nom = Column(String(255), nullable=False)
    client_email = Column(String(255), index=True)
    client_telephone = Column(String(50))
    description = Column(Text)
    valeur_declaree = Column(Numeric(10, 2))                           # declared value (EUR)
    photo_path = Column(Text)
    status = Column(Enum(ReclamationStatus, native_enum=False), default=ReclamationStatus.pending, nullable=False, index=True)


class ReclamationDocument(DocumentColumns, Base):
    __tablename__ = "reclamation_documents"

    reclamation_id = Column(PG_UUID(as_uuid=True), ForeignKey("reclamations.id"), nullable=False, index=True)


class ReclamationDecision(DecisionColumns, Base):
    __tablename__ = "reclamation_decisions"

    reclamation_id = Column(PG_UUID(as_uuid=True), ForeignKey("reclamations.id"), nullable=False, index=True)
    initial_decision = Column(Enum(ReclamationDecisionType, native_enum=False), index=True)
    final_decision = Column(Enum(ReclamationDecisionType, native_enum=False), index=True)
    decision = Column(Enum(ReclamationDecisionType, native_enum=False), nullable=False, index=True)


class TrackingEvent(Base):
    """One step of a parcel's journey (tracking timeline on the complaint page)."""
    __tablename__ = "tracking_events"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    numero_suivi = Column(String(100), nullable=False, index=True)
    event_type = Column(Enum(TrackingEventType, native_enum=False), nullable=False, index=True)
    event_date = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(255))
    detail = Column(Text)
    code_postal = Column(String(10))
    is_final = Column(Boolean, default=False)
    event_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)
