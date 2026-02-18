"""
End-to-End Integration Tests for Claim Processing Workflow.

Tests complete workflow from claim creation to decision with:
- Full database persistence verification
- Comprehensive logging validation
- All steps tracked
"""
import pytest
from unittest.mock import AsyncMock
from sqlalchemy import select

from app.services.claim_service import ClaimService
from app.services.agent.reviewer import ReviewService
from app.models.claim import Claim, ClaimDocument, ClaimDecision, ClaimStatus, DecisionType


class TestClaimWorkflowE2E:
    """End-to-end tests for complete claim processing workflow."""

    @pytest.mark.asyncio
    async def test_complete_claim_lifecycle_with_logging(
        self, db_session, sample_claim_data, capture_logs
    ):
        """
        Test complete claim lifecycle with full persistence and logging.

        Steps:
        1. Create claim (INSERT)
        2. Add document (INSERT)
        3. Process with agent (UPDATE status)
        4. Save decision (INSERT)
        5. Review action (UPDATE decision)

        Verifies:
        - All database operations persist
        - All steps logged
        - Data integrity maintained
        """
        service = ClaimService()
        service.orchestrator = AsyncMock()

        # STEP 1: Create claim
        claim = Claim(**sample_claim_data)
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        # Verify persistence
        assert claim.id is not None
        assert claim.status == ClaimStatus.pending

        # STEP 2: Add OCR document
        document = ClaimDocument(
            claim_id=claim.id,
            document_type="medical_bill",
            file_path=claim.document_path,
            raw_ocr_text="Patient: Jane Doe\nDiagnosis: Diabetes treatment\nAmount: $2500",
            structured_data={
                "patient_name": "Jane Doe",
                "diagnosis": "Diabetes treatment",
                "amount": "2500"
            },
            ocr_confidence=0.93
        )
        db_session.add(document)
        await db_session.commit()

        # Verify document persisted
        doc_result = await db_session.execute(
            select(ClaimDocument).where(ClaimDocument.claim_id == claim.id)
        )
        saved_doc = doc_result.scalar_one()
        assert saved_doc.raw_ocr_text is not None

        # STEP 3: Process with agent
        service.orchestrator.create_agent = AsyncMock(return_value={
            "agent_id": "e2e-agent-123"
        })
        service.orchestrator.create_session = AsyncMock(return_value={
            "session_id": "e2e-session-456"
        })
        service.orchestrator.execute_turn = AsyncMock(return_value={
            "turn_id": "e2e-turn-789",
            "response": {
                "content": """
                Based on comprehensive analysis:

                **Recommendation**: approve
                **Confidence**: 88%
                **Reasoning**: Diabetes treatment is covered under health insurance.
                Amount of $2500 is within annual coverage limit.
                """
            }
        })

        result = await service.process_claim_with_agent(
            db_session, str(claim.id), {"model": "test-model"}
        )

        # Verify status updated
        await db_session.refresh(claim)
        assert claim.status == ClaimStatus.completed
        assert claim.processed_at is not None

        # Verify processing logged
        log_messages = [r.message for r in capture_logs.records]
        assert any("Creating agent" in msg for msg in log_messages)
        assert any("Session created" in msg for msg in log_messages)
        assert any("Turn completed" in msg for msg in log_messages)

        # STEP 4: Save decision
        decision = await service.save_decision(
            db_session, str(claim.id), result["decision"]
        )

        # Verify decision persisted with all fields
        assert decision.id is not None
        assert decision.claim_id == claim.id
        assert decision.initial_decision == DecisionType.approve
        assert decision.initial_confidence == 0.88
        assert "Diabetes treatment is covered" in decision.initial_reasoning

        # Verify decision committed to database
        decision_result = await db_session.execute(
            select(ClaimDecision).where(ClaimDecision.id == decision.id)
        )
        saved_decision = decision_result.scalar_one()
        assert saved_decision.initial_decision == DecisionType.approve

        # Verify decision save logged
        assert any(f"Decision saved for claim {claim.id}" in msg for msg in log_messages)

        # STEP 5: Reviewer action (approve)
        review_service = ReviewService()
        action_result = review_service.build_decision_update(
            action="approve",
            reviewer_id="REV-001",
            reviewer_name="Dr. Smith",
            comment="Reviewed and confirmed coverage"
        )

        # Update decision with reviewer action
        decision.final_decision = action_result["final_decision"]
        decision.final_decision_by = action_result["final_decision_by"]
        decision.final_decision_by_name = action_result["final_decision_by_name"]
        decision.final_decision_at = action_result["final_decision_at"]
        decision.final_decision_notes = action_result["final_decision_notes"]
        await db_session.commit()

        # Verify final decision persisted
        await db_session.refresh(decision)
        assert decision.final_decision == DecisionType.approve
        assert decision.final_decision_by == "REV-001"
        assert decision.final_decision_by_name == "Dr. Smith"
        assert decision.final_decision_notes == "Reviewed and confirmed coverage"

        # FINAL VERIFICATION: Query all data to ensure integrity
        final_claim_result = await db_session.execute(
            select(Claim).where(Claim.id == claim.id)
        )
        final_claim = final_claim_result.scalar_one()

        final_decision_result = await db_session.execute(
            select(ClaimDecision).where(ClaimDecision.claim_id == claim.id)
        )
        final_decision = final_decision_result.scalar_one()

        final_document_result = await db_session.execute(
            select(ClaimDocument).where(ClaimDocument.claim_id == claim.id)
        )
        final_document = final_document_result.scalar_one()

        # Verify complete data integrity
        assert final_claim.status == ClaimStatus.completed
        assert final_decision.initial_decision == DecisionType.approve
        assert final_decision.final_decision == DecisionType.approve
        assert final_document.raw_ocr_text is not None

        # Verify logging completeness
        assert len(capture_logs.records) > 0
        assert any("agent" in msg.lower() for msg in log_messages)
        assert any("session" in msg.lower() for msg in log_messages)
        assert any("decision" in msg.lower() for msg in log_messages)

    @pytest.mark.asyncio
    async def test_manual_review_workflow_with_qa(
        self, db_session, sample_claim_data, capture_logs
    ):
        """
        Test manual review workflow with Q&A persistence and logging.

        Steps:
        1. Claim requires manual review
        2. Reviewer asks questions
        3. Agent answers (logged)
        4. Reviewer makes decision
        5. All interactions persisted and logged
        """
        service = ClaimService()
        review_service = ReviewService()

        service.orchestrator = AsyncMock()
        review_service.orchestrator = AsyncMock()

        # Create claim
        claim = Claim(**sample_claim_data)
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        # Process - results in manual review
        service.orchestrator.create_agent = AsyncMock(return_value={"agent_id": "agent-mr"})
        service.orchestrator.create_session = AsyncMock(return_value={"session_id": "session-mr"})
        service.orchestrator.execute_turn = AsyncMock(return_value={
            "response": {
                "content": "**Recommendation**: manual_review\nUncertain about coverage"
            }
        })

        result = await service.process_claim_with_agent(
            db_session, str(claim.id), {"model": "test"}
        )

        # Verify manual review status
        await db_session.refresh(claim)
        assert claim.status == ClaimStatus.manual_review

        # Save decision
        decision = await service.save_decision(
            db_session, str(claim.id), result["decision"]
        )
        assert decision.requires_manual_review is True

        # Reviewer asks question
        review_service.orchestrator.execute_turn = AsyncMock(return_value={
            "response": {
                "content": "Yes, this diagnosis is covered under policy section 3.2"
            }
        })

        qa_result = await review_service.ask_agent(
            agent_id=result["agent_id"],
            session_id=result["session_id"],
            question="Is this diagnosis covered?",
            context={
                "entity_type": "claim",
                "entity_id": str(claim.id),
                "entity_data": {"claim_number": claim.claim_number},
                "initial_decision": {
                    "decision": "manual_review",
                    "confidence": 0.5,
                    "reasoning": "Uncertain about coverage"
                },
                "conversation_history": []
            }
        )

        # Verify Q&A logged
        log_messages = [r.message for r in capture_logs.records]
        assert any("answered question" in msg.lower() for msg in log_messages)

        # Reviewer approves after Q&A
        final_action = review_service.build_decision_update(
            action="approve",
            reviewer_id="REV-002",
            reviewer_name="Dr. Johnson",
            comment="Confirmed coverage via Q&A"
        )

        decision.final_decision = final_action["final_decision"]
        decision.final_decision_by = final_action["final_decision_by"]
        decision.final_decision_by_name = final_action["final_decision_by_name"]
        decision.final_decision_notes = final_action["final_decision_notes"]
        await db_session.commit()

        # Verify complete persistence
        final_decision_result = await db_session.execute(
            select(ClaimDecision).where(ClaimDecision.id == decision.id)
        )
        final_decision = final_decision_result.scalar_one()

        assert final_decision.initial_decision == DecisionType.manual_review
        assert final_decision.final_decision == DecisionType.approve
        assert final_decision.requires_manual_review is True
        assert "Confirmed coverage via Q&A" in final_decision.final_decision_notes

        # Verify comprehensive logging
        assert len(capture_logs.records) > 5  # Multiple steps logged

    @pytest.mark.asyncio
    async def test_deny_workflow_persistence(
        self, db_session, sample_claim_data, capture_logs
    ):
        """Test deny workflow with full persistence verification."""
        service = ClaimService()
        service.orchestrator = AsyncMock()

        # Create claim
        claim = Claim(**sample_claim_data)
        db_session.add(claim)
        await db_session.commit()
        await db_session.refresh(claim)

        # Process - results in deny
        service.orchestrator.create_agent = AsyncMock(return_value={"agent_id": "agent-deny"})
        service.orchestrator.create_session = AsyncMock(return_value={"session_id": "session-deny"})
        service.orchestrator.execute_turn = AsyncMock(return_value={
            "response": {
                "content": """
                **Recommendation**: deny
                **Confidence**: 95%
                **Reasoning**: Diagnosis not covered under current policy
                """
            }
        })

        result = await service.process_claim_with_agent(
            db_session, str(claim.id), {"model": "test"}
        )

        # Verify deny status
        await db_session.refresh(claim)
        assert claim.status == ClaimStatus.failed  # deny maps to failed

        # Save decision
        decision = await service.save_decision(
            db_session, str(claim.id), result["decision"]
        )

        # Verify deny decision persisted
        assert decision.initial_decision == DecisionType.deny
        assert decision.initial_confidence == 0.95
        assert "not covered" in decision.initial_reasoning

        # Verify logged
        log_messages = [r.message for r in capture_logs.records]
        assert any(f"Decision saved for claim {claim.id}" in msg for msg in log_messages)
        assert any("deny" in msg.lower() for msg in log_messages)
