"""
MCP RAG Server - Vector retrieval using PostgreSQL + pgvector
FastMCP implementation with Streamable HTTP transport (SSE)

SIMPLE TOOLS: Return retrieved documents only.
The LlamaStack agent handles all LLM synthesis and analysis.

FIXES APPLIED:
- Async database queries using asyncio.to_thread()
- HTTP retry logic with tenacity
- Embedding validation to prevent injection
- Database connection check at startup
- Proper error handling throughout
- SSE transport compatible with LlamaStack
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP server with Streamable HTTP configuration (recommended)
# stateless_http=True: server doesn't maintain session state
# json_response=True: tools return JSON strings (optimal for scalability)
mcp = FastMCP(
    "rag-server",
    stateless_http=True,
    json_response=True
)

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgresql.claims-demo.svc.cluster.local")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DATABASE", "claims_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "claims_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ClaimsDemo2025!")
LLAMASTACK_ENDPOINT = os.getenv(
    "LLAMASTACK_ENDPOINT",
    "http://llamastack-test-v035.claims-demo.svc.cluster.local:8321"
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemma-300m")

# Database connection
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600    # Recycle connections after 1 hour
)
SessionLocal = sessionmaker(bind=engine)


# =============================================================================
# Database Utilities
# =============================================================================

def check_database_connection() -> bool:
    """
    Verify database connectivity on startup.
    
    Returns:
        True if connection successful
        
    Raises:
        Exception if connection fails
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # Check if pgvector extension is available
            result = conn.execute(text(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )).scalar()
            if not result:
                logger.warning("⚠️ pgvector extension not found - vector search may fail")
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise


async def run_db_query(query, params: dict) -> List[Any]:
    """
    Execute database query in thread pool (non-blocking).
    
    Args:
        query: SQLAlchemy text query
        params: Query parameters
        
    Returns:
        List of result rows
    """
    def _execute():
        with SessionLocal() as session:
            try:
                result = session.execute(query, params).fetchall()
                return result
            except Exception as e:
                session.rollback()
                raise
    
    return await asyncio.to_thread(_execute)


async def run_db_query_one(query, params: dict) -> Optional[Any]:
    """
    Execute database query and return single result.
    
    Args:
        query: SQLAlchemy text query
        params: Query parameters
        
    Returns:
        Single result row or None
    """
    def _execute():
        with SessionLocal() as session:
            try:
                result = session.execute(query, params).fetchone()
                return result
            except Exception as e:
                session.rollback()
                raise
    
    return await asyncio.to_thread(_execute)


# =============================================================================
# Embedding Utilities
# =============================================================================

def format_embedding(embedding: List[float]) -> str:
    """
    Format embedding for pgvector, with validation.
    
    Args:
        embedding: List of float values
        
    Returns:
        Formatted string for pgvector
        
    Raises:
        ValueError if embedding is invalid
    """
    if not embedding:
        raise ValueError("Empty embedding")
    
    if not isinstance(embedding, list):
        raise ValueError(f"Embedding must be a list, got {type(embedding)}")
    
    if not all(isinstance(x, (int, float)) for x in embedding):
        raise ValueError("All embedding values must be numeric")
    
    # Validate reasonable bounds (embeddings are typically normalized)
    if any(abs(x) > 100 for x in embedding):
        logger.warning("Embedding contains unusually large values")
    
    return '[' + ','.join(map(str, embedding)) + ']'


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException)),
    before_sleep=lambda retry_state: logger.warning(
        f"Embedding API retry {retry_state.attempt_number}/3 after error"
    )
)
async def create_embedding(text: str) -> List[float]:
    """
    Create embedding using LlamaStack Embeddings API.
    
    Includes retry logic for transient failures.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding vector
        
    Raises:
        Exception if embedding creation fails after retries
    """
    if not text or not text.strip():
        raise ValueError("Cannot create embedding for empty text")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{LLAMASTACK_ENDPOINT}/v1/embeddings",
                json={
                    "model": EMBEDDING_MODEL,
                    "input": text.strip()
                }
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "data" not in result or len(result["data"]) == 0:
                logger.error(f"Unexpected embedding response format: {result}")
                raise ValueError("Invalid embedding response format")
            
            embedding = result["data"][0].get("embedding")
            
            if not embedding:
                raise ValueError("No embedding in response")
            
            logger.debug(f"Created embedding with dimension: {len(embedding)}")
            return embedding

    except httpx.HTTPStatusError as e:
        logger.error(f"Embedding API HTTP error: {e.response.status_code} - {e.response.text}")
        raise
    except httpx.ConnectError as e:
        logger.error(f"Embedding API connection error: {e}")
        raise
    except httpx.TimeoutException as e:
        logger.error(f"Embedding API timeout: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating embedding: {str(e)}")
        raise


# =============================================================================
# MCP Tools
# =============================================================================

@mcp.tool()
async def retrieve_user_info(
    user_id: str,
    query: str = "",
    top_k: int = 5
) -> str:
    """
    Retrieve user information and insurance contracts using vector search.

    This tool performs ONLY retrieval. No LLM synthesis.
    The LlamaStack agent will analyze the retrieved contracts.

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

    # Input validation
    if not user_id or not user_id.strip():
        return json.dumps({
            "success": False,
            "error": "user_id is required"
        })

    user_id = user_id.strip()
    top_k = min(max(1, top_k), 50)  # Clamp between 1 and 50

    try:
        # Get user basic info
        user_query = text("""
            SELECT id, user_id, email, full_name, date_of_birth, phone_number, address
            FROM users
            WHERE user_id = :user_id
        """)
        user_result = await run_db_query_one(user_query, {"user_id": user_id})

        if not user_result:
            logger.warning(f"User not found: {user_id}")
            return json.dumps({
                "success": False,
                "error": f"User not found: {user_id}"
            })

        user_info = dict(user_result._mapping)
        
        # Convert non-serializable types
        for key, value in user_info.items():
            if hasattr(value, 'isoformat'):  # datetime/date objects
                user_info[key] = value.isoformat()

        # Create embedding for query if provided
        query_embedding = None
        if query and query.strip():
            try:
                query_embedding = await create_embedding(query.strip())
            except Exception as e:
                logger.warning(f"Failed to create query embedding, falling back to simple fetch: {e}")

        # Get user contracts
        if query_embedding:
            embedding_str = format_embedding(query_embedding)

            contract_query = text("""
                SELECT
                    id, contract_number, contract_type, coverage_amount,
                    full_text, key_terms, is_active,
                    COALESCE(1 - (embedding <=> CAST(:query_embedding AS vector)), 0.0) AS similarity
                FROM user_contracts
                WHERE user_id = :user_id AND is_active = true
                    AND embedding IS NOT NULL
                ORDER BY COALESCE(embedding <=> CAST(:query_embedding AS vector), 999999)
                LIMIT :top_k
            """)

            contract_results = await run_db_query(
                contract_query,
                {
                    "user_id": user_id,
                    "query_embedding": embedding_str,
                    "top_k": top_k
                }
            )
        else:
            # Simple fetch without similarity
            contract_query = text("""
                SELECT
                    id, contract_number, contract_type, coverage_amount,
                    full_text, key_terms, is_active,
                    0.0 AS similarity
                FROM user_contracts
                WHERE user_id = :user_id AND is_active = true
                LIMIT :top_k
            """)

            contract_results = await run_db_query(
                contract_query,
                {"user_id": user_id, "top_k": top_k}
            )

        contracts = []
        for row in contract_results:
            contract = dict(row._mapping)
            # Convert Decimal to float for JSON serialization
            if 'coverage_amount' in contract and contract['coverage_amount'] is not None:
                contract['coverage_amount'] = float(contract['coverage_amount'])
            if 'similarity' in contract and contract['similarity'] is not None:
                contract['similarity'] = float(contract['similarity'])
            contracts.append(contract)

        logger.info(f"Retrieved {len(contracts)} contracts for user {user_id}")

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True,
            "user_info": user_info,
            "contracts": contracts,
            "total_contracts": len(contracts),
            "processing_time_seconds": round(processing_time, 2)
        }, default=str)  # default=str handles any remaining non-serializable types

    except Exception as e:
        logger.error(f"Error retrieving user info: {str(e)}", exc_info=True)
        processing_time = time.time() - start_time
        return json.dumps({
            "success": False,
            "error": str(e),
            "processing_time_seconds": round(processing_time, 2)
        })


@mcp.tool()
async def retrieve_similar_claims(
    claim_text: str,
    claim_type: Optional[str] = None,
    top_k: int = 10,
    min_similarity: float = 0.7
) -> str:
    """
    Find similar historical claims using vector similarity search.

    This tool performs ONLY retrieval. No LLM analysis.
    The LlamaStack agent will analyze the similar claims patterns.

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

    logger.info(f"Searching for similar claims (top_k={top_k}, min_similarity={min_similarity})")

    # Input validation
    if not claim_text or not claim_text.strip():
        return json.dumps({
            "success": False,
            "error": "claim_text is required"
        })

    claim_text = claim_text.strip()
    top_k = min(max(1, top_k), 100)  # Clamp between 1 and 100
    min_similarity = min(max(0.0, min_similarity), 1.0)  # Clamp between 0 and 1

    try:
        # Create embedding for claim text
        claim_embedding = await create_embedding(claim_text)
        embedding_str = format_embedding(claim_embedding)

        # Vector search on claim documents
        query = text("""
            SELECT
                CAST(c.id AS text) as claim_id,
                c.claim_number,
                cd.raw_ocr_text as claim_text,
                1 - (cd.embedding <=> CAST(:claim_embedding AS vector)) AS similarity,
                c.status as outcome,
                c.total_processing_time_ms
            FROM claim_documents cd
            JOIN claims c ON cd.claim_id = c.id
            WHERE 1 - (cd.embedding <=> CAST(:claim_embedding AS vector)) >= :min_similarity
                AND (:claim_type IS NULL OR c.claim_type = :claim_type)
                AND c.status IN ('completed', 'manual_review')
                AND cd.embedding IS NOT NULL
            ORDER BY cd.embedding <=> CAST(:claim_embedding AS vector)
            LIMIT :top_k
        """)

        results = await run_db_query(
            query,
            {
                "claim_embedding": embedding_str,
                "min_similarity": min_similarity,
                "claim_type": claim_type,
                "top_k": top_k
            }
        )

        similar_claims = []
        for row in results:
            claim_text_truncated = ""
            if row.claim_text:
                claim_text_truncated = row.claim_text[:500]
                if len(row.claim_text) > 500:
                    claim_text_truncated += "..."
            
            similar_claims.append({
                "claim_id": row.claim_id,
                "claim_number": row.claim_number,
                "claim_text": claim_text_truncated,
                "similarity_score": float(row.similarity) if row.similarity else 0.0,
                "outcome": row.outcome,
                "processing_time_ms": row.total_processing_time_ms
            })

        logger.info(f"Found {len(similar_claims)} similar claims")

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True,
            "similar_claims": similar_claims,
            "total_found": len(similar_claims),
            "search_params": {
                "top_k": top_k,
                "min_similarity": min_similarity,
                "claim_type": claim_type
            },
            "processing_time_seconds": round(processing_time, 2)
        })

    except Exception as e:
        logger.error(f"Error retrieving similar claims: {str(e)}", exc_info=True)
        processing_time = time.time() - start_time
        return json.dumps({
            "success": False,
            "error": str(e),
            "processing_time_seconds": round(processing_time, 2)
        })


@mcp.tool()
async def search_knowledge_base(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None
) -> str:
    """
    Search the knowledge base for relevant policy information.

    This tool performs ONLY retrieval. No LLM synthesis.
    The LlamaStack agent will synthesize answers from the retrieved documents.

    Args:
        query: Search query
        top_k: Number of results to retrieve (default: 5)
        category: Optional category filter

    Returns:
        JSON string with knowledge base articles
    """
    import time
    start_time = time.time()

    logger.info(f"Searching knowledge base: {query}")

    # Input validation
    if not query or not query.strip():
        return json.dumps({
            "success": False,
            "error": "query is required"
        })

    query = query.strip()
    top_k = min(max(1, top_k), 50)  # Clamp between 1 and 50

    try:
        # Create embedding for query
        query_embedding = await create_embedding(query)
        embedding_str = format_embedding(query_embedding)

        # Vector search on knowledge base
        kb_query = text("""
            SELECT
                CAST(id AS text) as id,
                title,
                content,
                category,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM knowledge_base
            WHERE is_active = true
                AND embedding IS NOT NULL
                AND (:category IS NULL OR category = :category)
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        results = await run_db_query(
            kb_query,
            {
                "query_embedding": embedding_str,
                "top_k": top_k,
                "category": category
            }
        )

        kb_results = []
        for row in results:
            kb_results.append({
                "id": row.id,
                "title": row.title,
                "content": row.content,
                "category": row.category,
                "similarity_score": float(row.similarity) if row.similarity else 0.0
            })

        logger.info(f"Found {len(kb_results)} knowledge base articles")

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True,
            "articles": kb_results,
            "total_found": len(kb_results),
            "search_params": {
                "query": query,
                "top_k": top_k,
                "category": category
            },
            "processing_time_seconds": round(processing_time, 2)
        })

    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}", exc_info=True)
        processing_time = time.time() - start_time
        return json.dumps({
            "success": False,
            "error": str(e),
            "processing_time_seconds": round(processing_time, 2)
        })


# =============================================================================
# MCP Tools - Appels d'Offres (Tenders)
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
    Find similar Vinci project references using vector similarity search.

    This tool performs ONLY retrieval. No LLM analysis.
    The LlamaStack agent will analyze the similar references.

    Args:
        project_description: Description of the project from the tender
        project_type: Optional filter by project type (e.g., 'logements', 'infrastructure', 'genie_civil')
        budget_range: Optional budget range description
        top_k: Number of similar references to retrieve (default: 5)
        min_similarity: Minimum similarity score 0.0-1.0 (default: 0.5)

    Returns:
        JSON string with similar project references
    """
    import time
    start_time = time.time()

    logger.info(f"Searching for similar references (top_k={top_k}, min_similarity={min_similarity}, project_type={project_type}, desc={project_description[:100] if project_description else 'None'})")

    if not project_description or not project_description.strip():
        return json.dumps({
            "success": False,
            "error": "project_description is required"
        })

    project_description = project_description.strip()
    top_k = min(max(1, top_k), 100)
    min_similarity = min(max(0.0, min_similarity), 1.0)

    try:
        query_embedding = await create_embedding(project_description)
        embedding_str = format_embedding(query_embedding)

        query = text("""
            SELECT
                reference_number,
                project_name,
                maitre_ouvrage,
                nature_travaux,
                montant,
                region,
                LEFT(description, 200) as description,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM vinci_references
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        results = await run_db_query(
            query,
            {
                "query_embedding": embedding_str,
                "top_k": top_k
            }
        )

        references = []
        for row in results:
            ref = dict(row._mapping)
            if 'similarity' in ref and ref['similarity'] is not None:
                ref['similarity'] = float(ref['similarity'])
            if 'montant' in ref and ref['montant'] is not None:
                ref['montant'] = float(ref['montant'])
            references.append(ref)

        logger.info(f"Found {len(references)} similar references")

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True,
            "references": references,
            "total_found": len(references),
            "search_params": {
                "top_k": top_k,
                "min_similarity": min_similarity,
                "project_type": project_type
            },
            "processing_time_seconds": round(processing_time, 2)
        }, default=str)

    except Exception as e:
        logger.error(f"Error retrieving similar references: {str(e)}", exc_info=True)
        processing_time = time.time() - start_time
        return json.dumps({
            "success": False,
            "error": str(e),
            "processing_time_seconds": round(processing_time, 2)
        })


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

    This tool performs ONLY retrieval. No LLM analysis.
    The LlamaStack agent will analyze historical tender patterns.

    Args:
        tender_description: Description of the current tender
        tender_type: Optional filter by tender type
        client_type: Optional filter by client type (e.g., 'public', 'prive')
        top_k: Number of similar tenders to retrieve (default: 5)
        min_similarity: Minimum similarity score 0.0-1.0 (default: 0.5)

    Returns:
        JSON string with similar historical tenders
    """
    import time
    start_time = time.time()

    logger.info(f"Searching for historical tenders (top_k={top_k}, min_similarity={min_similarity}, tender_type={tender_type}, desc={tender_description[:100] if tender_description else 'None'})")

    if not tender_description or not tender_description.strip():
        return json.dumps({
            "success": False,
            "error": "tender_description is required"
        })

    tender_description = tender_description.strip()
    top_k = min(max(1, top_k), 100)
    min_similarity = min(max(0.0, min_similarity), 1.0)

    try:
        query_embedding = await create_embedding(tender_description)
        embedding_str = format_embedding(query_embedding)

        query = text("""
            SELECT
                ao_number,
                nature_travaux,
                maitre_ouvrage,
                montant_estime,
                resultat,
                LEFT(raison_resultat, 150) as raison_resultat,
                note_technique,
                note_prix,
                region,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM historical_tenders
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        results = await run_db_query(
            query,
            {
                "query_embedding": embedding_str,
                "top_k": top_k
            }
        )

        tenders = []
        for row in results:
            tender = dict(row._mapping)
            if 'similarity' in tender and tender['similarity'] is not None:
                tender['similarity'] = float(tender['similarity'])
            if 'montant_estime' in tender and tender['montant_estime'] is not None:
                tender['montant_estime'] = float(tender['montant_estime'])
            if 'montant_propose' in tender and tender['montant_propose'] is not None:
                tender['montant_propose'] = float(tender['montant_propose'])
            if 'note_technique' in tender and tender['note_technique'] is not None:
                tender['note_technique'] = float(tender['note_technique'])
            if 'note_prix' in tender and tender['note_prix'] is not None:
                tender['note_prix'] = float(tender['note_prix'])
            tenders.append(tender)

        won = sum(1 for t in tenders if t.get('resultat') == 'gagne')
        total = len(tenders)
        win_rate = (won / total * 100) if total > 0 else 0

        logger.info(f"Found {len(tenders)} historical tenders (win rate: {win_rate:.1f}%)")

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True,
            "historical_tenders": tenders,
            "total_found": len(tenders),
            "win_rate_percentage": round(win_rate, 1),
            "search_params": {
                "top_k": top_k,
                "min_similarity": min_similarity,
                "tender_type": tender_type
            },
            "processing_time_seconds": round(processing_time, 2)
        }, default=str)

    except Exception as e:
        logger.error(f"Error retrieving historical tenders: {str(e)}", exc_info=True)
        processing_time = time.time() - start_time
        return json.dumps({
            "success": False,
            "error": str(e),
            "processing_time_seconds": round(processing_time, 2)
        })


@mcp.tool()
async def retrieve_capabilities(
    required_capabilities: str,
    project_type: Optional[str] = None,
    category: Optional[str] = None,
    top_k: int = 10
) -> str:
    """
    Retrieve Vinci internal capabilities, certifications, and resources.

    This tool performs ONLY retrieval. No LLM analysis.
    The LlamaStack agent will assess capability adequacy.

    Args:
        required_capabilities: Description of required capabilities for the tender
        project_type: Optional project type filter
        category: Optional category filter (e.g., 'certification', 'materiel', 'personnel')
        top_k: Number of capabilities to retrieve (default: 20)

    Returns:
        JSON string with matching capabilities
    """
    import time
    start_time = time.time()

    logger.info(f"Retrieving capabilities (category={category}, top_k={top_k})")

    if not required_capabilities or not required_capabilities.strip():
        return json.dumps({
            "success": False,
            "error": "required_capabilities is required"
        })

    required_capabilities = required_capabilities.strip()
    top_k = min(max(1, top_k), 50)

    try:
        query_embedding = await create_embedding(required_capabilities)
        embedding_str = format_embedding(query_embedding)

        query = text("""
            SELECT
                name,
                category,
                LEFT(description, 150) as description,
                valid_until,
                region,
                availability,
                1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity
            FROM vinci_capabilities
            WHERE is_active = true
                AND embedding IS NOT NULL
                AND (:category IS NULL OR category = :category)
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        results = await run_db_query(
            query,
            {
                "query_embedding": embedding_str,
                "category": category,
                "top_k": top_k
            }
        )

        capabilities = []
        for row in results:
            cap = dict(row._mapping)
            if 'similarity' in cap and cap['similarity'] is not None:
                cap['similarity'] = float(cap['similarity'])
            capabilities.append(cap)

        # Group by category (for stats only)
        categories_found = list(set(cap.get('category', 'other') for cap in capabilities))

        logger.info(f"Found {len(capabilities)} capabilities across {len(categories_found)} categories")

        processing_time = time.time() - start_time
        return json.dumps({
            "success": True,
            "capabilities": capabilities,
            "total_found": len(capabilities),
            "categories_found": categories_found,
            "processing_time_seconds": round(processing_time, 2)
        }, default=str)

    except Exception as e:
        logger.error(f"Error retrieving capabilities: {str(e)}", exc_info=True)
        processing_time = time.time() - start_time
        return json.dumps({
            "success": False,
            "error": str(e),
            "processing_time_seconds": round(processing_time, 2)
        })


# =============================================================================
# Health Check Tool and Endpoint
# =============================================================================

@mcp.tool()
async def rag_health_check() -> str:
    """
    Check RAG server health and connectivity.

    Returns:
        JSON string with health status
    """
    health = {
        "status": "healthy",
        "checks": {}
    }

    # Check database
    try:
        await run_db_query_one(text("SELECT 1"), {})
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["checks"]["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    # Check embedding service
    try:
        await create_embedding("health check")
        health["checks"]["embedding_service"] = "ok"
    except Exception as e:
        health["checks"]["embedding_service"] = f"error: {str(e)}"
        health["status"] = "degraded"  # Can still work without embeddings for some queries

    return json.dumps(health)


# Health check endpoint for Kubernetes probes
async def health_check(request):
    """Simple health check endpoint for liveness/readiness probes"""
    health_status = {
        "status": "healthy",
        "service": "rag-server",
        "database_ready": False,
        "embedding_ready": False
    }

    # Check database
    try:
        await run_db_query_one(text("SELECT 1"), {})
        health_status["database_ready"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"

    # Check embedding service (non-critical)
    try:
        await create_embedding("test")
        health_status["embedding_ready"] = True
    except Exception as e:
        logger.warning(f"Embedding service health check failed: {e}")
        # Don't mark as unhealthy if only embeddings fail
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    return JSONResponse(health_status)


# OPTIONS endpoint for MCP discovery (required by LlamaStack)
async def sse_options(request):
    """Handle OPTIONS requests for MCP SSE endpoint discovery"""
    return JSONResponse({
        "methods": ["GET", "POST", "OPTIONS"],
        "mcp_version": "0.1.0",
        "server_name": "rag-server",
        "capabilities": {
            "tools": True,
            "streaming": True
        }
    })


# =============================================================================
# Starlette App with Health Check and MCP SSE
# =============================================================================

# Create wrapper app with health check and MCP SSE server
mcp_sse_app = mcp.sse_app()

app = Starlette(
    routes=[
        Route("/health", health_check),
        Route("/sse", sse_options, methods=["OPTIONS"]),
        Route("/", sse_options, methods=["OPTIONS"]),
        Mount("/", app=mcp_sse_app),
    ]
)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Verify database connection before starting
    try:
        check_database_connection()
    except Exception as e:
        logger.critical(f"Failed to connect to database: {e}")
        logger.critical("Server cannot start without database connection")
        exit(1)

    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting MCP RAG Server (FastMCP SSE) on {host}:{port}")
    logger.info(f"Embedding model: {EMBEDDING_MODEL}")
    logger.info(f"LlamaStack endpoint: {LLAMASTACK_ENDPOINT}")
    logger.info(f"Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    logger.info(f"MCP SSE endpoint will be available at: http://{host}:{port}/sse")
    logger.info("Tools:")
    logger.info("  - retrieve_user_info: Get user + contracts (vector search)")
    logger.info("  - retrieve_similar_claims: Find similar claims (vector search)")
    logger.info("  - search_knowledge_base: Search KB articles (vector search)")
    logger.info("  - retrieve_similar_references: Find similar Vinci project references (vector search)")
    logger.info("  - retrieve_historical_tenders: Find historical tenders won/lost (vector search)")
    logger.info("  - retrieve_capabilities: Get Vinci certifications and capabilities (vector search)")
    logger.info("  - rag_health_check: Check server health")

    # Run uvicorn with FastMCP SSE app
    uvicorn.run(app, host=host, port=port)
