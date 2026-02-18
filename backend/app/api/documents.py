"""
Documents API endpoints.

FIXES APPLIED:
- Removed file path from error messages (security)
- Added logging
- Added file size check
"""

import logging
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models import claim as models

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{claim_id}/view")
async def view_claim_document(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    View claim document PDF.
    
    Returns the PDF document associated with a claim.
    """
    try:
        # Get claim
        result = await db.execute(
            select(models.Claim).where(models.Claim.id == claim_id)
        )
        claim = result.scalar_one_or_none()

        if not claim:
            logger.warning(f"Claim not found: {claim_id}")
            raise HTTPException(status_code=404, detail="Claim not found")

        # Check if document path exists
        if not claim.document_path:
            logger.warning(f"No document path for claim: {claim_id}")
            raise HTTPException(status_code=404, detail="No document associated with this claim")

        # Check if file exists (don't expose path in error message)
        if not os.path.exists(claim.document_path):
            logger.error(f"Document file not found at path for claim {claim_id}")
            raise HTTPException(status_code=404, detail="Document file not found")

        # Check file size limit
        file_size = os.path.getsize(claim.document_path)
        max_size = settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_size:
            logger.warning(f"Document too large for claim {claim_id}: {file_size} bytes")
            raise HTTPException(status_code=413, detail="Document file too large")

        logger.info(f"Serving document for claim {claim_id}")
        
        # Return PDF file
        return FileResponse(
            claim.document_path,
            media_type="application/pdf",
            filename=os.path.basename(claim.document_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing document for claim {claim_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
