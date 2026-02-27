"""
Response Parser for Agent Outputs.

Parses and extracts structured data from agent responses.
Domain-agnostic and reusable across different use cases.
"""
import re
import json
from typing import Dict, Any, Optional


class ResponseParser:
    """Parse agent responses into structured data."""

    @staticmethod
    def _extract_balanced_json(text: str, start: int) -> Optional[str]:
        """
        Extract a balanced JSON object starting at position start.
        Handles nested braces, strings with escaped characters, etc.

        Args:
            text: Full text
            start: Position of the opening '{'

        Returns:
            The balanced JSON string, or None if not found
        """
        if start >= len(text) or text[start] != '{':
            return None

        depth = 0
        in_string = False
        escape = False
        i = start

        while i < len(text):
            ch = text[i]

            if escape:
                escape = False
                i += 1
                continue

            if ch == '\\' and in_string:
                escape = True
                i += 1
                continue

            if ch == '"' and not escape:
                in_string = not in_string
                i += 1
                continue

            if not in_string:
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start:i + 1]

            i += 1

        return None

    def parse_decision(self, response_text: str) -> Dict[str, Any]:
        """
        Parse decision from agent response.

        Extracts decision, confidence, reasoning, and supporting evidence.

        Args:
            response_text: Raw agent response

        Returns:
            Structured decision data
        """
        decision_data = {
            "recommendation": "manual_review",
            "confidence": 0.0,
            "reasoning": "",
            "evidence": {}
        }

        if not response_text:
            return decision_data

        # Strategy 1: Find JSON in ```json ... ``` code blocks
        code_block_pattern = r'```(?:json)?\s*'
        for m in re.finditer(code_block_pattern, response_text, re.IGNORECASE):
            block_start = m.end()
            # Find opening brace
            brace_pos = response_text.find('{', block_start)
            if brace_pos != -1 and brace_pos - block_start < 10:
                json_str = self._extract_balanced_json(response_text, brace_pos)
                if json_str:
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict):
                            decision_data.update(parsed)
                            return decision_data
                    except json.JSONDecodeError:
                        continue

        # Strategy 2: Find raw JSON with "recommendation" key
        for m in re.finditer(r'\{\s*"recommendation"', response_text):
            json_str = self._extract_balanced_json(response_text, m.start())
            if json_str:
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        decision_data.update(parsed)
                        return decision_data
                except json.JSONDecodeError:
                    continue

        # Strategy 3: Find any JSON object containing recommendation-like keys
        for m in re.finditer(r'\{', response_text):
            json_str = self._extract_balanced_json(response_text, m.start())
            if json_str and len(json_str) > 50:
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict) and any(
                        k in parsed for k in ['recommendation', 'decision', 'confidence']
                    ):
                        decision_data.update(parsed)
                        return decision_data
                except json.JSONDecodeError:
                    continue

        # Fallback to text parsing
        text_lower = response_text.lower()

        # Extract recommendation (French + English)
        if any(word in text_lower for word in ['approve', 'approved', 'accept', '"go"', ': go', 'recommendation: go']):
            decision_data['recommendation'] = 'approve'
        elif any(word in text_lower for word in ['deny', 'denied', 'reject', '"no_go"', 'no-go', 'no go']):
            decision_data['recommendation'] = 'deny'
        elif any(word in text_lower for word in ['a_approfondir', 'à approfondir', 'approfondir']):
            decision_data['recommendation'] = 'a_approfondir'
        elif any(word in text_lower for word in ['review', 'uncertain', 'manual']):
            decision_data['recommendation'] = 'manual_review'

        # Extract confidence
        confidence_match = re.search(r'confidence[:\s]+(\d+(?:\.\d+)?)\s*%?', text_lower)
        if confidence_match:
            conf_value = float(confidence_match.group(1))
            decision_data['confidence'] = conf_value / 100 if conf_value > 1 else conf_value

        # Extract reasoning
        reasoning_patterns = [
            r'reasoning[:\s]+(.+?)(?:\n\n|\n#|$)',
            r'rationale[:\s]+(.+?)(?:\n\n|\n#|$)',
            r'explanation[:\s]+(.+?)(?:\n\n|\n#|$)'
        ]
        for pattern in reasoning_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                decision_data['reasoning'] = match.group(1).strip()
                break

        # If no reasoning found, use first substantial paragraph
        if not decision_data['reasoning']:
            paragraphs = [p.strip() for p in response_text.split('\n\n') if len(p.strip()) > 50]
            if paragraphs:
                decision_data['reasoning'] = paragraphs[0]

        return decision_data

    def parse_qa_response(self, response_text: str) -> str:
        """
        Parse Q&A response from agent.

        Cleans and formats the answer.

        Args:
            response_text: Raw agent response

        Returns:
            Cleaned answer text
        """
        if not response_text:
            return "No response received from agent."

        # Remove markdown code blocks if present
        cleaned = re.sub(r'```(?:json|markdown|text)?\s*(.*?)\s*```', r'\1', response_text, flags=re.DOTALL)

        # Remove excessive whitespace
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        cleaned = cleaned.strip()

        return cleaned
