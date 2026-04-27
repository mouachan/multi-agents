"""Service générique pour récupérer les décisions."""

import logging
from typing import Any, Callable, Optional, Type
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_decision(
    entity_id: UUID,
    db: AsyncSession,
    decision_model: Type,
    id_column: str,
    response_schema: Type,
    entity_label: str,
    extra_fields_fn: Optional[Callable] = None,
) -> Any:
    """
    Récupère la dernière décision pour une entité.

    Args:
        entity_id: UUID de l'entité
        db: Session async SQLAlchemy
        decision_model: Modèle SQLAlchemy de la table decision
        id_column: Nom de la colonne FK (ex: "claim_id", "tender_id")
        response_schema: Schema Pydantic de réponse
        entity_label: Label pour les messages d'erreur (ex: "claim", "tender")
        extra_fields_fn: Fonction optionnelle (decision) -> dict de champs supplémentaires
    """
    try:
        fk_col = getattr(decision_model, id_column)
        query = (
            select(decision_model)
            .where(fk_col == entity_id)
            .order_by(decision_model.created_at.desc())
        )
        result = await db.execute(query)
        decision = result.scalar_one_or_none()

        if not decision:
            raise HTTPException(
                status_code=404,
                detail=f"No decision found for this {entity_label}",
            )

        # Build base fields
        fields = {
            "id": decision.id,
            id_column: entity_id,
            "initial_decision": decision.initial_decision.value if decision.initial_decision else None,
            "initial_confidence": decision.initial_confidence,
            "initial_reasoning": decision.initial_reasoning,
            "initial_decided_at": getattr(decision, "initial_decided_at", None),
            "final_decision": decision.final_decision.value if decision.final_decision else None,
            "final_decision_by": getattr(decision, "final_decision_by", None),
            "final_decision_by_name": getattr(decision, "final_decision_by_name", None),
            "final_decision_at": getattr(decision, "final_decision_at", None),
            "final_decision_notes": getattr(decision, "final_decision_notes", None),
            "decision": decision.decision.value,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "llm_model": decision.llm_model,
            "requires_manual_review": decision.requires_manual_review,
            "decided_at": getattr(decision, "decided_at", None) or decision.created_at,
            "metadata": decision.decision_metadata,
        }

        # Merge extra fields if provided
        if extra_fields_fn:
            fields.update(extra_fields_fn(decision))

        return response_schema(**fields)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting {entity_label} decision: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
