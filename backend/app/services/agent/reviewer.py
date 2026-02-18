"""
Review Service for Human-in-the-Loop workflows.

Provides reusable review workflows: ask questions, approve, deny.
Domain-agnostic and works with any entity type.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from .responses_orchestrator import ResponsesOrchestrator
from .context_builder import ContextBuilder
from .response_parser import ResponseParser

logger = logging.getLogger(__name__)


class ReviewService:
    """Service for managing review workflows with agents."""

    def __init__(
        self,
        orchestrator: Optional[ResponsesOrchestrator] = None,
        context_builder: Optional[ContextBuilder] = None,
        response_parser: Optional[ResponseParser] = None
    ):
        """
        Initialize review service.

        Args:
            orchestrator: Responses orchestrator instance
            context_builder: Context builder instance
            response_parser: Response parser instance
        """
        self.orchestrator = orchestrator or ResponsesOrchestrator()
        self.context_builder = context_builder or ContextBuilder()
        self.response_parser = response_parser or ResponseParser()

    async def ask_agent(
        self,
        agent_id: str,
        session_id: str,
        question: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ask agent a question in review context with conversation history.

        NOTE: agent_id and session_id are ignored with Responses API.
        Kept for backward compatibility with tests.

        Args:
            agent_id: Agent identifier (ignored)
            session_id: Session identifier (ignored)
            question: Reviewer's question
            context: Review context (entity data, decisions, conversation_history)

        Returns:
            Agent's answer and metadata

        Raises:
            Exception: If agent interaction fails
        """
        try:
            from app.core.config import settings

            # Build context for the question
            review_context = self.context_builder.build_review_context(
                entity_type=context.get('entity_type', 'entity'),
                entity_id=context.get('entity_id', 'unknown'),
                entity_data=context.get('entity_data', {}),
                initial_decision=context.get('initial_decision'),
                conversation_history=[]  # Don't include in text, we'll pass as messages
            )

            # Build message array with conversation history
            messages = []

            # First message: system context
            entity_label = context.get('entity_type', 'entity')
            context_message = f"{review_context}\n\nYou are helping a reviewer understand this {entity_label}. Answer their questions clearly and concisely."
            messages.append({"role": "user", "content": context_message})
            messages.append({"role": "assistant", "content": f"I understand the {entity_label} context. I'm ready to answer your questions."})

            # Add conversation history from agent_logs
            conversation_history = context.get('conversation_history', [])
            for entry in conversation_history:
                if entry.get('type') == 'reviewer_question':
                    messages.append({
                        "role": "user",
                        "content": entry.get('message', '')
                    })
                elif entry.get('type') == 'agent_answer':
                    messages.append({
                        "role": "assistant",
                        "content": entry.get('message', '')
                    })

            # Add current question
            messages.append({"role": "user", "content": question})

            # Process with Responses API using message array
            result = await self.orchestrator.process_with_agent(
                agent_config={
                    "model": settings.llamastack_default_model,
                    "instructions": f"You are a helpful {entity_label} processing assistant. Answer questions about this {entity_label} accurately and concisely based on the provided context and conversation history."
                },
                input_message=messages,  # Array of messages for history
                tools=None
            )

            # Extract response
            response_content = result.get('output', '')
            answer = self.response_parser.parse_qa_response(response_content)

            logger.info(f"Agent answered question with {len(conversation_history)} previous messages")

            return {
                "question": question,
                "answer": answer,
                "response_id": result.get('response_id'),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error asking agent: {e}", exc_info=True)
            raise

    async def ask_agent_standalone(
        self,
        question: str,
        agent_config: Dict[str, Any]
    ) -> str:
        """
        Ask agent a question using a temporary agent (no session persistence).

        Args:
            question: Question to ask
            agent_config: Agent configuration

        Returns:
            Agent's answer as string

        Raises:
            Exception: If agent interaction fails
        """
        try:
            # Use orchestrator to process with cleanup
            result = await self.orchestrator.process_with_agent(
                agent_config=agent_config,
                input_message=question,
                tools=None,
                cleanup=True  # Delete agent after processing
            )

            # Extract and clean response
            response_content = result.get('output', '')
            answer = self.response_parser.parse_qa_response(response_content)

            logger.info(f"Standalone agent answered question ({len(answer)} chars)")

            return answer

        except Exception as e:
            logger.error(f"Error in standalone ask-agent: {e}", exc_info=True)
            raise

    async def process_action(
        self,
        db: AsyncSession,
        action: str,
        entity_type: str,
        entity_id: str,
        reviewer_id: str,
        reviewer_name: str,
        comment: Optional[str] = None
    ) -> tuple:
        """
        Process reviewer action (approve/deny/comment) and update database.

        Args:
            db: Database session
            action: Action type ('approve', 'reject', 'comment', 'request_info')
            entity_type: Type of entity (e.g., 'claim')
            entity_id: Entity identifier
            reviewer_id: Reviewer identifier
            reviewer_name: Reviewer display name
            comment: Optional reviewer comment

        Returns:
            Tuple of (updated_entity, updated_decision)

        Raises:
            ValueError: If entity type not supported or entity not found
        """
        from sqlalchemy import select
        from sqlalchemy.orm.attributes import flag_modified

        if entity_type == "claim":
            from app.models import claim as models
            entity_model = models.Claim
            decision_model = models.ClaimDecision
            decision_fk = models.ClaimDecision.claim_id
            approve_decision = "approve"
            deny_decision = "deny"
        elif entity_type == "tender":
            from app.models import tender as models
            entity_model = models.Tender
            decision_model = models.TenderDecision
            decision_fk = models.TenderDecision.tender_id
            approve_decision = "go"
            deny_decision = "no_go"
        else:
            raise ValueError(f"Entity type '{entity_type}' not supported")

        # Get entity
        result = await db.execute(
            select(entity_model).where(entity_model.id == entity_id)
        )
        entity = result.scalar_one_or_none()

        if not entity:
            raise ValueError(f"{entity_type.title()} {entity_id} not found")

        # Get decision
        decision_result = await db.execute(
            select(decision_model).where(decision_fk == entity_id)
        )
        entity_decision = decision_result.scalar_one_or_none()

        timestamp = datetime.now(timezone.utc)

        # Process action
        if action == "approve":
            entity.status = "completed"
            entity.updated_at = timestamp

            if entity_decision:
                entity_decision.final_decision = approve_decision
                entity_decision.final_decision_by = reviewer_id
                entity_decision.final_decision_by_name = reviewer_name
                entity_decision.final_decision_at = timestamp
                entity_decision.final_decision_notes = comment
                entity_decision.updated_at = timestamp

            if not entity.agent_logs:
                entity.agent_logs = []
            entity.agent_logs.append({
                "timestamp": timestamp.isoformat(),
                "reviewer_id": reviewer_id,
                "reviewer_name": reviewer_name,
                "type": "approve",
                "message": comment or ""
            })
            flag_modified(entity, "agent_logs")

        elif action == "reject":
            entity.status = "failed"
            entity.updated_at = timestamp

            if entity_decision:
                entity_decision.final_decision = deny_decision
                entity_decision.final_decision_by = reviewer_id
                entity_decision.final_decision_by_name = reviewer_name
                entity_decision.final_decision_at = timestamp
                entity_decision.final_decision_notes = comment
                entity_decision.updated_at = timestamp

            if not entity.agent_logs:
                entity.agent_logs = []
            entity.agent_logs.append({
                "timestamp": timestamp.isoformat(),
                "reviewer_id": reviewer_id,
                "reviewer_name": reviewer_name,
                "type": "reject",
                "message": comment or ""
            })
            flag_modified(entity, "agent_logs")

        elif action == "comment":
            if not entity.agent_logs:
                entity.agent_logs = []
            entity.agent_logs.append({
                "timestamp": timestamp.isoformat(),
                "reviewer_id": reviewer_id,
                "reviewer_name": reviewer_name,
                "type": "comment",
                "message": comment or ""
            })
            flag_modified(entity, "agent_logs")

        elif action == "request_info":
            entity.status = "pending_info"
            if not entity.agent_logs:
                entity.agent_logs = []
            entity.agent_logs.append({
                "timestamp": timestamp.isoformat(),
                "reviewer_id": reviewer_id,
                "reviewer_name": reviewer_name,
                "type": "request_info",
                "message": comment or ""
            })
            flag_modified(entity, "agent_logs")

        await db.commit()
        await db.refresh(entity)
        if entity_decision:
            await db.refresh(entity_decision)

        logger.info(f"Processed {action} action for {entity_type} {entity_id} by {reviewer_name}")

        return entity, entity_decision

    async def validate_review_eligibility(
        self,
        entity_status: str,
        allowed_statuses: List[str]
    ) -> bool:
        """
        Validate if entity is eligible for review.

        Args:
            entity_status: Current entity status
            allowed_statuses: List of statuses that allow review

        Returns:
            True if review is allowed
        """
        return entity_status in allowed_statuses

    def build_decision_update(
        self,
        action: str,
        reviewer_id: str,
        reviewer_name: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build decision update data from reviewer action.

        Args:
            action: Reviewer action ('approve' or 'deny')
            reviewer_id: Reviewer identifier
            reviewer_name: Reviewer name
            comment: Optional comment

        Returns:
            Decision update dictionary
        """
        timestamp = datetime.now(timezone.utc)

        # Map action to decision
        decision_map = {
            'approve': 'approve',
            'deny': 'deny',
            'reject': 'deny'
        }

        final_decision = decision_map.get(action.lower(), 'manual_review')

        return {
            "final_decision": final_decision,
            "final_decision_by": reviewer_id,
            "final_decision_by_name": reviewer_name,
            "final_decision_at": timestamp,
            "final_decision_notes": comment
        }
