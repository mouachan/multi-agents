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


def _resolve_document_path(stored_path: str) -> str | None:
    """Resolve document path trying multiple base directories.

    Handles path variations between local Docker and OpenShift deployments:
    - /claim_documents/file.pdf  (seed data 001)
    - /mnt/documents/claims/file.pdf  (harmonized seed data 004)
    - /mnt/documents/tenders/file.pdf  (harmonized seed data 004)
    - claim_documents/file.pdf  (relative)
    """
    candidates = [
        stored_path,
        # Docker: ./documents:/documents
        os.path.join("/documents", stored_path.lstrip("/")),
    ]
    # /mnt/documents/... -> /documents/... (Docker) and /claim_documents/... (OpenShift)
    if stored_path.startswith("/mnt/documents/"):
        candidates.append(stored_path.replace("/mnt/documents/", "/documents/", 1))
        candidates.append(stored_path.replace("/mnt/documents/", "/claim_documents/", 1))
    # /claim_documents/... -> /documents/claim_documents/... (Docker path)
    if stored_path.startswith("/claim_documents/"):
        candidates.append("/documents" + stored_path)
    # Try just the filename under common subdirectories (Docker + OpenShift)
    basename = os.path.basename(stored_path)
    for base in ["/documents", "/claim_documents"]:
        for subdir in ["", "claim_documents", "claim_documents/ao", "claims", "tenders", "ao"]:
            candidates.append(os.path.join(base, subdir, basename) if subdir else os.path.join(base, basename))

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


@router.get("/{claim_id}/view")
async def view_claim_document(
    claim_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    View claim document PDF. Accepts UUID or claim_number (e.g. CLM-2024-0019).

    Returns the PDF document associated with a claim.
    """
    try:
        # Try UUID first, fallback to claim_number
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
            logger.warning(f"Claim not found: {claim_id}")
            raise HTTPException(status_code=404, detail="Claim not found")

        # Check if document path exists
        if not claim.document_path:
            logger.warning(f"No document path for claim: {claim_id}")
            raise HTTPException(status_code=404, detail="No document associated with this claim")

        # Resolve document path - try multiple locations
        doc_path = _resolve_document_path(claim.document_path)
        if not doc_path:
            logger.error(f"Document file not found for claim {claim_id}: {claim.document_path}")
            raise HTTPException(status_code=404, detail="Document file not found")

        # Check file size limit
        file_size = os.path.getsize(doc_path)
        max_size = settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_size:
            logger.warning(f"Document too large for claim {claim_id}: {file_size} bytes")
            raise HTTPException(status_code=413, detail="Document file too large")

        logger.info(f"Serving document for claim {claim_id}")

        # Return PDF file
        return FileResponse(
            doc_path,
            media_type="application/pdf",
            filename=os.path.basename(doc_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing document for claim {claim_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
