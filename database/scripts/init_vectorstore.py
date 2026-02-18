#!/usr/bin/env python3
"""
LlamaStack Vector Store Initialization Script.

Prerequisites:
- PostgreSQL database must be initialized (init.sql executed)
- Seed data must be loaded (001_sample_data.sql executed)
- LlamaStack must be running and accessible

This script:
1. Creates LlamaStack vector_store via API
2. Generates embeddings for knowledge_base articles (if missing)
3. Inserts all embeddings into LlamaStack via /v1/vector-io/insert

Run after: init.sql and 001_sample_data.sql have been executed
"""

import asyncio
import asyncpg
import httpx
import os
import sys
from typing import List, Dict, Any

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgresql.claims-demo.svc.cluster.local")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "claims_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "claims_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "claims_pass")

LLAMASTACK_ENDPOINT = os.getenv("LLAMASTACK_ENDPOINT", "http://claims-llamastack-service.claims-demo.svc.cluster.local:8321")
VECTOR_STORE_NAME = "claims_vector_db"
EMBEDDING_MODEL = "gemma-300m"
EMBEDDING_DIMENSION = 768


async def create_embedding(text: str, http_client: httpx.AsyncClient) -> List[float]:
    """Generate embedding using LlamaStack with gemma-300m model."""
    response = await http_client.post(
        f"{LLAMASTACK_ENDPOINT}/v1/embeddings",
        json={
            "model": EMBEDDING_MODEL,
            "input": text
        }
    )

    if response.status_code == 200:
        result = response.json()
        # OpenAI-compatible format: {"data": [{"embedding": [...]}]}
        if "data" in result and len(result["data"]) > 0:
            return result["data"][0]["embedding"]
        elif "embedding" in result:
            return result["embedding"]
        elif "embeddings" in result and len(result["embeddings"]) > 0:
            return result["embeddings"][0]
        else:
            raise ValueError(f"Unexpected embedding response: {result}")
    else:
        raise Exception(f"Embedding API error: {response.status_code} - {response.text}")


async def create_vector_store(http_client: httpx.AsyncClient) -> str:
    """Create vector_store in LlamaStack and return its ID."""
    print(f"🔍 Checking if vector_store '{VECTOR_STORE_NAME}' exists...")

    # Check if vector_store already exists
    response = await http_client.get(
        f"{LLAMASTACK_ENDPOINT}/v1/vector_stores",
        params={"name": VECTOR_STORE_NAME}
    )

    if response.status_code == 200:
        data = response.json()
        if data.get("data") and len(data["data"]) > 0:
            vector_store_id = data["data"][0]["id"]
            print(f"✓ Vector_store already exists: {vector_store_id}")
            return vector_store_id

    # Create new vector_store
    print(f"📦 Creating vector_store '{VECTOR_STORE_NAME}'...")
    response = await http_client.post(
        f"{LLAMASTACK_ENDPOINT}/v1/vector_stores",
        json={
            "name": VECTOR_STORE_NAME,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "provider_id": "pgvector"
        }
    )

    if response.status_code == 200:
        result = response.json()
        vector_store_id = result["id"]
        print(f"✓ Created vector_store: {vector_store_id}")
        return vector_store_id
    else:
        raise Exception(f"Failed to create vector_store: {response.status_code} - {response.text}")


async def insert_chunks_to_vectorstore(
    vector_store_id: str,
    chunks: List[Dict[str, Any]],
    http_client: httpx.AsyncClient
):
    """Insert chunks into LlamaStack vector_store."""
    if not chunks:
        return

    print(f"📤 Inserting {len(chunks)} chunks into vector_store...")

    response = await http_client.post(
        f"{LLAMASTACK_ENDPOINT}/v1/vector-io/insert",
        json={
            "vector_db_id": vector_store_id,
            "chunks": chunks
        }
    )

    if response.status_code != 200:
        print(f"⚠️  Warning: Failed to insert chunks: {response.status_code} - {response.text}")
    else:
        print(f"✓ Inserted {len(chunks)} chunks")


async def main():
    """Main initialization function."""
    print("\n" + "=" * 80)
    print("LLAMASTACK VECTOR STORE INITIALIZATION")
    print("=" * 80)
    print(f"PostgreSQL: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print(f"LlamaStack: {LLAMASTACK_ENDPOINT}")
    print("=" * 80)

    try:
        # Connect to PostgreSQL
        print("\n📊 Connecting to PostgreSQL...")
        conn = await asyncpg.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        print("✓ Connected to PostgreSQL")

        async with httpx.AsyncClient(timeout=60.0) as http_client:
            # Create vector_store
            vector_store_id = await create_vector_store(http_client)

            # ===== USER CONTRACTS =====
            print("\n📋 Processing user_contracts...")
            contracts = await conn.fetch("""
                SELECT id, user_id, contract_number, contract_type, coverage_amount,
                       is_active, start_date, end_date, full_text, embedding
                FROM user_contracts
            """)

            print(f"Found {len(contracts)} contracts")

            contract_chunks = []
            for contract in contracts:
                # Regenerate embeddings for all contracts (compatibility with gemma-300m)
                print(f"  Generating embedding for contract: {contract['contract_number']}...")
                embedding = await create_embedding(contract["full_text"], http_client)

                # Convert embedding list to PostgreSQL vector format string
                embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'

                # Update database
                await conn.execute("""
                    UPDATE user_contracts
                    SET embedding = $1::vector, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """, embedding_str, contract["id"])

                chunk = {
                    "content": contract["full_text"],
                    "token_count": len(contract["full_text"].split()),
                    "embedding": embedding,  # Include embedding for LlamaStack
                    "metadata": {
                        "collection": "user_contracts",
                        "id": str(contract["id"]),
                        "user_id": contract["user_id"],
                        "contract_number": contract["contract_number"],
                        "contract_type": contract["contract_type"],
                        "coverage_amount": float(contract["coverage_amount"]) if contract["coverage_amount"] else None,
                        "is_active": contract["is_active"]
                    }
                }
                contract_chunks.append(chunk)

            # Don't insert yet - collect all chunks first

            # ===== KNOWLEDGE BASE =====
            print("\n📚 Processing knowledge_base...")
            kb_articles = await conn.fetch("""
                SELECT id, title, content, category, tags, is_active, embedding
                FROM knowledge_base
                WHERE is_active = true
            """)

            print(f"Found {len(kb_articles)} knowledge base articles")

            kb_chunks = []
            for article in kb_articles:
                # Always regenerate embeddings for compatibility with gemma-300m
                print(f"  Generating embedding for: {article['title'][:50]}...")
                text_for_embedding = f"{article['title']}\n\n{article['content']}"
                embedding = await create_embedding(text_for_embedding, http_client)

                # Convert embedding list to PostgreSQL vector format string
                embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'

                # Update database
                await conn.execute("""
                    UPDATE knowledge_base
                    SET embedding = $1::vector, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """, embedding_str, article["id"])

                chunk = {
                    "content": article["content"],
                    "token_count": len(article["content"].split()),
                    "embedding": embedding,  # Include embedding for LlamaStack
                    "metadata": {
                        "collection": "knowledge_base",
                        "id": str(article["id"]),
                        "title": article["title"],
                        "category": article["category"],
                        "tags": article["tags"],
                        "is_active": article["is_active"]
                    }
                }
                kb_chunks.append(chunk)

            # Don't insert yet - collect all chunks first

            # ===== CLAIM DOCUMENTS (if any exist) =====
            print("\n📄 Processing claim_documents...")
            claim_docs = await conn.fetch("""
                SELECT cd.id, cd.claim_id, cd.raw_ocr_text, cd.embedding,
                       c.claim_number, c.claim_type, c.status
                FROM claim_documents cd
                JOIN claims c ON cd.claim_id = c.id
                WHERE cd.embedding IS NOT NULL
            """)

            print(f"Found {len(claim_docs)} claim documents with embeddings")

            claim_chunks = []
            for doc in claim_docs:
                chunk = {
                    "content": doc["raw_ocr_text"],
                    "token_count": len(doc["raw_ocr_text"].split()),
                    "metadata": {
                        "collection": "claim_documents",
                        "id": str(doc["id"]),
                        "claim_id": str(doc["claim_id"]),
                        "claim_number": doc["claim_number"],
                        "claim_type": doc["claim_type"],
                        "status": doc["status"]
                    }
                }
                claim_chunks.append(chunk)

            # ===== INSERT ALL CHUNKS AT ONCE =====
            print("\n📦 Combining all chunks for insertion...")
            all_chunks = contract_chunks + kb_chunks + claim_chunks
            print(f"Total chunks to insert: {len(all_chunks)}")

            if all_chunks:
                print(f"📤 Inserting {len(all_chunks)} chunks into vector_store...")
                await insert_chunks_to_vectorstore(vector_store_id, all_chunks, http_client)
            else:
                print("⚠️  No chunks to insert!")

        await conn.close()

        print("\n" + "=" * 80)
        print("✅ VECTOR STORE INITIALIZATION COMPLETED")
        print("=" * 80)
        print(f"   Vector Store ID: {vector_store_id}")
        print(f"   User Contracts: {len(contract_chunks)}")
        print(f"   Knowledge Base: {len(kb_chunks)}")
        print(f"   Claim Documents: {len(claim_chunks)}")
        print(f"   Total chunks: {len(all_chunks)}")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ INITIALIZATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
