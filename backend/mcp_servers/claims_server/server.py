"""
MCP Claims Server - CRUD operations on insurance_claims via PostgreSQL.

Pure CRUD server (no RAG/embeddings). The RAG server handles vector operations.
FastMCP implementation with Streamable HTTP transport (SSE).
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP(
    "claims-server",
    stateless_http=True,
    json_response=True
)

# Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgresql")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DATABASE", "claims_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "claims_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "claims_pass")

# Database connection
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
SessionLocal = sessionmaker(bind=engine)


def check_database_connection() -> bool:
    """Verify database connectivity on startup."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


async def run_db_query(query, params: dict) -> List[Any]:
    """Execute database query in thread pool (non-blocking)."""
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
    """Execute database query and return single result."""
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
# MCP Tools - Claims CRUD
# =============================================================================

@mcp.tool()
async def list_claims(
    status: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    List insurance claims with optional status filter.

    Args:
        status: Optional status filter (pending, processing, completed, failed, manual_review)
        limit: Maximum number of claims to return (default: 20)

    Returns:
        JSON string with list of claims
    """
    logger.info(f"Listing claims (status={status}, limit={limit})")

    limit = min(max(1, limit), 100)

    try:
        if status:
            query = text("""
                SELECT
                    c.id, c.claim_number, c.user_id, c.claim_type,
                    c.status::text as status, c.submitted_at, c.processed_at,
                    c.total_processing_time_ms,
                    u.full_name as user_name,
                    cd.decision as ai_decision,
                    cd.confidence as ai_confidence
                FROM claims c
                LEFT JOIN users u ON c.user_id = u.user_id
                LEFT JOIN claim_decisions cd ON cd.claim_id = c.id
                WHERE c.status::text = :status AND c.is_archived = false
                ORDER BY c.submitted_at DESC
                LIMIT :limit
            """)
            results = await run_db_query(query, {"status": status, "limit": limit})
        else:
            query = text("""
                SELECT
                    c.id, c.claim_number, c.user_id, c.claim_type,
                    c.status::text as status, c.submitted_at, c.processed_at,
                    c.total_processing_time_ms,
                    u.full_name as user_name,
                    cd.decision as ai_decision,
                    cd.confidence as ai_confidence
                FROM claims c
                LEFT JOIN users u ON c.user_id = u.user_id
                LEFT JOIN claim_decisions cd ON cd.claim_id = c.id
                WHERE c.is_archived = false
                ORDER BY c.submitted_at DESC
                LIMIT :limit
            """)
            results = await run_db_query(query, {"limit": limit})

        claims = []
        for row in results:
            claim = dict(row._mapping)
            # Convert non-serializable types
            for key, value in claim.items():
                if hasattr(value, 'isoformat'):
                    claim[key] = value.isoformat()
                elif hasattr(value, '__float__'):
                    claim[key] = float(value)
            claim['id'] = str(claim['id'])
            claims.append(claim)

        logger.info(f"Found {len(claims)} claims")

        return json.dumps({
            "success": True,
            "claims": claims,
            "total_found": len(claims),
            "filter": {"status": status, "limit": limit}
        }, default=str)

    except Exception as e:
        logger.error(f"Error listing claims: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_claim(claim_id: str) -> str:
    """
    Get detailed information about a specific claim.

    Args:
        claim_id: The claim number (e.g., CLM-2024-0001)

    Returns:
        JSON string with claim details including user info, decision, and processing logs
    """
    logger.info(f"Getting claim details: {claim_id}")

    if not claim_id or not claim_id.strip():
        return json.dumps({"success": False, "error": "claim_id is required"})

    claim_id = claim_id.strip()

    try:
        # Get claim with user info
        query = text("""
            SELECT
                c.id, c.claim_number, c.user_id, c.claim_type,
                c.document_path, c.status::text as status,
                c.submitted_at, c.processed_at,
                c.total_processing_time_ms, c.metadata,
                u.full_name as user_name, u.email as user_email,
                u.phone_number as user_phone, u.address as user_address
            FROM claims c
            LEFT JOIN users u ON c.user_id = u.user_id
            WHERE c.claim_number = :claim_id
        """)
        result = await run_db_query_one(query, {"claim_id": claim_id})

        if not result:
            return json.dumps({"success": False, "error": f"Claim {claim_id} not found"})

        claim = dict(result._mapping)
        claim_uuid = claim['id']
        claim['id'] = str(claim['id'])

        # Convert types
        for key, value in claim.items():
            if hasattr(value, 'isoformat'):
                claim[key] = value.isoformat()

        # Get decision
        decision_query = text("""
            SELECT decision, confidence, reasoning, llm_model, decided_at,
                   initial_decision, initial_confidence, initial_reasoning,
                   final_decision, final_decision_by_name, final_decision_at, final_decision_notes
            FROM claim_decisions
            WHERE claim_id = :claim_uuid
        """)
        decision_result = await run_db_query_one(decision_query, {"claim_uuid": claim_uuid})

        decision = None
        if decision_result:
            decision = dict(decision_result._mapping)
            for key, value in decision.items():
                if hasattr(value, 'isoformat'):
                    decision[key] = value.isoformat()
                elif hasattr(value, '__float__'):
                    decision[key] = float(value)

        # Get processing logs
        logs_query = text("""
            SELECT step::text as step, agent_name, started_at, completed_at,
                   duration_ms, status, error_message, confidence_score, tokens_used
            FROM processing_logs
            WHERE claim_id = :claim_uuid
            ORDER BY started_at ASC
        """)
        logs_results = await run_db_query(logs_query, {"claim_uuid": claim_uuid})

        logs = []
        for row in logs_results:
            log = dict(row._mapping)
            for key, value in log.items():
                if hasattr(value, 'isoformat'):
                    log[key] = value.isoformat()
                elif hasattr(value, '__float__'):
                    log[key] = float(value)
            logs.append(log)

        return json.dumps({
            "success": True,
            "claim": claim,
            "decision": decision,
            "processing_logs": logs
        }, default=str)

    except Exception as e:
        logger.error(f"Error getting claim: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_claim_documents(claim_id: str) -> str:
    """
    Get documents associated with a claim.

    Args:
        claim_id: The claim number (e.g., CLM-2024-0001)

    Returns:
        JSON string with claim documents and OCR data
    """
    logger.info(f"Getting documents for claim: {claim_id}")

    if not claim_id or not claim_id.strip():
        return json.dumps({"success": False, "error": "claim_id is required"})

    try:
        query = text("""
            SELECT
                cd.id, cd.document_type, cd.file_path, cd.file_size_bytes,
                cd.mime_type, cd.raw_ocr_text, cd.structured_data,
                cd.ocr_confidence, cd.ocr_processed_at, cd.page_count,
                cd.language
            FROM claim_documents cd
            JOIN claims c ON cd.claim_id = c.id
            WHERE c.claim_number = :claim_id
        """)
        results = await run_db_query(query, {"claim_id": claim_id.strip()})

        documents = []
        for row in results:
            doc = dict(row._mapping)
            doc['id'] = str(doc['id'])
            for key, value in doc.items():
                if hasattr(value, 'isoformat'):
                    doc[key] = value.isoformat()
                elif hasattr(value, '__float__'):
                    doc[key] = float(value)
            # Truncate OCR text for readability
            if doc.get('raw_ocr_text') and len(doc['raw_ocr_text']) > 1000:
                doc['raw_ocr_text'] = doc['raw_ocr_text'][:1000] + "..."
            documents.append(doc)

        return json.dumps({
            "success": True,
            "claim_number": claim_id.strip(),
            "documents": documents,
            "total_documents": len(documents)
        }, default=str)

    except Exception as e:
        logger.error(f"Error getting claim documents: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_claim_statistics() -> str:
    """
    Get aggregate statistics about all claims.

    Returns:
        JSON string with claim statistics (counts by status, average processing time, etc.)
    """
    logger.info("Getting claim statistics")

    try:
        # Count by status
        status_query = text("""
            SELECT status::text as status, COUNT(*) as count
            FROM claims
            WHERE is_archived = false
            GROUP BY status
            ORDER BY count DESC
        """)
        status_results = await run_db_query(status_query, {})

        status_counts = {}
        total = 0
        for row in status_results:
            status_counts[row.status] = row.count
            total += row.count

        # Average processing time
        avg_query = text("""
            SELECT
                AVG(total_processing_time_ms) as avg_processing_ms,
                MIN(total_processing_time_ms) as min_processing_ms,
                MAX(total_processing_time_ms) as max_processing_ms
            FROM claims
            WHERE total_processing_time_ms IS NOT NULL AND is_archived = false
        """)
        avg_result = await run_db_query_one(avg_query, {})

        processing_stats = {}
        if avg_result:
            mapping = dict(avg_result._mapping)
            for k, v in mapping.items():
                processing_stats[k] = float(v) if v is not None else None

        # Decision breakdown
        decision_query = text("""
            SELECT
                cd.decision, COUNT(*) as count,
                AVG(cd.confidence) as avg_confidence
            FROM claim_decisions cd
            JOIN claims c ON cd.claim_id = c.id
            WHERE c.is_archived = false
            GROUP BY cd.decision
        """)
        decision_results = await run_db_query(decision_query, {})

        decisions = {}
        for row in decision_results:
            decisions[row.decision or "unknown"] = {
                "count": row.count,
                "avg_confidence": round(float(row.avg_confidence), 3) if row.avg_confidence else None
            }

        return json.dumps({
            "success": True,
            "total_claims": total,
            "by_status": status_counts,
            "processing_time": processing_stats,
            "decisions": decisions
        }, default=str)

    except Exception as e:
        logger.error(f"Error getting claim statistics: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def analyze_claim(claim_id: str) -> str:
    """
    Get all data needed to analyze a specific claim (claim info, documents, user contracts).
    This provides a comprehensive view for the LLM to perform analysis.

    Args:
        claim_id: The claim number (e.g., CLM-2024-0001)

    Returns:
        JSON string with comprehensive claim data for analysis
    """
    logger.info(f"Analyzing claim: {claim_id}")

    if not claim_id or not claim_id.strip():
        return json.dumps({"success": False, "error": "claim_id is required"})

    claim_id = claim_id.strip()

    try:
        # Get claim with user info
        claim_query = text("""
            SELECT
                c.id, c.claim_number, c.user_id, c.claim_type,
                c.document_path, c.status::text as status,
                c.submitted_at, c.processed_at, c.metadata,
                u.full_name as user_name, u.email as user_email
            FROM claims c
            LEFT JOIN users u ON c.user_id = u.user_id
            WHERE c.claim_number = :claim_id
        """)
        claim_result = await run_db_query_one(claim_query, {"claim_id": claim_id})

        if not claim_result:
            return json.dumps({"success": False, "error": f"Claim {claim_id} not found"})

        claim = dict(claim_result._mapping)
        claim_uuid = claim['id']
        user_id = claim['user_id']

        # Get OCR text from documents
        doc_query = text("""
            SELECT raw_ocr_text, structured_data, ocr_confidence
            FROM claim_documents
            WHERE claim_id = :claim_uuid
        """)
        doc_result = await run_db_query_one(doc_query, {"claim_uuid": claim_uuid})

        ocr_data = None
        if doc_result:
            ocr_data = {
                "raw_text": doc_result.raw_ocr_text,
                "structured_data": doc_result.structured_data,
                "confidence": float(doc_result.ocr_confidence) if doc_result.ocr_confidence else None
            }

        # Get user contracts
        contracts_query = text("""
            SELECT contract_number, contract_type, coverage_amount,
                   key_terms, coverage_details, exclusions, is_active
            FROM user_contracts
            WHERE user_id = :user_id AND is_active = true
        """)
        contracts_results = await run_db_query(contracts_query, {"user_id": user_id})

        contracts = []
        for row in contracts_results:
            contract = dict(row._mapping)
            if contract.get('coverage_amount'):
                contract['coverage_amount'] = float(contract['coverage_amount'])
            contracts.append(contract)

        # Get existing decision if any
        decision_query = text("""
            SELECT decision, confidence, reasoning
            FROM claim_decisions
            WHERE claim_id = :claim_uuid
        """)
        decision_result = await run_db_query_one(decision_query, {"claim_uuid": claim_uuid})

        existing_decision = None
        if decision_result:
            existing_decision = {
                "decision": decision_result.decision,
                "confidence": float(decision_result.confidence) if decision_result.confidence else None,
                "reasoning": decision_result.reasoning
            }

        # Build comprehensive analysis data
        for key, value in claim.items():
            if hasattr(value, 'isoformat'):
                claim[key] = value.isoformat()
        claim['id'] = str(claim['id'])

        return json.dumps({
            "success": True,
            "claim": claim,
            "ocr_data": ocr_data,
            "user_contracts": contracts,
            "existing_decision": existing_decision,
            "analysis_ready": True
        }, default=str)

    except Exception as e:
        logger.error(f"Error analyzing claim: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


# =============================================================================
# Health Check
# =============================================================================

async def health_check(request):
    """Health check endpoint for liveness/readiness probes."""
    health_status = {
        "status": "healthy",
        "service": "claims-server",
        "database_ready": False
    }

    try:
        await run_db_query_one(text("SELECT 1"), {})
        health_status["database_ready"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"

    return JSONResponse(health_status)


async def sse_options(request):
    """Handle OPTIONS requests for MCP SSE endpoint discovery."""
    return JSONResponse({
        "methods": ["GET", "POST", "OPTIONS"],
        "mcp_version": "0.1.0",
        "server_name": "claims-server",
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
        check_database_connection()
    except Exception as e:
        logger.critical(f"Failed to connect to database: {e}")
        exit(1)

    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting MCP Claims Server on {host}:{port}")
    logger.info(f"Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    logger.info("Tools: list_claims, get_claim, get_claim_documents, get_claim_statistics, analyze_claim")

    uvicorn.run(app, host=host, port=port)
