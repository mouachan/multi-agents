"""One chat turn: the user's message, the agent's streamed answer, both saved in the conversation.

    1. the message is saved, then routed to an agent profile the user may use (routing.py)
    2. it is sent to the profile's A2A agent, which streams its answer: tool calls, guardrails
       verdicts, text (the events below are forwarded to the UI as they come)
    3. the answer is saved with the trace of the turn, and follow-up actions are proposed

Events sent to the UI (server-sent events, app/api/chat.py):
    routing        the chosen profile, the method (semantic / llm / sticky / keywords) and the scores
    agent_resolved the profile that answers
    a2a            the A2A request and task states (agent card, authentication, task id)
    guardrails     NeMo verdicts on the message (input) and the answer (output)
    governance     the agent's tools the user's profile does not allow (withheld_tools)
    tool_call / tool_result   each MCP tool call of the agent
    text_delta / text_replace the answer, as it is written
    done           the end: usage, model, tool calls, follow-up actions, MLflow trace link
    error          the turn failed

The turn is one MLflow trace (session = the conversation): the agent's spans join it.
"""
import logging
import re
from typing import Any, AsyncIterator, Dict, Optional

from app.agents import get_profile, profiles_for_domains
from app.core.auth import User, current_token
from app.models.conversation import ChatMessage, ChatSession
from app.services.a2a_client import get_a2a_client
from app.services.chat.config import detect_language, follow_up_actions
from app.services.chat.routing import route_message
from app.services.guardrails import mask_by_pattern
from app.services.turn_trace import TurnTrace

logger = logging.getLogger(__name__)

FORWARDED_EVENTS = {"tool_call", "tool_result", "text_delta", "text_replace", "a2a", "guardrails", "governance"}


def clean_for_display(text: str) -> str:
    """Remove what the model sometimes writes but is not for the reader: tool calls written as text,
    JSON blocks (e.g. the decision of a processing), "First I will..." narration."""
    text = re.sub(r"\[\w+\(.*?\)\]", "", text, flags=re.DOTALL)
    text = re.sub(r'\[\s*\{\s*"name"\s*:\s*"\w+"\s*,\s*"arguments"\s*:\s*\{[^}]*\}\s*\}\s*\]', "", text, flags=re.DOTALL)
    text = re.sub(r"```json\s*\n.*?\n```", "", text, flags=re.DOTALL)
    text = re.sub(r"(?:First|Next|Then|Now|Finally),?\s+I\s+will\s+[^\n]*\n?", "", text)
    text = re.sub(r"https?://[^/\s)]+(/api/v1/)", r"\1", text)   # invented host in front of an API link
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def token_usage(usage: Dict[str, Any]) -> Optional[Dict[str, int]]:
    if not usage:
        return None
    prompt = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
    completion = usage.get("output_tokens") or usage.get("completion_tokens") or 0
    return {"prompt_tokens": prompt, "completion_tokens": completion,
            "total_tokens": usage.get("total_tokens") or prompt + completion}


async def chat_turn(db, session: ChatSession, message: str, user: User) -> AsyncIterator[Dict[str, Any]]:
    """Process one message of the conversation (see the module doc); yields the UI events."""
    trace = TurnTrace(f"chat | {message[:80].strip()}", {"message": message}, session_id=session.session_id)
    try:
        async for event in _turn(db, session, message, user, trace):
            trace.add(event)
            yield event
    finally:
        trace.close()


async def _turn(db, session: ChatSession, message: str, user: User, trace: TurnTrace) -> AsyncIterator[Dict[str, Any]]:
    db.add(ChatMessage(session_id=session.id, role="user", content=message))
    await db.commit()

    allowed = {profile.id for profile in profiles_for_domains(user.domains)}
    if not allowed:
        yield {"type": "error", "message": "Your profile gives access to no agent"}
        return
    try:
        routing = await route_message(message, session.agent_id, allowed)
    except LookupError as e:
        yield {"type": "error", "message": str(e)}
        return
    yield routing.to_event()

    profile = get_profile(routing.agent_id)
    metadata = dict(session.session_metadata or {})
    if profile.id != session.agent_id:          # another agent: a new conversation thread for OGX
        session.agent_id = profile.id
        metadata.pop("last_response_id", None)
    if not profile.a2a_url:
        yield {"type": "error", "message": f"The {profile.domain} agent is not deployed"}
        return
    yield {"type": "agent_resolved", "agent_id": profile.id}

    language = detect_language(message)
    a2a_metadata = {
        "profile": profile.id, "mode": "chat", "language": language,
        "previous_response_id": metadata.get("last_response_id"),
        "instructions_override": metadata.get("custom_prompt"),   # prompt editor (prompts.py)
        "user_token": current_token(),   # the agent presents it to the MCP Gateway (per-user tool rights)
    }
    if user.tools is not None:
        a2a_metadata["allowed_tools"] = sorted(user.tools)   # the agent only offers these, explains the others
    traceparent = trace.start_a2a(profile.id)
    if traceparent:
        a2a_metadata["traceparent"] = traceparent

    done: Dict[str, Any] = {}
    streamed = False
    try:
        async for event in get_a2a_client().stream(base_url=profile.a2a_url, message=message,
                                                    context_id=session.session_id, metadata=a2a_metadata):
            if event.get("type") in FORWARDED_EVENTS:
                streamed = streamed or event["type"] in ("text_delta", "text_replace")
                yield event
            elif event.get("type") == "done":
                done = event
    except Exception as e:
        logger.exception("Chat turn with %s failed", profile.id)
        yield {"type": "error", "message": str(e)}
        return

    answer = done.get("output", "")
    if answer and not streamed:   # e.g. a message refused by the guardrails comes in the final status only
        yield {"type": "text_delta", "delta": answer}
    shown = clean_for_display(answer)
    if (done.get("guardrails") or {}).get("output", {}).get("status") == "error":
        shown = mask_by_pattern(shown)      # NeMo could not check the answer: mask by pattern
    if shown != answer:
        yield {"type": "text_replace", "text": shown}

    if done.get("response_id"):
        metadata["last_response_id"] = done["response_id"]
    session.session_metadata = metadata
    tool_calls = [{"name": call["name"], "status": "error" if call.get("error") else "completed",
                   "server_label": call.get("server")}
                  for call in done.get("tool_calls", []) if isinstance(call, dict) and call.get("name")]
    final = {
        "type": "done",
        "response_id": done.get("response_id"),
        "usage": token_usage(done.get("usage") or {}),
        "tool_calls": tool_calls,
        "agent_id": profile.id,
        "model_id": (done.get("model") or "").split("/")[-1] or None,
        "suggested_actions": follow_up_actions(profile.id, shown, language),
        "a2a": {**(done.get("a2a") or {}), "status": done.get("status"), "prompt": done.get("prompt", {}),
                "guardrails": done.get("guardrails", {})},
        "trace": trace.link(),
    }
    db.add(ChatMessage(
        session_id=session.id, role="assistant", content=shown, agent_id=profile.id,
        suggested_actions=final["suggested_actions"] or None, tool_calls=tool_calls or None,
        token_usage=final["usage"], model_id=final["model_id"], trace=trace.finish(shown, final),
    ))
    await db.commit()
    yield final
