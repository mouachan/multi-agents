"""Generic A2A executor — domain logic (prompts, tools) comes from agent profiles.

Request metadata (A2A Message.metadata, all optional) sent by the backend:
    profile               profile id (e.g. "courrier-info"); defaults to the agent's first profile
    mode                  "chat" (conversational wrapper) or "process" (batch processing)
    language              "fr" | "en" — enforced via the language-rule prompt
    previous_response_id  OGX response id to chain the conversation
    instructions_override session custom prompt (replaces the registry prompt)

Final task status message metadata returned to the caller:
    output, decision, tool_calls, response_id, model, usage, prompt{name,version,source},
    guardrails{input,output}
"""
import logging
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

from . import tracing
from .config import AgentSettings
from .guardrails import Guardrails, blocked_message
from .ogx_client import OGXClient
from .prompts import PromptStore, render
from .response_parser import ResponseParser

logger = logging.getLogger(__name__)

CHAT_WRAPPER_PROMPT = "chat-agent-wrapper"
LANGUAGE_RULE_PROMPT = "orchestrator-language-rule"
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
        self._buffer_output = self.guardrails.enabled and settings.guardrails_buffer_output

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
        if not gin.allowed:
            refusal = blocked_message(meta.get("language"))
            await updater.reject(_message(refusal, context, metadata={
                "output": refusal, "guardrails": {"input": gin.to_dict()},
            }))
            return
        llm_input = gin.text

        try:
            instructions, prompt_info = await self._instructions(profile, meta)
            model = profile.model or self.settings.ogx_default_model
            previous_response_id = meta.get("previous_response_id")

            result = await self._run(updater, model, instructions, llm_input, profile.tools, previous_response_id)

            # Retry once if the model wrote tool calls as plain text
            if not result["tool_calls"] and self.parser.contains_text_tool_calls(result["output"]):
                logger.warning("Model wrote tool calls as text — retrying with function calling")
                retry = await self._run(updater, model, instructions, TEXT_TOOL_CALL_RETRY,
                                        profile.tools, result["response_id"])
                retry["usage"] = _merge_usage(result["usage"], retry["usage"])
                result = retry

            output = result["output"]
            gout = await self.guardrails.check_output(output)
            final_text = gout.text if gout.allowed else blocked_message(meta.get("language"))
            if self._buffer_output or final_text != output:
                # Send the (masked) text — replaces any unmasked deltas already streamed
                await updater.add_artifact([new_text_part(final_text)], artifact_id="response",
                                           name="response", append=False, last_chunk=True)
            output = final_text

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
                "guardrails": {"input": gin.to_dict(), "output": gout.to_dict()},
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

    async def _run(self, updater: TaskUpdater, model, instructions, input_message, tools,
                   previous_response_id) -> Dict[str, Any]:
        """Stream one OGX response, forwarding deltas and tool activity as A2A events."""
        first_chunk = True
        done: Dict[str, Any] = {}
        async for ev in self.llm.stream(
            model=model,
            instructions=instructions,
            input_message=input_message,
            tools=tools,
            max_tokens=self.settings.ogx_max_tokens,
            previous_response_id=previous_response_id,
        ):
            etype = ev["type"]
            if etype == "text_delta" and not self._buffer_output:
                await updater.add_artifact([new_text_part(ev["delta"])], artifact_id="response",
                                           name="response", append=not first_chunk)
                first_chunk = False
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
        return done

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.cancel()


def _merge_usage(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    keys = set(a) | set(b)
    return {k: (a.get(k, 0) or 0) + (b.get(k, 0) or 0)
            for k in keys if isinstance(a.get(k, 0), (int, float)) and isinstance(b.get(k, 0), (int, float))}
