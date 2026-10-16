"""Processing of a case by its domain's A2A agent (the "Process" button of a case page).

POST /api/v1/<domain>/<id>/process marks the case "processing", starts process_case() in the background
(app/services/background.py) and returns at once; the page polls the case. The job:

  1. sends the processing request to the domain's agent (A2A): the prompt file of the domain, the case
     data, the tools of the guided workflow (run in this order) and the decision values;
  2. saves the agent's decision and the status that follows from it (app/services/decisions.py). When a
     tool removed instructions aimed at the AI from a document (prompt injection, MCP servers'
     shared/injection.py), the case goes to a person whatever the agent decided;
  3. keeps the processing steps (each tool call and its output) in the case metadata, for the page;
  4. embeds the case document, so that later cases find it as a precedent (app/services/embeddings.py);
  5. for claims, records the types of personal data found in the documents (app/services/pii_report.py).

The whole processing is one MLflow trace (session "<entity>-<id>"): the agent's spans join it.
"""
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import get_profile
from app.core.auth import current_token
from app.core.prompts import load_prompt
from app.domains import DomainSpec
from app.services import decisions
from app.services.a2a_client import get_a2a_client
from app.services.cases import case_data, case_number
from app.services.embeddings import embed_case_document
from app.services.pii_report import record_personal_data
from app.services.turn_trace import TurnTrace

logger = logging.getLogger(__name__)

OCR_PREVIEW_CHARS = 4000   # OCR text already known, given to the agent with the request
INJECTION_REASON = ("Le document contient {count} instruction(s) destinée(s) à l'IA, retirée(s) avant l'analyse "
                    "(tentative de manipulation) : vérifier le document avant de décider.")


def job_name(spec: DomainSpec, case_id) -> str:
    return f"process-{spec.entity}-{case_id}"


async def processing_request(db: AsyncSession, spec: DomainSpec, case) -> str:
    """The message sent to the agent: what to do (prompt file), the case data, the OCR text if known."""
    lines = [load_prompt(spec.message_file), "", f"# {spec.label} {case_number(spec, case)}"]
    lines += [f"- {key}: {value}" for key, value in case_data(spec, case).items() if value not in (None, "")]
    document = (await db.execute(
        select(spec.document_model).where(getattr(spec.document_model, spec.fk) == case.id)
        .order_by(spec.document_model.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if document and document.raw_ocr_text:
        lines += ["", "## Document (OCR text)", document.raw_ocr_text[:OCR_PREVIEW_CHARS]]
    return "\n".join(lines)


def processing_steps(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The tool calls of the agent, as shown in the processing timeline of the case page."""
    steps = []
    for call in tool_calls:
        try:
            output = json.loads(call.get("output") or "null")
        except (TypeError, ValueError):
            output = {"raw_text": call.get("output")}
        if not isinstance(output, dict):
            output = {"result": output}
        seconds = output.get("processing_time_seconds")
        steps.append({
            "step_name": call.get("name", "unknown"),
            "status": "failed" if call.get("error") else "completed",
            "duration_ms": int(seconds * 1000) if isinstance(seconds, (int, float)) else None,
            "output_data": output,
            "error_message": call.get("error"),
        })
    return steps


def instructions_removed(tool_calls: List[Dict[str, Any]]) -> int:
    """How many instructions aimed at the AI the tools removed from the documents."""
    return sum(step["output_data"].get("security", {}).get("instructions_removed", 0)
               for step in processing_steps(tool_calls))


def handed_over(spec: DomainSpec, decision: Dict[str, Any], removed: int) -> Dict[str, Any]:
    """The agent's decision turned into a review: a document tried to manipulate the agent."""
    review = dict(decision.get("review") or {})
    review["reasons"] = [INJECTION_REASON.format(count=removed), *(review.get("reasons") or [])]
    review["checks"] = ["Ouvrir le document et lire l'instruction retirée", *(review.get("checks") or [])]
    agent_choice = decision.get("recommendation")
    if agent_choice in spec.human_decisions:      # what the agent had decided becomes its suggestion
        review["suggestion"] = agent_choice
    return {**decision, "recommendation": spec.review_decision, "review": review}


async def ask_agent(spec: DomainSpec, case, request: str, prompt_alias: Optional[str] = None,
                    session: Optional[str] = None) -> Dict[str, Any]:
    """Run the processing task on the domain's A2A agent; returns the agent's final answer.

    prompt_alias: version of the agent's prompt (registry alias, default "production"; evaluations);
    session: MLflow session of the trace (default "<entity>-<id>", the case's processings).
    """
    profile = get_profile(spec.agent_profile)
    if profile is None or not profile.a2a_url:
        raise RuntimeError(f"The {spec.name} agent is not deployed")
    session = session or f"{spec.entity}-{case.id}"
    trace = TurnTrace(f"process | {spec.entity} {case_number(spec, case)}", {"message": request}, session_id=session)
    metadata = {
        "profile": profile.id,
        "mode": "process",
        "tools": spec.processing_tools,
        "decision_values": spec.decision_values,
        "review_decision": spec.review_decision,      # with it, the agent writes the brief for the reviewer
        "human_decisions": spec.human_decisions,
        "user_token": current_token(),   # the agent presents it to the MCP Gateway (per-user tool rights)
    }
    if prompt_alias:
        metadata["prompt_alias"] = prompt_alias
    traceparent = trace.start_a2a(profile.id)
    if traceparent:
        metadata["traceparent"] = traceparent
    result: Dict[str, Any] = {}
    try:
        result = await get_a2a_client().send(base_url=profile.a2a_url, message=request,
                                             context_id=session, metadata=metadata)
        if result.get("status") != "completed":
            raise RuntimeError(result.get("output") or f"agent task {result.get('status')}")
        return {**result, "trace": trace.link()}
    except Exception as e:
        trace.add({"type": "error", "message": str(e)})
        raise
    finally:
        trace.finish(result.get("output", ""), {"agent_id": profile.id, "a2a": result.get("a2a")})


async def process_case(db: AsyncSession, spec: DomainSpec, case_id) -> None:
    """Background job: the agent processes the case, its decision is saved (see the module doc)."""
    case = await db.get(spec.model, case_id)
    started = time.monotonic()
    try:
        result = await ask_agent(spec, case, await processing_request(db, spec, case))
        decision = result.get("decision") or {}
        removed = instructions_removed(result.get("tool_calls", []))
        if removed:
            logger.warning("%s %s: %d instruction(s) aimed at the AI removed from its documents",
                           spec.label, case_number(spec, case), removed)
            decision = handed_over(spec, decision, removed)
        await decisions.save_agent_decision(db, spec, case, decision, result.get("model"))
        case.meta = {**(case.meta or {}),
                     "processing_steps": processing_steps(result.get("tool_calls", [])),
                     "usage": result.get("usage") or {},
                     "response_id": result.get("response_id"),
                     "trace": result.get("trace")}
        case.processed_at = datetime.now(timezone.utc)
        case.total_processing_time_ms = int((time.monotonic() - started) * 1000)
        await db.commit()
    except Exception:
        logger.exception("Processing of %s %s failed", spec.entity, case_id)
        await db.rollback()
        case = await db.get(spec.model, case_id)
        case.status = "failed"
        await db.commit()
        return
    logger.info("%s %s processed: %s", spec.label, case_number(spec, case), case.status)
    await embed_case_document(db, spec, case.id)
    if spec.pii_report:
        await record_personal_data(db, case)
