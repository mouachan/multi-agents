"""A2A executor shared by the domain agents; what differs per agent is its profiles (agent.py).

A request is one A2A message. Its metadata (all optional) comes from the backend:
    profile               profile id (e.g. "courrier_info"); default: the agent's first profile
    mode                  "chat" (the chat rules are added to the prompt) or "process" (case processing)
    tools                 subset of the profile tools, in this order (never extends the profile)
    decision_values       mode=process: the decisions the agent may take (see decision.py)
    review_decision       mode=process: the decision that hands the case to a person
    human_decisions       mode=process: what that person can decide
    language              "fr" | "en", enforced by the language-rule prompt
    previous_response_id  OGX response to continue (the conversation)
    instructions_override prompt of the chat session (replaces the registry prompt)
    user_token            OpenShift token of the end user, presented to the MCP Gateway
    traceparent           W3C trace of the caller: the agent's spans join it

The answer is streamed as the "response" artifact; tool activity and guardrails verdicts are
"working" status updates (metadata "event": tool_call | tool_result | guardrails | fallback).
The final status message carries in its metadata:
    output, decision, tool_calls, response_id, model, usage, prompt{name,version,source},
    guardrails{input,output}, caller (SPIFFE ID), duration_ms, profile, agent_id

Processing (mode=process with decision values) is a guided workflow: one model call per tool, in
the caller's order, then the final analysis and the decision block (decision.py). Llama writes
several tool calls as Python-like text when it wants many tools at once, which OGX cannot parse;
with one tool offered per step and tool_choice=required it always makes real tool calls. A step
stops once its tool has run (max_infer_iters=1): the model writes only the final analysis.
"""
import json
import logging
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from a2a.helpers.proto_helpers import new_task, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, Role, TaskState
from google.protobuf import json_format, struct_pb2

from . import spiffe_auth, tracing
from .config import AgentSettings
from .decision import final_request, parse_decision
from .guardrails import Guardrails, blocked_message
from .ogx_client import OGXClient, wrote_tool_calls_as_text
from .prompts import PromptStore, render
from .streaming import AnswerStream

logger = logging.getLogger(__name__)

# OpenShift token of the end user of the current request (metadata "user_token"), presented to the
# MCP Gateway on every OGX call (tools governance). Never logged nor traced.
_user_token: ContextVar[Optional[str]] = ContextVar("user_token", default=None)

CHAT_RULES_PROMPT = "chat-rules"
LANGUAGE_RULE_PROMPT = "language-rule"

EMPTY_ANSWER_RETRY = "Answer the user's request now, in the user's language."
TEXT_TOOL_CALL_RETRY = ("You wrote tool calls as text instead of calling them. "
                        "Use the function calling mechanism to actually execute the tools now.")

# Processing: tools only offered in the final analysis (the others are one step each)
OPTIONAL_TOOLS = {"search_knowledge_base", "search_courrier_knowledge"}
GUIDED_FIRST_STEP = ("\n\nAutomated processing, step {i}/{n}: call the {tool} tool now for this "
                     "request, with the identifiers given above.")
GUIDED_NEXT_STEP = "Step {i}/{n}: call the {tool} tool now for this request."
GUIDED_STEP_ATTEMPTS = 2

# Shown in the UI for each tool call: its arguments, and the sandbox execution when the tool ran code
# in the OpenShell sandbox (run_python, or "sandbox_run" in the output of e.g. compute_payout).
# The other outputs are not forwarded: they hold personal data.
TOOL_ARGUMENTS_MAX = 2000
SANDBOX_TOOL = "run_python"
SANDBOX_FIELDS = ("success", "exit_code", "stdout", "stderr", "denials", "sandbox", "error")


@dataclass
class Profile:
    """One role of an agent: its system prompt (MLflow Prompt Registry name) and its tools."""
    prompt: str
    tools: List[str]
    model: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)   # added to the agent's traces


class DomainAgentExecutor(AgentExecutor):
    def __init__(self, settings: AgentSettings, profiles: Dict[str, Profile]):
        self.settings = settings
        self.profiles = profiles
        self.default_profile = next(iter(profiles))
        self.llm = OGXClient(settings.ogx_endpoint, settings.ogx_timeout,
                             mcp_gateway_url=settings.mcp_gateway_url,
                             mcp_server_url_template=settings.mcp_server_url_template,
                             mcp_servers=[s for s in settings.mcp_servers.split(",") if s])
        self.prompts = PromptStore(settings)
        self.guardrails = Guardrails(settings)

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        started = time.time()
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        if not context.current_task:
            # The request handler expects the task itself before any status update
            history = [context.message] if context.message else []
            await event_queue.enqueue_event(new_task(
                context.task_id, context.context_id, TaskState.TASK_STATE_SUBMITTED, history=history))
        await updater.start_work()

        meta = _metadata(context)
        _user_token.set(meta.pop("user_token", None))
        profile_id = meta.get("profile") or self.default_profile
        profile = self.profiles.get(profile_id)
        if profile is None:
            await updater.reject(_message(f"Unknown profile '{profile_id}'", context))
            return
        user_text = context.get_user_input()
        if not user_text:
            await updater.reject(_message("Empty message.", context))
            return

        # Input rails: block (jailbreak, off-topic) or mask personal data before the model sees it
        checked_input = await self.guardrails.check_input(user_text)
        await self._guardrails_event(updater, "input", checked_input.to_dict())
        if not checked_input.allowed:
            refusal = blocked_message(meta.get("language"))
            await updater.reject(_message(refusal, context, metadata={
                "output": refusal, "guardrails": {"input": checked_input.to_dict()}}))
            return

        try:
            instructions, prompt_info = await self._instructions(profile, meta)
            result = await self._answer(updater, profile, meta, instructions, checked_input.text)

            checked_output = result["guardrails_output"]
            output = result["streamed_output"]
            if not checked_output["allowed"]:
                output = blocked_message(meta.get("language"))
                await updater.add_artifact([new_text_part(output)], artifact_id="response",
                                           name="response", append=False, last_chunk=True)
            await self._guardrails_event(updater, "output", checked_output)

            final = {
                "output": output,
                "decision": parse_decision(output) if meta.get("mode") == "process" else {},
                "tool_calls": result["tool_calls"],
                "response_id": result["response_id"],
                "model": result["model"],
                "usage": result["usage"],
                "duration_ms": int((time.time() - started) * 1000),
                "profile": profile_id,
                "prompt": prompt_info,
                "guardrails": {"input": checked_input.to_dict(), "output": checked_output},
                "caller": spiffe_auth.current_caller(),
                "agent_id": self.settings.agent_id,
            }
            tracing.log_agent_trace(
                agent_id=self.settings.agent_id, profile=profile_id, model=result["model"],
                input_text=checked_input.text, output_text=output, tool_calls=result["tool_calls"],
                usage=result["usage"], response_id=result["response_id"], duration_ms=final["duration_ms"],
                metadata={"prompt": prompt_info, "decision": final["decision"], "task_id": context.task_id,
                          "context_id": context.context_id, "guardrails": final["guardrails"], **profile.tags},
                traceparent=meta.get("traceparent"),
            )
            await updater.complete(_message(output, context, metadata=final))
        except Exception as e:
            logger.error("Agent %s/%s failed: %s", self.settings.agent_id, profile_id, e, exc_info=True)
            await updater.failed(_message(f"Agent error: {e}", context))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await TaskUpdater(event_queue, context.task_id, context.context_id).cancel()

    # ---- the answer --------------------------------------------------------------------------

    async def _instructions(self, profile: Profile, meta: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """System prompt: the profile's prompt (or the session's), the chat rules, the language rule."""
        if meta.get("instructions_override"):
            base = meta["instructions_override"]
            prompt_info = {"name": profile.prompt, "version": None, "source": "session"}
        else:
            prompt = await self.prompts.get(profile.prompt)
            base, prompt_info = prompt.text, prompt.info()

        instructions = base
        if meta.get("mode", "chat") == "chat":
            rules = await self.prompts.get(CHAT_RULES_PROMPT)
            instructions = render(rules.text, agent_instructions=base) if rules.text else base
        if meta.get("language"):
            rule = await self.prompts.get(LANGUAGE_RULE_PROMPT)
            if rule.text:
                instructions += render(rule.text, lang_name="English" if meta["language"] == "en" else "French")
        return instructions, prompt_info

    async def _answer(self, updater: TaskUpdater, profile: Profile, meta: Dict[str, Any],
                      instructions: str, message: str) -> Dict[str, Any]:
        """Run the request (chat or guided processing), with the retries the models need."""
        processing = meta.get("mode") == "process"
        model = profile.model or (processing and self.settings.ogx_process_model) or self.settings.ogx_default_model
        # in the caller's order: the processing runs the OCR before the precedent search, which reads it
        tools = [t for t in meta["tools"] if t in profile.tools] if meta.get("tools") else profile.tools
        previous = meta.get("previous_response_id")

        async def run(model: str) -> Dict[str, Any]:
            if processing and meta.get("decision_values") and tools:
                return await self._guided(updater, model, instructions, message, tools, previous, meta)
            return await self._respond(updater, model, instructions, message, tools, previous)

        try:
            result = await run(model)
        except RuntimeError as e:
            # OGX failed (e.g. malformed tool-call arguments): once more, with the other model if any
            fallback = next((m for m in (self.settings.ogx_process_model, self.settings.ogx_default_model)
                             if m and m != model), model)
            logger.warning("OGX response failed with %s (%s) — retrying with %s", model, e, fallback)
            await updater.update_status(TaskState.TASK_STATE_WORKING, _message(
                f"fallback to {fallback}",
                metadata={"event": "fallback", "from": model, "to": fallback, "reason": str(e)[:200]}))
            model = fallback
            result = await run(model)

        if not result["tool_calls"] and wrote_tool_calls_as_text(result["output"]):
            logger.warning("Model wrote tool calls as text — retrying with function calling")
            result = _continued(result, await self._respond(
                updater, model, instructions, TEXT_TOOL_CALL_RETRY, tools, result["response_id"]))
        if not result["streamed_output"].strip() and result["guardrails_output"]["allowed"]:
            logger.warning("Empty answer (seen with Llama on some prompts) — retrying once")
            result = _continued(result, await self._respond(
                updater, model, instructions, EMPTY_ANSWER_RETRY, tools, result["response_id"]))
        return result

    async def _guided(self, updater: TaskUpdater, model: str, instructions: str, message: str,
                      tools: List[str], previous: Optional[str], meta: Dict[str, Any]) -> Dict[str, Any]:
        """Processing: one model call per workflow tool (tool_choice=required, chained by response id,
        no text shown), then the analysis and the decision, where the optional tools remain offered."""
        steps = [t for t in tools if t not in OPTIONAL_TOOLS and not t.startswith("save_")]
        optional = [t for t in tools if t in OPTIONAL_TOOLS]
        done: Dict[str, Any] = {"tool_calls": [], "usage": {}, "response_id": previous}
        for i, tool in enumerate(steps, 1):
            # only the templates are formatted: the request may contain braces (JSON data)
            if i == 1:
                request = message + GUIDED_FIRST_STEP.format(i=i, n=len(steps), tool=tool)
            else:
                request = GUIDED_NEXT_STEP.format(i=i, n=len(steps), tool=tool)
            step = await self._guided_step(updater, model, instructions, request, tool, done["response_id"])
            if step is None:
                # the decision is made with the other results
                done["tool_calls"].append({"name": tool, "error": f"step failed after {GUIDED_STEP_ATTEMPTS} attempts"})
            else:
                done = _continued(done, step)

        request = final_request(meta["decision_values"], meta.get("review_decision"),
                                meta.get("human_decisions"), optional)
        if not steps:
            request = message + "\n\n" + request
        return _continued(done, await self._respond(updater, model, instructions, request, optional,
                                                    done["response_id"]))

    async def _guided_step(self, updater: TaskUpdater, model: str, instructions: str, request: str,
                           tool: str, previous: Optional[str]) -> Optional[Dict[str, Any]]:
        for attempt in range(1, GUIDED_STEP_ATTEMPTS + 1):
            logger.info("Guided step %s (attempt %d)", tool, attempt)
            try:
                # max_tool_calls=1: with tool_choice=required OGX would otherwise call the tool again on every
                # turn; max_infer_iters=1: no text about the result (it was discarded, and took most of the time)
                return await self._respond(updater, model, instructions, request, [tool], previous,
                                           tool_choice="required", max_tool_calls=1, max_infer_iters=1,
                                           show_text=False)
            except RuntimeError as e:
                # intermittent: malformed tool-call arguments ("Extra data"), MaaS disconnects
                logger.warning("Guided step %s failed (attempt %d): %s", tool, attempt, e)
        return None

    async def _respond(self, updater: TaskUpdater, model: str, instructions: str, message: str,
                       tools: List[str], previous: Optional[str], tool_choice: Optional[str] = None,
                       max_tool_calls: Optional[int] = None, max_infer_iters: Optional[int] = None,
                       show_text: bool = True) -> Dict[str, Any]:
        """One OGX response, streamed: text to the "response" artifact (through the output rails),
        tool activity as status updates. Returns OGX's `done` event, plus `streamed_output` (the text
        sent) and `guardrails_output` (the output rails verdict)."""
        answer = AnswerStream(updater, self.guardrails, self.settings.guardrails_buffer_output, show_text)
        done: Dict[str, Any] = {}
        async for event in self.llm.stream(
            model=model, instructions=instructions, input_message=message, tools=tools,
            max_tokens=self.settings.ogx_max_tokens, previous_response_id=previous,
            tool_choice=tool_choice, max_tool_calls=max_tool_calls, max_infer_iters=max_infer_iters,
            authorization=_user_token.get(),
        ):
            if event["type"] == "text_delta":
                await answer.add(event["delta"])
            elif event["type"] in ("tool_call", "tool_result"):
                await updater.update_status(TaskState.TASK_STATE_WORKING, _message(event["name"], metadata={
                    "event": event["type"], "name": event["name"], "server": event.get("server", ""),
                    "status": event.get("status", "in_progress"), **_tool_trace(event)}))
            elif event["type"] == "done":
                done = event
        await answer.finish(done.get("output", ""))
        return {**done, "streamed_output": answer.text, "guardrails_output": answer.verdict}

    async def _guardrails_event(self, updater: TaskUpdater, stage: str, result: Dict[str, Any]) -> None:
        if self.guardrails.enabled:
            await updater.update_status(TaskState.TASK_STATE_WORKING, _message(f"guardrails {stage}", metadata={
                "event": "guardrails", "stage": stage, "status": result.get("status"), "rail": result.get("rail")}))


def _continued(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """`after` continues `before` (same conversation): the tool calls and the token usage add up."""
    return {**after,
            "tool_calls": before.get("tool_calls", []) + after.get("tool_calls", []),
            "usage": _add_usage(before.get("usage") or {}, after.get("usage") or {})}


def _add_usage(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    numbers = lambda value: isinstance(value, (int, float))
    return {key: (a.get(key) or 0) + (b.get(key) or 0)
            for key in set(a) | set(b) if numbers(a.get(key, 0)) and numbers(b.get(key, 0))}


def _tool_trace(event: Dict[str, Any]) -> Dict[str, Any]:
    """Arguments of a finished tool call and, if it ran code in the sandbox, that execution."""
    trace: Dict[str, Any] = {}
    if event.get("arguments"):
        trace["arguments"] = str(event["arguments"])[:TOOL_ARGUMENTS_MAX]
    if event.get("error"):
        trace["error"] = str(event["error"])[:500]
    try:
        output = json.loads(event.get("output") or "")
    except (ValueError, TypeError):
        return trace
    if not isinstance(output, dict):
        return trace
    run = output if event.get("name") == SANDBOX_TOOL else output.get("sandbox_run")
    if isinstance(run, dict):
        trace["sandbox"] = {k: run[k] for k in SANDBOX_FIELDS if k in run}
        if output.get("code"):
            trace["sandbox"]["code"] = output["code"]
    return trace


def _metadata(context: RequestContext) -> Dict[str, Any]:
    message = context.message
    if message is None or not message.HasField("metadata"):
        return {}
    return json_format.MessageToDict(message.metadata)


def _message(text: str, context: Optional[RequestContext] = None,
             metadata: Optional[Dict[str, Any]] = None) -> Message:
    message = Message(role=Role.ROLE_AGENT, message_id=str(uuid.uuid4()), parts=[new_text_part(text)])
    if context is not None:
        message.context_id = context.context_id or ""
        message.task_id = context.task_id or ""
    if metadata:
        struct = struct_pb2.Struct()
        json_format.ParseDict(_jsonable(metadata), struct)
        message.metadata.CopyFrom(struct)
    return message


def _jsonable(value: Any) -> Any:
    """What google.protobuf.Struct accepts (string keys, plain values)."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return str(value)
