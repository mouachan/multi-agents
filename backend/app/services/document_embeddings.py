"""Embeddings of processed documents, used by the RAG precedent searches.

The save_*_decision MCP tools used to embed the document's OCR text when the agent
called them; the guided processing now saves the decision in the backend, so the
backend embeds the document after the decision (same text, truncation and model as
the MCP servers, see backend/mcp_servers/shared/ogx.py). Failures are logged only.
"""
import logging

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

DOCUMENT_TABLES = {
    "claim": ("claim_documents", "claim_id"),
    "tender": ("tender_documents", "tender_id"),
    "reclamation": ("reclamation_documents", "reclamation_id"),
}
MAX_CHARS = 2000  # MCP servers embed the first 2000 characters


async def embed_document(db: AsyncSession, kind: str, entity_id: str) -> bool:
    """Embed the latest OCR document of the entity if it has none yet; True when created."""
    table, fk = DOCUMENT_TABLES[kind]
    row = (await db.execute(
        text(f"""
            SELECT id, raw_ocr_text FROM {table}
            WHERE {fk} = :eid AND raw_ocr_text IS NOT NULL AND raw_ocr_text <> '' AND embedding IS NULL
            ORDER BY created_at DESC LIMIT 1
        """),
        {"eid": str(entity_id)},
    )).first()
    if not row:
        return False
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{settings.ogx_endpoint}/v1/embeddings",
                json={"model": settings.ogx_embedding_model, "input": row.raw_ocr_text.strip()[:MAX_CHARS]},
            )
            resp.raise_for_status()
            vector = resp.json()["data"][0]["embedding"]
        await db.execute(
            text(f"UPDATE {table} SET embedding = CAST(:emb AS vector) WHERE id = :id"),
            {"emb": "[" + ",".join(map(str, vector)) + "]", "id": row.id},
        )
        await db.commit()
        logger.info("Embedded %s document of %s (dim=%d)", kind, entity_id, len(vector))
        return True
    except Exception as e:
        await db.rollback()
        logger.warning("Embedding of the %s document of %s failed: %s", kind, entity_id, e)
        return False
