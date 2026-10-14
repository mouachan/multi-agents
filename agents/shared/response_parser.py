import json
import re
from typing import Any, Dict, Optional

# Tool calls written as text by the LLM instead of function calling, e.g. [get_claim(id="x")]
_TEXT_TOOL_CALL_RE = re.compile(r'\[\w+\(.*?\)\]', re.DOTALL)
_JSON_TOOL_CALL_RE = re.compile(
    r'\[\s*\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*\{[^}]*\}\s*\}\s*\]',
    re.DOTALL,
)


_TRAILING_COMMA = re.compile(r",\s*([}\]])")


class ResponseParser:
    @staticmethod
    def contains_text_tool_calls(text: str) -> bool:
        return bool(text) and bool(_TEXT_TOOL_CALL_RE.search(text) or _JSON_TOOL_CALL_RE.search(text))

    @staticmethod
    def _loads(raw: str) -> Any:
        """json.loads that also accepts trailing commas (``"reasoning": "...",\n}``), a
        frequent LLM slip that otherwise loses the confidence and the reasoning."""
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return json.loads(_TRAILING_COMMA.sub(r"\1", raw))

    @staticmethod
    def _extract_balanced_json(text: str, start: int) -> Optional[str]:
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start, len(text)):
            c = text[i]
            if escape_next:
                escape_next = False
                continue
            if c == "\\":
                escape_next = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        return None

    def parse_decision(self, response_text: str) -> Dict[str, Any]:
        default = {
            "recommendation": "manual_review",
            "confidence": 0.0,
            "reasoning": "",
            "evidence": {},
        }

        if not response_text:
            return default

        # Strategy 1: JSON in code blocks
        code_blocks = re.findall(r"```(?:json)?\s*\n(.*?)\n```", response_text, re.DOTALL)
        for block in code_blocks:
            try:
                data = self._loads(block.strip())
                if isinstance(data, dict) and ("recommendation" in data or "decision" in data):
                    return {
                        "recommendation": data.get("recommendation", data.get("decision", "manual_review")),
                        "confidence": float(data.get("confidence", 0.0)),
                        "reasoning": data.get("reasoning", data.get("reasoning_en", "")),
                        "evidence": data.get("evidence", {}),
                    }
            except (json.JSONDecodeError, ValueError):
                continue

        # Strategy 2: Raw JSON with recommendation key
        idx = response_text.find('"recommendation"')
        if idx == -1:
            idx = response_text.find('"decision"')
        if idx != -1:
            brace = response_text.rfind("{", 0, idx)
            if brace != -1:
                raw = self._extract_balanced_json(response_text, brace)
                if raw:
                    try:
                        data = self._loads(raw)
                        return {
                            "recommendation": data.get("recommendation", data.get("decision", "manual_review")),
                            "confidence": float(data.get("confidence", 0.0)),
                            "reasoning": data.get("reasoning", data.get("reasoning_en", "")),
                            "evidence": data.get("evidence", {}),
                        }
                    except (json.JSONDecodeError, ValueError):
                        pass

        # Strategy 3: Text-based keyword extraction
        text_lower = response_text.lower()
        recommendation = "manual_review"

        decision_keywords = {
            "approve": "approve",
            "approuv": "approve",
            "deny": "deny",
            "refus": "deny",
            "rejet": "rejeter",
            "manual_review": "manual_review",
            "revue manuelle": "manual_review",
            "go": "go",
            "no.go": "no_go",
            "no_go": "no_go",
            "a approfondir": "a_approfondir",
            "à approfondir": "a_approfondir",
            "rembourser": "rembourser",
            "réexpédier": "reexpedier",
            "reexpedier": "reexpedier",
            "rejeter": "rejeter",
            "escalader": "escalader",
        }

        for keyword, value in decision_keywords.items():
            if keyword in text_lower:
                recommendation = value
                break

        confidence = 0.0
        conf_match = re.search(r"(\d{1,3})\s*%", response_text)
        if conf_match:
            confidence = int(conf_match.group(1)) / 100.0

        reasoning = ""
        reason_match = re.search(
            r"(?:reasoning|raisonnement|explanation|justification)\s*[:\-]\s*(.+?)(?:\n|$)",
            response_text,
            re.IGNORECASE,
        )
        if reason_match:
            reasoning = reason_match.group(1).strip()

        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": {},
        }
