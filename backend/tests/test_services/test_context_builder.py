"""
Tests for ContextBuilder service.

Tests context building for various scenarios.
"""
import pytest
from app.services.agent.context_builder import ContextBuilder


class TestContextBuilder:
    """Test suite for ContextBuilder."""

    @pytest.fixture
    def builder(self):
        """Create ContextBuilder instance."""
        return ContextBuilder()

    def test_build_processing_context_basic(self, builder):
        """Test basic processing context building."""
        entity_data = {
            "user_id": "USR001",
            "claim_number": "CLM-001",
            "amount": 150.00
        }

        context = builder.build_processing_context(
            entity_type="claim",
            entity_id="test-claim-123",
            entity_data=entity_data
        )

        # Verify structure
        assert "# CLAIM PROCESSING" in context
        assert "Entity ID: test-claim-123" in context
        assert "user_id: USR001" in context
        assert "claim_number: CLM-001" in context
        assert "amount: 150.0" in context

    def test_build_processing_context_with_additional(self, builder):
        """Test processing context with additional context."""
        entity_data = {"claim_number": "CLM-001"}
        additional_context = {
            "OCR Data": "Patient: John Doe\nAmount: $150",
            "RAG Results": ["Policy A covers this", "Similar claim approved"]
        }

        context = builder.build_processing_context(
            entity_type="claim",
            entity_id="test-123",
            entity_data=entity_data,
            additional_context=additional_context
        )

        assert "## OCR Data:" in context
        assert "Patient: John Doe" in context
        assert "## RAG Results:" in context
        assert "Policy A covers this" in context

    def test_build_review_context(self, builder):
        """Test review context building."""
        entity_data = {"claim_number": "CLM-001", "user_id": "USR001"}
        initial_decision = {
            "decision": "approve",
            "confidence": 0.85,
            "reasoning": "Claim is valid"
        }

        context = builder.build_review_context(
            entity_type="claim",
            entity_id="test-123",
            entity_data=entity_data,
            initial_decision=initial_decision
        )

        assert "# CLAIM REVIEW" in context
        assert "## Initial System Decision:" in context
        assert "Decision: approve" in context
        assert "Confidence: 85.00%" in context
        assert "Reasoning: Claim is valid" in context

    def test_build_review_context_with_history(self, builder):
        """Test review context with conversation history."""
        entity_data = {"claim_number": "CLM-001"}
        conversation_history = [
            {"question": "Is this covered?", "answer": "Yes, it is covered"},
            {"question": "What is the limit?", "answer": "The limit is $50,000"}
        ]

        context = builder.build_review_context(
            entity_type="claim",
            entity_id="test-123",
            entity_data=entity_data,
            conversation_history=conversation_history
        )

        assert "## Previous Q&A:" in context
        assert "1. Q: Is this covered?" in context
        assert "   A: Yes, it is covered" in context
        assert "2. Q: What is the limit?" in context

    def test_extract_ocr_context(self, builder):
        """Test OCR context extraction."""
        ocr_data = {
            "raw_ocr_text": "Patient: John Doe\nDiagnosis: Flu\nAmount: $150.00",
            "structured_data": {
                "patient_name": "John Doe",
                "diagnosis": "Flu",
                "amount": "150.00"
            }
        }

        context = builder.extract_ocr_context(ocr_data)

        assert "## OCR Extracted Text:" in context
        assert "Patient: John Doe" in context
        assert "## Structured Data:" in context
        assert "patient_name: John Doe" in context

    def test_extract_ocr_context_truncation(self, builder):
        """Test OCR context truncates long text."""
        long_text = "A" * 3000  # More than 2000 chars
        ocr_data = {"raw_ocr_text": long_text}

        context = builder.extract_ocr_context(ocr_data)

        assert "... (truncated)" in context
        assert len(context) < len(long_text)

    def test_extract_rag_context(self, builder):
        """Test RAG context extraction."""
        rag_results = [
            {
                "title": "Policy A",
                "content": "This policy covers flu treatment",
                "similarity_score": 0.95
            },
            {
                "title": "Policy B",
                "content": "Outpatient care is covered up to $50,000",
                "similarity_score": 0.87
            }
        ]

        context = builder.extract_rag_context(rag_results)

        assert "## Retrieved Information:" in context
        assert "1. Policy A (similarity: 95.00%)" in context
        assert "This policy covers flu treatment" in context
        assert "2. Policy B (similarity: 87.00%)" in context

    def test_extract_rag_context_max_results(self, builder):
        """Test RAG context respects max_results."""
        rag_results = [{"title": f"Result {i}", "content": f"Content {i}", "similarity_score": 0.9}
                       for i in range(10)]

        context = builder.extract_rag_context(rag_results, max_results=3)

        # Should only include 3 results
        assert "1. Result 0" in context
        assert "2. Result 1" in context
        assert "3. Result 2" in context
        assert "4. Result 3" not in context

    def test_extract_rag_context_empty(self, builder):
        """Test RAG context with no results."""
        context = builder.extract_rag_context([])

        assert "No retrieval results available" in context
