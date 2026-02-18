#!/usr/bin/env python3
"""
Kubernetes Job: Generate embeddings for historical claim documents.

This job:
1. Waits for LlamaStack endpoint to be ready
2. Reads all claim_documents without embeddings
3. Generates embeddings using LlamaStack API
4. Updates database with embeddings

Run after seed.sql has been loaded into PostgreSQL.
"""

import asyncio
import logging
import os
import sys
import time
from typing import List, Optional

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgresql.claims-demo.svc.cluster.local")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DATABASE", "claims_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "claims_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
LLAMASTACK_ENDPOINT = os.getenv(
    "LLAMASTACK_ENDPOINT",
    "http://llamastack-test-v035.claims-demo.svc.cluster.local:8321"
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemma-300m")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5"))  # Process 5 documents at a time
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "30"))  # Wait up to 5 minutes for LlamaStack


# Database connection
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


async def wait_for_llamastack(max_retries: int = MAX_RETRIES) -> bool:
    """
    Wait for LlamaStack to be ready.

    Returns:
        True if ready, False if timeout
    """
    logger.info(f"Waiting for LlamaStack at {LLAMASTACK_ENDPOINT}...")

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{LLAMASTACK_ENDPOINT}/health")
                if response.status_code == 200:
                    logger.info("✅ LlamaStack is ready")
                    return True
        except Exception as e:
            logger.debug(f"Attempt {attempt}/{max_retries}: {e}")

        if attempt < max_retries:
            await asyncio.sleep(10)  # Wait 10 seconds between attempts

    logger.error(f"❌ LlamaStack not ready after {max_retries} attempts")
    return False


async def create_embedding(text: str, client: httpx.AsyncClient) -> Optional[List[float]]:
    """
    Create embedding for text using LlamaStack API.

    Args:
        text: Text to embed
        client: HTTP client

    Returns:
        Embedding vector or None if error
    """
    try:
        response = await client.post(
            f"{LLAMASTACK_ENDPOINT}/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "content": text
            },
            timeout=60.0
        )

        if response.status_code == 200:
            data = response.json()
            # Handle both formats: direct array or nested in 'embedding' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'embedding' in data:
                return data['embedding']
            else:
                logger.error(f"Unexpected response format: {data}")
                return None
        else:
            logger.error(f"Embedding API error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error creating embedding: {e}")
        return None


def format_embedding_for_postgres(embedding: List[float]) -> str:
    """
    Format embedding vector for PostgreSQL pgvector.

    Args:
        embedding: Embedding vector

    Returns:
        Formatted string like '[0.1, 0.2, ...]'
    """
    return '[' + ','.join(str(x) for x in embedding) + ']'


async def process_documents():
    """Main processing function."""

    # Wait for LlamaStack
    if not await wait_for_llamastack():
        logger.error("LlamaStack not ready. Exiting.")
        sys.exit(1)

    # Connect to database
    logger.info(f"Connecting to PostgreSQL at {POSTGRES_HOST}...")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )
    SessionLocal = sessionmaker(bind=engine)

    try:
        # Get documents without embeddings
        with SessionLocal() as session:
            query = text("""
                SELECT
                    CAST(cd.id AS text) as doc_id,
                    cd.raw_ocr_text,
                    c.claim_number
                FROM claim_documents cd
                JOIN claims c ON cd.claim_id = c.id
                WHERE cd.embedding IS NULL
                  AND cd.raw_ocr_text IS NOT NULL
                ORDER BY c.claim_number
            """)

            result = session.execute(query).fetchall()
            documents = [(row.doc_id, row.raw_ocr_text, row.claim_number) for row in result]

        if not documents:
            logger.info("✅ No documents need embeddings. Job complete.")
            return

        logger.info(f"Found {len(documents)} documents without embeddings")

        # Process in batches
        async with httpx.AsyncClient() as client:
            processed = 0
            failed = 0

            for i in range(0, len(documents), BATCH_SIZE):
                batch = documents[i:i + BATCH_SIZE]
                batch_num = (i // BATCH_SIZE) + 1
                total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE

                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)...")

                for doc_id, ocr_text, claim_number in batch:
                    # Truncate text if too long (keep first 2000 chars)
                    text_to_embed = ocr_text[:2000] if len(ocr_text) > 2000 else ocr_text

                    logger.info(f"  Generating embedding for {claim_number}...")
                    embedding = await create_embedding(text_to_embed, client)

                    if embedding:
                        # Update database
                        try:
                            with SessionLocal() as session:
                                update_query = text("""
                                    UPDATE claim_documents
                                    SET embedding = CAST(:embedding AS vector)
                                    WHERE CAST(id AS text) = :doc_id
                                """)

                                session.execute(
                                    update_query,
                                    {
                                        "embedding": format_embedding_for_postgres(embedding),
                                        "doc_id": doc_id
                                    }
                                )
                                session.commit()
                                processed += 1
                                logger.info(f"    ✅ Updated {claim_number} ({processed}/{len(documents)})")
                        except Exception as e:
                            logger.error(f"    ❌ Database update failed for {claim_number}: {e}")
                            failed += 1
                    else:
                        logger.error(f"    ❌ Embedding generation failed for {claim_number}")
                        failed += 1

                # Small delay between batches to avoid overwhelming the API
                if i + BATCH_SIZE < len(documents):
                    await asyncio.sleep(2)

        logger.info(f"\n{'='*60}")
        logger.info(f"Embedding Generation Complete")
        logger.info(f"{'='*60}")
        logger.info(f"✅ Processed: {processed}/{len(documents)}")
        logger.info(f"❌ Failed: {failed}/{len(documents)}")
        logger.info(f"{'='*60}")

        if failed > 0:
            logger.warning(f"Some documents failed. Check logs above for details.")
            sys.exit(1)
        else:
            logger.info("🎉 All embeddings generated successfully!")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    logger.info("Starting embedding generation job...")
    logger.info(f"LlamaStack: {LLAMASTACK_ENDPOINT}")
    logger.info(f"Model: {EMBEDDING_MODEL}")
    logger.info(f"Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    logger.info(f"Batch size: {BATCH_SIZE}")

    asyncio.run(process_documents())
