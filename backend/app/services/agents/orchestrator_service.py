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
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.llamastack.orchestrator_prompts import (
    CHAT_AGENT_WRAPPER,
    ORCHESTRATOR_CLASSIFICATION_PROMPT,
    ORCHESTRATOR_SYSTEM_INSTRUCTIONS,
    SIMPLE_QUERY_CLAIMS,
    SIMPLE_QUERY_TENDERS,
)
from app.services.agent.responses_orchestrator import ResponsesOrchestrator
from .registry import AgentRegistry

logger = logging.getLogger(__name__)


class OrchestratorService:
    """High-level orchestrator that routes messages to specialized agents."""

    def __init__(self, orchestrator: Optional[ResponsesOrchestrator] = None):
        self.orchestrator = orchestrator or ResponsesOrchestrator()

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
        if agent_id:
            agent_def = AgentRegistry.get(agent_id)
            if agent_def:
                welcome = f"Session demarree avec l'agent **{agent_def.name}**. Comment puis-je vous aider ?" if is_fr else f"Session started with agent **{agent_def.name}**. How can I help you?"
            else:
                welcome = "Session demarree." if is_fr else "Session started."
        else:
            welcome = (
                "Bienvenue ! Je suis l'orchestrateur multi-agents. Decrivez ce que vous souhaitez faire et je vous orienterai vers l'agent specialise."
                if is_fr else
                "Welcome! I'm the multi-agent orchestrator. Describe what you'd like to do and I'll route you to the right specialized agent."
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

        # Get conversation history
        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc())
        )
        history = history_result.scalars().all()

        # Fast keyword classification (no LLM call - saves ~10s)
        classification = self._fallback_classification(message, session.agent_id)
        intent = classification.get("intent", "general")
        agent_id = classification.get("agent_id") or session.agent_id
        response_text = classification.get("message", "")
        suggested_actions = classification.get("suggested_actions", [])
        tool_calls = []

        # Update session agent if routed
        if agent_id and agent_id != session.agent_id:
            session.agent_id = agent_id
            await db.commit()

        # Single LLM call WITH MCP tools (the agent handles everything)
        if agent_id:
            agent_def = AgentRegistry.get(agent_id)
            if agent_def and agent_def.tools:
                try:
                    # Build conversation for context
                    conversation = []
                    for msg in history[-10:]:  # Last 10 messages for context
                        conversation.append({
                            "role": msg.role,
                            "content": msg.content,
                        })

                    # Select tools, instructions, and iteration limit based on complexity
                    is_simple = self._is_simple_query(message)
                    tools, instructions = self._select_tools_for_request(
                        message, agent_id, agent_def
                    )

                    result = await self.orchestrator.process_with_agent(
                        agent_config={
                            "model": settings.llamastack_default_model,
                            "instructions": instructions,
                        },
                        input_message=conversation,
                        tools=tools,
                        max_infer_iters=2 if is_simple else 10,
                    )

                    agent_response = result.get("output", "")
                    tool_calls = result.get("tool_calls", [])

                    if agent_response and agent_response.strip():
                        response_text = agent_response
                        # Generate post-response actions (chaining)
                        suggested_actions = self._generate_post_response_actions(
                            response_text, agent_id
                        )

                except Exception as e:
                    logger.error(f"Agent {agent_id} MCP call failed: {e}", exc_info=True)
                    response_text = f"Erreur lors du traitement: {str(e)}"

        # Save assistant response
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
            agent_id=agent_id or "orchestrator",
            suggested_actions=suggested_actions if suggested_actions else None,
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
            "tool_calls": tool_calls,
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

    async def _classify_intent(
        self,
        message: str,
        context: str,
        current_agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Classify user intent using LLM."""
        try:
            prompt = ORCHESTRATOR_CLASSIFICATION_PROMPT.format(
                message=message,
                context=context or "No previous context.",
            )

            # Add info about current agent if pre-routed
            if current_agent_id:
                agent_def = AgentRegistry.get(current_agent_id)
                if agent_def:
                    prompt += f"\n\nCurrently routed to agent: {current_agent_id} ({agent_def.name})"

            result = await self.orchestrator.process_with_agent(
                agent_config={
                    "model": settings.llamastack_default_model,
                    "instructions": ORCHESTRATOR_SYSTEM_INSTRUCTIONS,
                },
                input_message=prompt,
                tools=None,
            )

            output = result.get("output", "")

            # Try to parse JSON from response
            try:
                # Find JSON in the response
                start = output.find("{")
                end = output.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(output[start:end])
            except json.JSONDecodeError:
                pass

            # Fallback: simple keyword matching
            return self._fallback_classification(message, current_agent_id)

        except Exception as e:
            logger.error(f"Error classifying intent: {e}", exc_info=True)
            return self._fallback_classification(message, current_agent_id)

    # Tools needed only for simple CRUD queries (list, get, stats)
    CRUD_TOOLS = {
        "claims": ["list_claims", "get_claim", "get_claim_statistics"],
        "tenders": ["list_tenders", "get_tender", "get_tender_statistics"],
    }

    # Keywords indicating a simple list/query (no processing needed)
    SIMPLE_QUERY_KEYWORDS = [
        "list", "lister", "liste", "montre", "affiche", "show",
        "combien", "how many", "stats", "statistiques", "statistics",
        "pending", "en attente", "status", "statut",
        "premier", "first", "dernier", "last", "recent",
    ]

    def _is_simple_query(self, message: str) -> bool:
        """Detect if the user request is a simple list/query (no processing)."""
        msg_lower = message.lower()
        # Simple query if it matches list keywords AND doesn't ask for processing
        process_keywords = [
            "traite", "process", "analyse", "analyser", "decide",
            "decision", "approve", "deny", "go/no-go",
        ]
        has_simple = any(kw in msg_lower for kw in self.SIMPLE_QUERY_KEYWORDS)
        has_process = any(kw in msg_lower for kw in process_keywords)
        return has_simple and not has_process

    def _select_tools_for_request(
        self, message: str, agent_id: str, agent_def
    ) -> tuple:
        """Select tools and instructions based on request complexity.

        Returns (tools, instructions) tuple. Simple queries get fewer tools
        and a lightweight prompt for faster responses.
        """
        if self._is_simple_query(message):
            tools = self.CRUD_TOOLS.get(agent_id, agent_def.tools[:3])
            simple_prompts = {
                "claims": SIMPLE_QUERY_CLAIMS,
                "tenders": SIMPLE_QUERY_TENDERS,
            }
            instructions = self._wrap_instructions_for_chat(
                simple_prompts.get(agent_id, "Use the available tools to answer.")
            )
            logger.info(f"Simple query detected - using {len(tools)} CRUD tools only")
        else:
            tools = agent_def.tools
            instructions = self._wrap_instructions_for_chat(agent_def.instructions)
            logger.info(f"Complex query - using all {len(tools)} tools")
        return tools, instructions

    @staticmethod
    def _wrap_instructions_for_chat(agent_instructions: str) -> str:
        """Wrap agent instructions with chat-specific guidance."""
        return CHAT_AGENT_WRAPPER.format(agent_instructions=agent_instructions)

    def _fallback_classification(
        self,
        message: str,
        current_agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fast intent classification using keyword matching (no LLM call)."""
        msg_lower = message.lower()

        # Tender keywords (checked first - more specific)
        tender_keywords = [
            "appel d'offres", "appels d'offres", "appel d offres",
            "ao-", "ao ", "tender", "tenders",
            "marche public", "marches publics", "soumission",
            "btp", "construction", "go/no-go", "go no go",
            "offre", "offres",
        ]
        # Claim keywords
        claim_keywords = [
            "claim", "claims", "clm-", "sinistre", "sinistres",
            "assurance", "dommage", "remboursement",
            "indemnisation", "police d'assurance", "contrat d'assurance",
            "pending", "approve", "deny",
        ]

        agent_id = current_agent_id
        intent = "general"

        for kw in tender_keywords:
            if kw in msg_lower:
                agent_id = "tenders"
                intent = "agent_request"
                break

        if intent == "general":
            for kw in claim_keywords:
                if kw in msg_lower:
                    agent_id = "claims"
                    intent = "agent_request"
                    break

        # If still no match but session has an agent, keep routing there
        if intent == "general" and current_agent_id:
            agent_id = current_agent_id
            intent = "follow_up"

        suggested_actions = self._generate_actions_for_intent(intent, agent_id)

        return {
            "intent": intent,
            "agent_id": agent_id,
            "message": "",
            "suggested_actions": suggested_actions,
        }

    def _generate_actions_for_intent(
        self,
        intent: str,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate contextual suggested actions based on intent and agent."""
        if agent_id == "tenders":
            return [
                {"label": "Voir les appels d'offres", "action": "navigate", "params": {"path": "/tenders"}},
                {"label": "Analyser un AO", "action": "chat", "params": {}},
                {"label": "Lister les AO en attente", "action": "chat", "params": {}},
            ]
        elif agent_id == "claims":
            return [
                {"label": "Voir les sinistres", "action": "navigate", "params": {"path": "/claims"}},
                {"label": "Traiter un sinistre", "action": "chat", "params": {}},
                {"label": "Lister les claims en attente", "action": "chat", "params": {}},
            ]
        else:
            # General / no agent: suggest both domains
            return [
                {"label": "Sinistres (Claims)", "action": "navigate", "params": {"path": "/claims"}},
                {"label": "Appels d'offres (AO)", "action": "navigate", "params": {"path": "/tenders"}},
                {"label": "Parler a l'agent Sinistres", "action": "chat", "params": {}},
                {"label": "Parler a l'agent AO", "action": "chat", "params": {}},
            ]

    def _generate_post_response_actions(
        self,
        response_text: str,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate follow-up actions after an agent response (chaining)."""
        if not response_text:
            return []

        resp_lower = response_text.lower()
        actions: List[Dict[str, Any]] = []

        if agent_id == "tenders":
            # After a Go decision → suggest chaining to claims
            if any(kw in resp_lower for kw in ["recommandation : go", "recommandation: go", "decision: go", "decision : go", "go/no-go: go", "go/no-go : go"]):
                actions.append({"label": "Deposer un claim assurance pour ce projet", "action": "chat", "params": {}})
            actions.append({"label": "Voir les details de l'AO", "action": "navigate", "params": {"path": "/tenders"}})
            actions.append({"label": "Analyser un autre AO", "action": "chat", "params": {}})
        elif agent_id == "claims":
            # After a claim decision
            if any(kw in resp_lower for kw in ["approved", "approuve", "denied", "refuse", "manual_review", "revue manuelle"]):
                actions.append({"label": "Voir les details du sinistre", "action": "navigate", "params": {"path": "/claims"}})
                actions.append({"label": "Demander une revue manuelle", "action": "chat", "params": {}})
            actions.append({"label": "Traiter un autre sinistre", "action": "chat", "params": {}})
        else:
            actions = self._generate_actions_for_intent("general", None)

        return actions
