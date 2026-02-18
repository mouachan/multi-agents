"""
Tests for ResponseParser service.

Tests parsing of agent responses in various formats.
"""
import pytest
import json
from app.services.agent.response_parser import ResponseParser, ResponseFormat


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

    def test_extract_tool_calls_openai_style(self, parser):
        """Test extracting OpenAI-style tool calls."""
        response = {
            "tool_calls": [
                {
                    "id": "call_123",
                    "function": {
                        "name": "ocr_document",
                        "arguments": {"document_path": "/test.pdf"}
                    }
                }
            ]
        }

        tool_calls = parser.extract_tool_calls(response)

        assert len(tool_calls) == 1
        assert tool_calls[0]["tool_name"] == "ocr_document"
        assert tool_calls[0]["arguments"]["document_path"] == "/test.pdf"
        assert tool_calls[0]["call_id"] == "call_123"

    def test_extract_tool_calls_llamastack_style(self, parser):
        """Test extracting LlamaStack-style tool calls."""
        response = {
            "completion_message": {
                "tool_calls": [
                    {
                        "tool_name": "retrieve_user_info",
                        "arguments": {"user_id": "USR001"},
                        "call_id": "turn_456"
                    }
                ]
            }
        }

        tool_calls = parser.extract_tool_calls(response)

        assert len(tool_calls) == 1
        assert tool_calls[0]["tool_name"] == "retrieve_user_info"
        assert tool_calls[0]["arguments"]["user_id"] == "USR001"

    def test_extract_tool_calls_none(self, parser):
        """Test extracting tool calls when none present."""
        response = {"content": "Just text response"}

        tool_calls = parser.extract_tool_calls(response)

        assert tool_calls == []

    def test_extract_metadata(self, parser):
        """Test extracting metadata from response."""
        response = {
            "usage": {
                "total_tokens": 350,
                "prompt_tokens": 250,
                "completion_tokens": 100
            },
            "model": "llama-3-70b",
            "created": 1234567890,
            "choices": [
                {"finish_reason": "stop"}
            ]
        }

        metadata = parser.extract_metadata(response)

        assert metadata["tokens_used"] == 350
        assert metadata["prompt_tokens"] == 250
        assert metadata["completion_tokens"] == 100
        assert metadata["model"] == "llama-3-70b"
        assert metadata["finish_reason"] == "stop"

    def test_extract_metadata_minimal(self, parser):
        """Test extracting metadata with minimal response."""
        metadata = parser.extract_metadata({})

        assert metadata == {}

    def test_parse_structured_output_json(self, parser):
        """Test parsing structured JSON output."""
        response_text = """
        ```json
        {
            "claim_number": "CLM-001",
            "amount": 150.00,
            "status": "approved"
        }
        ```
        """

        result = parser.parse_structured_output(response_text, ResponseFormat.JSON)

        assert result["claim_number"] == "CLM-001"
        assert result["amount"] == 150.00
        assert result["status"] == "approved"

    def test_parse_structured_output_json_direct(self, parser):
        """Test parsing direct JSON output."""
        response_text = '{"key": "value", "number": 42}'

        result = parser.parse_structured_output(response_text, ResponseFormat.JSON)

        assert result["key"] == "value"
        assert result["number"] == 42

    def test_parse_structured_output_invalid_json(self, parser):
        """Test parsing invalid JSON."""
        response_text = "This is not JSON"

        result = parser.parse_structured_output(response_text, ResponseFormat.JSON)

        assert result is None
