"""
Claim Service - Business logic for claims processing.

Extends BaseAgentService with claim-specific logic:
- Decision mapping (approve/deny/manual_review)
- Claim-specific context building
- PII shield integration
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import claim as models
from app.core.config import settings
from app.llamastack.prompts import (
    CLAIMS_PROCESSING_AGENT_INSTRUCTIONS,
    USER_MESSAGE_FULL_WORKFLOW_TEMPLATE,
)
from .agents.base_agent_service import BaseAgentService

logger = logging.getLogger(__name__)

# Tools used by the claims agent
CLAIM_TOOLS = [
    # CRUD (claims-server)
    "list_claims",
    "get_claim",
    "get_claim_documents",
    "analyze_claim",
    "get_claim_statistics",
    # RAG/semantic (rag-server)
    "retrieve_user_info",
    "retrieve_similar_claims",
    "search_knowledge_base",
    # OCR (ocr-server)
    "ocr_document",
]


class ClaimService(BaseAgentService):
    """Service for claim processing business logic."""

    # ── BaseAgentService implementations ────────────────────────────

    def get_entity_type(self) -> str:
        return "claim"

    def get_instructions(self) -> str:
        return CLAIMS_PROCESSING_AGENT_INSTRUCTIONS

    def get_user_message_template(self) -> str:
        return USER_MESSAGE_FULL_WORKFLOW_TEMPLATE

    def get_tools(self) -> List[str]:
        return CLAIM_TOOLS

    def get_entity_number(self, entity) -> str:
        return entity.claim_number

    def map_recommendation_to_status(self, recommendation: str) -> str:
        mapping = {
            "approve": "completed",
            "deny": "failed",
        }
        return mapping.get(recommendation, "manual_review")

    def set_entity_status(self, entity, status: str) -> None:
        entity.status = models.ClaimStatus(status)

    def set_entity_processed(self, entity, processing_time_ms: Optional[int]) -> None:
        entity.processed_at = datetime.now(timezone.utc)
        entity.total_processing_time_ms = processing_time_ms

    def get_entity_metadata(self, entity) -> dict:
        return entity.claim_metadata or {}

    def set_entity_metadata(self, entity, metadata: dict) -> None:
        entity.claim_metadata = metadata

    async def get_entity_by_id(self, db: AsyncSession, entity_id: str):
        result = await db.execute(
            select(models.Claim).where(models.Claim.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def build_entity_context(self, db: AsyncSession, entity) -> Dict[str, Any]:
        return await self.build_claim_context(db, entity)

    # ── Claim-specific methods ──────────────────────────────────────

    async def get_claim_by_id(self, db: AsyncSession, claim_id: str) -> Optional[models.Claim]:
        return await self.get_entity_by_id(db, claim_id)

    async def build_claim_context(self, db: AsyncSession, claim: models.Claim) -> Dict[str, Any]:
        context = {
            "entity_type": "claim",
            "entity_id": str(claim.id),
            "entity_data": {
                "claim_number": claim.claim_number,
                "user_id": claim.user_id,
                "claim_type": claim.claim_type,
                "document_path": claim.document_path,
                "status": claim.status.value,
                "submitted_at": claim.submitted_at.isoformat() if claim.submitted_at else None,
            },
        }

        # Add OCR data if available
        ocr_result = await db.execute(
            select(models.ClaimDocument)
            .where(models.ClaimDocument.claim_id == claim.id)
            .order_by(models.ClaimDocument.created_at.desc())
            .limit(1)
        )
        claim_doc = ocr_result.scalar_one_or_none()

        if claim_doc:
            ocr_context = self.context_builder.extract_ocr_context({
                "raw_ocr_text": claim_doc.raw_ocr_text,
                "structured_data": claim_doc.structured_data,
            })
            context["additional_context"] = {"OCR Data": ocr_context}

        return context

    async def process_claim_with_agent(
        self,
        db: AsyncSession,
        claim_id: str,
        agent_config: Dict[str, Any],
        tools: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Process claim using BaseAgentService pattern."""
        return await self.process_entity(db, claim_id, agent_config, tools)

    async def save_decision(
        self,
        db: AsyncSession,
        claim_id: str,
        decision_data: Dict[str, Any],
    ) -> models.ClaimDecision:
        recommendation = decision_data.get("recommendation", "manual_review")

        decision = models.ClaimDecision(
            claim_id=claim_id,
            initial_decision=recommendation,
            initial_confidence=decision_data.get("confidence", 0.0),
            initial_reasoning=decision_data.get("reasoning", ""),
            initial_decided_at=datetime.now(timezone.utc),
            decision=recommendation,
            confidence=decision_data.get("confidence", 0.0),
            reasoning=decision_data.get("reasoning", ""),
            relevant_policies=decision_data.get("evidence", {}),
            llm_model=settings.llamastack_default_model,
            requires_manual_review=(recommendation == "manual_review"),
        )

        db.add(decision)
        await db.commit()
        await db.refresh(decision)

        logger.info(f"Decision saved for claim {claim_id}: {recommendation}")
        return decision

    async def check_pii_shield(self, text: str, claim_id: str) -> Dict[str, Any]:
        if not settings.enable_pii_detection:
            return {"violations_found": False, "detections": []}

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.llamastack_endpoint}/v1/safety/run-shield",
                    json={
                        "shield_id": settings.pii_shield_id,
                        "messages": [{"content": text, "role": "user"}],
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    logger.warning(f"Shield API returned {response.status_code}: {response.text}")
                    return {"violations_found": False, "detections": []}

                result = response.json()
                violation_data = result.get("violation", {})
                metadata = violation_data.get("metadata", {})
                status = metadata.get("status", "pass")

                if status == "violation":
                    detections = metadata.get("results", [])
                    logger.info(f"PII detected in claim {claim_id}: {len(detections)} violations")
                    return {
                        "violations_found": True,
                        "detections": detections,
                        "summary": metadata.get("summary", {}),
                    }

        except Exception as e:
            logger.error(f"Error checking PII shield: {e}", exc_info=True)

        return {"violations_found": False, "detections": []}

    async def save_pii_detections(
        self,
        db: AsyncSession,
        claim_id: str,
        detections: list,
    ) -> None:
        for detection in detections:
            detection_entry = models.GuardrailsDetection(
                claim_id=UUID(claim_id),
                detection_type="pii",
                severity="medium",
                action_taken="logged",
                detected_at=datetime.now(timezone.utc),
                record_metadata={
                    "text": detection.get("text", ""),
                    "detection_type": detection.get("detection_type", ""),
                    "score": detection.get("score", 0.0),
                    "detector_results": detection.get("individual_detector_results", []),
                    "source_step": detection.get("source_step", "unknown"),
                    "detected_fields": detection.get("detected_fields", []),
                },
            )
            db.add(detection_entry)

        await db.commit()
        logger.info(f"Saved {len(detections)} PII detections for claim {claim_id}")
