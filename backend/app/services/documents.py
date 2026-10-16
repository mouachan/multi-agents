"""The PDF of a case.

data-init uploads each case document to the OGX Files API and stores its file id ("file-...") in the
case's document_path (metadata document_file_id_en for the English version). In the local stack
(podman compose) the documents folder is mounted on /documents, and a path relative to it also works.
"""
import logging
from pathlib import Path
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

LOCAL_FOLDER = Path("/documents")


async def read_document(stored: str) -> Optional[bytes]:
    """Content of a stored document (OGX file id or local path), None when it is not found."""
    if stored.startswith("file-"):
        return await _from_ogx(stored)
    for path in (LOCAL_FOLDER / stored.lstrip("/"), Path(stored)):
        if path.is_file():
            return path.read_bytes()
    logger.warning("Document %s not found", stored)
    return None


async def _from_ogx(file_id: str) -> Optional[bytes]:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{settings.ogx_endpoint}/v1/files/{file_id}/content")
    except httpx.HTTPError as e:
        logger.warning("OGX file %s not read: %s", file_id, e)
        return None
    if response.status_code != 200:
        logger.warning("OGX file %s: HTTP %s", file_id, response.status_code)
        return None
    return response.content
