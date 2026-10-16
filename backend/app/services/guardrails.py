"""NeMo Guardrails (TrustyAI, OpenShift AI) as seen from the backend: personal data masking.

The text is sent to the NeMo server's /v1/checks endpoint as an assistant message, so only the
output rails run: Presidio masking, no LLM call. Personal data comes back replaced by <ENTITY_TYPE>
placeholders (<EMAIL_ADDRESS>, <FR_IBAN>...). The agents call the same endpoint around their LLM
calls (agents/shared/guardrails.py).

mask_by_pattern() is the safety net of the chat when NeMo could not check an answer (the agents let
the text through when NeMo fails, guardrails.failOpen): emails, phone numbers and IBANs by pattern.
"""
import logging
import re
from collections import Counter
from typing import Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9_]*)>")


async def mask_personal_data(text: str) -> Optional[str]:
    """`text` with its personal data masked; None when the guardrails server is not configured or fails."""
    if not settings.guardrails_server_url or not text:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{settings.guardrails_server_url.rstrip('/')}/v1/checks", json={
                "model": settings.guardrails_model_name,
                "messages": [{"role": "assistant", "content": text}],
                "guardrails": {"config_id": settings.guardrails_config_id},
            })
            resp.raise_for_status()
            result = resp.json()
    except Exception as e:
        logger.warning("NeMo Guardrails masking failed: %s", e)
        return None
    return result.get("content") if result.get("status") == "modified" else text


def masked_entities(masked_text: str) -> Dict[str, int]:
    """Personal data types found in a masked text, with their counts ({"EMAIL_ADDRESS": 2, ...})."""
    return dict(Counter(PLACEHOLDER.findall(masked_text or "")))


_PATTERNS = {
    "EMAIL_ADDRESS": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "IBAN_CODE": re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,4})?\b"),
    "PHONE_NUMBER": re.compile(r"(?<!\w)(?:\+33\s?|0)[1-9](?:[\s.-]?\d{2}){4}(?!\w)"),
}


def mask_by_pattern(text: str) -> str:
    """Emails, IBANs and French phone numbers of `text` replaced by [ENTITY_TYPE] (NeMo's format in the UI)."""
    for entity_type, pattern in _PATTERNS.items():
        text = pattern.sub(f"[{entity_type}]", text)
    return text
