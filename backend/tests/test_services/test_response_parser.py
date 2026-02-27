"""
Tests for ResponseParser service.

Tests parsing of agent responses in various formats.
"""
import pytest
import json
from app.services.agent.response_parser import ResponseParser


class TestResponseParser:
    """Test suite for ResponseParser."""

    @pytest.fixture
    def parser(self):
        """Create ResponseParser instance."""
        return ResponseParser()

    def test_parse_decision_json_format(self, parser):
        """Test parsing decision from JSON format."""
        response_text = """
        Here is the decision:
        ```json
        {
            "recommendation": "approve",
            "confidence": 0.85,
            "reasoning": "Claim is valid and covered",
            "evidence": {"policy": "POL-001"}
        }
        ```
        """

        decision = parser.parse_decision(response_text)

        assert decision["recommendation"] == "approve"
        assert decision["confidence"] == 0.85
        assert decision["reasoning"] == "Claim is valid and covered"
        assert decision["evidence"]["policy"] == "POL-001"

    def test_parse_decision_text_format_approve(self, parser):
        """Test parsing approve decision from text."""
        response_text = """
        Based on my analysis, I recommend to APPROVE this claim.
        Confidence: 85%
        Reasoning: The claim meets all requirements and is within coverage limits.
        """

        decision = parser.parse_decision(response_text)

        assert decision["recommendation"] == "approve"
        assert decision["confidence"] == 0.85  # 85% converted to 0.85
        assert "claim meets all requirements" in decision["reasoning"].lower()

    def test_parse_decision_text_format_deny(self, parser):
        """Test parsing deny decision from text."""
        response_text = """
        I must DENY this claim.
        Confidence: 95%
        Reasoning: The diagnosis is not covered under the current policy.
        """

        decision = parser.parse_decision(response_text)

        assert decision["recommendation"] == "deny"
        assert decision["confidence"] == 0.95

    def test_parse_decision_text_format_manual_review(self, parser):
        """Test parsing manual review decision."""
        response_text = """
        This claim requires MANUAL REVIEW.
        There is uncertainty about coverage eligibility.
        """

        decision = parser.parse_decision(response_text)

        assert decision["recommendation"] == "manual_review"

    def test_parse_decision_confidence_without_percent(self, parser):
        """Test parsing confidence value without % sign."""
        response_text = """
        Approve
        Confidence: 0.92
        """

        decision = parser.parse_decision(response_text)

        assert decision["confidence"] == 0.92  # Already in 0-1 range

    def test_parse_decision_no_confidence(self, parser):
        """Test parsing decision without confidence."""
        response_text = "I approve this claim."

        decision = parser.parse_decision(response_text)

        assert decision["recommendation"] == "approve"
        assert decision["confidence"] == 0.0  # Default

    def test_parse_decision_empty_response(self, parser):
        """Test parsing empty response."""
        decision = parser.parse_decision("")

        assert decision["recommendation"] == "manual_review"  # Default
        assert decision["confidence"] == 0.0

    def test_parse_qa_response(self, parser):
        """Test parsing Q&A response."""
        response_text = """
        ```text
        Yes, flu treatment is covered under your health insurance policy.
        The coverage limit is $50,000 per year for outpatient care.
        ```
        """

        answer = parser.parse_qa_response(response_text)

        assert "flu treatment is covered" in answer
        assert "```" not in answer  # Markdown removed
        assert "$50,000" in answer

    def test_parse_qa_response_with_whitespace(self, parser):
        """Test Q&A response cleaning."""
        response_text = """


        This is the answer.


        Multiple paragraphs here.


        """

        answer = parser.parse_qa_response(response_text)

        # Excessive whitespace removed
        assert "\n\n\n" not in answer
        assert answer.startswith("This is")

    def test_parse_qa_response_empty(self, parser):
        """Test empty Q&A response."""
        answer = parser.parse_qa_response("")

        assert "No response received" in answer

