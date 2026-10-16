"""Personal data never leaves an MCP server: the agents' model only reads placeholders.

Every tool result goes through mask() (shared/tools.py) before it is returned:

  - the fields that are personal by nature (name, e-mail, phone, address, date of birth) are replaced
    by their type:  "client_email": "[EMAIL_ADDRESS]";
  - the free text (document text, descriptions, reasonings) is masked by NeMo Guardrails, with the
    detectors of the agents' output rails (Presidio patterns and models; GLiNER for the names when its
    rail is enabled). All the texts of a result go in one NeMo call.
    Without NeMo (local stack), or when it does not answer, the text is masked by patterns (e-mail,
    IBAN, phone, social security and card numbers): it is never returned as is. Names in free text
    are only found by NeMo.

The records keep the real values in the database: the backend shows them to the users allowed to see
the case, and the tools compute with them (payout, similarity search).
"""
import logging
import os
import re
from typing import Any, Callable, Dict, List

import httpx

logger = logging.getLogger(__name__)

GUARDRAILS_ENDPOINT = os.getenv("GUARDRAILS_ENDPOINT", "").rstrip("/")
GUARDRAILS_CONFIG_ID = os.getenv("GUARDRAILS_CONFIG_ID", "multi-agents")
GUARDRAILS_MODEL = os.getenv("GUARDRAILS_MODEL", "llama-scout-17b")
GUARDRAILS_TIMEOUT = float(os.getenv("GUARDRAILS_TIMEOUT", "20"))

# Fields that hold one personal value, and the type that replaces it
PERSONAL_FIELDS = {
    "full_name": "PERSON", "user_name": "PERSON", "client_nom": "PERSON", "final_decision_by_name": "PERSON",
    "email": "EMAIL_ADDRESS", "user_email": "EMAIL_ADDRESS", "client_email": "EMAIL_ADDRESS",
    "phone_number": "PHONE_NUMBER", "user_phone": "PHONE_NUMBER", "client_telephone": "PHONE_NUMBER",
    "address": "LOCATION", "user_address": "LOCATION", "client_adresse": "LOCATION",
    "date_of_birth": "DATE_OF_BIRTH",
}
# Fields of free text, which may mention people
FREE_TEXT_FIELDS = {
    "raw_text", "raw_ocr_text", "claim_text", "full_text", "description", "detail",
    "reasoning", "initial_reasoning", "final_decision_notes",
}

# When NeMo is not there: what patterns can find reliably
PATTERNS = [
    ("EMAIL_ADDRESS", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("IBAN_CODE", re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[0-9A-Z]{4}){3,7}(?:\s?[0-9A-Z]{1,3})?\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b")),
    ("FR_NIR", re.compile(r"\b[1278]\s?\d{2}\s?(?:0[1-9]|1[0-2])\s?(?:\d{2}|2[AB])\s?\d{3}\s?\d{3}\s?\d{2}\b")),
    ("PHONE_NUMBER", re.compile(r"(?:(?:\+|\b00)33[\s.-]?(?:\(0\)[\s.-]?)?|\b0)[1-9](?:[\s.-]?\d{2}){4}\b")),   # French
    ("PHONE_NUMBER", re.compile(r"\+\d{1,3}(?:[\s.-]?\d{2,4}){2,5}\b")),                                     # international
    ("PHONE_NUMBER", re.compile(r"(?:\(\d{3}\)\s?|\b\d{3}[\s.-])\d{3}[\s.-]\d{4}\b")),                       # (555) 123-4567
]
PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9_]*)>")   # NeMo writes <TYPE>; the agents use [TYPE]
SEPARATOR = "\n\n¶¶¶\n\n"                         # between the texts of one NeMo call


async def mask(result: Dict[str, Any]) -> Dict[str, Any]:
    """The tool result with its personal data replaced by placeholders."""
    texts: List[str] = []
    setters: List[Callable[[str], None]] = []
    masked = _walk(result, texts, setters)
    if texts:
        for set_text, text in zip(setters, await mask_texts(texts)):
            set_text(text)
    return masked


def _walk(value: Any, texts: List[str], setters: List[Callable[[str], None]]) -> Any:
    """A copy of the value: personal fields replaced, free texts collected (set later)."""
    if isinstance(value, list):
        return [_walk(item, texts, setters) for item in value]
    if not isinstance(value, dict):
        return value
    copy: Dict[str, Any] = {}
    for key, item in value.items():
        if key in PERSONAL_FIELDS and item not in (None, ""):
            copy[key] = f"[{PERSONAL_FIELDS[key]}]"
        elif key in FREE_TEXT_FIELDS and isinstance(item, str) and item.strip():
            copy[key] = item
            texts.append(item)
            setters.append(lambda text, target=copy, field=key: target.__setitem__(field, text))
        else:
            copy[key] = _walk(item, texts, setters)
    return copy


async def mask_texts(texts: List[str]) -> List[str]:
    """The texts masked by NeMo Guardrails, else by patterns (never returned unmasked)."""
    if GUARDRAILS_ENDPOINT:
        try:
            masked = await _nemo(SEPARATOR.join(texts))
            parts = masked.split(SEPARATOR)
            if len(parts) == len(texts):
                return [mask_by_patterns(part) for part in parts]   # patterns too: NeMo's list may be shorter
            logger.warning("NeMo changed the text separators: masking by patterns")
        except Exception as e:
            logger.warning("NeMo masking failed (%s): masking by patterns", e)
    return [mask_by_patterns(text) for text in texts]


async def _nemo(text: str) -> str:
    """The output rails of NeMo (masking only, no LLM call) on the text."""
    async with httpx.AsyncClient(timeout=GUARDRAILS_TIMEOUT) as client:
        response = await client.post(f"{GUARDRAILS_ENDPOINT}/v1/checks", json={
            "model": GUARDRAILS_MODEL,
            "messages": [{"role": "assistant", "content": text}],
            "guardrails": {"config_id": GUARDRAILS_CONFIG_ID},
        })
        response.raise_for_status()
    data = response.json()
    if data.get("status") == "modified" and data.get("content"):
        return PLACEHOLDER.sub(r"[\1]", data["content"])
    return text


def mask_by_patterns(text: str) -> str:
    for kind, pattern in PATTERNS:
        text = pattern.sub(f"[{kind}]", text)
    return text
