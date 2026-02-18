"""
MCP Tenders Server - CRUD operations on tenders (Appels d'Offres) via PostgreSQL.

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
    "tenders-server",
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
# MCP Tools - Tenders CRUD
# =============================================================================

@mcp.tool()
async def list_tenders(
    status: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    List tenders (appels d'offres) with optional status filter.

    Args:
        status: Optional status filter (pending, processing, completed, failed)
        limit: Maximum number of tenders to return (default: 20)

    Returns:
        JSON string with list of tenders
    """
    logger.info(f"Listing tenders (status={status}, limit={limit})")

    limit = min(max(1, limit), 100)

    try:
        if status:
            query = text("""
                SELECT
                    t.id, t.tender_number, t.entity_id, t.tender_type,
                    t.status, t.submitted_at, t.processed_at,
                    t.total_processing_time_ms, t.metadata,
                    td.decision as ai_decision,
                    td.confidence as ai_confidence
                FROM tenders t
                LEFT JOIN tender_decisions td ON td.tender_id = t.id
                WHERE t.status = :status AND t.is_archived = false
                ORDER BY t.submitted_at DESC
                LIMIT :limit
            """)
            results = await run_db_query(query, {"status": status, "limit": limit})
        else:
            query = text("""
                SELECT
                    t.id, t.tender_number, t.entity_id, t.tender_type,
                    t.status, t.submitted_at, t.processed_at,
                    t.total_processing_time_ms, t.metadata,
                    td.decision as ai_decision,
                    td.confidence as ai_confidence
                FROM tenders t
                LEFT JOIN tender_decisions td ON td.tender_id = t.id
                WHERE t.is_archived = false
                ORDER BY t.submitted_at DESC
                LIMIT :limit
            """)
            results = await run_db_query(query, {"limit": limit})

        tenders = []
        for row in results:
            tender = dict(row._mapping)
            tender['id'] = str(tender['id'])
            for key, value in tender.items():
                if hasattr(value, 'isoformat'):
                    tender[key] = value.isoformat()
                elif hasattr(value, '__float__') and key != 'id':
                    tender[key] = float(value)
            tenders.append(tender)

        logger.info(f"Found {len(tenders)} tenders")

        return json.dumps({
            "success": True,
            "tenders": tenders,
            "total_found": len(tenders),
            "filter": {"status": status, "limit": limit}
        }, default=str)

    except Exception as e:
        logger.error(f"Error listing tenders: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_tender(tender_id: str) -> str:
    """
    Get detailed information about a specific tender (appel d'offres).

    Args:
        tender_id: The tender number (e.g., AO-2025-IDF-001)

    Returns:
        JSON string with tender details including decision and processing logs
    """
    logger.info(f"Getting tender details: {tender_id}")

    if not tender_id or not tender_id.strip():
        return json.dumps({"success": False, "error": "tender_id is required"})

    tender_id = tender_id.strip()

    try:
        # Get tender
        query = text("""
            SELECT
                t.id, t.tender_number, t.entity_id, t.tender_type,
                t.document_path, t.status,
                t.submitted_at, t.processed_at,
                t.total_processing_time_ms, t.metadata
            FROM tenders t
            WHERE t.tender_number = :tender_id
        """)
        result = await run_db_query_one(query, {"tender_id": tender_id})

        if not result:
            return json.dumps({"success": False, "error": f"Tender {tender_id} not found"})

        tender = dict(result._mapping)
        tender_uuid = tender['id']
        tender['id'] = str(tender['id'])

        for key, value in tender.items():
            if hasattr(value, 'isoformat'):
                tender[key] = value.isoformat()

        # Get decision
        decision_query = text("""
            SELECT decision, confidence, reasoning, risk_analysis,
                   similar_references, historical_ao_analysis, internal_capabilities,
                   llm_model, decided_at,
                   initial_decision, initial_confidence, initial_reasoning,
                   final_decision, final_decision_by_name, final_decision_at, final_decision_notes
            FROM tender_decisions
            WHERE tender_id = :tender_uuid
        """)
        decision_result = await run_db_query_one(decision_query, {"tender_uuid": tender_uuid})

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
            SELECT step, agent_name, started_at, completed_at,
                   duration_ms, status, error_message, confidence_score, tokens_used
            FROM tender_processing_logs
            WHERE tender_id = :tender_uuid
            ORDER BY started_at ASC
        """)
        logs_results = await run_db_query(logs_query, {"tender_uuid": tender_uuid})

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
            "tender": tender,
            "decision": decision,
            "processing_logs": logs
        }, default=str)

    except Exception as e:
        logger.error(f"Error getting tender: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_tender_documents(tender_id: str) -> str:
    """
    Get documents associated with a tender.

    Args:
        tender_id: The tender number (e.g., AO-2025-IDF-001)

    Returns:
        JSON string with tender documents and OCR data
    """
    logger.info(f"Getting documents for tender: {tender_id}")

    if not tender_id or not tender_id.strip():
        return json.dumps({"success": False, "error": "tender_id is required"})

    try:
        query = text("""
            SELECT
                td.id, td.document_type, td.file_path, td.file_size_bytes,
                td.mime_type, td.raw_ocr_text, td.structured_data,
                td.ocr_confidence, td.ocr_processed_at, td.page_count,
                td.language
            FROM tender_documents td
            JOIN tenders t ON td.tender_id = t.id
            WHERE t.tender_number = :tender_id
        """)
        results = await run_db_query(query, {"tender_id": tender_id.strip()})

        documents = []
        for row in results:
            doc = dict(row._mapping)
            doc['id'] = str(doc['id'])
            for key, value in doc.items():
                if hasattr(value, 'isoformat'):
                    doc[key] = value.isoformat()
                elif hasattr(value, '__float__'):
                    doc[key] = float(value)
            if doc.get('raw_ocr_text') and len(doc['raw_ocr_text']) > 1000:
                doc['raw_ocr_text'] = doc['raw_ocr_text'][:1000] + "..."
            documents.append(doc)

        return json.dumps({
            "success": True,
            "tender_number": tender_id.strip(),
            "documents": documents,
            "total_documents": len(documents)
        }, default=str)

    except Exception as e:
        logger.error(f"Error getting tender documents: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_tender_statistics() -> str:
    """
    Get aggregate statistics about all tenders (appels d'offres).

    Returns:
        JSON string with tender statistics (counts by status, decisions, etc.)
    """
    logger.info("Getting tender statistics")

    try:
        # Count by status
        status_query = text("""
            SELECT status, COUNT(*) as count
            FROM tenders
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
            FROM tenders
            WHERE total_processing_time_ms IS NOT NULL AND is_archived = false
        """)
        avg_result = await run_db_query_one(avg_query, {})

        processing_stats = {}
        if avg_result:
            mapping = dict(avg_result._mapping)
            for k, v in mapping.items():
                processing_stats[k] = float(v) if v is not None else None

        # Decision breakdown (Go/No-Go)
        decision_query = text("""
            SELECT
                td.decision, COUNT(*) as count,
                AVG(td.confidence) as avg_confidence
            FROM tender_decisions td
            JOIN tenders t ON td.tender_id = t.id
            WHERE t.is_archived = false
            GROUP BY td.decision
        """)
        decision_results = await run_db_query(decision_query, {})

        decisions = {}
        for row in decision_results:
            decisions[row.decision or "unknown"] = {
                "count": row.count,
                "avg_confidence": round(float(row.avg_confidence), 3) if row.avg_confidence else None
            }

        # By tender type
        type_query = text("""
            SELECT tender_type, COUNT(*) as count
            FROM tenders
            WHERE is_archived = false AND tender_type IS NOT NULL
            GROUP BY tender_type
            ORDER BY count DESC
        """)
        type_results = await run_db_query(type_query, {})

        by_type = {}
        for row in type_results:
            by_type[row.tender_type] = row.count

        return json.dumps({
            "success": True,
            "total_tenders": total,
            "by_status": status_counts,
            "by_type": by_type,
            "processing_time": processing_stats,
            "decisions": decisions
        }, default=str)

    except Exception as e:
        logger.error(f"Error getting tender statistics: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def analyze_tender(tender_id: str) -> str:
    """
    Get all data needed to analyze a specific tender (appel d'offres).
    This provides a comprehensive view for the LLM to perform Go/No-Go analysis.

    Args:
        tender_id: The tender number (e.g., AO-2025-IDF-001)

    Returns:
        JSON string with comprehensive tender data for analysis
    """
    logger.info(f"Analyzing tender: {tender_id}")

    if not tender_id or not tender_id.strip():
        return json.dumps({"success": False, "error": "tender_id is required"})

    tender_id = tender_id.strip()

    try:
        # Get tender info
        tender_query = text("""
            SELECT
                t.id, t.tender_number, t.entity_id, t.tender_type,
                t.document_path, t.status,
                t.submitted_at, t.processed_at, t.metadata
            FROM tenders t
            WHERE t.tender_number = :tender_id
        """)
        tender_result = await run_db_query_one(tender_query, {"tender_id": tender_id})

        if not tender_result:
            return json.dumps({"success": False, "error": f"Tender {tender_id} not found"})

        tender = dict(tender_result._mapping)
        tender_uuid = tender['id']

        # Get OCR text from documents
        doc_query = text("""
            SELECT raw_ocr_text, structured_data, ocr_confidence
            FROM tender_documents
            WHERE tender_id = :tender_uuid
        """)
        doc_results = await run_db_query(doc_query, {"tender_uuid": tender_uuid})

        ocr_data = []
        for row in doc_results:
            ocr_data.append({
                "raw_text": row.raw_ocr_text,
                "structured_data": row.structured_data,
                "confidence": float(row.ocr_confidence) if row.ocr_confidence else None
            })

        # Get existing decision if any
        decision_query = text("""
            SELECT decision, confidence, reasoning, risk_analysis
            FROM tender_decisions
            WHERE tender_id = :tender_uuid
        """)
        decision_result = await run_db_query_one(decision_query, {"tender_uuid": tender_uuid})

        existing_decision = None
        if decision_result:
            existing_decision = {
                "decision": decision_result.decision,
                "confidence": float(decision_result.confidence) if decision_result.confidence else None,
                "reasoning": decision_result.reasoning,
                "risk_analysis": decision_result.risk_analysis
            }

        # Build comprehensive analysis data
        for key, value in tender.items():
            if hasattr(value, 'isoformat'):
                tender[key] = value.isoformat()
        tender['id'] = str(tender['id'])

        return json.dumps({
            "success": True,
            "tender": tender,
            "ocr_data": ocr_data,
            "existing_decision": existing_decision,
            "analysis_ready": True
        }, default=str)

    except Exception as e:
        logger.error(f"Error analyzing tender: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


# =============================================================================
# Health Check
# =============================================================================

async def health_check(request):
    """Health check endpoint for liveness/readiness probes."""
    health_status = {
        "status": "healthy",
        "service": "tenders-server",
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
        "server_name": "tenders-server",
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

    logger.info(f"Starting MCP Tenders Server on {host}:{port}")
    logger.info(f"Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    logger.info("Tools: list_tenders, get_tender, get_tender_documents, get_tender_statistics, analyze_tender")

    uvicorn.run(app, host=host, port=port)
