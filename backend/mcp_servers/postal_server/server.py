"""
MCP Postal Server - CRUD operations on postal/parcel reclamations via PostgreSQL.

Includes decision persistence with automatic embedding generation.
FastMCP implementation with Streamable HTTP transport (SSE).
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

from shared.db import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB,
    check_database_connection, run_db_query, run_db_query_one, run_db_execute,
)

# LlamaStack endpoint for embedding generation
LLAMASTACK_ENDPOINT = os.getenv("LLAMASTACK_ENDPOINT", "http://llamastack:8321")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# Cached LLM model name (resolved from LlamaStack at first use)
_cached_llm_model: Optional[str] = None


def _get_llm_model_name() -> str:
    """Get the LLM model short name from LLAMASTACK_DEFAULT_MODEL env var."""
    global _cached_llm_model
    if _cached_llm_model:
        return _cached_llm_model
    import re
    full_model = os.getenv("LLAMASTACK_DEFAULT_MODEL", "unknown")
    short = full_model.split("/")[-1] if "/" in full_model else full_model
    _cached_llm_model = re.sub(r'-W\d+A\d+$', '', short)
    return _cached_llm_model

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP(
    "postal-server",
    stateless_http=True,
    json_response=True
)


# =============================================================================
# MCP Tools - Reclamations CRUD
# =============================================================================

@mcp.tool()
async def list_reclamations(
    status: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    List reclamations with optional status filter.

    Args:
        status: Optional status filter (pending, processing, completed, rejected, escalated, failed)
        limit: Maximum number of reclamations to return (default: 10)

    Returns:
        JSON string with list of reclamations including latest tracking event
    """
    logger.info(f"Listing reclamations (status={status}, limit={limit})")

    limit = min(max(1, limit), 100)

    try:
        if status:
            query = text("""
                SELECT
                    r.id, r.reclamation_number, r.numero_suivi, r.reclamation_type,
                    r.client_nom, r.document_path,
                    r.status, r.submitted_at, r.processed_at,
                    r.total_processing_time_ms,
                    rd.decision as ai_decision,
                    rd.confidence as ai_confidence,
                    te.event_type as latest_event_type,
                    te.event_date as latest_event_date,
                    te.location as latest_event_location
                FROM reclamations r
                LEFT JOIN reclamation_decisions rd ON rd.reclamation_id = r.id
                LEFT JOIN LATERAL (
                    SELECT event_type, event_date, location
                    FROM tracking_events
                    WHERE numero_suivi = r.numero_suivi
                    ORDER BY event_date DESC
                    LIMIT 1
                ) te ON true
                WHERE r.status = :status AND r.is_archived = false
                ORDER BY r.submitted_at DESC
                LIMIT :limit
            """)
            results = await run_db_query(query, {"status": status, "limit": limit})
        else:
            query = text("""
                SELECT
                    r.id, r.reclamation_number, r.numero_suivi, r.reclamation_type,
                    r.client_nom, r.document_path,
                    r.status, r.submitted_at, r.processed_at,
                    r.total_processing_time_ms,
                    rd.decision as ai_decision,
                    rd.confidence as ai_confidence,
                    te.event_type as latest_event_type,
                    te.event_date as latest_event_date,
                    te.location as latest_event_location
                FROM reclamations r
                LEFT JOIN reclamation_decisions rd ON rd.reclamation_id = r.id
                LEFT JOIN LATERAL (
                    SELECT event_type, event_date, location
                    FROM tracking_events
                    WHERE numero_suivi = r.numero_suivi
                    ORDER BY event_date DESC
                    LIMIT 1
                ) te ON true
                WHERE r.is_archived = false
                ORDER BY r.submitted_at DESC
                LIMIT :limit
            """)
            results = await run_db_query(query, {"limit": limit})

        reclamations = []
        for row in results:
            recl = dict(row._mapping)
            uuid_id = str(recl['id'])
            # Convert non-serializable types
            for key, value in recl.items():
                if hasattr(value, 'isoformat'):
                    recl[key] = value.isoformat()
                elif hasattr(value, '__float__'):
                    recl[key] = float(value)
            recl['id'] = uuid_id
            recl['has_document'] = bool(recl.get('document_path'))
            recl.pop('document_path', None)
            reclamations.append(recl)

        logger.info(f"Found {len(reclamations)} reclamations")

        return json.dumps({
            "success": True,
            "reclamations": reclamations,
            "total_found": len(reclamations),
            "filter": {"status": status, "limit": limit}
        }, default=str)

    except Exception as e:
        logger.error(f"Error listing reclamations: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_reclamation(reclamation_id: str) -> str:
    """
    Get detailed information about a specific reclamation.

    Returns: reclamation fields (number, type, status, dates, has_document), user info
    (name, email, phone, address), latest tracking events, existing AI decision,
    and processing logs.

    Args:
        reclamation_id: The reclamation number (e.g., RECL-2024-0001) or UUID

    Returns:
        JSON with keys: reclamation, tracking_events, decision, processing_logs
    """
    logger.info(f"Getting reclamation details: {reclamation_id}")

    if not reclamation_id or not reclamation_id.strip():
        return json.dumps({"success": False, "error": "reclamation_id is required"})

    reclamation_id = reclamation_id.strip()

    try:
        # Get reclamation -- try reclamation_number first, fallback to UUID
        base_query = """
            SELECT
                r.id, r.reclamation_number, r.numero_suivi, r.reclamation_type,
                r.client_nom, r.client_email, r.client_telephone,
                r.description, r.valeur_declaree,
                r.document_path, r.status,
                r.submitted_at, r.processed_at,
                r.total_processing_time_ms, r.metadata
            FROM reclamations r
        """
        result = await run_db_query_one(
            text(base_query + " WHERE r.reclamation_number = :reclamation_id"),
            {"reclamation_id": reclamation_id},
        )
        if not result:
            # Fallback: try as UUID
            try:
                result = await run_db_query_one(
                    text(base_query + " WHERE r.id = :reclamation_id::uuid"),
                    {"reclamation_id": reclamation_id},
                )
            except Exception:
                pass  # Not a valid UUID, ignore

        if not result:
            return json.dumps({"success": False, "error": f"Reclamation {reclamation_id} not found"})

        recl = dict(result._mapping)
        recl_uuid = recl['id']
        uuid_str = str(recl['id'])
        recl['id'] = uuid_str

        # Convert types
        for key, value in recl.items():
            if hasattr(value, 'isoformat'):
                recl[key] = value.isoformat()

        # Document availability flag (document_path is internal, not exposed to LLM)
        recl['has_document'] = bool(recl.get('document_path'))
        recl.pop('document_path', None)

        # Get tracking events (linked via numero_suivi)
        numero_suivi = recl.get('numero_suivi', '')
        tracking_query = text("""
            SELECT event_type::text AS event_type, event_date, location, detail,
                   code_postal, is_final
            FROM tracking_events
            WHERE numero_suivi = :numero_suivi
            ORDER BY event_date DESC
            LIMIT 20
        """)
        tracking_results = await run_db_query(tracking_query, {"numero_suivi": numero_suivi})

        tracking = []
        for row in tracking_results:
            evt = dict(row._mapping)
            for key, value in evt.items():
                if hasattr(value, 'isoformat'):
                    evt[key] = value.isoformat()
            tracking.append(evt)

        # Get decision
        decision_query = text("""
            SELECT decision, confidence, reasoning, llm_model, decided_at,
                   initial_decision, initial_confidence, initial_reasoning,
                   final_decision, final_decision_by_name, final_decision_at, final_decision_notes
            FROM reclamation_decisions
            WHERE reclamation_id = :recl_uuid
        """)
        decision_result = await run_db_query_one(decision_query, {"recl_uuid": recl_uuid})

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
            FROM reclamation_processing_logs
            WHERE reclamation_id = :recl_uuid
            ORDER BY started_at ASC
        """)
        logs_results = await run_db_query(logs_query, {"recl_uuid": recl_uuid})

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
            "reclamation": recl,
            "tracking_events": tracking,
            "decision": decision,
            "processing_logs": logs
        }, default=str)

    except Exception as e:
        logger.error(f"Error getting reclamation: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_reclamation_documents(reclamation_id: str) -> str:
    """
    Get documents associated with a reclamation, including their OCR text.

    Returns the list of documents with their raw OCR text (truncated to 1000 chars),
    structured data, confidence score, and file metadata (file_path, mime_type, size).

    Args:
        reclamation_id: The reclamation number (e.g., RECL-2024-0001) or UUID

    Returns:
        JSON with keys: reclamation_number, documents (list), total_documents
    """
    logger.info(f"Getting documents for reclamation: {reclamation_id}")

    if not reclamation_id or not reclamation_id.strip():
        return json.dumps({"success": False, "error": "reclamation_id is required"})

    try:
        cid = reclamation_id.strip()
        base_query = """
            SELECT
                rd.id, rd.document_type, rd.file_path, rd.file_size_bytes,
                rd.mime_type, rd.raw_ocr_text, rd.structured_data,
                rd.ocr_confidence, rd.ocr_processed_at, rd.page_count,
                rd.language
            FROM reclamation_documents rd
            JOIN reclamations r ON rd.reclamation_id = r.id
        """
        results = await run_db_query(
            text(base_query + " WHERE r.reclamation_number = :reclamation_id"), {"reclamation_id": cid}
        )
        if not results:
            try:
                results = await run_db_query(
                    text(base_query + " WHERE r.id = :reclamation_id::uuid"), {"reclamation_id": cid}
                )
            except Exception:
                results = []

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
            "reclamation_number": reclamation_id.strip(),
            "documents": documents,
            "total_documents": len(documents)
        }, default=str)

    except Exception as e:
        logger.error(f"Error getting reclamation documents: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def get_reclamation_statistics() -> str:
    """
    Get aggregate statistics about all reclamations.

    Returns:
        JSON string with reclamation statistics (counts by status, by type, etc.)
    """
    logger.info("Getting reclamation statistics")

    try:
        # Count by status
        status_query = text("""
            SELECT status, COUNT(*) as count
            FROM reclamations
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

        # Count by type
        type_query = text("""
            SELECT reclamation_type, COUNT(*) as count
            FROM reclamations
            WHERE is_archived = false
            GROUP BY reclamation_type
            ORDER BY count DESC
        """)
        type_results = await run_db_query(type_query, {})

        type_counts = {}
        for row in type_results:
            type_counts[row.reclamation_type or "unknown"] = row.count

        # Average processing time
        avg_query = text("""
            SELECT
                AVG(total_processing_time_ms) as avg_processing_ms,
                MIN(total_processing_time_ms) as min_processing_ms,
                MAX(total_processing_time_ms) as max_processing_ms
            FROM reclamations
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
                rd.decision, COUNT(*) as count,
                AVG(rd.confidence) as avg_confidence
            FROM reclamation_decisions rd
            JOIN reclamations r ON rd.reclamation_id = r.id
            WHERE r.is_archived = false
            GROUP BY rd.decision
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
            "total_reclamations": total,
            "by_status": status_counts,
            "by_type": type_counts,
            "processing_time": processing_stats,
            "decisions": decisions
        }, default=str)

    except Exception as e:
        logger.error(f"Error getting reclamation statistics: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def analyze_reclamation(reclamation_id: str) -> str:
    """
    Retrieve everything needed to evaluate a reclamation in a single call.

    Returns: reclamation details (type, status, user name/email), the full OCR text
    extracted from the reclamation document (if available), tracking timeline
    (all events), and the existing AI decision (if one was already made).
    Use this instead of calling get_reclamation + get_reclamation_documents separately.

    Args:
        reclamation_id: The reclamation number (e.g., RECL-2024-0001) or UUID

    Returns:
        JSON with keys: reclamation, ocr_data (raw_text + structured_data + confidence),
        tracking_events (list), existing_decision (decision + confidence + reasoning)
    """
    logger.info(f"Analyzing reclamation: {reclamation_id}")

    if not reclamation_id or not reclamation_id.strip():
        return json.dumps({"success": False, "error": "reclamation_id is required"})

    reclamation_id = reclamation_id.strip()

    try:
        # Get reclamation -- try reclamation_number first, fallback to UUID
        base_query = """
            SELECT
                r.id, r.reclamation_number, r.numero_suivi, r.reclamation_type,
                r.client_nom, r.client_email,
                r.document_path, r.status,
                r.submitted_at, r.processed_at, r.metadata
            FROM reclamations r
        """
        recl_result = await run_db_query_one(
            text(base_query + " WHERE r.reclamation_number = :reclamation_id"),
            {"reclamation_id": reclamation_id},
        )
        if not recl_result:
            try:
                recl_result = await run_db_query_one(
                    text(base_query + " WHERE r.id = :reclamation_id::uuid"),
                    {"reclamation_id": reclamation_id},
                )
            except Exception:
                pass

        if not recl_result:
            return json.dumps({"success": False, "error": f"Reclamation {reclamation_id} not found"})

        recl = dict(recl_result._mapping)
        recl_uuid = recl['id']
        numero_suivi = recl.get('numero_suivi', '')

        # Get OCR text from documents
        doc_query = text("""
            SELECT raw_ocr_text, structured_data, ocr_confidence
            FROM reclamation_documents
            WHERE reclamation_id = :recl_uuid
        """)
        doc_result = await run_db_query_one(doc_query, {"recl_uuid": recl_uuid})

        ocr_data = None
        if doc_result:
            ocr_data = {
                "raw_text": doc_result.raw_ocr_text,
                "structured_data": doc_result.structured_data,
                "confidence": float(doc_result.ocr_confidence) if doc_result.ocr_confidence else None
            }

        # Get tracking events (full timeline, linked via numero_suivi)
        tracking_query = text("""
            SELECT event_type::text AS event_type, event_date, location, detail,
                   code_postal, is_final
            FROM tracking_events
            WHERE numero_suivi = :numero_suivi
            ORDER BY event_date ASC
        """)
        tracking_results = await run_db_query(tracking_query, {"numero_suivi": numero_suivi})

        tracking = []
        for row in tracking_results:
            evt = dict(row._mapping)
            for key, value in evt.items():
                if hasattr(value, 'isoformat'):
                    evt[key] = value.isoformat()
            tracking.append(evt)

        # Get existing decision if any
        decision_query = text("""
            SELECT decision, confidence, reasoning
            FROM reclamation_decisions
            WHERE reclamation_id = :recl_uuid
        """)
        decision_result = await run_db_query_one(decision_query, {"recl_uuid": recl_uuid})

        existing_decision = None
        if decision_result:
            existing_decision = {
                "decision": decision_result.decision,
                "confidence": float(decision_result.confidence) if decision_result.confidence else None,
                "reasoning": decision_result.reasoning
            }

        # Build comprehensive analysis data
        for key, value in recl.items():
            if hasattr(value, 'isoformat'):
                recl[key] = value.isoformat()
        recl['id'] = str(recl['id'])

        return json.dumps({
            "success": True,
            "reclamation": recl,
            "ocr_data": ocr_data,
            "tracking_events": tracking,
            "existing_decision": existing_decision,
            "analysis_ready": True
        }, default=str)

    except Exception as e:
        logger.error(f"Error analyzing reclamation: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


async def _generate_embedding(text_input: str) -> Optional[List[float]]:
    """Generate embedding via LlamaStack /v1/embeddings API. Returns None on failure."""
    if not text_input or not text_input.strip():
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{LLAMASTACK_ENDPOINT}/v1/embeddings",
                json={"model": EMBEDDING_MODEL, "input": text_input.strip()[:2000]},
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if data:
                return data[0].get("embedding")
    except Exception as e:
        logger.warning(f"Embedding generation failed (non-blocking): {e}")
    return None


@mcp.tool()
async def save_reclamation_decision(
    reclamation_id: str,
    recommendation: str,
    confidence: float,
    reasoning: str,
) -> str:
    """
    Save a reclamation decision (rembourser/reexpedier/rejeter/escalader),
    update reclamation status, and generate an embedding for future similarity search.

    Args:
        reclamation_id: The reclamation number (e.g., RECL-2024-0001)
        recommendation: Decision - "rembourser", "reexpedier", "rejeter", or "escalader"
        confidence: Confidence score between 0.0 and 1.0
        reasoning: Explanation of the decision

    Returns:
        JSON string with save result
    """
    import time as _time
    _start_time = _time.time()
    logger.info(f"Saving reclamation decision: {reclamation_id} -> {recommendation} ({confidence})")

    if not reclamation_id or not reclamation_id.strip():
        return json.dumps({"success": False, "error": "reclamation_id is required"})

    valid_recommendations = {"rembourser", "reexpedier", "rejeter", "escalader"}
    if recommendation not in valid_recommendations:
        return json.dumps({"success": False, "error": f"recommendation must be one of: {valid_recommendations}"})

    confidence = max(0.0, min(1.0, confidence))

    try:
        # Lookup reclamation by reclamation_number to get UUID
        recl_result = await run_db_query_one(
            text("SELECT id FROM reclamations WHERE reclamation_number = :rn"),
            {"rn": reclamation_id.strip()},
        )
        if not recl_result:
            return json.dumps({"success": False, "error": f"Reclamation {reclamation_id} not found"})

        recl_uuid = recl_result.id

        # Map recommendation to status
        status_map = {
            "rembourser": "completed",
            "reexpedier": "completed",
            "rejeter": "rejected",
            "escalader": "escalated",
        }
        new_status = status_map[recommendation]

        # DELETE any previous decision for this reclamation (avoid duplicates)
        await run_db_execute(
            text("DELETE FROM reclamation_decisions WHERE reclamation_id = :recl_uuid"),
            {"recl_uuid": recl_uuid},
        )

        # Get model name from LlamaStack (cached)
        llm_model = _get_llm_model_name()

        # INSERT into reclamation_decisions
        await run_db_execute(
            text("""
                INSERT INTO reclamation_decisions (
                    reclamation_id, initial_decision, initial_confidence, initial_reasoning,
                    initial_decided_at, decision, confidence, reasoning, llm_model,
                    requires_manual_review
                ) VALUES (
                    :recl_uuid, :recommendation, :confidence, :reasoning,
                    NOW(), :recommendation, :confidence, :reasoning, :llm_model,
                    :requires_review
                )
            """),
            {
                "recl_uuid": recl_uuid,
                "recommendation": recommendation,
                "confidence": confidence,
                "reasoning": reasoning,
                "llm_model": llm_model,
                "requires_review": recommendation == "escalader",
            },
        )

        # Generate embedding for the document if available
        embedding_status = "skipped"
        doc_result = await run_db_query_one(
            text("""
                SELECT rd.id, rd.raw_ocr_text, rd.embedding IS NOT NULL as has_embedding
                FROM reclamation_documents rd WHERE rd.reclamation_id = :rid
                ORDER BY rd.created_at DESC LIMIT 1
            """),
            {"rid": recl_uuid},
        )
        if doc_result and not doc_result.has_embedding and doc_result.raw_ocr_text:
            embedding = await _generate_embedding(doc_result.raw_ocr_text)
            if embedding:
                emb_str = '[' + ','.join(map(str, embedding)) + ']'
                await run_db_execute(
                    text("UPDATE reclamation_documents SET embedding = CAST(:emb AS vector) WHERE id = :doc_id"),
                    {"emb": emb_str, "doc_id": doc_result.id},
                )
                embedding_status = "created"
                logger.info(f"Embedding generated for {reclamation_id} (dim={len(embedding)})")
            else:
                embedding_status = "failed"
        elif doc_result and doc_result.has_embedding:
            embedding_status = "already_exists"

        # Compute actual processing time
        processing_time_ms = int((_time.time() - _start_time) * 1000)

        # UPDATE reclamation status and processed_at
        logger.info(f"Updating reclamation {reclamation_id} (uuid={recl_uuid}) status to '{new_status}'")
        rows_updated = await run_db_execute(
            text("""
                UPDATE reclamations SET
                    status = :status,
                    processed_at = NOW(),
                    total_processing_time_ms = :processing_time_ms
                WHERE id = :recl_uuid
            """),
            {"status": new_status, "recl_uuid": recl_uuid, "processing_time_ms": processing_time_ms},
        )
        logger.info(f"UPDATE reclamations: {rows_updated} row(s) affected for {reclamation_id}")
        logger.info(f"Decision saved for {reclamation_id}: {recommendation} (confidence={confidence}, embedding={embedding_status}, time={processing_time_ms}ms)")

        return json.dumps({
            "success": True,
            "reclamation_number": reclamation_id.strip(),
            "recommendation": recommendation,
            "confidence": confidence,
            "status": new_status,
            "embedding": embedding_status,
        })

    except Exception as e:
        logger.error(f"Error saving reclamation decision: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


# =============================================================================
# Health Check
# =============================================================================

async def health_check(request):
    """Health check endpoint for liveness/readiness probes."""
    health_status = {
        "status": "healthy",
        "service": "postal-server",
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
        "server_name": "postal-server",
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

    logger.info(f"Starting MCP Postal Server on {host}:{port}")
    logger.info(f"Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    logger.info("Tools: list_reclamations, get_reclamation, get_reclamation_documents, get_reclamation_statistics, analyze_reclamation, save_reclamation_decision")

    uvicorn.run(app, host=host, port=port)
