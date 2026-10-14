"""
Shared OGX (formerly LlamaStack) settings and helpers for MCP servers.

OGX keeps the LlamaStack HTTP API (/v1/embeddings, /v1/chat/completions,
/v1/files, /v1/health). Model IDs are the plain MaaS model names.
"""

import logging
import os
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

OGX_ENDPOINT = os.getenv("OGX_ENDPOINT", "http://ogx:8321").rstrip("/")
OGX_DEFAULT_MODEL = os.getenv("OGX_DEFAULT_MODEL", "gpt-oss-120b")
OGX_EMBEDDING_MODEL = os.getenv("OGX_EMBEDDING_MODEL", "nomic-embed-text-v1-5")
OGX_EMBEDDING_DIMENSION = int(os.getenv("OGX_EMBEDDING_DIMENSION", "768"))
OGX_TIMEOUT = float(os.getenv("OGX_TIMEOUT", "30"))


def get_llm_model_name() -> str:
    """Short name of the reasoning model, stored alongside saved decisions."""
    return OGX_DEFAULT_MODEL.split("/")[-1]


async def generate_embedding(text_input: str, max_chars: int = 2000) -> Optional[List[float]]:
    """Generate an embedding via OGX /v1/embeddings. Returns None on failure (non-blocking)."""
    if not text_input or not text_input.strip():
        return None
    try:
        async with httpx.AsyncClient(timeout=OGX_TIMEOUT) as client:
            resp = await client.post(
                f"{OGX_ENDPOINT}/v1/embeddings",
                json={"model": OGX_EMBEDDING_MODEL, "input": text_input.strip()[:max_chars]},
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if data:
                embedding = data[0].get("embedding")
                if embedding and len(embedding) != OGX_EMBEDDING_DIMENSION:
                    logger.warning(
                        "Embedding dimension %d != expected %d (model %s)",
                        len(embedding), OGX_EMBEDDING_DIMENSION, OGX_EMBEDDING_MODEL,
                    )
                return embedding
    except Exception as e:
        logger.warning(f"Embedding generation failed (non-blocking): {e}")
    return None
