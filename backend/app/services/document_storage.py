"""
Document storage service — OGX Files API with local filesystem fallback.

Primary: OGX Files API (document_path / metadata.document_file_id_en = "file-xxx").
Fallback: local filesystem (document_path like "claims/file.pdf").
"""

import logging
import os
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _get_from_ogx(file_id: str) -> Optional[tuple[bytes, str]]:
    """Fetch document content from OGX Files API."""
    url = f"{settings.ogx_endpoint}/v1/files/{file_id}/content"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
        if resp.status_code == 200:
            cd = resp.headers.get("content-disposition", "")
            if "filename=" in cd:
                filename = cd.split("filename=")[-1].strip('" ')
            else:
                filename = f"{file_id}.pdf"
            logger.info(f"Document served from OGX: {file_id} ({len(resp.content)} bytes)")
            return resp.content, filename
        logger.warning(f"OGX file not available: {file_id} (HTTP {resp.status_code})")
        return None
    except Exception as e:
        logger.warning(f"OGX fetch error for {file_id}: {e}")
        return None


def _resolve_local_path(stored_path: str) -> Optional[str]:
    """Resolve document path on local filesystem (fallback)."""
    candidates = [
        os.path.join("/documents", stored_path.lstrip("/")),
        stored_path,
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


async def get_document(file_id: str, fallback_path: Optional[str] = None) -> Optional[tuple[bytes, str]]:
    """Fetch a document for a claim/tender/reclamation number.

    Resolution order:
    1. OGX Files API, when the stored path is an OGX file ID (file-xxx, set by data-init)
    2. Local filesystem (podman compose mounts ./documents on /documents)

    Returns (file_bytes, filename) or None if not found.
    """
    path = fallback_path or file_id
    if path.startswith("file-"):
        result = await _get_from_ogx(path)
        if result:
            # Name the download after the business number
            return result[0], f"{file_id}.pdf"

    filename = os.path.basename(path)
    local_path = _resolve_local_path(path)
    if local_path:
        with open(local_path, "rb") as f:
            data = f.read()
        logger.info(f"Document served from filesystem: {local_path} ({len(data)} bytes)")
        return data, filename

    logger.warning(f"Document not found for {file_id} (stored path: {path})")
    return None
