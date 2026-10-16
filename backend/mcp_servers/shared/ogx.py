"""OGX (formerly LlamaStack): the embedding model of the similarity searches.

The texts of the documents and of the reference data are embedded with the same model and the
same length limit by data-init and by the backend, so the vectors are comparable.
"""
import asyncio
import logging
import os
from typing import List

import httpx

logger = logging.getLogger(__name__)

OGX_ENDPOINT = os.getenv("OGX_ENDPOINT", "http://ogx:8321").rstrip("/")
EMBEDDING_MODEL = os.getenv("OGX_EMBEDDING_MODEL", "nomic-embed-text-v1-5")
TIMEOUT = float(os.getenv("OGX_TIMEOUT", "30"))
EMBEDDED_CHARS = 2000      # the text embedded is cut to this length
ATTEMPTS = 3


async def embed(text: str) -> List[float]:
    """The embedding of a text (retried: the MaaS sometimes drops a request)."""
    if not text or not text.strip():
        raise ValueError("Nothing to embed")
    for attempt in range(1, ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(f"{OGX_ENDPOINT}/v1/embeddings",
                                             json={"model": EMBEDDING_MODEL, "input": text.strip()[:EMBEDDED_CHARS]})
                response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except (httpx.HTTPError, KeyError, IndexError) as e:
            if attempt == ATTEMPTS:
                raise
            logger.warning("Embedding failed (%d/%d): %s", attempt, ATTEMPTS, e)
            await asyncio.sleep(attempt)


def as_vector(embedding: List[float]) -> str:
    """The embedding as pgvector reads it: CAST(:vector AS vector)."""
    return "[" + ",".join(map(str, embedding)) + "]"
