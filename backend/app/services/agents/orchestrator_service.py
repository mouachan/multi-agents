"""
Orchestrator Service - High-level agent that routes messages to specialized agents.

Responsibilities:
- Receive natural language messages
- Classify intent via LLM
- Route to specialized agent
- Maintain conversation history per session
- Suggest follow-up actions
- Chain agents (e.g., AO Go -> suggest Claim)
"""
import logging
import re
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.services.agents.turn_trace import TurnTrace
from app.services.pii.redactor import redact_text_pii

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.prompts.orchestrator_prompts import (
    CHAT_AGENT_WRAPPER,
    LANGUAGE_RULE_TEMPLATE,
    ORCHESTRATOR_CONFIG,
    ORCHESTRATOR_SYSTEM_INSTRUCTIONS,
)
from app.core import tracing
from app.services.agent.a2a_client import get_a2a_client
from app.services.agents.semantic_router import get_semantic_router
from app.services.agent.responses_orchestrator import ResponsesOrchestrator
from .conversation_utils import ConversationHelper
from .registry import AgentRegistry

logger = logging.getLogger(__name__)


class OrchestratorService:
    """High-level orchestrator that routes messages to specialized agents."""

    def __init__(self, orchestrator: Optional[ResponsesOrchestrator] = None):
        self.orchestrator = orchestrator or ResponsesOrchestrator()
        self.a2a = get_a2a_client()
        self.router = get_semantic_router()
        self.conv = ConversationHelper(ORCHESTRATOR_CONFIG.get("conversation"))

    async def create_session(
        self,
        db: AsyncSession,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        locale: Optional[str] = "fr",
    ) -> Dict[str, Any]:
        """Create a new chat session, optionally pre-routed to an agent."""
        from app.models.conversation import ChatSession

        session_id = f"session_{uuid.uuid4().hex[:12]}"

        session = ChatSession(
            session_id=session_id,
            agent_id=agent_id,
            status="active",
            session_metadata=metadata or {},
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Build welcome message based on locale
        logger.info(f"CREATE SESSION locale={locale!r} agent_id={agent_id!r}")
        is_fr = (locale or "fr").startswith("fr")
        lang_key = "fr" if is_fr else "en"
        welcome_cfg = ORCHESTRATOR_CONFIG.get("welcome_messages", {}).get(lang_key, {})

        if agent_id:
            agent_def = AgentRegistry.get(agent_id)
            if agent_def:
                tpl = welcome_cfg.get(
                    "agent",
                    "Session demarree avec l'agent **{agent_name}**. Comment puis-je vous aider ?"
                    if is_fr else
                    "Session started with agent **{agent_name}**. How can I help you?",
                )
                localized_name = (agent_def.name_fr if is_fr and agent_def.name_fr else agent_def.name)
                welcome = tpl.format(agent_name=localized_name)
            else:
                welcome = welcome_cfg.get(
                    "fallback",
                    "Session demarree." if is_fr else "Session started.",
                )
        else:
            welcome = welcome_cfg.get(
                "orchestrator",
                "Bienvenue ! Je suis l'orchestrateur multi-agents. Decrivez ce que vous souhaitez faire et je vous orienterai vers l'agent specialise."
                if is_fr else
                "Welcome! I'm the multi-agent orchestrator. Describe what you'd like to do and I'll route you to the right specialized agent.",
            )

        # Save welcome message
        from app.models.conversation import ChatMessage

        welcome_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=welcome,
            agent_id="orchestrator",
        )
        db.add(welcome_msg)
        await db.commit()

        return {
            "session_id": session_id,
            "id": str(session.id),
            "agent_id": agent_id,
            "status": "active",
            "welcome_message": welcome,
        }

    async def process_message(
        self,
        db: AsyncSession,
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message: classify intent, route to agent, return response.
        """
        from app.models.conversation import ChatMessage, ChatSession

        # Get session
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Save user message
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=message,
        )
        db.add(user_msg)
        await db.commit()

        # Semantic routing over the A2A agent cards (keyword fallback)
        classification = await self._classify(message, session.agent_id)
        intent = classification.get("intent", "general")
        agent_id = classification.get("agent_id") or session.agent_id
        response_text = classification.get("message", "")
        suggested_actions = classification.get("suggested_actions", [])
        tool_calls = []
        token_usage = None
        model = None
        result = {}

        # Get previous_response_id for stateful conversation chaining
        metadata = dict(session.session_metadata or {})
        previous_response_id = metadata.get("last_response_id")

        # Update session agent if routed — clear response chain on agent switch
        if agent_id and agent_id != session.agent_id:
            session.agent_id = agent_id
            previous_response_id = None  # New agent = new conversation context
            await db.commit()

        # Input guardrails check — before any LLM call. Decoupled A2A agents run their own
        # NeMo input/output rails (PII masking), so only the legacy in-process path checks here.
        routed_def = AgentRegistry.get(agent_id) if agent_id else None
        blocked_msg = None
        if not (routed_def and routed_def.a2a_url):
            blocked_msg = await self._check_input_guardrails(message)
        if blocked_msg:
            from app.models.conversation import ChatMessage
            assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=blocked_msg,
                agent_id=agent_id or "orchestrator",
            )
            db.add(assistant_msg)
            await db.commit()
            return {
                "session_id": session_id,
                "intent": "blocked",
                "agent_id": agent_id,
                "message": blocked_msg,
                "suggested_actions": [],
                "entity_reference": None,
                "tool_calls": [],
                "token_usage": None,
                "model_id": None,
            }

        # Route to agent — A2A (remote) or direct OGX (legacy)
        if agent_id:
            agent_def = AgentRegistry.get(agent_id)
            if agent_def:
                try:
                    user_lang = self._detect_language(message)

                    if agent_def.a2a_url:
                        result = await self._call_via_a2a(
                            agent_def, message, session_id, user_lang, session, previous_response_id,
                        )
                    elif agent_def.tools:
                        result = await self._call_via_ogx(
                            agent_def, message, user_lang, session, previous_response_id,
                        )
                    else:
                        result = {}

                    agent_response = result.get("output", "")
                    tool_calls = result.get("tool_calls", [])
                    token_usage = ConversationHelper.normalize_token_usage(result.get("usage", {}))

                    if agent_response and agent_response.strip():
                        if not tool_calls and self.conv.contains_text_tool_calls(agent_response):
                            text_tool_names = ConversationHelper.extract_tool_names_from_text(agent_response)
                            tool_calls = [{"name": n, "server": None, "output": None, "error": None} for n in text_tool_names]

                        agent_response = ConversationHelper.clean_response_for_chat(agent_response)
                        response_text = redact_text_pii(agent_response)
                        if response_text != agent_response:
                            logger.info("PII detected and redacted in agent response")
                        suggested_actions = self._generate_post_response_actions(
                            response_text, agent_id, user_lang
                        )

                    tracing.log_agent_trace(
                        agent_id=agent_id,
                        model=result.get("model", ""),
                        input_text=str(message)[:2000],
                        output_text=result.get("output", "")[:2000],
                        tool_calls=result.get("tool_calls", []),
                        usage=result.get("usage"),
                        stream=False,
                        session_id=session_id,
                        user_id=user_id,
                        response_id=result.get("response_id"),
                    )

                except Exception as e:
                    logger.error(f"Agent {agent_id} call failed: {e}", exc_info=True)
                    response_text = f"Erreur lors du traitement: {str(e)}"

        # Build enriched tool_calls with full metadata
        enriched_tool_calls = [
            {
                "name": tc.get("name", "unknown"),
                "status": "error" if tc.get("error") else "completed",
                "server_label": tc.get("server"),
                "output": tc.get("output"),
                "error": tc.get("error"),
            }
            for tc in tool_calls
            if isinstance(tc, dict) and tc.get("name")
        ]

        # Store last_response_id for conversation chaining
        new_response_id = result.get("response_id") if isinstance(result, dict) else None
        if new_response_id:
            metadata["last_response_id"] = new_response_id
            session.session_metadata = metadata

        # Determine which model was used (short name for display)
        model_id = None
        if agent_id and AgentRegistry.get(agent_id):
            full_model = model if isinstance(model, str) else settings.ogx_default_model
            short = full_model.split("/")[-1] if "/" in full_model else full_model
            short = re.sub(r'-W\d+A\d+$', '', short)
            model_id = short

        # Save assistant response
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
            agent_id=agent_id or "orchestrator",
            suggested_actions=suggested_actions if suggested_actions else None,
            tool_calls=enriched_tool_calls if enriched_tool_calls else None,
            token_usage=token_usage,
            model_id=model_id,
        )
        db.add(assistant_msg)
        await db.commit()

        return {
            "session_id": session_id,
            "intent": intent,
            "agent_id": agent_id,
            "message": response_text,
            "suggested_actions": suggested_actions,
            "entity_reference": classification.get("entity_reference"),
            "tool_calls": enriched_tool_calls,
            "token_usage": token_usage,
            "model_id": model_id,
        }

    async def process_message_stream(
        self,
        db: AsyncSession,
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user message with SSE streaming.

        Same routing logic as process_message() but yields events progressively. The turn is
        traced once (turn_trace): application trace saved with the assistant message, and the
        same events as one MLflow trace that the agent's spans join.
        """
        turn = TurnTrace(f"chat | {message[:80].strip()}", {"message": message}, session_id=session_id)
        try:
            async for event in self._message_stream(db, session_id, message, user_id, turn):
                turn.add(event)
                yield event
        finally:
            turn.close()

    async def _message_stream(
        self,
        db: AsyncSession,
        session_id: str,
        message: str,
        user_id: Optional[str],
        turn: TurnTrace,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        from app.models.conversation import ChatMessage, ChatSession

        # Get session
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            yield {"type": "error", "message": f"Session {session_id} not found"}
            return

        # Save user message
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=message,
        )
        db.add(user_msg)
        await db.commit()

        # Semantic routing over the A2A agent cards (keyword fallback)
        classification = await self._classify(message, session.agent_id)
        yield classification["routing"]
        intent = classification.get("intent", "general")
        agent_id = classification.get("agent_id") or session.agent_id

        # Get previous_response_id for stateful conversation chaining
        metadata = dict(session.session_metadata or {})
        previous_response_id = metadata.get("last_response_id")

        # Update session agent if routed
        if agent_id and agent_id != session.agent_id:
            session.agent_id = agent_id
            previous_response_id = None
            await db.commit()

        if not agent_id:
            yield {"type": "error", "message": "No agent resolved for this request"}
            return

        agent_def = AgentRegistry.get(agent_id)
        if not agent_def or not (agent_def.tools or agent_def.a2a_url):
            yield {"type": "error", "message": f"Agent {agent_id} not found or has no tools"}
            return

        # Input guardrails check — A2A agents apply their own NeMo rails
        blocked_msg = None if agent_def.a2a_url else await self._check_input_guardrails(message)
        if blocked_msg:
            from app.models.conversation import ChatMessage
            assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=blocked_msg,
                agent_id=agent_id or "orchestrator",
                trace=turn.finish(blocked_msg, {"agent_id": agent_id}),
            )
            db.add(assistant_msg)
            await db.commit()
            yield {"type": "text_delta", "delta": blocked_msg}
            yield {
                "type": "done",
                "response_id": None,
                "usage": None,
                "tool_calls": [],
                "agent_id": agent_id,
                "model_id": None,
                "suggested_actions": [],
            }
            return

        # Emit agent info immediately so frontend can update badge/icon
        yield {"type": "agent_resolved", "agent_id": agent_id}

        user_lang = self._detect_language(message)

        tool_calls = []
        full_text = ""
        streamed_text = False
        a2a_summary: Dict[str, Any] = {}
        response_id = None
        token_usage = None
        model = agent_def.model or settings.ogx_streaming_model or settings.ogx_default_model

        try:
            if agent_def.a2a_url:
                # A2A path — the agent streams OGX deltas and tool activity as A2A events
                logger.info("A2A stream to '%s' at %s", agent_id, agent_def.a2a_url)
                a2a_metadata = self._a2a_metadata(agent_def, user_lang, session, previous_response_id)
                traceparent = turn.start_a2a(agent_id)  # the agent's spans join the turn trace
                if traceparent:
                    a2a_metadata["traceparent"] = traceparent
                async for event in self.a2a.stream(
                    base_url=agent_def.a2a_url,
                    message=message,
                    context_id=str(session_id),
                    metadata=a2a_metadata,
                ):
                    event_type = event.get("type")
                    if event_type in ("tool_call", "tool_result", "text_delta", "text_replace",
                                      "a2a", "guardrails"):
                        streamed_text = streamed_text or event_type in ("text_delta", "text_replace")
                        yield event
                    elif event_type == "done":
                        full_text = event.get("output", "")
                        a2a_summary = {
                            **event.get("a2a", {}),
                            "status": event.get("status"),
                            "prompt": event.get("prompt", {}),
                            "guardrails": event.get("guardrails", {}),
                        }
                        if full_text and not streamed_text:
                            # e.g. input rejected by the guardrails: the refusal only comes in the final status
                            yield {"type": "text_delta", "delta": full_text}
                            streamed_text = True
                        response_id = event.get("response_id")
                        model = event.get("model") or model
                        token_usage = ConversationHelper.normalize_token_usage(event.get("usage", {}))
                        tool_calls = [
                            {
                                "name": tc.get("name", "unknown"),
                                "status": "error" if tc.get("error") else "completed",
                                "server_label": tc.get("server"),
                            }
                            for tc in event.get("tool_calls", [])
                            if isinstance(tc, dict) and tc.get("name")
                        ]

            else:
                # Legacy OGX streaming path
                lang_name = "English" if user_lang == "en" else "French"
                lang_suffix = LANGUAGE_RULE_TEMPLATE.format(lang_name=lang_name)
                custom_prompt = (session.session_metadata or {}).get("custom_prompt")
                agent_instructions = custom_prompt or agent_def.instructions
                instructions = self._wrap_instructions_for_chat(agent_instructions) + lang_suffix

                logger.info("Streaming agent '%s': model=%s, tools=%d", agent_id, model, len(agent_def.tools))

                async for event in self.orchestrator.process_with_agent_stream(
                    agent_config={"model": model, "instructions": instructions},
                    input_message=message,
                    tools=agent_def.tools,
                    previous_response_id=previous_response_id,
                ):
                    event_type = event.get("type")

                    if event_type == "tool_call":
                        yield event
                    elif event_type == "tool_result":
                        tool_calls.append({"name": event.get("name"), "status": event.get("status")})
                        yield event
                    elif event_type == "text_delta":
                        yield event
                    elif event_type == "done":
                        full_text = event.get("output", "")
                        response_id = event.get("response_id")
                        token_usage = ConversationHelper.normalize_token_usage(event.get("usage", {}))
                        tool_calls = [
                            {
                                "name": tc.get("name", "unknown"),
                                "status": "error" if tc.get("error") else "completed",
                                "server_label": tc.get("server"),
                            }
                            for tc in event.get("tool_calls", [])
                            if isinstance(tc, dict) and tc.get("name")
                        ]

        except Exception as e:
            logger.error(f"Stream error for agent {agent_id}: {e}", exc_info=True)
            yield {"type": "error", "message": str(e)}
            return

        if full_text:
            full_text = ConversationHelper.clean_response_for_chat(full_text)
            redacted = redact_text_pii(full_text)
            if redacted != full_text:
                logger.info("PII detected and redacted in streamed response")
                full_text = redacted
                yield {"type": "text_replace", "text": full_text}

        suggested_actions = self._generate_post_response_actions(full_text, agent_id, user_lang)

        # Legacy in-process path: summary trace to MLflow (the A2A path is traced by `turn`)
        if not agent_def.a2a_url:
            tracing.log_agent_trace(
                agent_id=agent_id,
                model=model if isinstance(model, str) else "",
                input_text=str(message)[:2000],
                output_text=full_text[:2000],
                tool_calls=tool_calls,
                usage=token_usage,
                stream=True,
                session_id=session_id,
                user_id=user_id,
                response_id=response_id,
            )

        # Store last_response_id for conversation chaining
        if response_id:
            metadata["last_response_id"] = response_id
            session.session_metadata = metadata

        # Model short name
        model_id = None
        full_model = model if isinstance(model, str) else settings.ogx_default_model
        short = full_model.split("/")[-1] if "/" in full_model else full_model
        short = re.sub(r'-W\d+A\d+$', '', short)
        model_id = short

        # Final done event with enriched data
        done = {
            "type": "done",
            "response_id": response_id,
            "usage": token_usage,
            "tool_calls": tool_calls,
            "agent_id": agent_id,
            "model_id": model_id,
            "suggested_actions": suggested_actions,
            "a2a": a2a_summary or None,
            "trace": turn.link(),
        }

        # Save assistant response to DB, with the trace of the turn
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=full_text,
            agent_id=agent_id or "orchestrator",
            suggested_actions=suggested_actions if suggested_actions else None,
            tool_calls=tool_calls if tool_calls else None,
            token_usage=token_usage,
            model_id=model_id,
            trace=turn.finish(full_text, done),
        )
        db.add(assistant_msg)
        await db.commit()

        yield done

    async def list_sessions(
        self,
        db: AsyncSession,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """List recent chat sessions with last message preview."""
        from app.models.conversation import ChatMessage, ChatSession

        result = await db.execute(
            select(ChatSession)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()

        session_list = []
        for s in sessions:
            # Get last message for preview
            last_msg_result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == s.id)
                .order_by(ChatMessage.created_at.desc())
                .limit(1)
            )
            last_msg = last_msg_result.scalar_one_or_none()

            session_list.append({
                "session_id": s.session_id,
                "agent_id": s.agent_id,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                "last_message": last_msg.content[:80] if last_msg else None,
            })

        return session_list

    async def get_session_messages(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        from app.models.conversation import ChatMessage, ChatSession

        # Get session
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get messages
        msg_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = msg_result.scalars().all()

        return [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "agent_id": msg.agent_id,
                "entity_id": str(msg.entity_id) if msg.entity_id else None,
                "entity_type": msg.entity_type,
                "suggested_actions": msg.suggested_actions,
                "tool_calls": msg.tool_calls,
                "token_usage": msg.token_usage,
                "model_id": msg.model_id,
                "saved_trace": msg.trace,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ]

    async def delete_session(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> None:
        """Delete a session and its messages (CASCADE)."""
        from app.models.conversation import ChatSession

        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        await db.delete(session)
        await db.commit()

    async def delete_all_sessions(
        self,
        db: AsyncSession,
    ) -> int:
        """Delete all sessions and their messages."""
        from sqlalchemy import delete as sql_delete
        from app.models.conversation import ChatMessage, ChatSession

        # Delete messages first, then sessions
        await db.execute(sql_delete(ChatMessage))
        result = await db.execute(sql_delete(ChatSession))
        await db.commit()
        return result.rowcount

    async def get_session_prompt(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> Dict[str, Any]:
        """Return effective prompt for a session (custom or default)."""
        from app.models.conversation import ChatSession

        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        custom_prompt = (session.session_metadata or {}).get("custom_prompt")
        if custom_prompt:
            prompt = self._wrap_instructions_for_chat(custom_prompt)
            return {"prompt": prompt, "is_custom": True, "agent_id": session.agent_id}

        # Build default prompt the same way process_message does
        agent_id = session.agent_id
        if agent_id:
            agent_def = AgentRegistry.get(agent_id)
            if agent_def:
                prompt = self._wrap_instructions_for_chat(agent_def.instructions)
                return {"prompt": prompt, "is_custom": False, "agent_id": agent_id}

        # No agent assigned — return orchestrator instructions
        return {
            "prompt": ORCHESTRATOR_SYSTEM_INSTRUCTIONS,
            "is_custom": False,
            "agent_id": None,
        }

    async def set_session_prompt(
        self,
        db: AsyncSession,
        session_id: str,
        custom_prompt: str,
    ) -> Dict[str, Any]:
        """Set custom prompt for this session."""
        from app.models.conversation import ChatSession

        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        metadata = dict(session.session_metadata or {})
        metadata["custom_prompt"] = custom_prompt
        session.session_metadata = metadata
        await db.commit()

        prompt = self._wrap_instructions_for_chat(custom_prompt)
        return {"prompt": prompt, "is_custom": True, "agent_id": session.agent_id}

    async def reset_session_prompt(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> Dict[str, Any]:
        """Remove custom prompt, revert to default."""
        from app.models.conversation import ChatSession

        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        metadata = dict(session.session_metadata or {})
        metadata.pop("custom_prompt", None)
        session.session_metadata = metadata
        await db.commit()

        # Return default prompt
        return await self.get_session_prompt(db, session_id)

    @staticmethod
    def _a2a_metadata(agent_def, user_lang: str, session, previous_response_id: Optional[str]) -> Dict[str, Any]:
        """A2A message metadata understood by the agents' executor (see agents/shared/executor.py)."""
        return {
            "profile": agent_def.id,
            "mode": "chat",
            "language": user_lang,
            "previous_response_id": previous_response_id,
            "instructions_override": (session.session_metadata or {}).get("custom_prompt"),
        }

    async def _call_via_a2a(
        self, agent_def, message: str, session_id: str, user_lang: str,
        session, previous_response_id: Optional[str],
    ) -> Dict[str, Any]:
        """Route a message to a remote A2A agent."""
        logger.info("A2A call to '%s' at %s", agent_def.id, agent_def.a2a_url)
        return await self.a2a.send(
            base_url=agent_def.a2a_url,
            message=message,
            context_id=str(session_id),
            metadata=self._a2a_metadata(agent_def, user_lang, session, previous_response_id),
        )

    async def _call_via_ogx(
        self, agent_def, message: str, user_lang: str,
        session, previous_response_id: Optional[str],
    ) -> Dict[str, Any]:
        """Route a message directly to OGX (legacy path)."""
        lang_name = "English" if user_lang == "en" else "French"
        lang_suffix = LANGUAGE_RULE_TEMPLATE.format(lang_name=lang_name)

        custom_prompt = (session.session_metadata or {}).get("custom_prompt")
        agent_instructions = custom_prompt or agent_def.instructions
        instructions = self._wrap_instructions_for_chat(agent_instructions) + lang_suffix
        model = agent_def.model or settings.ogx_default_model

        logger.info("OGX call to '%s': model=%s, tools=%d", agent_def.id, model, len(agent_def.tools))

        result = await self.orchestrator.process_with_agent(
            agent_config={"model": model, "instructions": instructions},
            input_message=message,
            tools=agent_def.tools,
            previous_response_id=previous_response_id,
        )

        agent_response = result.get("output", "")
        tool_calls = result.get("tool_calls", [])
        last_response_id = result.get("response_id")

        if (
            not tool_calls
            and self.conv.contains_text_tool_calls(agent_response)
            and self.conv.max_tool_call_retries > 0
        ):
            logger.warning("LLM wrote tool calls as text — retrying")
            result = await self.orchestrator.process_with_agent(
                agent_config={"model": model, "instructions": instructions},
                input_message="You wrote tool calls as text instead of calling them. "
                              "Use the function calling mechanism to actually execute the tools now.",
                tools=agent_def.tools,
                previous_response_id=last_response_id,
            )

        return result

    _GUARDRAILS_BLOCKED_FR = (
        "Désolé, cette requête a été bloquée par notre système de sécurité (NeMo Guardrails). "
        "Veuillez reformuler votre demande."
    )
    _GUARDRAILS_BLOCKED_EN = (
        "Sorry, this request has been blocked by our safety system (NeMo Guardrails). "
        "Please rephrase your request."
    )

    async def _check_input_guardrails(self, message: str) -> Optional[str]:
        """Check user input via NeMo Guardrails. Returns refusal message if blocked, None if allowed."""
        guardrails_url = settings.guardrails_server_url
        if not guardrails_url:
            return None
        try:
            async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
                resp = await client.post(
                    f"{guardrails_url}/v1/checks",
                    json={
                        "model": settings.guardrails_model_name,
                        "messages": [{"role": "user", "content": message}],
                        "guardrails": {"config_id": settings.guardrails_config_id},
                    },
                )
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get("status") == "blocked":
                        logger.warning(f"NeMo Guardrails blocked input: {message[:100]}")
                        lang = self._detect_language(message)
                        return self._GUARDRAILS_BLOCKED_FR if lang == "fr" else self._GUARDRAILS_BLOCKED_EN
        except Exception as e:
            logger.warning(f"Guardrails check failed (allowing request): {e}")
        return None

    @staticmethod
    def _wrap_instructions_for_chat(agent_instructions: str) -> str:
        """Wrap agent instructions with chat-specific guidance."""
        return CHAT_AGENT_WRAPPER.format(agent_instructions=agent_instructions)

    # Default French words for language detection (used when config not mounted)
    _DEFAULT_FR_WORDS = {
        "le", "la", "les", "des", "du", "un", "une", "est", "sont", "avec",
        "pour", "dans", "sur", "par", "que", "qui", "ce", "cette", "mon",
        "mes", "ton", "tes", "son", "ses", "nous", "vous", "leur", "leurs",
        "je", "tu", "il", "elle", "nous", "ils", "elles", "et", "ou",
        "mais", "donc", "sinistre", "sinistres", "attente", "traiter",
        "lister", "afficher", "combien", "appel", "offres", "voir",
        "colis", "courrier", "poste", "reclamation", "reclamations",
        "tarif", "tarifs", "suivi", "suivre", "livraison",
    }

    @staticmethod
    def _detect_language(message: str) -> str:
        """Detect user language from message. Returns 'en' or 'fr'."""
        lang_cfg = ORCHESTRATOR_CONFIG.get("language_detection", {})
        fr_words = set(lang_cfg.get("fr_words", OrchestratorService._DEFAULT_FR_WORDS))
        min_match = lang_cfg.get("min_match_count", 1)
        words = set(message.lower().split())
        fr_count = len(words & fr_words)
        return "fr" if fr_count >= min_match else "en"

    @staticmethod
    def _match_keywords(message_lower: str, words: set, keywords: list) -> bool:
        """Match keywords against message using word boundaries.

        - Multi-word keywords (containing space/apostrophe/slash): substring match
        - Short keywords (<=3 chars): exact word match to avoid false positives
        - Prefix keywords (ending with -): substring match (e.g. "clm-" matches "CLM-2024")
        - Other keywords: substring match
        """
        for kw in keywords:
            if " " in kw or "'" in kw or "/" in kw:
                if kw in message_lower:
                    return True
            elif kw.endswith("-"):
                if kw in message_lower:
                    return True
            elif len(kw) <= 3:
                if kw in words:
                    return True
            else:
                if kw in message_lower:
                    return True
        return False

    async def _classify(self, message: str, current_agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Semantic routing (see semantic_router.py); keyword routing when disabled or on error."""
        if settings.router_enabled:
            try:
                decision = await self.router.route(message, current_agent_id)
                intent = "follow_up" if decision.method == "sticky" else "agent_request"
                return {
                    "intent": intent,
                    "agent_id": decision.agent_id,
                    "message": "",
                    "suggested_actions": self._generate_actions_for_intent(
                        intent, decision.agent_id, self._detect_language(message)),
                    "routing": decision.to_event(),
                }
            except Exception as e:
                logger.warning("Semantic routing failed, using keywords: %s", e)
        result = self._fallback_classification(message, current_agent_id)
        result["routing"] = {"type": "routing", "agent_id": result["agent_id"], "method": "keywords",
                             "score": None, "candidates": [], "duration_ms": 0}
        return result

    def _fallback_classification(
        self,
        message: str,
        current_agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fast intent classification using keyword matching from agent registry.

        Iterates over all registered agents and their routing_keywords.
        No hardcoded agent IDs — adding a new agent with routing_keywords
        is enough for routing to work.
        """
        msg_lower = message.lower()
        msg_words = set(re.sub(r'[^\w\s-]', ' ', msg_lower).split())

        agent_id = current_agent_id
        intent = "general"

        for agent_def in AgentRegistry.list_agents():
            if agent_def.routing_keywords and self._match_keywords(
                msg_lower, msg_words, agent_def.routing_keywords
            ):
                agent_id = agent_def.id
                intent = "agent_request"
                break

        # If still no match but session has an agent, keep routing there
        if intent == "general" and current_agent_id:
            agent_id = current_agent_id
            intent = "follow_up"

        user_lang = self._detect_language(message)
        suggested_actions = self._generate_actions_for_intent(intent, agent_id, user_lang)

        return {
            "intent": intent,
            "agent_id": agent_id,
            "message": "",
            "suggested_actions": suggested_actions,
        }

    # Default suggested actions (used when config not mounted)
    _DEFAULT_SUGGESTED_ACTIONS = {
        "tenders": {
            "fr": [
                {"label": "Voir les appels d'offres", "action": "navigate", "params": {"path": "/tenders"}},
                {"label": "Analyser un AO", "action": "chat", "params": {}},
                {"label": "Lister les AO en attente", "action": "chat", "params": {}},
            ],
            "en": [
                {"label": "View tenders", "action": "navigate", "params": {"path": "/tenders"}},
                {"label": "Analyze a tender", "action": "chat", "params": {}},
                {"label": "List pending tenders", "action": "chat", "params": {}},
            ],
        },
        "claims": {
            "fr": [
                {"label": "Voir les sinistres", "action": "navigate", "params": {"path": "/claims"}},
                {"label": "Traiter un sinistre", "action": "chat", "params": {}},
                {"label": "Lister les claims en attente", "action": "chat", "params": {}},
            ],
            "en": [
                {"label": "View claims", "action": "navigate", "params": {"path": "/claims"}},
                {"label": "Process a claim", "action": "chat", "params": {}},
                {"label": "List pending claims", "action": "chat", "params": {}},
            ],
        },
        "courrier_reclamation": {
            "fr": [
                {"label": "Voir les reclamations", "action": "navigate", "params": {"path": "/postal"}},
                {"label": "Traiter une reclamation", "action": "chat", "params": {}},
                {"label": "Lister les reclamations en attente", "action": "chat", "params": {}},
            ],
            "en": [
                {"label": "View complaints", "action": "navigate", "params": {"path": "/postal"}},
                {"label": "Process a complaint", "action": "chat", "params": {}},
                {"label": "List pending complaints", "action": "chat", "params": {}},
            ],
        },
        "courrier_info": {
            "fr": [
                {"label": "Tarifs Colissimo", "action": "chat", "params": {}},
                {"label": "Conditions de transport", "action": "chat", "params": {}},
                {"label": "Guide emballage", "action": "chat", "params": {}},
            ],
            "en": [
                {"label": "Colissimo rates", "action": "chat", "params": {}},
                {"label": "Shipping conditions", "action": "chat", "params": {}},
                {"label": "Packaging guide", "action": "chat", "params": {}},
            ],
        },
        "courrier_suivi": {
            "fr": [
                {"label": "Suivre un colis", "action": "chat", "params": {}},
                {"label": "Rechercher par email", "action": "chat", "params": {}},
            ],
            "en": [
                {"label": "Track a parcel", "action": "chat", "params": {}},
                {"label": "Search by email", "action": "chat", "params": {}},
            ],
        },
        "general": {
            "fr": [
                {"label": "Sinistres (Claims)", "action": "navigate", "params": {"path": "/claims"}},
                {"label": "Appels d'offres (AO)", "action": "navigate", "params": {"path": "/tenders"}},
                {"label": "Courrier & Colis", "action": "navigate", "params": {"path": "/postal"}},
                {"label": "Parler a l'agent Sinistres", "action": "chat", "params": {}},
            ],
            "en": [
                {"label": "Claims", "action": "navigate", "params": {"path": "/claims"}},
                {"label": "Tenders", "action": "navigate", "params": {"path": "/tenders"}},
                {"label": "Courrier & Colis", "action": "navigate", "params": {"path": "/postal"}},
                {"label": "Talk to Claims agent", "action": "chat", "params": {}},
            ],
        },
    }

    def _generate_actions_for_intent(
        self,
        intent: str,
        agent_id: Optional[str] = None,
        lang: str = "fr",
    ) -> List[Dict[str, Any]]:
        """Generate contextual suggested actions based on intent, agent and language."""
        cfg_actions = ORCHESTRATOR_CONFIG.get("suggested_actions", {})
        key = agent_id if agent_id in self._DEFAULT_SUGGESTED_ACTIONS else "general"
        defaults = self._DEFAULT_SUGGESTED_ACTIONS[key]
        actions = cfg_actions.get(key, defaults)
        return actions.get(lang, actions.get("fr", defaults.get("fr", [])))

    # Default post-response actions config (used when config not mounted)
    _DEFAULT_POST_RESPONSE_ACTIONS = {
        "tenders": {
            "go_keywords": [
                "recommandation : go", "recommandation: go",
                "decision: go", "decision : go",
                "go/no-go: go", "go/no-go : go",
                "recommendation: go",
            ],
            "go_action": {
                "fr": "Deposer un claim assurance pour ce projet",
                "en": "File an insurance claim for this project",
            },
            "common": {
                "fr": [
                    {"label": "Voir les details de l'AO", "action": "navigate", "params": {"path": "/tenders"}},
                    {"label": "Analyser un autre AO", "action": "chat", "params": {}},
                ],
                "en": [
                    {"label": "View tender details", "action": "navigate", "params": {"path": "/tenders"}},
                    {"label": "Analyze another tender", "action": "chat", "params": {}},
                ],
            },
        },
        "claims": {
            "result_keywords": [
                "approved", "approuve", "denied", "refuse",
                "manual_review", "revue manuelle",
            ],
            "result_actions": {
                "fr": [
                    {"label": "Voir les details du sinistre", "action": "navigate", "params": {"path": "/claims"}},
                    {"label": "Demander une revue manuelle", "action": "chat", "params": {}},
                ],
                "en": [
                    {"label": "View claim details", "action": "navigate", "params": {"path": "/claims"}},
                    {"label": "Request manual review", "action": "chat", "params": {}},
                ],
            },
            "common": {
                "fr": [
                    {"label": "Traiter un autre sinistre", "action": "chat", "params": {}},
                ],
                "en": [
                    {"label": "Process another claim", "action": "chat", "params": {}},
                ],
            },
        },
        "courrier_reclamation": {
            "result_keywords": [
                "rembourser", "reexpedier", "rejeter", "escalader",
                "remboursement", "reexpedition", "reimbursed", "reshipped",
            ],
            "result_actions": {
                "fr": [
                    {"label": "Voir la reclamation", "action": "navigate", "params": {"path": "/postal"}},
                    {"label": "Escalader la reclamation", "action": "chat", "params": {}},
                ],
                "en": [
                    {"label": "View complaint", "action": "navigate", "params": {"path": "/postal"}},
                    {"label": "Escalate complaint", "action": "chat", "params": {}},
                ],
            },
            "common": {
                "fr": [
                    {"label": "Traiter une autre reclamation", "action": "chat", "params": {}},
                ],
                "en": [
                    {"label": "Process another complaint", "action": "chat", "params": {}},
                ],
            },
        },
        "courrier_info": {
            "common": {
                "fr": [
                    {"label": "Poser une autre question", "action": "chat", "params": {}},
                    {"label": "Voir les reclamations", "action": "navigate", "params": {"path": "/postal"}},
                ],
                "en": [
                    {"label": "Ask another question", "action": "chat", "params": {}},
                    {"label": "View complaints", "action": "navigate", "params": {"path": "/postal"}},
                ],
            },
        },
        "courrier_suivi": {
            "common": {
                "fr": [
                    {"label": "Suivre un autre colis", "action": "chat", "params": {}},
                    {"label": "Deposer une reclamation", "action": "chat", "params": {}},
                ],
                "en": [
                    {"label": "Track another parcel", "action": "chat", "params": {}},
                    {"label": "File a complaint", "action": "chat", "params": {}},
                ],
            },
        },
    }

    def _generate_post_response_actions(
        self,
        response_text: str,
        agent_id: Optional[str] = None,
        lang: str = "fr",
    ) -> List[Dict[str, Any]]:
        """Generate follow-up actions after an agent response (chaining)."""
        if not response_text:
            return []

        resp_lower = response_text.lower()
        actions: List[Dict[str, Any]] = []
        cfg_post = ORCHESTRATOR_CONFIG.get("post_response_actions", {})

        if agent_id and agent_id in self._DEFAULT_POST_RESPONSE_ACTIONS:
            agent_cfg = cfg_post.get(agent_id, self._DEFAULT_POST_RESPONSE_ACTIONS[agent_id])
            defaults = self._DEFAULT_POST_RESPONSE_ACTIONS[agent_id]

            # Handle go_keywords (tenders-style chaining)
            if "go_keywords" in defaults:
                go_keywords = agent_cfg.get("go_keywords", defaults["go_keywords"])
                if any(kw in resp_lower for kw in go_keywords):
                    go_action = agent_cfg.get("go_action", defaults.get("go_action", {}))
                    label = go_action.get(lang, go_action.get("fr", ""))
                    if label:
                        actions.append({"label": label, "action": "chat", "params": {}})

            # Handle result_keywords (claims/reclamation-style)
            if "result_keywords" in defaults:
                result_keywords = agent_cfg.get("result_keywords", defaults["result_keywords"])
                if any(kw in resp_lower for kw in result_keywords):
                    result_actions = agent_cfg.get("result_actions", defaults.get("result_actions", {}))
                    actions.extend(result_actions.get(lang, result_actions.get("fr", [])))

            # Common actions
            common = agent_cfg.get("common", defaults.get("common", {}))
            actions.extend(common.get(lang, common.get("fr", [])))
        else:
            actions = self._generate_actions_for_intent("general", None, lang)

        return actions
