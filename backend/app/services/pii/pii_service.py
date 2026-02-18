"""
PII Service - Centralized PII detection and redaction.

Provides dual-level storage:
- Original data stored in regular columns
- Redacted versions stored in _redacted columns
- Detection records saved in guardrails_detections
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from .redactor import (
    redact_address,
    redact_date,
    redact_email,
    redact_name,
    redact_phone,
    redact_text_pii,
)

logger = logging.getLogger(__name__)


@dataclass
class PIIDetection:
    """A single PII detection."""
    field_name: str
    pii_type: str
    original_value: str
    redacted_value: str
    source: str = "regex"
    confidence: float = 1.0


@dataclass
class PIIResult:
    """Result of PII detection and redaction."""
    original_text: str
    redacted_text: str
    detections: List[PIIDetection] = field(default_factory=list)

    @property
    def has_pii(self) -> bool:
        return len(self.detections) > 0


# Regex patterns for PII detection
PII_PATTERNS = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE_FR": re.compile(r"(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}"),
    "DATE_ISO": re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    "DATE_FR": re.compile(r"\b\d{2}/\d{2}/\d{4}\b"),
    "SSN_FR": re.compile(r"\b[12]\s*\d{2}\s*\d{2}\s*\d{2}\s*\d{3}\s*\d{3}\s*\d{2}\b"),
    "CREDIT_CARD": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
}


class PIIService:
    """Centralized PII detection and redaction service."""

    def detect_and_redact(self, text: str, source: str = "unknown") -> PIIResult:
        """
        Detect PII in text and produce redacted version.

        Args:
            text: Text to scan for PII
            source: Source identifier (e.g., "ocr_text", "reasoning")

        Returns:
            PIIResult with original, redacted text, and detections
        """
        if not text:
            return PIIResult(original_text="", redacted_text="")

        detections = []

        # Detect PII patterns
        for pii_type, pattern in PII_PATTERNS.items():
            for match in pattern.finditer(text):
                original = match.group()
                detections.append(PIIDetection(
                    field_name=source,
                    pii_type=pii_type,
                    original_value=original,
                    redacted_value=self._redact_by_type(pii_type, original),
                    source="regex",
                    confidence=1.0,
                ))

        # Apply redaction
        redacted_text = redact_text_pii(text)

        return PIIResult(
            original_text=text,
            redacted_text=redacted_text,
            detections=detections,
        )

    def redact_user_fields(
        self,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        address: Optional[dict] = None,
    ) -> Dict[str, Optional[str]]:
        """
        Redact known user fields.

        Returns:
            Dict with redacted values for each field.
        """
        return {
            "email_redacted": redact_email(email) if email else None,
            "full_name_redacted": redact_name(full_name) if full_name else None,
            "phone_number_redacted": redact_phone(phone_number) if phone_number else None,
            "date_of_birth_redacted": redact_date(str(date_of_birth)) if date_of_birth else None,
            "address_redacted": redact_address(address) if address else None,
        }

    async def process_entity_pii(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        ocr_text: Optional[str] = None,
        reasoning: Optional[str] = None,
    ) -> List[PIIDetection]:
        """
        Process PII for an entity after agent processing.

        1. Detect and redact OCR text -> store in raw_ocr_text_redacted
        2. Detect and redact reasoning -> store in reasoning_redacted
        3. Save detections to guardrails_detections

        Returns:
            List of all detections found
        """
        if not settings.enable_pii_detection:
            return []

        all_detections = []

        # Process OCR text
        if ocr_text:
            ocr_result = self.detect_and_redact(ocr_text, source="ocr_text")
            all_detections.extend(ocr_result.detections)

        # Process reasoning
        if reasoning:
            reasoning_result = self.detect_and_redact(reasoning, source="reasoning")
            all_detections.extend(reasoning_result.detections)

        # Save detections to DB
        if all_detections:
            await self._save_detections(db, entity_type, entity_id, all_detections)

        return all_detections

    async def _save_detections(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        detections: List[PIIDetection],
    ) -> None:
        """Save PII detections to guardrails_detections table."""
        from uuid import UUID
        from datetime import datetime, timezone
        from app.models.claim import GuardrailsDetection

        for detection in detections:
            entry = GuardrailsDetection(
                claim_id=UUID(entity_id) if entity_type == "claim" else None,
                detection_type=detection.pii_type,
                severity="medium",
                action_taken="redacted",
                detected_at=datetime.now(timezone.utc),
                record_metadata={
                    "field_name": detection.field_name,
                    "pii_type": detection.pii_type,
                    "source": detection.source,
                    "confidence": detection.confidence,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                },
            )
            db.add(entry)

        await db.commit()
        logger.info(f"Saved {len(detections)} PII detections for {entity_type} {entity_id}")

    def _redact_by_type(self, pii_type: str, value: str) -> str:
        """Apply type-specific redaction."""
        if pii_type == "EMAIL":
            return redact_email(value)
        elif pii_type.startswith("PHONE"):
            return redact_phone(value)
        elif pii_type.startswith("DATE"):
            return redact_date(value)
        elif pii_type.startswith("SSN"):
            return re.sub(r"\d", "*", value)
        elif pii_type == "CREDIT_CARD":
            return re.sub(r"\d", "*", value)
        return "***REDACTED***"
