"""
Tender Service - Business logic for tenders (Appels d'Offres) processing.

Extends BaseAgentService with tender-specific logic:
- Decision mapping (go/no_go/a_approfondir)
- Tender-specific context building
- Risk analysis and supporting data
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import tender as models
from app.core.config import settings
from app.llamastack.ao_prompts import (
    AO_PROCESSING_AGENT_INSTRUCTIONS,
    AO_USER_MESSAGE_TEMPLATE,
)
from .agents.base_agent_service import BaseAgentService

logger = logging.getLogger(__name__)

# Tools used by the tenders agent
TENDER_TOOLS = [
    # CRUD (tenders-server)
    "list_tenders",
    "get_tender",
    "get_tender_documents",
    "analyze_tender",
    "get_tender_statistics",
    "save_tender_decision",
    # RAG/semantic (rag-server)
    "retrieve_similar_references",
    "retrieve_historical_tenders",
    "retrieve_capabilities",
    "search_knowledge_base",
    "generate_document_embedding",
    # OCR (ocr-server)
    "ocr_document",
]


class TenderService(BaseAgentService):
    """Service for tender processing business logic."""

    # ── BaseAgentService implementations ────────────────────────────

    def get_entity_type(self) -> str:
        return "tender"

    def get_instructions(self) -> str:
        return AO_PROCESSING_AGENT_INSTRUCTIONS

    def get_user_message_template(self) -> str:
        return AO_USER_MESSAGE_TEMPLATE

    def get_tools(self) -> List[str]:
        return TENDER_TOOLS

    def get_entity_number(self, entity) -> str:
        return entity.tender_number

    def map_recommendation_to_status(self, recommendation: str) -> str:
        mapping = {
            "go": "completed",
            "no_go": "failed",
        }
        return mapping.get(recommendation, "manual_review")

    def set_entity_status(self, entity, status: str) -> None:
        entity.status = models.TenderStatus(status)

    def set_entity_processed(self, entity, processing_time_ms: Optional[int]) -> None:
        entity.processed_at = datetime.now(timezone.utc)
        entity.total_processing_time_ms = processing_time_ms

    def get_entity_metadata(self, entity) -> dict:
        return entity.tender_metadata or {}

    def set_entity_metadata(self, entity, metadata: dict) -> None:
        entity.tender_metadata = metadata

    async def get_entity_by_id(self, db: AsyncSession, entity_id: str):
        result = await db.execute(
            select(models.Tender).where(models.Tender.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def build_entity_context(self, db: AsyncSession, entity) -> Dict[str, Any]:
        return await self.build_tender_context(db, entity)

    # ── Tender-specific methods ─────────────────────────────────────

    async def get_tender_by_id(self, db: AsyncSession, tender_id: str) -> Optional[models.Tender]:
        return await self.get_entity_by_id(db, tender_id)

    async def build_tender_context(self, db: AsyncSession, tender: models.Tender) -> Dict[str, Any]:
        context = {
            "entity_type": "tender",
            "entity_id": str(tender.id),
            "entity_data": {
                "entity_id": tender.entity_id,
                "tender_number": tender.tender_number,
                "tender_type": tender.tender_type,
                "document_path": tender.document_path,
                "status": tender.status.value,
                "submitted_at": tender.submitted_at.isoformat() if tender.submitted_at else None,
            },
        }

        # Add OCR data if available
        ocr_result = await db.execute(
            select(models.TenderDocument)
            .where(models.TenderDocument.tender_id == tender.id)
            .order_by(models.TenderDocument.created_at.desc())
            .limit(1)
        )
        tender_doc = ocr_result.scalar_one_or_none()

        if tender_doc:
            ocr_context = self.context_builder.extract_ocr_context({
                "raw_ocr_text": tender_doc.raw_ocr_text,
                "structured_data": tender_doc.structured_data,
            })
            context["additional_context"] = {"OCR Data": ocr_context}

        return context

    async def process_tender_with_agent(
        self,
        db: AsyncSession,
        tender_id: str,
        agent_config: Dict[str, Any],
        tools: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Process tender using BaseAgentService pattern."""
        return await self.process_entity(db, tender_id, agent_config, tools)

    async def save_decision(
        self,
        db: AsyncSession,
        tender_id: str,
        decision_data: Dict[str, Any],
    ) -> models.TenderDecision:
        recommendation = decision_data.get("recommendation", "a_approfondir")

        decision_type_map = {
            "go": models.TenderDecisionType.go,
            "no_go": models.TenderDecisionType.no_go,
            "a_approfondir": models.TenderDecisionType.a_approfondir,
        }
        decision_type = decision_type_map.get(
            recommendation, models.TenderDecisionType.a_approfondir
        )

        # Delete any existing decision to avoid duplicates
        existing = await db.execute(
            select(models.TenderDecision).where(
                models.TenderDecision.tender_id == tender_id
            )
        )
        for old in existing.scalars().all():
            await db.delete(old)
        await db.flush()

        decision = models.TenderDecision(
            tender_id=tender_id,
            initial_decision=decision_type,
            initial_confidence=decision_data.get("confidence", 0.0),
            initial_reasoning=decision_data.get("reasoning", ""),
            initial_decided_at=datetime.now(timezone.utc),
            decision=decision_type,
            confidence=decision_data.get("confidence", 0.0),
            reasoning=decision_data.get("reasoning", ""),
            risk_analysis=decision_data.get("risk_analysis"),
            similar_references=decision_data.get("similar_references"),
            historical_ao_analysis=decision_data.get("historical_ao_analysis"),
            internal_capabilities=decision_data.get("internal_capabilities"),
            llm_model=settings.llamastack_default_model,
            requires_manual_review=(recommendation == "a_approfondir"),
        )

        db.add(decision)
        await db.commit()
        await db.refresh(decision)

        logger.info(f"Decision saved for tender {tender_id}: {decision_type.value}")
        return decision
