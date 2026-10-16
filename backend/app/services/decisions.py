"""Decisions on a case, and the case status that follows from them.

Every processing adds a row to the domain's decision table (history); the most recent row is the
case's current decision. The agent's decision fills `initial_*` and the current values; a reviewer's
decision (app/services/review.py) fills `final_*` and replaces the current values.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains import DomainSpec


# Parts of the agent's answer kept with its decision: the facts it relied on, the brief for the
# reviewer (reasons, points to check), and the English version of the reasoning (shown in English)
AGENT_DETAILS = ("evidence", "review", "reasoning_en")


async def latest_decision(db: AsyncSession, spec: DomainSpec, case_id) -> Optional[Any]:
    """The current decision of a case (None before its first processing)."""
    table = spec.decision_model
    return (await db.execute(
        select(table).where(getattr(table, spec.fk) == case_id).order_by(table.created_at.desc()).limit(1)
    )).scalar_one_or_none()


def model_display_name(model: Optional[str]) -> Optional[str]:
    """"maas/llama-scout-17b" -> "llama-scout-17b"."""
    return model.split("/")[-1] if model else None


async def save_agent_decision(db: AsyncSession, spec: DomainSpec, case, decision: Dict[str, Any],
                              model: Optional[str]) -> Any:
    """Record the agent's decision and set the case status that follows from it.

    `decision` is what the agent returned: recommendation, confidence, reasoning, evidence, and
    for a case handed to a human the review brief (reasons and points to check). A value outside
    the domain's decisions sends the case to human review.
    """
    value = decision.get("recommendation")
    if value not in spec.statuses_by_decision:
        value = spec.review_decision
    confidence = float(decision.get("confidence") or 0.0)
    reasoning = decision.get("reasoning") or ""
    now = datetime.now(timezone.utc)
    row = spec.decision_model(
        **{spec.fk: case.id},
        initial_decision=value, initial_confidence=confidence, initial_reasoning=reasoning, initial_decided_at=now,
        decision=value, confidence=confidence, reasoning=reasoning, decided_at=now,
        llm_model=model_display_name(model),
        requires_manual_review=(value == spec.review_decision),
        decision_metadata={key: decision[key] for key in AGENT_DETAILS if decision.get(key)},
    )
    db.add(row)
    case.status = spec.status_after(value)
    await db.flush()
    return row


def decision_to_api(row) -> Dict[str, Any]:
    """The decision as the API returns it (same shape for every domain)."""
    meta = row.decision_metadata or {}
    return {
        "id": str(row.id),
        "decision": _value(row.decision),
        "confidence": row.confidence,
        "reasoning": row.reasoning,
        "reasoning_en": meta.get("reasoning_en"),
        "decided_at": row.decided_at,
        "llm_model": row.llm_model,
        "requires_manual_review": row.requires_manual_review,
        # What the agent decided, and what a reviewer decided afterwards (if anyone did)
        "agent": {
            "decision": _value(row.initial_decision),
            "confidence": row.initial_confidence,
            "reasoning": row.initial_reasoning,
            "decided_at": row.initial_decided_at,
        },
        "reviewer": None if row.final_decision is None else {
            "decision": _value(row.final_decision),
            "user": row.final_decision_by,
            "name": row.final_decision_by_name,
            "decided_at": row.final_decision_at,
            "justification": row.final_decision_notes,
        },
        "review": meta.get("review") or {},     # the agent's brief for a reviewer (reasons, checks)
    }


def _value(enum_or_str) -> Optional[str]:
    return getattr(enum_or_str, "value", enum_or_str)
