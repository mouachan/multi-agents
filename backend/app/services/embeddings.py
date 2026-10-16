"""Embedding of a processed case's document, so that later cases find it as a precedent.

The RAG MCP server (retrieve_similar_claims / _reclamations, retrieve_historical_tenders) compares a new
case's text with these embeddings. Same text, truncation and model as the MCP servers
(backend/mcp_servers/shared/ogx.py). A failure is logged only: the decision is already saved.
"""
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domains import DomainSpec

logger = logging.getLogger(__name__)

MAX_CHARS = 2000  # the MCP servers embed the first 2000 characters


async def embed_case_document(db: AsyncSession, spec: DomainSpec, case_id) -> bool:
    """Embed the latest OCR text of the case if it has no embedding yet; True when one was created."""
    table = spec.document_model
    document = (await db.execute(
        select(table)
        .where(getattr(table, spec.fk) == case_id, table.raw_ocr_text.isnot(None),
               table.raw_ocr_text != "", table.embedding.is_(None))
        .order_by(table.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if document is None:
        return False
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.ogx_endpoint}/v1/embeddings",
                json={"model": settings.ogx_embedding_model, "input": document.raw_ocr_text.strip()[:MAX_CHARS]},
            )
            resp.raise_for_status()
            document.embedding = resp.json()["data"][0]["embedding"]
        await db.commit()
        logger.info("Embedded the %s document of %s", spec.entity, case_id)
        return True
    except Exception as e:
        await db.rollback()
        logger.warning("Embedding of the %s document of %s failed: %s", spec.entity, case_id, e)
        return False
