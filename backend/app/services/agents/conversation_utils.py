"""
Conversation utilities for orchestrator LLM interactions.

Handles:
- Text tool call detection and cleanup
- Response cleaning for chat display
- Token usage normalization
- LLM iteration config
"""
import re
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Regex: matches tool calls written as text by the LLM, e.g. [tool_name(arg="value")]
_TEXT_TOOL_CALL_RE = re.compile(r'\[\w+\(.*?\)\]', re.DOTALL)

# Regex: extract tool name from text-based tool call
_TEXT_TOOL_NAME_RE = re.compile(r'\[(\w+)\(')

# Regex: matches JSON-format tool calls written as text by the LLM,
# e.g. [{"name": "ocr_document", "arguments": {...}}]
_JSON_TOOL_CALL_RE = re.compile(
    r'\[\s*\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*\{[^}]*\}\s*\}\s*\]',
    re.DOTALL,
)

# Regex: extract tool name from JSON-format tool call text
_JSON_TOOL_NAME_RE = re.compile(r'"name"\s*:\s*"(\w+)"')

# Regex: matches ```json ... ``` fenced code blocks
_JSON_BLOCK_RE = re.compile(r'```json\s*\n.*?\n```', re.DOTALL)

# Regex: matches "## Tool Output" sections (LLM simulated tool results)
_TOOL_OUTPUT_SECTION_RE = re.compile(r'##\s*Tool Output\s*\n.*?(?=\n##|\Z)', re.DOTALL)


class ConversationHelper:
    """Utility class for LLM response processing and config."""

    _DEFAULTS = {
        "max_tool_call_retries": 1,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        for key, default in self._DEFAULTS.items():
            setattr(self, key, cfg.get(key, default))

    def contains_text_tool_calls(self, text: str) -> bool:
        """Detect if LLM response contains tool calls written as text.

        Matches both bracket syntax [tool_name(args)] and JSON syntax
        [{"name": "tool_name", "arguments": {...}}].
        """
        return bool(_TEXT_TOOL_CALL_RE.search(text) or _JSON_TOOL_CALL_RE.search(text))

    @staticmethod
    def extract_tool_names_from_text(text: str) -> List[str]:
        """Extract tool names from text-based tool calls.

        Handles both bracket syntax [tool_name(args)] and JSON syntax
        [{"name": "tool_name", "arguments": {...}}].
        Returns unique names in order of appearance.
        """
        seen = set()
        names = []
        # Bracket syntax: [tool_name(args)]
        for match in _TEXT_TOOL_NAME_RE.finditer(text):
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                names.append(name)
        # JSON syntax: [{"name": "tool_name", "arguments": {...}}]
        for match in _JSON_TOOL_NAME_RE.finditer(text):
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                names.append(name)
        return names

    @staticmethod
    def clean_response_for_chat(text: str) -> str:
        """Clean LLM response for chat display.

        Strips text tool calls (bracket and JSON format), JSON blocks,
        simulated tool output sections, empty step headers, narration lines,
        and fixes hallucinated domain prefixes on relative API URLs.
        """
        cleaned = _TEXT_TOOL_CALL_RE.sub('', text)
        cleaned = _JSON_TOOL_CALL_RE.sub('', cleaned)
        cleaned = _JSON_BLOCK_RE.sub('', cleaned)
        cleaned = _TOOL_OUTPUT_SECTION_RE.sub('', cleaned)
        cleaned = re.sub(r'###\s+Step\s+\d+:.*?\n\s*\n(?=###|\Z)', '', cleaned)
        cleaned = re.sub(r'(?:First|Next|Then|Now|Finally),?\s+I\s+will\s+[^\n]*\n?', '', cleaned)
        # Fix hallucinated domain on relative API links (LLM adds https://example.com)
        cleaned = re.sub(r'https?://[^/\s)]+(/api/v1/)', r'\1', cleaned)
        # Strip escalation marker if it leaked through
        cleaned = cleaned.replace('<<ESCALATE>>', '')
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    @staticmethod
    def normalize_token_usage(raw_usage: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """Normalize LlamaStack usage response to standard token_usage dict."""
        if not raw_usage:
            return None
        prompt = raw_usage.get("input_tokens", 0) or raw_usage.get("prompt_tokens", 0)
        completion = raw_usage.get("output_tokens", 0) or raw_usage.get("completion_tokens", 0)
        return {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": raw_usage.get("total_tokens", 0) or (prompt + completion),
        }
