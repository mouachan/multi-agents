"""
Document storage service — LlamaStack Files API with local filesystem fallback.

Primary: LlamaStack Files API (file ID = claim/tender number).
Fallback: local filesystem (document_path like "claims/file.pdf").
"""

import logging
import os
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_from_llamastack(file_id: str) -> Optional[tuple[bytes, str]]:
    """Fetch document content from LlamaStack Files API."""
    url = f"{settings.llamastack_endpoint}/v1/files/{file_id}/content"
    try:
        resp = httpx.get(url, timeout=30)
        if resp.status_code == 200:
            cd = resp.headers.get("content-disposition", "")
            if "filename=" in cd:
                filename = cd.split("filename=")[-1].strip('" ')
            else:
                filename = f"{file_id}.pdf"
            logger.info(f"Document served from LlamaStack: {file_id} ({len(resp.content)} bytes)")
            return resp.content, filename
        else:
            logger.debug(f"LlamaStack file not found: {file_id} (HTTP {resp.status_code})")
            return None
    except Exception as e:
        logger.debug(f"LlamaStack fetch error for {file_id}: {e}")
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


def get_document(file_id: str, fallback_path: Optional[str] = None) -> Optional[tuple[bytes, str]]:
    """Fetch a document by its file ID (claim/tender number).

    Resolution order:
    1. LlamaStack Files API using fallback_path (the actual file-xxx ID stored in DB)
    2. LlamaStack Files API using file_id (claim/tender number)
    3. Local filesystem fallback

    Returns (file_bytes, filename) or None if not found.
    """
    # Try LlamaStack with the actual file ID (document_path = file-xxx)
    if fallback_path and fallback_path != file_id:
        result = _get_from_llamastack(fallback_path)
        if result:
            # Override filename with the claim/tender number
            return result[0], f"{file_id}.pdf"

    # Try LlamaStack with claim/tender number
    result = _get_from_llamastack(file_id)
    if result:
        return result

    # Fallback: local filesystem
    path = fallback_path or file_id
    filename = os.path.basename(path)
    local_path = _resolve_local_path(path)
    if local_path:
        with open(local_path, "rb") as f:
            data = f.read()
        logger.info(f"Document served from filesystem: {local_path} ({len(data)} bytes)")
        return data, filename

    return None
