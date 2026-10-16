"""The decision that ends the processing of a case (A2A metadata mode=process).

Once the workflow tools have returned (executor), the agent receives final_request(): write the
analysis, then one JSON block. parse_decision() reads that block back; the backend saves it
(backend/app/services/decisions.py) and shows it to the reviewer (backend/app/services/review.py):

    recommendation  one of the decision values sent by the backend (metadata "decision_values")
    confidence      0.0 to 1.0
    reasoning       2 to 4 sentences
    reasoning_en    the same reasoning in English (shown to English readers)
    review          only when the recommendation hands the case to a person (metadata "review_decision"):
                      reasons     why a person must decide
                      checks      what the reviewer should verify, the most important first
                      suggestion  the decision the agent leans to (one of metadata "human_decisions"), or null

An answer without a readable block has no recommendation: the backend then hands the case to a reviewer.
"""
import json
import re
from typing import Any, Dict, List, Optional

FINAL_REQUEST = """All workflow tools have returned. This request comes from the automated processing
pipeline, not from a chat: write your analysis based on the tool results{optional}, then end your
answer with exactly one JSON code block:
```json
{{"recommendation": <one of {values}>, "confidence": <number between 0.0 and 1.0>, "reasoning": "<2 to 4 sentences>", "reasoning_en": "<the same reasoning in English>", "review": null}}
```{review}"""

REVIEW_REQUEST = """
When your recommendation is "{review_decision}", a person decides: replace null in "review" with
{{"reasons": ["<why a person must decide>"], "checks": ["<a fact the reviewer should verify>"], "suggestion": <the decision you lean to, one of {human_decisions}, or null>}}"""

_CODE_BLOCK = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)
_TRAILING_COMMA = re.compile(r",\s*([}\]])")
REASONING_MAX = 1000   # reasoning kept when the answer has no decision block


def _quoted(values: List[str]) -> str:
    return ", ".join(f'"{v}"' for v in values)


def final_request(decision_values: List[str], review_decision: Optional[str] = None,
                  human_decisions: Optional[List[str]] = None, optional_tools: Optional[List[str]] = None) -> str:
    """The last request of the processing: the analysis and the decision block."""
    optional = f" (you may use {', '.join(optional_tools)} if useful)" if optional_tools else ""
    review = REVIEW_REQUEST.format(review_decision=review_decision, human_decisions=_quoted(human_decisions or [])) \
        if review_decision else ""
    return FINAL_REQUEST.format(values=_quoted(decision_values), optional=optional, review=review)


def parse_decision(answer: str) -> Dict[str, Any]:
    """The decision block of the agent's answer (the last one if there are several)."""
    data = next((d for d in map(_loads, reversed(_CODE_BLOCK.findall(answer or ""))) if _is_decision(d)), None)
    if data is None:
        data = _loads(_braces_around(answer or "", '"recommendation"'))
    if not _is_decision(data):
        return {"recommendation": None, "confidence": 0.0, "reasoning": (answer or "").strip()[-REASONING_MAX:]}
    return {
        "recommendation": str(data["recommendation"]),
        "confidence": _confidence(data.get("confidence")),
        "reasoning": str(data.get("reasoning") or ""),
        "reasoning_en": str(data.get("reasoning_en") or ""),
        "review": _review(data.get("review")),
    }


def _is_decision(data: Any) -> bool:
    return isinstance(data, dict) and bool(data.get("recommendation"))


def _loads(raw: Optional[str]) -> Any:
    """json.loads that also accepts trailing commas (a frequent LLM slip); None when unreadable."""
    if not raw:
        return None
    for text in (raw, _TRAILING_COMMA.sub(r"\1", raw)):
        try:
            return json.loads(text.strip())
        except ValueError:
            continue
    return None


def _braces_around(text: str, key: str) -> Optional[str]:
    """The JSON object written without a code block that contains `key`."""
    start = text.rfind("{", 0, max(text.find(key), 0))
    if start == -1:
        return None
    depth, in_string, escaped = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if escaped:
            escaped = False
        elif c == "\\":
            escaped = True
        elif c == '"':
            in_string = not in_string
        elif not in_string and c in "{}":
            depth += 1 if c == "{" else -1
            if depth == 0:
                return text[start:i + 1]
    return None


def _confidence(value: Any) -> float:
    """0.0 to 1.0 (85 and "85%" are read as 0.85)."""
    try:
        number = float(str(value).rstrip("% "))
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(number / 100 if number > 1 else number, 1.0))


def _review(value: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(value, dict):
        return None
    texts = lambda key: [str(v) for v in value.get(key) or [] if v] if isinstance(value.get(key), list) else []
    suggestion = value.get("suggestion")
    return {"reasons": texts("reasons"), "checks": texts("checks"),
            "suggestion": str(suggestion) if suggestion else None}
