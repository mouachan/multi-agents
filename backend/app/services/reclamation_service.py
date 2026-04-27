"""
Reclamation Service - Business logic for postal/parcel complaint processing.

Extends BaseAgentService with reclamation-specific logic:
- Decision mapping (rembourser/reexpedier/rejeter/escalader)
- Reclamation-specific context building
- Tracking and photo/document analysis integration
"""
import logging
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import reclamation as models
from app.core.config import settings
from app.llamastack.courrier_prompts import (
    COURRIER_RECLAMATION_INSTRUCTIONS,
    COURRIER_RECLAMATION_USER_TEMPLATE,
)
from .agents.base_agent_service import BaseAgentService

logger = logging.getLogger(__name__)

# Tools used by the reclamation agent
RECLAMATION_TOOLS = [
    # CRUD (postal-server)
    "list_reclamations",
    "get_reclamation",
    "get_reclamation_documents",
    "get_reclamation_statistics",
    "save_reclamation_decision",
    # Tracking
    "get_tracking",
    # RAG/semantic (rag-server)
    "search_courrier_knowledge",
    "retrieve_similar_reclamations",
    # OCR (ocr-server)
    "ocr_document",
]


class ReclamationService(BaseAgentService):
    """Service for postal/parcel reclamation processing business logic."""

    # ── BaseAgentService implementations ────────────────────────────

    def get_entity_type(self) -> str:
        return "reclamation"

    def get_instructions(self) -> str:
        return COURRIER_RECLAMATION_INSTRUCTIONS

    def get_user_message_template(self) -> str:
        return COURRIER_RECLAMATION_USER_TEMPLATE

    def get_tools(self) -> List[str]:
        return RECLAMATION_TOOLS

    def get_entity_number(self, entity) -> str:
        return entity.reclamation_number

    def map_recommendation_to_status(self, recommendation: str) -> str:
        mapping = {
            "rembourser": "completed",
            "reexpedier": "completed",
            "rejeter": "rejected",
            "escalader": "escalated",
        }
        return mapping.get(recommendation, "manual_review")

    def set_entity_status(self, entity, status: str) -> None:
        entity.status = models.ReclamationStatus(status)

    def set_entity_processed(self, entity, processing_time_ms: Optional[int]) -> None:
        entity.processed_at = datetime.now(timezone.utc)
        entity.total_processing_time_ms = processing_time_ms

    def get_entity_metadata(self, entity) -> dict:
        return entity.reclamation_metadata or {}

    def set_entity_metadata(self, entity, metadata: dict) -> None:
        entity.reclamation_metadata = metadata

    async def get_entity_by_id(self, db: AsyncSession, entity_id: str):
        result = await db.execute(
            select(models.Reclamation).where(models.Reclamation.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def build_entity_context(self, db: AsyncSession, entity) -> Dict[str, Any]:
        return await self.build_reclamation_context(db, entity)

    # ── Reclamation-specific methods ───────────────────────────────

    async def get_reclamation_by_id(self, db: AsyncSession, reclamation_id: str) -> Optional[models.Reclamation]:
        return await self.get_entity_by_id(db, reclamation_id)

    async def build_reclamation_context(self, db: AsyncSession, reclamation: models.Reclamation) -> Dict[str, Any]:
        context = {
            "entity_type": "reclamation",
            "entity_id": str(reclamation.id),
            "entity_data": {
                "reclamation_number": reclamation.reclamation_number,
                "reclamation_type": reclamation.reclamation_type,
                "numero_suivi": reclamation.numero_suivi,
                "client_nom": reclamation.client_nom,
                "document_path": reclamation.document_path,
                "status": reclamation.status.value,
                "submitted_at": reclamation.submitted_at.isoformat() if reclamation.submitted_at else None,
            },
        }

        # Add OCR data if available
        ocr_result = await db.execute(
            select(models.ReclamationDocument)
            .where(models.ReclamationDocument.reclamation_id == reclamation.id)
            .order_by(models.ReclamationDocument.created_at.desc())
            .limit(1)
        )
        reclamation_doc = ocr_result.scalar_one_or_none()

        if reclamation_doc:
            ocr_context = self.context_builder.extract_ocr_context({
                "raw_ocr_text": reclamation_doc.raw_ocr_text,
                "structured_data": reclamation_doc.structured_data,
            })
            context["additional_context"] = {"OCR Data": ocr_context}

        return context

    async def process_reclamation_with_agent(
        self,
        db: AsyncSession,
        reclamation_id: str,
        agent_config: Dict[str, Any],
        tools: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Process reclamation using BaseAgentService pattern."""
        return await self.process_entity(db, reclamation_id, agent_config, tools)

    async def save_decision(
        self,
        db: AsyncSession,
        reclamation_id: str,
        decision_data: Dict[str, Any],
    ) -> models.ReclamationDecision:
        recommendation = decision_data.get("recommendation", "escalader")

        decision_type_map = {
            "rembourser": models.ReclamationDecisionType.rembourser,
            "reexpedier": models.ReclamationDecisionType.reexpedier,
            "rejeter": models.ReclamationDecisionType.rejeter,
            "escalader": models.ReclamationDecisionType.escalader,
        }
        decision_type = decision_type_map.get(
            recommendation, models.ReclamationDecisionType.escalader
        )

        # Delete any existing decision to avoid duplicates
        existing = await db.execute(
            select(models.ReclamationDecision).where(
                models.ReclamationDecision.reclamation_id == reclamation_id
            )
        )
        for old in existing.scalars().all():
            await db.delete(old)
        await db.flush()

        model_name = self.clean_model_name(settings.llamastack_default_model)

        # Build decision metadata (bilingual reasoning, etc.)
        decision_metadata = {}
        if decision_data.get("reasoning_en"):
            decision_metadata["reasoning_en"] = decision_data["reasoning_en"]

        decision = models.ReclamationDecision(
            reclamation_id=reclamation_id,
            initial_decision=decision_type,
            initial_confidence=decision_data.get("confidence", 0.0),
            initial_reasoning=decision_data.get("reasoning", ""),
            initial_decided_at=datetime.now(timezone.utc),
            decision=decision_type,
            confidence=decision_data.get("confidence", 0.0),
            reasoning=decision_data.get("reasoning", ""),
            llm_model=model_name,
            requires_manual_review=(recommendation == "escalader"),
            decision_metadata=decision_metadata,
        )

        db.add(decision)
        await db.commit()
        await db.refresh(decision)

        logger.info(f"Decision saved for reclamation {reclamation_id}: {decision_type.value}")
        return decision
