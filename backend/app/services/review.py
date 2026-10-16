"""Human review of the cases the agent hands over to a person.

A case waits for a reviewer when the agent's decision is the domain's review decision (claims
"manual_review", tenders "a_approfondir", postal "escalader", app/domains). The reviewer:

  1. finds it in the inbox (inbox()), with why it is there and since when;
  2. reads its brief (brief()):
       agent     the agent's recommendation and confidence, the reasons it hesitated, the points to check
                 (the "review" part of the agent's answer, see the agents' prompts)
       evidence  facts taken from the outputs of the agent's tools, without any LLM (evidence() of the
                 domain; in the case, app/services/cases.py)
       journal   the questions asked to the agent and its answers, the decisions taken;
  3. asks the domain's agent questions (ask_agent()): same agent, guardrails and read-only tools as the
     processing, traced in MLflow (session "review-<entity>-<id>");
  4. decides (decide()): one of the domain's human decisions. Going against the agent requires a
     justification. The case gets the status of the decision; the decision keeps who, when and why.
     The decision is also recorded as feedback on the MLflow trace of the processing
     ("reviewer_decision", and "agent_correct": the agent decided or suggested the same thing), which
     measures the agent's quality over time.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.agents import get_profile
from app.core import tracing
from app.core.auth import User, current_token
from app.domains import DomainSpec
from app.services import decisions
from app.services.a2a_client import get_a2a_client
from app.services.cases import case_number, case_to_api
from app.services.turn_trace import TurnTrace


class ReviewError(ValueError):
    """A review request that cannot be done (shown to the reviewer as is)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _value(enum_or_str) -> Optional[str]:
    return getattr(enum_or_str, "value", enum_or_str)


def agent_view(spec: DomainSpec, decision) -> Dict[str, Any]:
    """What the agent concluded, and what it would choose if it had to (its "suggestion")."""
    brief = (decision.decision_metadata or {}).get("review") or {}
    suggestion = brief.get("suggestion")
    agent_decision = _value(decision.initial_decision)
    return {
        "decision": agent_decision,
        "confidence": decision.initial_confidence,
        "reasoning": decision.initial_reasoning,
        # the agent's choice when it decided itself, else what it leans to (if a human choice)
        "suggestion": agent_decision if agent_decision in spec.human_decisions
        else suggestion if suggestion in spec.human_decisions else None,
        "reasons": brief.get("reasons") or ([decision.initial_reasoning] if decision.initial_reasoning else []),
        "checks": brief.get("checks") or [],
    }


async def inbox(db: AsyncSession, domains: Iterable[DomainSpec]) -> List[Dict[str, Any]]:
    """The cases waiting for a reviewer in these domains, the oldest first."""
    waiting = []
    for spec in domains:
        cases = (await db.execute(
            select(spec.model).where(spec.model.status == spec.review_status, spec.model.is_archived.is_(False))
        )).scalars().all()
        for case in cases:
            decision = await decisions.latest_decision(db, spec, case.id)
            view = agent_view(spec, decision) if decision else {}
            waiting.append({
                "domain": spec.name, "id": str(case.id), "number": case_number(spec, case),
                "waiting_since": case.processed_at or case.updated_at,
                "confidence": view.get("confidence"), "suggestion": view.get("suggestion"),
                "reason": (view.get("reasons") or [""])[0],
            })
    return sorted(waiting, key=lambda item: item["waiting_since"] or datetime.min.replace(tzinfo=timezone.utc))


async def brief(db: AsyncSession, spec: DomainSpec, case) -> Dict[str, Any]:
    """Everything the reviewer of a case needs (see the module doc)."""
    decision = await decisions.latest_decision(db, spec, case.id)
    if decision is None:
        raise ReviewError(f"This {spec.label.lower()} has not been processed yet")
    return {
        "case": case_to_api(spec, case),      # with the evidence of the processing
        "awaiting_review": _value(case.status) == spec.review_status,
        "agent": agent_view(spec, decision),
        # what the reviewer can decide, and the status the case then gets
        "choices": [{"decision": choice, "status": spec.status_after(choice)} for choice in spec.human_decisions],
        "decision": decisions.decision_to_api(decision),
        "journal": case.agent_logs or [],
    }


def _record(case, entry: Dict[str, Any]) -> None:
    case.agent_logs = [*(case.agent_logs or []), entry]
    flag_modified(case, "agent_logs")


async def ask_agent(db: AsyncSession, spec: DomainSpec, case, question: str, language: str, user: User) -> Dict[str, Any]:
    """Ask the domain's agent a question about the case; the exchange is kept in the journal."""
    question = question.strip()
    if not question:
        raise ReviewError("Empty question")
    decision = await decisions.latest_decision(db, spec, case.id)
    profile = get_profile(spec.agent_profile)
    if profile is None or not profile.a2a_url:
        raise ReviewError(f"The {spec.name} agent is not deployed")

    view = agent_view(spec, decision) if decision else {}
    message = "\n".join([
        f"A reviewer must decide on {spec.label.lower()} {case_number(spec, case)}, which your processing "
        f"handed over to a human (your decision: {view.get('decision')}, confidence {view.get('confidence')}).",
        f"Your reasoning was: {view.get('reasoning') or '-'}",
        "Answer the reviewer's question about this case. Use your tools if you need facts. "
        "Do not take or save any decision: the reviewer decides.",
        "", f"Reviewer's question: {question}",
    ])
    session = f"review-{spec.entity}-{case.id}"
    trace = TurnTrace(f"review | {spec.entity} {case_number(spec, case)}", {"message": question}, session_id=session)
    metadata = {"profile": profile.id, "mode": "chat", "language": language,
                "tools": spec.processing_tools,   # read-only tools: no save_*_decision in a review
                "user_token": current_token()}
    traceparent = trace.start_a2a(profile.id)
    if traceparent:
        metadata["traceparent"] = traceparent
    result: Dict[str, Any] = {}
    try:
        result = await get_a2a_client().send(base_url=profile.a2a_url, message=message,
                                             context_id=session, metadata=metadata)
    finally:
        trace.finish(result.get("output", ""), {"agent_id": profile.id})

    entry = {"type": "question", "question": question, "answer": result.get("output") or "",
             "by": user.username, "at": _now(), "trace": trace.link()}
    _record(case, entry)
    await db.commit()
    return entry


async def decide(db: AsyncSession, spec: DomainSpec, case, choice: str, justification: str, user: User) -> Dict[str, Any]:
    """The reviewer's final decision on the case (see the module doc)."""
    if choice not in spec.human_decisions:
        raise ReviewError(f"Unknown decision '{choice}' (expected one of {', '.join(spec.human_decisions)})")
    decision = await decisions.latest_decision(db, spec, case.id)
    if decision is None:
        raise ReviewError(f"This {spec.label.lower()} has not been processed yet")
    justification = (justification or "").strip()
    agent_choice = agent_view(spec, decision)["suggestion"]
    if agent_choice and agent_choice != choice and not justification:
        raise ReviewError("Explain why you decide differently from the agent")

    decision.final_decision = choice
    decision.final_decision_by = user.username
    decision.final_decision_by_name = user.username
    decision.final_decision_at = datetime.now(timezone.utc)
    decision.final_decision_notes = justification or None
    decision.decision = choice
    decision.requires_manual_review = False
    case.status = spec.status_after(choice)
    _record(case, {"type": "decision", "decision": choice, "agent_decision": _value(decision.initial_decision),
                   "justification": justification, "by": user.username, "at": _now()})
    await db.commit()
    trace_id = ((case.meta or {}).get("trace") or {}).get("mlflow_trace_id")
    await tracing.log_feedback(trace_id, "reviewer_decision", choice, user.username, justification or None)
    await tracing.log_feedback(trace_id, "agent_correct", agent_choice == choice, user.username,
                               f"agent: {agent_choice or _value(decision.initial_decision)}, reviewer: {choice}")
    return decisions.decision_to_api(decision)
