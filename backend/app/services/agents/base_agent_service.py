"""
Base Agent Service - Common processing logic for all agents.

Extracts the 90% identical pattern from ClaimService and TenderService:
1. Get entity from DB, set status "processing"
2. Build context via ContextBuilder
3. Call ResponsesOrchestrator.process_with_agent()
4. Parse decision via ResponseParser
5. Extract processing steps
6. Update entity status
7. Save metadata
"""
import json as json_lib
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.agent.context_builder import ContextBuilder
from app.services.agent.response_parser import ResponseParser
from app.services.agent.responses_orchestrator import ResponsesOrchestrator

logger = logging.getLogger(__name__)


class BaseAgentService(ABC):
    """Base class for agent-specific services."""

    def __init__(
        self,
        orchestrator: Optional[ResponsesOrchestrator] = None,
        context_builder: Optional[ContextBuilder] = None,
        response_parser: Optional[ResponseParser] = None,
    ):
        self.orchestrator = orchestrator or ResponsesOrchestrator()
        self.context_builder = context_builder or ContextBuilder()
        self.response_parser = response_parser or ResponseParser()

    # ── Abstract methods that subclasses must implement ──────────────

    @abstractmethod
    async def get_entity_by_id(self, db: AsyncSession, entity_id: str):
        """Fetch the entity from the database."""

    @abstractmethod
    async def build_entity_context(self, db: AsyncSession, entity) -> Dict[str, Any]:
        """Build processing context for the entity."""

    @abstractmethod
    def get_instructions(self) -> str:
        """Return agent system instructions."""

    @abstractmethod
    def get_user_message_template(self) -> str:
        """Return the user message template."""

    @abstractmethod
    def get_tools(self) -> List[str]:
        """Return list of tool names for this agent."""

    @abstractmethod
    def map_recommendation_to_status(self, recommendation: str) -> str:
        """Map agent recommendation to entity status."""

    @abstractmethod
    def get_entity_type(self) -> str:
        """Return entity type string (e.g. 'claim', 'tender')."""

    @abstractmethod
    def get_entity_number(self, entity) -> str:
        """Return entity number/identifier for session naming."""

    @abstractmethod
    def set_entity_status(self, entity, status: str) -> None:
        """Set entity status (handles enum conversion)."""

    @abstractmethod
    def set_entity_processed(self, entity, processing_time_ms: Optional[int]) -> None:
        """Set entity as processed with timing."""

    @abstractmethod
    def get_entity_metadata(self, entity) -> dict:
        """Get the entity metadata dict."""

    @abstractmethod
    def set_entity_metadata(self, entity, metadata: dict) -> None:
        """Set the entity metadata dict."""

    @abstractmethod
    async def save_decision(self, db: AsyncSession, entity_id: str, decision_data: Dict[str, Any]):
        """Save the decision to the database."""

    # ── Tool name to agent name mapping ─────────────────────────────

    def map_tool_to_agent_name(self, tool_name: str) -> str:
        """Map a tool name to its agent name for logging."""
        if "ocr" in tool_name.lower():
            return "ocr-agent"
        elif tool_name in [
            "retrieve_user_info", "retrieve_similar_claims", "search_knowledge_base",
            "retrieve_similar_references", "retrieve_historical_tenders", "retrieve_capabilities",
        ]:
            return "rag-agent"
        return "unknown"

    # ── Common processing logic ─────────────────────────────────────

    def _extract_processing_steps(self, tool_calls: List[Dict]) -> List[Dict[str, Any]]:
        """Extract processing steps from tool calls."""
        processing_steps = []

        for tc in tool_calls:
            tool_name = tc.get("name", "unknown")
            agent_name = self.map_tool_to_agent_name(tool_name)

            output_data = None
            duration_ms = None

            if tc.get("output"):
                try:
                    output_data = json_lib.loads(tc["output"])
                    if isinstance(output_data, dict) and "processing_time_seconds" in output_data:
                        duration_ms = int(output_data["processing_time_seconds"] * 1000)
                except Exception:
                    output_data = {"raw_text": tc["output"]}

            processing_steps.append({
                "step_name": tool_name,
                "agent_name": agent_name,
                "status": "failed" if tc.get("error") else "completed",
                "output_data": output_data,
                "error_message": tc.get("error"),
                "duration_ms": duration_ms,
            })

        return processing_steps

    async def process_entity(
        self,
        db: AsyncSession,
        entity_id: str,
        agent_config: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Process an entity using the agent.

        This is the main orchestration method that encapsulates the common
        pattern shared by ClaimService and TenderService.
        """
        # Get entity
        entity = await self.get_entity_by_id(db, entity_id)
        if not entity:
            raise ValueError(f"{self.get_entity_type().title()} {entity_id} not found")

        # Set status to processing
        self.set_entity_status(entity, "processing")
        await db.commit()

        try:
            # Build context
            context = await self.build_entity_context(db, entity)

            # Build processing message
            context_str = self.context_builder.build_processing_context(
                entity_type=self.get_entity_type(),
                entity_id=str(entity_id),
                entity_data=context["entity_data"],
                additional_context=context.get("additional_context"),
            )

            processing_message = f"{self.get_user_message_template()}\n\n{context_str}"

            # Build agent config
            effective_config = agent_config or {
                "model": settings.llamastack_default_model,
                "instructions": self.get_instructions(),
            }

            # Process with Responses API
            result = await self.orchestrator.process_with_agent(
                agent_config=effective_config,
                input_message=processing_message,
                tools=tools or self.get_tools(),
                session_name=f"{self.get_entity_type()}_{self.get_entity_number(entity)}_{datetime.now().isoformat()}",
            )

            # Parse decision
            response_content = result.get("output", "")
            decision_data = self.response_parser.parse_decision(response_content)

            # Extract processing steps
            tool_calls = result.get("tool_calls", [])
            processing_steps = self._extract_processing_steps(tool_calls)

            # Update entity status based on recommendation
            recommendation = decision_data.get("recommendation", "manual_review")
            new_status = self.map_recommendation_to_status(recommendation)
            self.set_entity_status(entity, new_status)

            # Set processed timestamp and timing
            total_duration_ms = sum(
                step.get("duration_ms", 0) for step in processing_steps if step.get("duration_ms")
            )
            self.set_entity_processed(entity, total_duration_ms if total_duration_ms > 0 else None)

            # Save processing metadata
            metadata = dict(self.get_entity_metadata(entity) or {})
            metadata["response_id"] = result.get("response_id")
            metadata["processing_steps"] = processing_steps
            metadata["usage"] = result.get("usage", {})
            self.set_entity_metadata(entity, metadata)

            await db.commit()

            return {
                "response_id": result.get("response_id"),
                "decision": decision_data,
                f"{self.get_entity_type()}_status": new_status,
                "processing_steps": processing_steps,
                "tool_calls": tool_calls,
                "usage": result.get("usage", {}),
            }

        except Exception as e:
            logger.error(f"Error processing {self.get_entity_type()} {entity_id}: {e}", exc_info=True)
            self.set_entity_status(entity, "failed")
            await db.commit()
            raise
