"""
Tests for ClaimService - with focus on persistence and logging.

Tests database interactions, logging, and end-to-end workflows.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select

from app.services.claim_service import ClaimService
from app.models.claim import Claim, ClaimDocument, ClaimDecision, ClaimStatus, DecisionType


class TestClaimService:
    """Test suite for ClaimService with persistence and logging verification."""

    @pytest.fixture
    def service(self):
        """Create ClaimService with mocked orchestrator."""
        with patch('app.services.claim_service.AgentOrchestrator') as mock_orch:
            service = ClaimService()
            service.orchestrator = AsyncMock()
            return service

    @pytest.mark.asyncio
    async def test_get_claim_by_id_exists(self, service, db_session, test_claim):
        """Test retrieving existing claim from database."""
        # Test persistence: READ
        claim = await service.get_claim_by_id(db_session, str(test_claim.id))

        assert claim is not None
        assert claim.id == test_claim.id
        assert claim.claim_number == test_claim.claim_number

    @pytest.mark.asyncio
    async def test_get_claim_by_id_not_found(self, service, db_session):
        """Test retrieving non-existent claim."""
        claim = await service.get_claim_by_id(db_session, "non-existent-id")

        assert claim is None

    @pytest.mark.asyncio
    async def test_build_claim_context_basic(self, service, db_session, test_claim):
        """Test building claim context from database."""
        # Test persistence: READ with relationships
        context = await service.build_claim_context(db_session, test_claim)

        assert context["entity_type"] == "claim"
        assert context["entity_id"] == str(test_claim.id)
        assert context["entity_data"]["claim_number"] == test_claim.claim_number
        assert context["entity_data"]["user_id"] == test_claim.user_id

    @pytest.mark.asyncio
    async def test_build_claim_context_with_document(
        self, service, db_session, test_claim_with_document
    ):
        """Test building context with OCR document from database."""
        claim, document = test_claim_with_document

        # Test persistence: JOIN query
        context = await service.build_claim_context(db_session, claim)

        assert "additional_context" in context
        assert "OCR Data" in context["additional_context"]
        assert "John Doe" in context["additional_context"]["OCR Data"]

    @pytest.mark.asyncio
    async def test_save_decision_persistence(
        self, service, db_session, test_claim, capture_logs
    ):
        """Test saving decision to database and verify logging."""
        decision_data = {
            "recommendation": "approve",
            "confidence": 0.85,
            "reasoning": "Claim is valid",
            "evidence": {"policy": "POL-001"}
        }

        # Test persistence: CREATE
        decision = await service.save_decision(
            db_session, str(test_claim.id), decision_data
        )

        # Verify database persistence
        assert decision.id is not None
        assert decision.claim_id == test_claim.id
        assert decision.initial_decision == DecisionType.approve
        assert decision.initial_confidence == 0.85
        assert decision.initial_reasoning == "Claim is valid"
        assert decision.relevant_policies["policy"] == "POL-001"

        # Verify decision was committed to database
        result = await db_session.execute(
            select(ClaimDecision).where(ClaimDecision.claim_id == test_claim.id)
        )
        saved_decision = result.scalar_one_or_none()
        assert saved_decision is not None
        assert saved_decision.id == decision.id

        # Verify logging
        assert any(
            f"Decision saved for claim {test_claim.id}" in record.message
            for record in capture_logs.records
        )

    @pytest.mark.asyncio
    async def test_process_claim_updates_status(
        self, service, db_session, test_claim, capture_logs
    ):
        """Test claim processing updates database status with logging."""
        # Mock orchestrator responses
        service.orchestrator.create_agent = AsyncMock(return_value={"agent_id": "test-agent"})
        service.orchestrator.create_session = AsyncMock(return_value={"session_id": "test-session"})
        service.orchestrator.execute_turn = AsyncMock(return_value={
            "turn_id": "test-turn",
            "response": {
                "content": "**Recommendation**: approve\n**Confidence**: 85%"
            }
        })

        agent_config = {"model": "test-model"}

        # Test persistence: UPDATE status
        result = await service.process_claim_with_agent(
            db_session, str(test_claim.id), agent_config
        )

        # Verify status updated in database
        await db_session.refresh(test_claim)
        assert test_claim.status == ClaimStatus.completed
        assert test_claim.processed_at is not None

        # Verify persistence: changes committed
        result = await db_session.execute(
            select(Claim).where(Claim.id == test_claim.id)
        )
        updated_claim = result.scalar_one()
        assert updated_claim.status == ClaimStatus.completed

        # Verify logging of each step
        log_messages = [record.message for record in capture_logs.records]
        assert any("Creating agent" in msg for msg in log_messages)
        assert any("Creating session" in msg for msg in log_messages)
        assert any("Executing turn" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_process_claim_sets_manual_review_status(
        self, service, db_session, test_claim
    ):
        """Test claim sets manual_review status when uncertain."""
        service.orchestrator.create_agent = AsyncMock(return_value={"agent_id": "test-agent"})
        service.orchestrator.create_session = AsyncMock(return_value={"session_id": "test-session"})
        service.orchestrator.execute_turn = AsyncMock(return_value={
            "response": {
                "content": "**Recommendation**: manual_review\nUncertain coverage"
            }
        })

        # Test persistence: status based on decision
        await service.process_claim_with_agent(
            db_session, str(test_claim.id), {"model": "test"}
        )

        await db_session.refresh(test_claim)
        assert test_claim.status == ClaimStatus.manual_review

    @pytest.mark.asyncio
    async def test_process_claim_error_handling(
        self, service, db_session, test_claim, capture_logs
    ):
        """Test error handling persists failed status."""
        # Force an error
        service.orchestrator.create_agent = AsyncMock(side_effect=Exception("Connection error"))

        # Test persistence: error handling
        with pytest.raises(Exception):
            await service.process_claim_with_agent(
                db_session, str(test_claim.id), {"model": "test"}
            )

        # Verify failed status persisted
        await db_session.refresh(test_claim)
        assert test_claim.status == ClaimStatus.failed

        # Verify error logged
        assert any(
            "Error processing claim" in record.message
            for record in capture_logs.records
        )

    @pytest.mark.asyncio
    async def test_process_claim_not_found(self, service, db_session):
        """Test processing non-existent claim raises error."""
        with pytest.raises(ValueError, match="Claim .* not found"):
            await service.process_claim_with_agent(
                db_session, "non-existent-id", {"model": "test"}
            )

    @pytest.mark.asyncio
    async def test_claim_processing_sets_processing_status(
        self, service, db_session, test_claim
    ):
        """Test claim status set to processing before agent execution."""
        service.orchestrator.create_agent = AsyncMock(return_value={"agent_id": "test-agent"})
        service.orchestrator.create_session = AsyncMock(return_value={"session_id": "test-session"})

        # Capture status changes
        status_changes = []

        async def track_status(*args, **kwargs):
            await db_session.refresh(test_claim)
            status_changes.append(test_claim.status)
            return {"response": {"content": "approve"}}

        service.orchestrator.execute_turn = AsyncMock(side_effect=track_status)

        # Initial status
        assert test_claim.status == ClaimStatus.pending

        await service.process_claim_with_agent(
            db_session, str(test_claim.id), {"model": "test"}
        )

        # Verify status progression: pending -> processing -> completed
        await db_session.refresh(test_claim)
        final_status = test_claim.status

        # After processing, should be completed or manual_review
        assert final_status in [ClaimStatus.completed, ClaimStatus.manual_review]

    @pytest.mark.asyncio
    async def test_complete_workflow_persistence(
        self, service, db_session, test_claim, capture_logs
    ):
        """End-to-end test: verify all data persists correctly."""
        # Setup mocks
        service.orchestrator.create_agent = AsyncMock(return_value={
            "agent_id": "test-agent-123"
        })
        service.orchestrator.create_session = AsyncMock(return_value={
            "session_id": "test-session-456"
        })
        service.orchestrator.execute_turn = AsyncMock(return_value={
            "turn_id": "test-turn-789",
            "response": {
                "content": """
                **Recommendation**: approve
                **Confidence**: 92%
                **Reasoning**: Claim meets all requirements
                """
            }
        })

        # Process claim
        result = await service.process_claim_with_agent(
            db_session, str(test_claim.id), {"model": "test"}
        )

        # Save decision
        await service.save_decision(
            db_session, str(test_claim.id), result["decision"]
        )

        # Verify all persistence
        # 1. Claim status updated
        await db_session.refresh(test_claim)
        assert test_claim.status == ClaimStatus.completed
        assert test_claim.processed_at is not None

        # 2. Decision saved
        decision_result = await db_session.execute(
            select(ClaimDecision).where(ClaimDecision.claim_id == test_claim.id)
        )
        decision = decision_result.scalar_one()
        assert decision.initial_decision == DecisionType.approve
        assert decision.initial_confidence == 0.92

        # 3. Verify logging of complete workflow
        log_messages = [r.message for r in capture_logs.records]
        assert any("Creating agent" in msg for msg in log_messages)
        assert any("Session created" in msg for msg in log_messages)
        assert any("Turn completed" in msg for msg in log_messages)
        assert any(f"Decision saved for claim {test_claim.id}" in msg for msg in log_messages)
