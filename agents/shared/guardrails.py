"""NeMo Guardrails (TrustyAI, RHOAI 3.5) — input/output rails with PII masking.

Uses the server's `POST /v1/checks` endpoint (Colang 1.0 configs), which runs the
rails without generating an LLM answer and returns the processed text:
    request : {"model", "messages": [{"role": "user"|"assistant", "content"}], "guardrails": {"config_id"}}
    response: {"status": "passed" | "modified" | "blocked", "content": "<text after rails>", "rail": "<name>"}
A user message triggers the input rails, an assistant-only message the output rails.
Presidio masking replaces entities with <ENTITY_TYPE> placeholders; they are rewritten
as [ENTITY_TYPE]: the LLM answers nothing when its input contains "<IBAN_CODE>"-like
tags, and markdown renderers drop them as unknown HTML.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from .config import AgentSettings

logger = logging.getLogger(__name__)

PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9_]*)>")

BLOCKED_MESSAGES = {
    "fr": "Désolé, cette requête a été bloquée par notre système de sécurité (NeMo Guardrails). "
          "Veuillez reformuler votre demande.",
    "en": "Sorry, this request was blocked by our safety system (NeMo Guardrails). "
          "Please rephrase your request.",
}
BLOCKED_MESSAGE = BLOCKED_MESSAGES["fr"]


def blocked_message(language: str | None) -> str:
    return BLOCKED_MESSAGES.get(language or "fr", BLOCKED_MESSAGE)


@dataclass
class GuardrailResult:
    allowed: bool
    text: str
    status: str = "passed"  # passed | modified | blocked | skipped | error
    rail: Optional[str] = None
    error: Optional[str] = None

    @property
    def masked(self) -> bool:
        return self.status == "modified"

    def to_dict(self) -> Dict[str, Any]:
        return {"allowed": self.allowed, "status": self.status, "rail": self.rail, "error": self.error}


class Guardrails:
    def __init__(self, settings: AgentSettings):
        self.endpoint = settings.guardrails_endpoint.rstrip("/")
        self.config_id = settings.guardrails_config_id
        self.model = settings.guardrails_model
        self.timeout = settings.guardrails_timeout
        self.fail_open = settings.guardrails_fail_open

    @property
    def enabled(self) -> bool:
        return bool(self.endpoint)

    async def check_input(self, text: str) -> GuardrailResult:
        return await self._check("user", text)

    async def check_output(self, text: str) -> GuardrailResult:
        return await self._check("assistant", text)

    async def _check(self, role: str, text: str) -> GuardrailResult:
        if not self.enabled or not text:
            return GuardrailResult(True, text, status="skipped")

        payload = {
            "model": self.model,
            "messages": [{"role": role, "content": text}],
            "guardrails": {"config_id": self.config_id},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.endpoint}/v1/checks", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            kind = "input" if role == "user" else "output"
            logger.warning("NeMo %s rails call failed (%s): %s", kind,
                           "fail-open" if self.fail_open else "fail-closed", e)
            return GuardrailResult(self.fail_open, text, status="error", error=str(e))

        status = data.get("status", "passed")
        rail = data.get("rail")
        if status == "blocked":
            logger.info("NeMo blocked %s message (rail=%s)", role, rail)
            return GuardrailResult(False, text, status=status, rail=rail)
        content = data.get("content")
        if status == "modified" and content:
            logger.info("NeMo masked sensitive data in %s message", role)
            return GuardrailResult(True, PLACEHOLDER.sub(r"[\1]", content), status=status, rail=rail)
        return GuardrailResult(True, text, status="passed", rail=rail)
