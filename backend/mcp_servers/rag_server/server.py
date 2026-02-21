"""
MCP RAG Server - Vector retrieval using PostgreSQL + pgvector.
FastMCP implementation with Streamable HTTP transport (SSE).

ARCHITECTURE NOTE:
These MCP tools perform domain-specific vector search with SQL JOINs on business
tables (company_references, historical_tenders, claim_documents, etc.) that have
rich schemas (montant, region, resultat, note_technique...).

LlamaStack's native Vector IO manages its own generic vector stores, which cannot
replicate these domain-specific JOINs and filters. The embedding generation itself
uses LlamaStack's /v1/embeddings API — only the storage and retrieval stay in MCP
because they require business-table JOINs that Vector IO's query API doesn't support.

LlamaStack's builtin::rag/knowledge_search is used for the generic knowledge base.
"""

import json
import logging
import os
from typing import List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from sqlalchemy import text
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from shared.db import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB,
    check_database_connection, run_db_query, run_db_query_one, run_db_execute,
)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP(
    "rag-server",
    stateless_http=True,
    json_response=True
)

# LlamaStack endpoint for embeddings
LLAMASTACK_ENDPOINT = os.getenv(
    "LLAMASTACK_ENDPOINT",
    "http://llamastack-test-v035.multi-agents.svc.cluster.local:8321"
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemma-300m")


# =============================================================================
# Embedding Utilities (LlamaStack /v1/embeddings)
# =============================================================================

def format_embedding(embedding: List[float]) -> str:
    """Format embedding list for pgvector, with validation."""
    if not embedding or not isinstance(embedding, list):
        raise ValueError("Embedding must be a non-empty list")
    if not all(isinstance(x, (int, float)) for x in embedding):
        raise ValueError("All embedding values must be numeric")
    return '[' + ','.join(map(str, embedding)) + ']'


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
    before_sleep=lambda retry_state: logger.warning(
        f"Embedding API retry {retry_state.attempt_number}/3 after error"
    )
)
async def create_embedding(text_input: str) -> List[float]:
    """Create embedding via LlamaStack Embeddings API with retry logic."""
    if not text_input or not text_input.strip():
        raise ValueError("Cannot create embedding for empty text")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{LLAMASTACK_ENDPOINT}/v1/embeddings",
            json={"model": EMBEDDING_MODEL, "input": text_input.strip()}
        )
        response.raise_for_status()
        result = response.json()

        if "data" not in result or len(result["data"]) == 0:
            raise ValueError("Invalid embedding response format")

        embedding = result["data"][0].get("embedding")
        if not embedding:
            raise ValueError("No embedding in response")

        logger.debug(f"Created embedding with dimension: {len(embedding)}")
        return embedding


# =============================================================================
# MCP Tools - Claims Domain
# =============================================================================

@mcp.tool()
async def retrieve_user_info(
    user_id: str,
    query: str = "",
    top_k: int = 5
) -> str:
    """
    Retrieve user information and insurance contracts using vector search.

    Args:
        user_id: User identifier
        query: Search query for contracts (optional, used for similarity ranking)
        top_k: Number of contracts to retrieve (default: 5)

    Returns:
        JSON string with user info and contracts
    """
    import time
    start_time = time.time()

    logger.info(f"Retrieving user info for: {user_id}")

    if not user_id or not user_id.strip():
        return json.dumps({"success": False, "error": "user_id is required"})

    user_id = user_id.strip()
    top_k = min(max(1, top_k), 50)

    try:
        user_query = text("""
            SELECT id, user_id, email, full_name, date_of_birth, phone_number, address
            FROM users WHERE user_id = :user_id
        """)
        user_result = await run_db_query_one(user_query, {"user_id": user_id})

        if not user_result:
            return json.dumps({"success": False, "error": f"User not found: {user_id}"})

        user_info = dict(user_result._mapping)
        for key, value in user_info.items():
            if hasattr(value, 'isoformat'):
                user_info[key] = value.isoformat()

        # Create embedding for query if provided
        query_embedding = None
        if query and query.strip():
            try:
                query_embedding = await create_embedding(query.strip())
            except Exception as e:
                logger.warning(f"Failed to create query embedding, falling back to simple fetch: {e}")

        if query_embedding:
            embedding_str = format_embedding(query_embedding)
            contract_query = text("""
                SELECT id, contract_number, contract_type, coverage_amount,
                    full_text, key_terms, is_active,
                    COALESCE(1 - (embedding <=> CAST(:query_embedding AS vector)), 0.0) AS similarity
                FROM user_contracts
                WHERE user_id = :user_id AND is_active = true AND embedding IS NOT NULL
                ORDER BY COALESCE(embedding <=> CAST(:query_embedding AS vector), 999999)
                LIMIT :top_k
            """)
            contract_results = await run_db_query(
                contract_query, {"user_id": user_id, "query_embedding": embedding_str, "top_k": top_k}
            )
        else:
            contract_query = text("""
                SELECT id, contract_number, contract_type, coverage_amount,
                    full_text, key_terms, is_active, 0.0 AS similarity
                FROM user_contracts
                WHERE user_id = :user_id AND is_active = true
                LIMIT :top_k
            """)
            contract_results = await run_db_query(contract_query, {"user_id": user_id, "top_k": top_k})

        contracts = []
        for row in contract_results:
            contract = dict(row._mapping)
            if contract.get('coverage_amount') is not None:
                contract['coverage_amount'] = float(contract['coverage_amount'])
            if contract.get('similarity') is not None:
                contract['similarity'] = float(contract['similarity'])
            contracts.append(contract)

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True,
            "user_info": user_info,
            "contracts": contracts,
            "total_contracts": len(contracts),
            "processing_time_seconds": round(processing_time, 2)
        }, default=str)

    except Exception as e:
        logger.error(f"Error retrieving user info: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e), "processing_time_seconds": round(time.time() - start_time, 2)})


@mcp.tool()
async def retrieve_similar_claims(
    claim_text: str,
    claim_type: Optional[str] = None,
    top_k: int = 10,
    min_similarity: float = 0.7
) -> str:
    """
    Find similar historical claims using vector similarity search.
    Requires SQL JOINs on claim_documents + claims tables with business filters.

    Args:
        claim_text: Text of the current claim
        claim_type: Optional filter by claim type
        top_k: Number of similar claims to retrieve (default: 10)
        min_similarity: Minimum similarity score 0.0-1.0 (default: 0.7)

    Returns:
        JSON string with similar claims
    """
    import time
    start_time = time.time()

    if not claim_text or not claim_text.strip():
        return json.dumps({"success": False, "error": "claim_text is required"})

    claim_text = claim_text.strip()
    top_k = min(max(1, top_k), 100)
    min_similarity = min(max(0.0, min_similarity), 1.0)

    try:
        claim_embedding = await create_embedding(claim_text)
        embedding_str = format_embedding(claim_embedding)

        query = text("""
            SELECT
                CAST(c.id AS text) as claim_id, c.claim_number,
                cd.raw_ocr_text as claim_text,
                1 - (cd.embedding <=> CAST(:claim_embedding AS vector)) AS similarity,
                c.status as outcome, c.total_processing_time_ms
            FROM claim_documents cd
            JOIN claims c ON cd.claim_id = c.id
            WHERE 1 - (cd.embedding <=> CAST(:claim_embedding AS vector)) >= :min_similarity
                AND (:claim_type IS NULL OR c.claim_type = :claim_type)
                AND c.status IN ('completed', 'manual_review')
                AND cd.embedding IS NOT NULL
            ORDER BY cd.embedding <=> CAST(:claim_embedding AS vector)
            LIMIT :top_k
        """)

        results = await run_db_query(query, {
            "claim_embedding": embedding_str, "min_similarity": min_similarity,
            "claim_type": claim_type, "top_k": top_k
        })

        similar_claims = []
        for row in results:
            claim_text_truncated = (row.claim_text[:500] + "...") if row.claim_text and len(row.claim_text) > 500 else (row.claim_text or "")
            similar_claims.append({
                "claim_id": row.claim_id, "claim_number": row.claim_number,
                "claim_text": claim_text_truncated,
                "similarity_score": float(row.similarity) if row.similarity else 0.0,
                "outcome": row.outcome, "processing_time_ms": row.total_processing_time_ms
            })

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True, "similar_claims": similar_claims,
            "total_found": len(similar_claims),
            "search_params": {"top_k": top_k, "min_similarity": min_similarity, "claim_type": claim_type},
            "processing_time_seconds": round(processing_time, 2)
        })

    except Exception as e:
        logger.error(f"Error retrieving similar claims: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e), "processing_time_seconds": round(time.time() - start_time, 2)})


@mcp.tool()
async def search_knowledge_base(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None
) -> str:
    """
    Search the knowledge base for relevant policy information.

    Args:
        query: Search query
        top_k: Number of results to retrieve (default: 5)
        category: Optional category filter

    Returns:
        JSON string with knowledge base articles
    """
    import time
    start_time = time.time()

    if not query or not query.strip():
        return json.dumps({"success": False, "error": "query is required"})

    query = query.strip()
    top_k = min(max(1, top_k), 50)

    try:
        query_embedding = await create_embedding(query)
        embedding_str = format_embedding(query_embedding)

        kb_query = text("""
            SELECT CAST(id AS text) as id, title, content, category,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM knowledge_base
            WHERE is_active = true AND embedding IS NOT NULL
                AND (:category IS NULL OR category = :category)
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        results = await run_db_query(kb_query, {
            "query_embedding": embedding_str, "top_k": top_k, "category": category
        })

        kb_results = [
            {"id": row.id, "title": row.title, "content": row.content,
             "category": row.category, "similarity_score": float(row.similarity) if row.similarity else 0.0}
            for row in results
        ]

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True, "articles": kb_results, "total_found": len(kb_results),
            "search_params": {"query": query, "top_k": top_k, "category": category},
            "processing_time_seconds": round(processing_time, 2)
        })

    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e), "processing_time_seconds": round(time.time() - start_time, 2)})


# =============================================================================
# MCP Tools - Tenders Domain
# =============================================================================

@mcp.tool()
async def retrieve_similar_references(
    project_description: str,
    project_type: Optional[str] = None,
    budget_range: Optional[str] = None,
    top_k: int = 5,
    min_similarity: float = 0.5
) -> str:
    """
    Find similar company project references using vector similarity search.
    Requires business columns: montant, region, maitre_ouvrage, nature_travaux.

    Args:
        project_description: Description of the project from the tender
        project_type: Optional filter by project type
        budget_range: Optional budget range description
        top_k: Number of similar references to retrieve (default: 5)
        min_similarity: Minimum similarity score 0.0-1.0 (default: 0.5)

    Returns:
        JSON string with similar project references
    """
    import time
    start_time = time.time()

    if not project_description or not project_description.strip():
        return json.dumps({"success": False, "error": "project_description is required"})

    project_description = project_description.strip()
    top_k = min(max(1, top_k), 100)

    try:
        query_embedding = await create_embedding(project_description)
        embedding_str = format_embedding(query_embedding)

        query = text("""
            SELECT reference_number, project_name, maitre_ouvrage, nature_travaux,
                montant, region, LEFT(description, 200) as description,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM company_references
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        results = await run_db_query(query, {"query_embedding": embedding_str, "top_k": top_k})

        references = []
        for row in results:
            ref = dict(row._mapping)
            if ref.get('similarity') is not None:
                ref['similarity'] = float(ref['similarity'])
            if ref.get('montant') is not None:
                ref['montant'] = float(ref['montant'])
            references.append(ref)

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True, "references": references, "total_found": len(references),
            "search_params": {"top_k": top_k, "min_similarity": min_similarity, "project_type": project_type},
            "processing_time_seconds": round(processing_time, 2)
        }, default=str)

    except Exception as e:
        logger.error(f"Error retrieving similar references: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e), "processing_time_seconds": round(time.time() - start_time, 2)})


@mcp.tool()
async def retrieve_historical_tenders(
    tender_description: str,
    tender_type: Optional[str] = None,
    client_type: Optional[str] = None,
    top_k: int = 5,
    min_similarity: float = 0.5
) -> str:
    """
    Find similar historical tenders (won/lost) using vector similarity search.
    Requires business columns: resultat, note_technique, note_prix, montant_estime.

    Args:
        tender_description: Description of the current tender
        tender_type: Optional filter by tender type
        client_type: Optional filter by client type
        top_k: Number of similar tenders to retrieve (default: 5)
        min_similarity: Minimum similarity score 0.0-1.0 (default: 0.5)

    Returns:
        JSON string with similar historical tenders
    """
    import time
    start_time = time.time()

    if not tender_description or not tender_description.strip():
        return json.dumps({"success": False, "error": "tender_description is required"})

    tender_description = tender_description.strip()
    top_k = min(max(1, top_k), 100)

    try:
        query_embedding = await create_embedding(tender_description)
        embedding_str = format_embedding(query_embedding)

        query = text("""
            SELECT ao_number, nature_travaux, maitre_ouvrage, montant_estime,
                resultat, LEFT(raison_resultat, 150) as raison_resultat,
                note_technique, note_prix, region,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM historical_tenders
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        results = await run_db_query(query, {"query_embedding": embedding_str, "top_k": top_k})

        tenders = []
        for row in results:
            tender = dict(row._mapping)
            for key in ('similarity', 'montant_estime', 'montant_propose', 'note_technique', 'note_prix'):
                if key in tender and tender[key] is not None:
                    tender[key] = float(tender[key])
            tenders.append(tender)

        won = sum(1 for t in tenders if t.get('resultat') == 'gagne')
        total = len(tenders)
        win_rate = (won / total * 100) if total > 0 else 0

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True, "historical_tenders": tenders, "total_found": total,
            "win_rate_percentage": round(win_rate, 1),
            "search_params": {"top_k": top_k, "min_similarity": min_similarity, "tender_type": tender_type},
            "processing_time_seconds": round(processing_time, 2)
        }, default=str)

    except Exception as e:
        logger.error(f"Error retrieving historical tenders: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e), "processing_time_seconds": round(time.time() - start_time, 2)})


@mcp.tool()
async def retrieve_capabilities(
    required_capabilities: str,
    project_type: Optional[str] = None,
    category: Optional[str] = None,
    top_k: int = 10
) -> str:
    """
    Retrieve company internal capabilities, certifications, and resources.
    Requires business columns: category, valid_until, availability.

    Args:
        required_capabilities: Description of required capabilities
        project_type: Optional project type filter
        category: Optional category filter (certification, materiel, personnel)
        top_k: Number of capabilities to retrieve (default: 10)

    Returns:
        JSON string with matching capabilities
    """
    import time
    start_time = time.time()

    if not required_capabilities or not required_capabilities.strip():
        return json.dumps({"success": False, "error": "required_capabilities is required"})

    required_capabilities = required_capabilities.strip()
    top_k = min(max(1, top_k), 50)

    try:
        query_embedding = await create_embedding(required_capabilities)
        embedding_str = format_embedding(query_embedding)

        query = text("""
            SELECT name, category, LEFT(description, 150) as description,
                valid_until, region, availability,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM company_capabilities
            WHERE is_active = true AND embedding IS NOT NULL
                AND (:category IS NULL OR category = :category)
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        results = await run_db_query(query, {
            "query_embedding": embedding_str, "category": category, "top_k": top_k
        })

        capabilities = []
        for row in results:
            cap = dict(row._mapping)
            if cap.get('similarity') is not None:
                cap['similarity'] = float(cap['similarity'])
            capabilities.append(cap)

        categories_found = list(set(cap.get('category', 'other') for cap in capabilities))

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True, "capabilities": capabilities,
            "total_found": len(capabilities), "categories_found": categories_found,
            "processing_time_seconds": round(processing_time, 2)
        }, default=str)

    except Exception as e:
        logger.error(f"Error retrieving capabilities: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e), "processing_time_seconds": round(time.time() - start_time, 2)})


# =============================================================================
# MCP Tools - Embedding Generation
# =============================================================================

@mcp.tool()
async def generate_document_embedding(
    entity_type: str,
    entity_id: str,
    text_content: str = "",
) -> str:
    """
    Generate and store an embedding for a claim or tender document.
    Uses LlamaStack /v1/embeddings API for vector creation, stores in pgvector.

    Args:
        entity_type: Type of entity - "claim" or "tender"
        entity_id: The entity number (e.g., CLM-2024-0001 or AO-2025-IDF-001)
        text_content: Optional OCR text to use if no document exists in DB yet

    Returns:
        JSON string with embedding generation result
    """
    import time
    start_time = time.time()

    logger.info(f"Generating embedding for {entity_type}: {entity_id}")

    if entity_type not in ("claim", "tender"):
        return json.dumps({"success": False, "error": "entity_type must be 'claim' or 'tender'"})

    if not entity_id or not entity_id.strip():
        return json.dumps({"success": False, "error": "entity_id is required"})

    entity_id = entity_id.strip()

    try:
        # Look up existing document
        if entity_type == "claim":
            doc_result = await run_db_query_one(
                text("""
                    SELECT cd.id, cd.raw_ocr_text, cd.embedding IS NOT NULL as has_embedding
                    FROM claim_documents cd JOIN claims c ON cd.claim_id = c.id
                    WHERE c.claim_number = :entity_id LIMIT 1
                """),
                {"entity_id": entity_id},
            )
        else:
            doc_result = await run_db_query_one(
                text("""
                    SELECT td.id, td.raw_ocr_text, td.embedding IS NOT NULL as has_embedding
                    FROM tender_documents td JOIN tenders t ON td.tender_id = t.id
                    WHERE t.tender_number = :entity_id LIMIT 1
                """),
                {"entity_id": entity_id},
            )

        ocr_text = None

        if doc_result:
            if doc_result.has_embedding:
                return json.dumps({
                    "success": True, "entity_type": entity_type, "entity_id": entity_id,
                    "status": "already_exists", "processing_time_seconds": round(time.time() - start_time, 2),
                })
            ocr_text = doc_result.raw_ocr_text
        else:
            # No document row — create one from text_content or entity fields
            ocr_text = await _create_document_entry(entity_type, entity_id, text_content)
            if not ocr_text:
                return json.dumps({"success": False, "error": f"No text available for {entity_type} {entity_id}"})

            # Re-fetch the document to get its ID
            if entity_type == "claim":
                doc_result = await run_db_query_one(
                    text("""
                        SELECT cd.id FROM claim_documents cd JOIN claims c ON cd.claim_id = c.id
                        WHERE c.claim_number = :entity_id ORDER BY cd.created_at DESC LIMIT 1
                    """),
                    {"entity_id": entity_id},
                )
            else:
                doc_result = await run_db_query_one(
                    text("""
                        SELECT td.id FROM tender_documents td JOIN tenders t ON td.tender_id = t.id
                        WHERE t.tender_number = :entity_id ORDER BY td.created_at DESC LIMIT 1
                    """),
                    {"entity_id": entity_id},
                )

            if not doc_result:
                return json.dumps({"success": False, "error": f"Failed to create document entry for {entity_type} {entity_id}"})

        if not ocr_text or not ocr_text.strip():
            return json.dumps({"success": False, "error": f"No OCR text available for {entity_type} {entity_id}"})

        # Create embedding via LlamaStack (truncate to 2000 chars for embedding model)
        embedding = await create_embedding(ocr_text[:2000])
        embedding_str = format_embedding(embedding)

        # Store in pgvector
        table = "claim_documents" if entity_type == "claim" else "tender_documents"
        await run_db_execute(
            text(f"UPDATE {table} SET embedding = CAST(:embedding AS vector) WHERE id = :doc_id"),
            {"embedding": embedding_str, "doc_id": doc_result.id},
        )

        processing_time = time.time() - start_time
        logger.info(f"Embedding generated for {entity_type} {entity_id}: dim={len(embedding)}")

        return json.dumps({
            "success": True, "entity_type": entity_type, "entity_id": entity_id,
            "status": "created", "dimension": len(embedding),
            "processing_time_seconds": round(processing_time, 2),
        })

    except Exception as e:
        logger.error(f"Error generating embedding: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e), "processing_time_seconds": round(time.time() - start_time, 2)})


async def _create_document_entry(entity_type: str, entity_id: str, text_content: str) -> Optional[str]:
    """Create a document entry from provided text or entity structured fields. Returns the text used."""
    if text_content and text_content.strip():
        logger.info(f"Creating document entry from provided text for {entity_type} {entity_id}")
        if entity_type == "claim":
            entity_row = await run_db_query_one(
                text("SELECT id, document_path FROM claims WHERE claim_number = :cn"), {"cn": entity_id}
            )
            if not entity_row:
                return None
            await run_db_execute(
                text("INSERT INTO claim_documents (claim_id, document_type, raw_ocr_text, file_path) VALUES (:eid, 'ocr', :txt, :dp)"),
                {"eid": entity_row.id, "txt": text_content.strip(), "dp": entity_row.document_path or ""},
            )
        else:
            entity_row = await run_db_query_one(
                text("SELECT id, document_path FROM tenders WHERE tender_number = :tn"), {"tn": entity_id}
            )
            if not entity_row:
                return None
            await run_db_execute(
                text("INSERT INTO tender_documents (tender_id, document_type, raw_ocr_text, file_path) VALUES (:eid, 'ocr', :txt, :dp)"),
                {"eid": entity_row.id, "txt": text_content.strip(), "dp": entity_row.document_path or ""},
            )
        return text_content.strip()

    # Fallback: build text from entity structured fields (stored in metadata jsonb)
    logger.info(f"Building text from entity fields for {entity_type} {entity_id}")
    if entity_type == "claim":
        entity_data = await run_db_query_one(
            text("SELECT id, claim_number, claim_type, document_path, metadata FROM claims WHERE claim_number = :cn"),
            {"cn": entity_id},
        )
        if not entity_data:
            return None
        meta = entity_data.metadata or {}
        fallback_text = f"Claim {entity_data.claim_number} - Type: {entity_data.claim_type or 'N/A'} - {meta.get('description', '')} - Amount: {meta.get('amount', 'N/A')}"
        await run_db_execute(
            text("INSERT INTO claim_documents (claim_id, document_type, raw_ocr_text, file_path) VALUES (:eid, 'metadata', :txt, :dp)"),
            {"eid": entity_data.id, "txt": fallback_text.strip(), "dp": entity_data.document_path or ""},
        )
    else:
        entity_data = await run_db_query_one(
            text("SELECT id, tender_number, document_path, metadata FROM tenders WHERE tender_number = :tn"),
            {"tn": entity_id},
        )
        if not entity_data:
            return None
        meta = entity_data.metadata or {}
        fallback_text = f"Tender {entity_data.tender_number} - {meta.get('titre', '')} - Client: {meta.get('maitre_ouvrage', 'N/A')} - Amount: {meta.get('montant_estime', 'N/A')} - Region: {meta.get('region', 'N/A')}"
        await run_db_execute(
            text("INSERT INTO tender_documents (tender_id, document_type, raw_ocr_text, file_path) VALUES (:eid, 'metadata', :txt, :dp)"),
            {"eid": entity_data.id, "txt": fallback_text.strip(), "dp": entity_data.document_path or ""},
        )

    return fallback_text.strip()


# =============================================================================
# Health Check
# =============================================================================

@mcp.tool()
async def rag_health_check() -> str:
    """Check RAG server health and connectivity."""
    health = {"status": "healthy", "checks": {}}

    try:
        await run_db_query_one(text("SELECT 1"), {})
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["checks"]["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    try:
        await create_embedding("health check")
        health["checks"]["embedding_service"] = "ok"
    except Exception as e:
        health["checks"]["embedding_service"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return json.dumps(health)


async def health_check(request):
    """Health check endpoint for liveness/readiness probes."""
    health_status = {"status": "healthy", "service": "rag-server", "database_ready": False, "embedding_ready": False}

    try:
        await run_db_query_one(text("SELECT 1"), {})
        health_status["database_ready"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"

    try:
        await create_embedding("test")
        health_status["embedding_ready"] = True
    except Exception as e:
        logger.warning(f"Embedding service health check failed: {e}")
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    return JSONResponse(health_status)


async def sse_options(request):
    """Handle OPTIONS requests for MCP SSE endpoint discovery."""
    return JSONResponse({
        "methods": ["GET", "POST", "OPTIONS"],
        "mcp_version": "0.1.0",
        "server_name": "rag-server",
        "capabilities": {"tools": True, "streaming": True}
    })


# =============================================================================
# Starlette App
# =============================================================================

mcp_sse_app = mcp.sse_app()

app = Starlette(
    routes=[
        Route("/health", health_check),
        Route("/sse", sse_options, methods=["OPTIONS"]),
        Route("/", sse_options, methods=["OPTIONS"]),
        Mount("/", app=mcp_sse_app),
    ]
)


if __name__ == "__main__":
    import uvicorn

    try:
        check_database_connection(check_pgvector=True)
    except Exception as e:
        logger.critical(f"Failed to connect to database: {e}")
        exit(1)

    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting MCP RAG Server on {host}:{port}")
    logger.info(f"Embedding model: {EMBEDDING_MODEL}")
    logger.info(f"LlamaStack endpoint: {LLAMASTACK_ENDPOINT}")
    logger.info(f"Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")

    uvicorn.run(app, host=host, port=port)
