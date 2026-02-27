"""
Documents API endpoints.

Serves claim/tender PDFs from LlamaStack Files API (file ID = claim/tender number)
with local filesystem fallback.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models import claim as models
from app.services.document_storage import get_document

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{claim_id}/view")
async def view_claim_document(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    """View claim document PDF. Accepts UUID or claim_number (e.g. CLM-2024-0019)."""
    try:
        try:
            claim_uuid = UUID(claim_id)
            result = await db.execute(
                select(models.Claim).where(models.Claim.id == claim_uuid)
            )
        except ValueError:
            result = await db.execute(
                select(models.Claim).where(models.Claim.claim_number == claim_id)
            )
        claim = result.scalar_one_or_none()

        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        if not claim.document_path:
            raise HTTPException(status_code=404, detail="No document associated with this claim")

        # Use claim_number as LlamaStack file ID, fallback to document_path for local
        doc = get_document(claim.claim_number, fallback_path=claim.document_path)
        if not doc:
            logger.error(f"Document not found for claim {claim_id}")
            raise HTTPException(status_code=404, detail="Document file not found")

        data, filename = doc

        max_size = settings.max_upload_size_mb * 1024 * 1024
        if len(data) > max_size:
            raise HTTPException(status_code=413, detail="Document file too large")

        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing document for claim {claim_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
