"""Generic A2A executor — domain logic (prompts, tools) comes from agent profiles.

Request metadata (A2A Message.metadata, all optional) sent by the backend:
    profile               profile id (e.g. "courrier-info"); defaults to the agent's first profile
    mode                  "chat" (conversational wrapper) or "process" (batch processing,
                          OGX_PROCESS_MODEL)
    tools                 subset of the profile tools to use, in this order (never extends the profile)
    decision_values       allowed recommendations (mode=process): the user message asks for a
                          final JSON block {recommendation, confidence, reasoning}
    language              "fr" | "en" — enforced via the language-rule prompt
    previous_response_id  OGX response id to chain the conversation
    instructions_override session custom prompt (replaces the registry prompt)

Final task status message metadata returned to the caller:
    output, decision, tool_calls, response_id, model, usage, prompt{name,version,source},
    guardrails{input,output}, caller (SPIFFE ID), duration_ms

Working status updates (metadata "event"): tool_call / tool_result, and guardrails
(stage input|output). With output rails on, the answer is masked sentence by sentence
and streamed as soon as each sentence is masked (no unmasked PII ever leaves the agent).
"""
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import uuid

from a2a.helpers.proto_helpers import new_task, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, Role, TaskState
from google.protobuf import json_format, struct_pb2

from . import spiffe_auth, tracing
from .config import AgentSettings
from .guardrails import Guardrails, blocked_message
from .ogx_client import OGXClient
from .prompts import PromptStore, render
from .response_parser import ResponseParser

logger = logging.getLogger(__name__)

CHAT_WRAPPER_PROMPT = "chat-agent-wrapper"
LANGUAGE_RULE_PROMPT = "orchestrator-language-rule"
EMPTY_ANSWER_RETRY = "Answer the user's request now, in the user's language."
# Batch processing (mode=process): a guided workflow. Llama-scout writes several tool calls
# as Python-like text ("[get_tender(...), ocr_document(...)]") when it wants many tools at
# once, which the MaaS does not parse (OGX then fails on the arguments). With one tool
# offered per step and tool_choice=required it always emits structured calls.
OPTIONAL_TOOLS = {"run_python", "search_knowledge_base", "search_courrier_knowledge"}
GUIDED_STEP = ("\n\nAutomated processing, step {i}/{n}: call the {tool} tool now for this "
               "request, with the identifiers given above.")
GUIDED_NEXT = "Step {i}/{n}: call the {tool} tool now for this request."
# The backend parses the decision from this block (chat prompts forbid JSON)
GUIDED_FINAL = """All workflow tools have returned. This request comes from the automated processing
pipeline, not from a chat: write your analysis based on the tool results{optional}, then end
your answer with exactly one JSON code block:
```json
{{"recommendation": <one of {values}>, "confidence": <number between 0.0 and 1.0>, "reasoning": "<2 to 4 sentences>"}}
```"""
# End of a sentence: punctuation (or a newline) followed by whitespace
SENTENCE_END = re.compile(r"[.!?:;\n](?=\s)")
TEXT_TOOL_CALL_RETRY = (
    "You wrote tool calls as text instead of calling them. "
    "Use the function calling mechanism to actually execute the tools now."
)


@dataclass
class Profile:
    prompt: str
    tools: List[str]
    model: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


def _metadata(context: RequestContext) -> Dict[str, Any]:
    msg = context.message
    if msg is None or not msg.HasField("metadata"):
        return {}
    return json_format.MessageToDict(msg.metadata)


def _message(text: str, context: Optional[RequestContext] = None,
             metadata: Optional[Dict[str, Any]] = None) -> Message:
    msg = Message(role=Role.ROLE_AGENT, message_id=str(uuid.uuid4()), parts=[new_text_part(text)])
    if context is not None:
        msg.context_id = context.context_id or ""
        msg.task_id = context.task_id or ""
    if metadata:
        meta = struct_pb2.Struct()
        json_format.ParseDict(_jsonable(metadata), meta)
        msg.metadata.CopyFrom(meta)
    return msg


def _jsonable(value: Any) -> Any:
    """Coerce values into what google.protobuf.Struct accepts (no None in lists, str keys)."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


class BaseA2AExecutor(AgentExecutor):
    def __init__(self, settings: AgentSettings, profiles: Dict[str, Profile]):
        self.settings = settings
        self.profiles = profiles
        self.default_profile = next(iter(profiles))
        self.llm = OGXClient(
            settings.ogx_endpoint,
            settings.ogx_timeout,
            mcp_gateway_url=settings.mcp_gateway_url,
            mcp_server_url_template=settings.mcp_server_url_template,
        )
        self.prompts = PromptStore(settings)
        self.guardrails = Guardrails(settings)
        self.parser = ResponseParser()
        self._mask_stream = self.guardrails.enabled and settings.guardrails_buffer_output

    async def _instructions(self, profile: Profile, meta: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        override = meta.get("instructions_override")
        if override:
            base, prompt_info = override, {"name": profile.prompt, "version": None, "source": "session"}
        else:
            p = await self.prompts.get(profile.prompt)
            base, prompt_info = p.text, p.info()

        instructions = base
        if meta.get("mode", "chat") == "chat":
            wrapper = await self.prompts.get(CHAT_WRAPPER_PROMPT)
            instructions = render(wrapper.text, agent_instructions=base) if wrapper.text else base
        lang = meta.get("language")
        if lang:
            rule = await self.prompts.get(LANGUAGE_RULE_PROMPT)
            if rule.text:
                instructions += render(rule.text, lang_name="English" if lang == "en" else "French")
        return instructions, prompt_info

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        start = time.time()
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            # The v2 request handler expects the Task itself before any status update
            history = [context.message] if context.message else []
            await event_queue.enqueue_event(new_task(
                context.task_id, context.context_id, TaskState.TASK_STATE_SUBMITTED, history=history,
            ))
        await updater.start_work()

        meta = _metadata(context)
        profile_id = meta.get("profile") or self.default_profile
        profile = self.profiles.get(profile_id)
        if profile is None:
            await updater.reject(_message(f"Unknown profile '{profile_id}'", context))
            return

        user_text = context.get_user_input()
        if not user_text:
            await updater.reject(_message("Empty message.", context))
            return

        # Input rails: block (jailbreak / off-topic) or mask PII before it reaches the LLM
        gin = await self.guardrails.check_input(user_text)
        await self._guardrails_event(updater, "input", gin.to_dict())
        if not gin.allowed:
            refusal = blocked_message(meta.get("language"))
            await updater.reject(_message(refusal, context, metadata={
                "output": refusal, "guardrails": {"input": gin.to_dict()},
            }))
            return
        llm_input = gin.text

        try:
            instructions, prompt_info = await self._instructions(profile, meta)
            process = meta.get("mode") == "process"
            model = profile.model or (process and self.settings.ogx_process_model) or self.settings.ogx_default_model
            requested = meta.get("tools")
            # caller order: the guided workflow runs the tools in this order (OCR before the
            # precedent search, which reads the OCR text)
            tools = [t for t in requested if t in profile.tools] if requested else profile.tools
            previous_response_id = meta.get("previous_response_id")

            run = self._run
            if process and meta.get("decision_values") and tools:
                values = ", ".join(f'"{v}"' for v in meta["decision_values"])
                run = lambda u, m, i, inp, t, prev: self._guided(u, m, i, inp, t, prev, values)
            try:
                result = await run(updater, model, instructions, llm_input, tools, previous_response_id)
            except RuntimeError as e:
                # OGX failed (e.g. malformed tool-call arguments): retry once, with the other
                # model when one is configured
                fallback = next((m for m in (self.settings.ogx_process_model, self.settings.ogx_default_model)
                                 if m and m != model), model)
                logger.warning("OGX response failed with %s (%s) — retrying with %s", model, e, fallback)
                await updater.update_status(TaskState.TASK_STATE_WORKING, _message(
                    f"fallback to {fallback}", metadata={"event": "fallback", "from": model, "to": fallback,
                                                         "reason": str(e)[:200]}))
                model = fallback
                result = await run(updater, model, instructions, llm_input, tools, previous_response_id)

            # Retry once if the model wrote tool calls as plain text
            if not result["tool_calls"] and self.parser.contains_text_tool_calls(result["output"]):
                logger.warning("Model wrote tool calls as text — retrying with function calling")
                retry = await self._run(updater, model, instructions, TEXT_TOOL_CALL_RETRY,
                                        tools, result["response_id"])
                retry["usage"] = _merge_usage(result["usage"], retry["usage"])
                result = retry

            # Retry once if the model returned an empty answer (seen with Llama on some prompts)
            if not result["streamed_output"].strip() and result["guardrails_output"]["allowed"]:
                logger.warning("Empty answer — retrying once")
                retry = await self._run(updater, model, instructions, EMPTY_ANSWER_RETRY,
                                        tools, result["response_id"])
                retry["usage"] = _merge_usage(result["usage"], retry["usage"])
                retry["tool_calls"] = result["tool_calls"] + retry["tool_calls"]
                result = retry

            gout = result["guardrails_output"]
            if not gout["allowed"]:
                output = blocked_message(meta.get("language"))
                await updater.add_artifact([new_text_part(output)], artifact_id="response",
                                           name="response", append=False, last_chunk=True)
            else:
                output = result["streamed_output"]
            await self._guardrails_event(updater, "output", gout)

            decision = self.parser.parse_decision(output) if meta.get("mode") == "process" else {}
            duration_ms = int((time.time() - start) * 1000)
            final = {
                "output": output,
                "decision": decision,
                "tool_calls": result["tool_calls"],
                "response_id": result["response_id"],
                "model": result["model"],
                "usage": result["usage"],
                "duration_ms": duration_ms,
                "profile": profile_id,
                "prompt": prompt_info,
                "guardrails": {"input": gin.to_dict(), "output": gout},
                "caller": spiffe_auth.current_caller(),
                "agent_id": self.settings.agent_id,
            }

            tracing.log_agent_trace(
                agent_id=self.settings.agent_id,
                profile=profile_id,
                model=result["model"],
                input_text=llm_input,
                output_text=output,
                tool_calls=result["tool_calls"],
                usage=result["usage"],
                response_id=result["response_id"],
                duration_ms=duration_ms,
                metadata={"prompt": prompt_info, "decision": decision, "task_id": context.task_id,
                          "context_id": context.context_id, **profile.tags},
            )

            await updater.complete(_message(output, context, metadata=final))

        except Exception as e:
            logger.error("Agent %s/%s failed: %s", self.settings.agent_id, profile_id, e, exc_info=True)
            await updater.failed(_message(f"Agent error: {e}", context))

    async def _guardrails_event(self, updater: TaskUpdater, stage: str, result: Dict[str, Any]) -> None:
        if not self.guardrails.enabled:
            return
        await updater.update_status(
            TaskState.TASK_STATE_WORKING,
            _message(f"guardrails {stage}", metadata={
                "event": "guardrails", "stage": stage,
                "status": result.get("status"), "rail": result.get("rail"),
            }),
        )

    async def _guided(self, updater: TaskUpdater, model, instructions, input_message, tools,
                      previous_response_id, values: str) -> Dict[str, Any]:
        """Batch processing: one OGX call per workflow tool (tool_choice=required, chained by
        previous_response_id, no text shown), then the final analysis + JSON decision, where
        the optional tools (e.g. run_python for the payout) remain available."""
        forced = [t for t in tools if t not in OPTIONAL_TOOLS and not t.startswith("save_")]
        optional = [t for t in tools if t in OPTIONAL_TOOLS]
        tool_calls: List[Dict[str, Any]] = []
        usage: Dict[str, Any] = {}
        response_id = previous_response_id
        for i, tool in enumerate(forced, 1):
            # Only the templates are formatted: the request may contain braces (JSON data)
            step = GUIDED_STEP if i == 1 else GUIDED_NEXT
            step_input = (input_message if i == 1 else "") + step.format(i=i, n=len(forced), tool=tool)
            # max_tool_calls=1: with tool_choice=required OGX would otherwise call the tool
            # again on every turn (4 get_reclamation calls in one step)
            done: Dict[str, Any] = {}
            for attempt in (1, 2):
                logger.info("Guided step %d/%d: %s (attempt %d)", i, len(forced), tool, attempt)
                try:
                    done = await self._run(updater, model, instructions, step_input, [tool], response_id,
                                           tool_choice="required", max_tool_calls=1, emit_text=False)
                    break
                except RuntimeError as e:
                    # Intermittent: malformed tool-call arguments ("Extra data"), MaaS disconnects
                    logger.warning("Guided step %s failed (attempt %d): %s", tool, attempt, e)
            if not done:
                # Keep going: the decision is made with the other results
                tool_calls.append({"name": tool, "error": "step failed after 2 attempts"})
                continue
            tool_calls += done.get("tool_calls", [])
            usage = _merge_usage(usage, done.get("usage") or {})
            response_id = done.get("response_id") or response_id
        final_input = GUIDED_FINAL.format(
            values=values,
            optional=f" (you may use {', '.join(optional)} if useful)" if optional else "")
        if not forced:
            final_input = input_message + "\n\n" + final_input
        final = await self._run(updater, model, instructions, final_input, optional, response_id)
        final["tool_calls"] = tool_calls + final.get("tool_calls", [])
        final["usage"] = _merge_usage(usage, final.get("usage") or {})
        return final

    async def _run(self, updater: TaskUpdater, model, instructions, input_message, tools,
                   previous_response_id, tool_choice: Optional[str] = None,
                   max_tool_calls: Optional[int] = None, emit_text: bool = True) -> Dict[str, Any]:
        """Stream one OGX response, forwarding (masked) text and tool activity as A2A events.

        The first chunk starts (or, on a retry, replaces) the "response" artifact.
        Returns the OGX `done` event plus `streamed_output` (the text actually sent) and
        `guardrails_output` (aggregated output rails verdict).
        """
        sent: List[str] = []
        pending = ""
        verdict: Dict[str, Any] = {"allowed": True, "status": "passed", "rail": None, "error": None}

        async def emit(chunk: str) -> None:
            if not chunk or not verdict["allowed"] or not emit_text:
                return
            if self._mask_stream and chunk.strip():
                core = chunk.strip()
                lead, trail = chunk[:len(chunk) - len(chunk.lstrip())], chunk[len(chunk.rstrip()):]
                g = await self.guardrails.check_output(core)
                if not g.allowed:
                    verdict.update(allowed=False, status="blocked", rail=g.rail)
                    return
                if g.status == "modified":
                    verdict.update(status="modified", rail=g.rail)
                elif g.status == "error" and verdict["status"] == "passed":
                    verdict.update(status="error", error=g.error)
                chunk = lead + g.text + trail
            first = not sent
            sent.append(chunk)
            await updater.add_artifact([new_text_part(chunk)], artifact_id="response",
                                       name="response", append=not first)

        done: Dict[str, Any] = {}
        async for ev in self.llm.stream(
            model=model,
            instructions=instructions,
            input_message=input_message,
            tools=tools,
            max_tokens=self.settings.ogx_max_tokens,
            previous_response_id=previous_response_id,
            tool_choice=tool_choice,
            max_tool_calls=max_tool_calls,
        ):
            etype = ev["type"]
            if etype == "text_delta":
                pending += ev["delta"]
                if not self._mask_stream:
                    await emit(pending)
                    pending = ""
                    continue
                ends = list(SENTENCE_END.finditer(pending))
                if ends:
                    cut = ends[-1].end()
                    chunk, pending = pending[:cut], pending[cut:]
                    await emit(chunk)
            elif etype in ("tool_call", "tool_result"):
                await updater.update_status(
                    TaskState.TASK_STATE_WORKING,
                    _message(ev["name"], metadata={
                        "event": etype, "name": ev["name"], "server": ev.get("server", ""),
                        "status": ev.get("status", "in_progress"),
                    }),
                )
            elif etype == "done":
                done = ev
        await emit(pending)
        if not sent and done.get("output") and emit_text:
            # No text deltas (non-streamed answer): send the whole output once
            await emit(done["output"])
        done["streamed_output"] = "".join(sent)
        done["guardrails_output"] = verdict
        return done

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()


def _merge_usage(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    keys = set(a) | set(b)
    return {k: (a.get(k, 0) or 0) + (b.get(k, 0) or 0)
            for k in keys if isinstance(a.get(k, 0), (int, float)) and isinstance(b.get(k, 0), (int, float))}
