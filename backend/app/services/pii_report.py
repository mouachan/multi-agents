"""Personal data found in a claim (the "Personal data" card of the claim page).

After a claim is processed, its document's OCR text and the claimant's record are masked by NeMo
Guardrails (app/services/guardrails.py). Each type of personal data found becomes a row of
guardrails_detections: the type (EMAIL_ADDRESS, FR_IBAN...), how many, and where it was found.
The values themselves are never stored or logged.
"""
import logging

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim, ClaimDocument, GuardrailsDetection
from app.services.guardrails import mask_personal_data, masked_entities

logger = logging.getLogger(__name__)


async def record_personal_data(db: AsyncSession, claim: Claim) -> int:
    """Replace the claim's personal data report; returns the number of types found."""
    document = (await db.execute(
        select(ClaimDocument).where(ClaimDocument.claim_id == claim.id)
        .order_by(ClaimDocument.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    sources = {"claim document (OCR)": document.raw_ocr_text if document else None}
    if claim.claimant:
        person = claim.claimant
        sources["claimant record"] = f"{person.full_name}, {person.email}, {person.phone_number}, born {person.date_of_birth}"

    found = []
    for source, text in sources.items():
        masked = await mask_personal_data(text) if text else None
        for entity_type, count in masked_entities(masked).items():
            found.append(GuardrailsDetection(
                claim_id=claim.id, detection_type="pii", severity="medium", action_taken="masked",
                record_metadata={"detection_type": entity_type, "count": count, "source_step": source},
            ))
    await db.execute(delete(GuardrailsDetection).where(GuardrailsDetection.claim_id == claim.id))
    db.add_all(found)
    await db.commit()
    logger.info("Personal data report of claim %s: %d types found", claim.claim_number, len(found))
    return len(found)
