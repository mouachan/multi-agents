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

from app.services.pii.redactor import redact_text_pii

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.llamastack.orchestrator_prompts import (
    CHAT_AGENT_WRAPPER,
    LANGUAGE_RULE_TEMPLATE,
    ORCHESTRATOR_CONFIG,
    ORCHESTRATOR_SYSTEM_INSTRUCTIONS,
)
from app.services.agent.responses_orchestrator import ResponsesOrchestrator
from .conversation_utils import ConversationHelper
from .registry import AgentRegistry

logger = logging.getLogger(__name__)


class OrchestratorService:
    """High-level orchestrator that routes messages to specialized agents."""

    def __init__(self, orchestrator: Optional[ResponsesOrchestrator] = None):
        self.orchestrator = orchestrator or ResponsesOrchestrator()
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
                welcome = tpl.format(agent_name=agent_def.name)
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

        # Fast keyword classification (no LLM call - saves ~10s)
        classification = self._fallback_classification(message, session.agent_id)
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

        # Single LLM call — one model, all tools, the LLM decides everything
        if agent_id:
            agent_def = AgentRegistry.get(agent_id)
            if agent_def and agent_def.tools:
                try:
                    user_lang = self._detect_language(message)
                    lang_name = "English" if user_lang == "en" else "French"
                    lang_suffix = LANGUAGE_RULE_TEMPLATE.format(lang_name=lang_name)

                    custom_prompt = (session.session_metadata or {}).get("custom_prompt")
                    agent_instructions = custom_prompt or agent_def.instructions
                    tools = agent_def.tools
                    instructions = self._wrap_instructions_for_chat(agent_instructions) + lang_suffix
                    model = settings.llamastack_default_model

                    logger.info(f"Calling agent '{agent_id}': model={model}, tools={len(tools)}, lang={user_lang}")

                    result = await self.orchestrator.process_with_agent(
                        agent_config={"model": model, "instructions": instructions},
                        input_message=message,
                        tools=tools,
                        previous_response_id=previous_response_id,
                    )

                    agent_response = result.get("output", "")
                    tool_calls = result.get("tool_calls", [])
                    token_usage = ConversationHelper.normalize_token_usage(result.get("usage", {}))

                    # Retry if LLM wrote tool calls as text instead of function calling
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
                            tools=tools,
                            previous_response_id=last_response_id,
                        )
                        agent_response = result.get("output", "")
                        tool_calls = result.get("tool_calls", [])
                        retry_usage = ConversationHelper.normalize_token_usage(result.get("usage", {}))
                        if token_usage and retry_usage:
                            token_usage = {k: token_usage[k] + retry_usage[k] for k in token_usage}
                        elif retry_usage:
                            token_usage = retry_usage

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

                except Exception as e:
                    logger.error(f"Agent {agent_id} MCP call failed: {e}", exc_info=True)
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

        # Save assistant response
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
            agent_id=agent_id or "orchestrator",
            suggested_actions=suggested_actions if suggested_actions else None,
            tool_calls=enriched_tool_calls if enriched_tool_calls else None,
            token_usage=token_usage,
        )
        db.add(assistant_msg)
        await db.commit()

        # Determine which model was used (short name for display)
        model_id = None
        if agent_id and AgentRegistry.get(agent_id):
            full_model = model if isinstance(model, str) else settings.llamastack_default_model
            # Extract short name: "litemaas/Mistral-Small-24B-W8A8" → "Mistral-Small-24B"
            short = full_model.split("/")[-1] if "/" in full_model else full_model
            # Remove quantization suffix (e.g. -W8A8, -W4A16)
            short = re.sub(r'-W\d+A\d+$', '', short)
            model_id = short

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

        Same routing logic as process_message() but yields events progressively.
        """
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

        # Fast keyword classification
        classification = self._fallback_classification(message, session.agent_id)
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
        if not agent_def or not agent_def.tools:
            yield {"type": "error", "message": f"Agent {agent_id} not found or has no tools"}
            return

        # Emit agent info immediately so frontend can update badge/icon
        yield {"type": "agent_resolved", "agent_id": agent_id}

        user_lang = self._detect_language(message)
        lang_name = "English" if user_lang == "en" else "French"
        lang_suffix = LANGUAGE_RULE_TEMPLATE.format(lang_name=lang_name)

        custom_prompt = (session.session_metadata or {}).get("custom_prompt")
        agent_instructions = custom_prompt or agent_def.instructions
        tools = agent_def.tools
        instructions = self._wrap_instructions_for_chat(agent_instructions) + lang_suffix
        model = settings.llamastack_streaming_model or settings.llamastack_default_model

        logger.info(f"Streaming agent '{agent_id}': model={model}, tools={len(tools)}, lang={user_lang}")

        tool_calls = []
        full_text = ""
        response_id = None
        token_usage = None

        try:
            async for event in self.orchestrator.process_with_agent_stream(
                agent_config={"model": model, "instructions": instructions},
                input_message=message,
                tools=tools,
                previous_response_id=previous_response_id,
            ):
                event_type = event.get("type")

                if event_type == "tool_call":
                    yield event

                elif event_type == "tool_result":
                    tool_calls.append({
                        "name": event.get("name"),
                        "status": event.get("status"),
                    })
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
                            "output": tc.get("output"),
                            "error": tc.get("error"),
                        }
                        for tc in event.get("tool_calls", [])
                        if isinstance(tc, dict) and tc.get("name")
                    ]

        except Exception as e:
            logger.error(f"Stream error for agent {agent_id}: {e}", exc_info=True)
            yield {"type": "error", "message": str(e)}
            return

        # Post-processing: PII redaction on complete text
        if full_text:
            full_text = ConversationHelper.clean_response_for_chat(full_text)
            redacted = redact_text_pii(full_text)
            if redacted != full_text:
                logger.info("PII detected and redacted in streamed response")
                full_text = redacted
                # Send replacement so frontend swaps the unredacted deltas
                yield {"type": "text_replace", "text": full_text}

        suggested_actions = self._generate_post_response_actions(full_text, agent_id, user_lang)

        # Store last_response_id for conversation chaining
        if response_id:
            metadata["last_response_id"] = response_id
            session.session_metadata = metadata

        # Save assistant response to DB
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=full_text,
            agent_id=agent_id or "orchestrator",
            suggested_actions=suggested_actions if suggested_actions else None,
            tool_calls=tool_calls if tool_calls else None,
            token_usage=token_usage,
        )
        db.add(assistant_msg)
        await db.commit()

        # Model short name
        model_id = None
        full_model = model if isinstance(model, str) else settings.llamastack_default_model
        short = full_model.split("/")[-1] if "/" in full_model else full_model
        short = re.sub(r'-W\d+A\d+$', '', short)
        model_id = short

        # Final done event with enriched data
        yield {
            "type": "done",
            "response_id": response_id,
            "usage": token_usage,
            "tool_calls": tool_calls,
            "agent_id": agent_id,
            "model_id": model_id,
            "suggested_actions": suggested_actions,
        }

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
    }

    @staticmethod
    def _detect_language(message: str) -> str:
        """Detect user language from message. Returns 'en' or 'fr'."""
        lang_cfg = ORCHESTRATOR_CONFIG.get("language_detection", {})
        fr_words = set(lang_cfg.get("fr_words", OrchestratorService._DEFAULT_FR_WORDS))
        min_match = lang_cfg.get("min_match_count", 2)
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
        "general": {
            "fr": [
                {"label": "Sinistres (Claims)", "action": "navigate", "params": {"path": "/claims"}},
                {"label": "Appels d'offres (AO)", "action": "navigate", "params": {"path": "/tenders"}},
                {"label": "Parler a l'agent Sinistres", "action": "chat", "params": {}},
                {"label": "Parler a l'agent AO", "action": "chat", "params": {}},
            ],
            "en": [
                {"label": "Claims", "action": "navigate", "params": {"path": "/claims"}},
                {"label": "Tenders", "action": "navigate", "params": {"path": "/tenders"}},
                {"label": "Talk to Claims agent", "action": "chat", "params": {}},
                {"label": "Talk to Tenders agent", "action": "chat", "params": {}},
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
        key = agent_id if agent_id in ("tenders", "claims") else "general"
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

        if agent_id == "tenders":
            tender_cfg = cfg_post.get("tenders", self._DEFAULT_POST_RESPONSE_ACTIONS["tenders"])
            go_keywords = tender_cfg.get("go_keywords", self._DEFAULT_POST_RESPONSE_ACTIONS["tenders"]["go_keywords"])
            if any(kw in resp_lower for kw in go_keywords):
                go_action = tender_cfg.get("go_action", self._DEFAULT_POST_RESPONSE_ACTIONS["tenders"]["go_action"])
                label = go_action.get(lang, go_action.get("fr", ""))
                actions.append({"label": label, "action": "chat", "params": {}})
            common = tender_cfg.get("common", self._DEFAULT_POST_RESPONSE_ACTIONS["tenders"]["common"])
            actions.extend(common.get(lang, common.get("fr", [])))
        elif agent_id == "claims":
            claims_cfg = cfg_post.get("claims", self._DEFAULT_POST_RESPONSE_ACTIONS["claims"])
            result_keywords = claims_cfg.get("result_keywords", self._DEFAULT_POST_RESPONSE_ACTIONS["claims"]["result_keywords"])
            if any(kw in resp_lower for kw in result_keywords):
                result_actions = claims_cfg.get("result_actions", self._DEFAULT_POST_RESPONSE_ACTIONS["claims"]["result_actions"])
                actions.extend(result_actions.get(lang, result_actions.get("fr", [])))
            common = claims_cfg.get("common", self._DEFAULT_POST_RESPONSE_ACTIONS["claims"]["common"])
            actions.extend(common.get(lang, common.get("fr", [])))
        else:
            actions = self._generate_actions_for_intent("general", None, lang)

        return actions
