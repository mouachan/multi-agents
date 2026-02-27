"""
MCP Tenders Server - CRUD operations on tenders (Appels d'Offres) via PostgreSQL.

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


async def _get_llm_model_name() -> str:
    """Get the LLM model name from LlamaStack /v1/models, cached after first call."""
    global _cached_llm_model
    if _cached_llm_model:
        return _cached_llm_model
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{LLAMASTACK_ENDPOINT}/v1/models")
            resp.raise_for_status()
            models = resp.json().get("data", resp.json()) if isinstance(resp.json(), dict) else resp.json()
            if isinstance(models, list):
                for m in models:
                    identifier = m.get("identifier") or m.get("id") or ""
                    model_type = m.get("model_type") or m.get("type") or ""
                    if "embedding" not in identifier.lower() and model_type != "embedding":
                        import re
                        short = identifier.split("/")[-1] if "/" in identifier else identifier
                        _cached_llm_model = re.sub(r'-W\d+A\d+$', '', short)
                        return _cached_llm_model
    except Exception as e:
        logger.warning(f"Failed to query LlamaStack models: {e}")
    _cached_llm_model = os.getenv("LLAMASTACK_DEFAULT_MODEL", "unknown")
    return _cached_llm_model

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


# =============================================================================
# MCP Tools - Tenders CRUD
# =============================================================================

@mcp.tool()
async def list_tenders(
    status: Optional[str] = None,
    limit: int = 10
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
                    t.document_path,
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
                    t.document_path,
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
            uuid_id = str(tender['id'])
            tender['id'] = uuid_id
            for key, value in tender.items():
                if hasattr(value, 'isoformat'):
                    tender[key] = value.isoformat()
                elif hasattr(value, '__float__') and key != 'id':
                    tender[key] = float(value)
            tender['has_document'] = bool(tender.get('document_path'))
            tender.pop('document_path', None)
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

    Returns: tender fields (number, type, status, dates, has_document,
    metadata with titre/budget/region/maitre_ouvrage), existing AI decision
    (with risk_analysis, similar_references, historical analysis), and processing logs.
    If has_document is true, use ocr_document(document_id=tender_number) to extract text.

    Args:
        tender_id: The tender number (e.g., AO-2025-IDF-001)

    Returns:
        JSON with keys: tender, decision, processing_logs
    """
    logger.info(f"Getting tender details: {tender_id}")

    if not tender_id or not tender_id.strip():
        return json.dumps({"success": False, "error": "tender_id is required"})

    tender_id = tender_id.strip()

    try:
        # Get tender — try tender_number first, fallback to UUID
        base_query = """
            SELECT
                t.id, t.tender_number, t.entity_id, t.tender_type,
                t.document_path, t.status,
                t.submitted_at, t.processed_at,
                t.total_processing_time_ms, t.metadata
            FROM tenders t
        """
        result = await run_db_query_one(
            text(base_query + " WHERE t.tender_number = :tender_id"),
            {"tender_id": tender_id},
        )
        if not result:
            try:
                result = await run_db_query_one(
                    text(base_query + " WHERE t.id = :tender_id::uuid"),
                    {"tender_id": tender_id},
                )
            except Exception:
                pass

        if not result:
            return json.dumps({"success": False, "error": f"Tender {tender_id} not found"})

        tender = dict(result._mapping)
        tender_uuid = tender['id']
        uuid_str = str(tender['id'])
        tender['id'] = uuid_str

        for key, value in tender.items():
            if hasattr(value, 'isoformat'):
                tender[key] = value.isoformat()

        # Document availability flag (document_path is internal, not exposed to LLM)
        tender['has_document'] = bool(tender.get('document_path'))
        tender.pop('document_path', None)

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
    Get documents associated with a tender, including their OCR text.

    Returns the list of documents with their raw OCR text (truncated to 1000 chars),
    structured data, confidence score, and file metadata (file_path, mime_type, size).
    If no documents exist or OCR text is empty, use ocr_document(document_id=tender_number)
    to extract text first.

    Args:
        tender_id: The tender number (e.g., AO-2025-IDF-001)

    Returns:
        JSON with keys: tender_number, documents (list), total_documents
    """
    logger.info(f"Getting documents for tender: {tender_id}")

    if not tender_id or not tender_id.strip():
        return json.dumps({"success": False, "error": "tender_id is required"})

    try:
        tid = tender_id.strip()
        base_query = """
            SELECT
                td.id, td.document_type, td.file_path, td.file_size_bytes,
                td.mime_type, td.raw_ocr_text, td.structured_data,
                td.ocr_confidence, td.ocr_processed_at, td.page_count,
                td.language
            FROM tender_documents td
            JOIN tenders t ON td.tender_id = t.id
        """
        results = await run_db_query(
            text(base_query + " WHERE t.tender_number = :tender_id"),
            {"tender_id": tid},
        )
        if not results:
            try:
                results = await run_db_query(
                    text(base_query + " WHERE t.id = :tender_id::uuid"),
                    {"tender_id": tid},
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
    Retrieve everything needed to evaluate a tender (appel d'offres) in a single call.

    Returns: tender details (type, status, metadata with titre/budget/region/maitre_ouvrage),
    the full OCR text from tender documents (if available), and the existing AI decision
    (if one was already made). Use this instead of calling get_tender + get_tender_documents
    separately.

    Args:
        tender_id: The tender number (e.g., AO-2025-IDF-001)

    Returns:
        JSON with keys: tender, ocr_data (list of raw_text + structured_data + confidence
        per document), existing_decision (decision + confidence + reasoning + risk_analysis)
    """
    logger.info(f"Analyzing tender: {tender_id}")

    if not tender_id or not tender_id.strip():
        return json.dumps({"success": False, "error": "tender_id is required"})

    tender_id = tender_id.strip()

    try:
        # Get tender info — try tender_number first, fallback to UUID
        base_query = """
            SELECT
                t.id, t.tender_number, t.entity_id, t.tender_type,
                t.document_path, t.status,
                t.submitted_at, t.processed_at, t.metadata
            FROM tenders t
        """
        tender_result = await run_db_query_one(
            text(base_query + " WHERE t.tender_number = :tender_id"),
            {"tender_id": tender_id},
        )
        if not tender_result:
            try:
                tender_result = await run_db_query_one(
                    text(base_query + " WHERE t.id = :tender_id::uuid"),
                    {"tender_id": tender_id},
                )
            except Exception:
                pass

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
async def save_tender_decision(
    tender_id: str,
    recommendation: str,
    confidence: float,
    reasoning: str,
) -> str:
    """
    Save a tender Go/No-Go decision, update tender status,
    and generate an embedding for future similarity search.

    Args:
        tender_id: The tender number (e.g., AO-2025-IDF-001)
        recommendation: Decision - "go", "no_go", or "a_approfondir"
        confidence: Confidence score between 0.0 and 1.0
        reasoning: Explanation of the decision

    Returns:
        JSON string with save result
    """
    import time as _time
    _start_time = _time.time()
    logger.info(f"Saving tender decision: {tender_id} -> {recommendation} ({confidence})")

    if not tender_id or not tender_id.strip():
        return json.dumps({"success": False, "error": "tender_id is required"})

    valid_recommendations = {"go", "no_go", "a_approfondir"}
    if recommendation not in valid_recommendations:
        return json.dumps({"success": False, "error": f"recommendation must be one of: {valid_recommendations}"})

    confidence = max(0.0, min(1.0, confidence))

    try:
        # Lookup tender by tender_number to get UUID
        tender_result = await run_db_query_one(
            text("SELECT id FROM tenders WHERE tender_number = :tn"),
            {"tn": tender_id.strip()},
        )
        if not tender_result:
            return json.dumps({"success": False, "error": f"Tender {tender_id} not found"})

        tender_uuid = tender_result.id

        # Map recommendation to status
        status_map = {"go": "completed", "no_go": "failed", "a_approfondir": "manual_review"}
        new_status = status_map[recommendation]

        # DELETE existing decision to avoid duplicates
        await run_db_execute(
            text("DELETE FROM tender_decisions WHERE tender_id = :tender_uuid"),
            {"tender_uuid": tender_uuid},
        )

        # Get model name from LlamaStack (cached)
        llm_model = await _get_llm_model_name()

        # INSERT into tender_decisions
        await run_db_execute(
            text("""
                INSERT INTO tender_decisions (
                    tender_id, initial_decision, initial_confidence, initial_reasoning,
                    initial_decided_at, decision, confidence, reasoning, llm_model,
                    requires_manual_review
                ) VALUES (
                    :tender_uuid, :recommendation, :confidence, :reasoning,
                    NOW(), :recommendation, :confidence, :reasoning, :llm_model,
                    :requires_review
                )
            """),
            {
                "tender_uuid": tender_uuid,
                "recommendation": recommendation,
                "confidence": confidence,
                "reasoning": reasoning,
                "llm_model": llm_model,
                "requires_review": recommendation == "a_approfondir",
            },
        )

        # Build processing steps with real data from DB
        steps = []

        # 1. OCR step - get real OCR data if available
        ocr_result = await run_db_query_one(
            text("""
                SELECT raw_ocr_text, structured_data, ocr_confidence,
                       page_count, language
                FROM tender_documents WHERE tender_id = :tid
                ORDER BY created_at DESC LIMIT 1
            """),
            {"tid": tender_uuid},
        )
        if ocr_result and ocr_result.raw_ocr_text:
            ocr_output = {
                "success": True,
                "raw_text": ocr_result.raw_ocr_text[:2000],
                "structured_data": ocr_result.structured_data or {},
                "confidence": float(ocr_result.ocr_confidence) if ocr_result.ocr_confidence else None,
                "pages_processed": ocr_result.page_count or 1,
            }
            steps.append({"step_name": "ocr_document", "agent_name": "ocr-agent", "status": "completed",
                          "output_data": ocr_output})
        else:
            steps.append({"step_name": "ocr_document", "agent_name": "ocr-agent", "status": "completed",
                          "output_data": {"description": "Document OCR extraction"}})

        # 2. Ensure embedding exists BEFORE querying similar references/tenders
        embedding_status = "skipped"
        doc_result = await run_db_query_one(
            text("""
                SELECT td.id, td.raw_ocr_text, td.embedding IS NOT NULL as has_embedding
                FROM tender_documents td WHERE td.tender_id = :tid
                ORDER BY td.created_at DESC LIMIT 1
            """),
            {"tid": tender_uuid},
        )
        if doc_result and not doc_result.has_embedding and doc_result.raw_ocr_text:
            embedding = await _generate_embedding(doc_result.raw_ocr_text)
            if embedding:
                emb_str = '[' + ','.join(map(str, embedding)) + ']'
                await run_db_execute(
                    text("UPDATE tender_documents SET embedding = CAST(:emb AS vector) WHERE id = :doc_id"),
                    {"emb": emb_str, "doc_id": doc_result.id},
                )
                embedding_status = "created"
                logger.info(f"Embedding generated for {tender_id} (dim={len(embedding)})")
            else:
                embedding_status = "failed"
        elif doc_result and doc_result.has_embedding:
            embedding_status = "already_exists"

        # 3. Similar references step - embedding now guaranteed
        try:
            ref_results = await run_db_query(
                text("""
                    SELECT project_name, maitre_ouvrage, nature_travaux,
                           montant, region, description,
                           doc.embedding <=> tdoc.embedding AS distance
                    FROM company_references cr
                    JOIN company_reference_documents crd ON cr.id = crd.reference_id
                    JOIN tender_documents tdoc ON tdoc.tender_id = :tid
                    JOIN company_reference_documents doc ON doc.reference_id = cr.id
                    WHERE tdoc.embedding IS NOT NULL AND doc.embedding IS NOT NULL
                    ORDER BY doc.embedding <=> tdoc.embedding
                    LIMIT 5
                """),
                {"tid": tender_uuid},
            )
            if ref_results:
                refs = []
                for r in ref_results:
                    rd = dict(r._mapping)
                    rd["similarity"] = round(1 - float(rd.pop("distance", 1)), 3)
                    if rd.get("montant"):
                        rd["montant"] = float(rd["montant"])
                    refs.append(rd)
                steps.append({"step_name": "retrieve_similar_references", "agent_name": "rag-agent", "status": "completed",
                              "output_data": {"success": True, "references": refs, "total_found": len(refs)}})
        except Exception as e:
            logger.debug(f"Could not query company_references: {e}")

        # 4. Historical tenders step
        try:
            hist_results = await run_db_query(
                text("""
                    SELECT ao_number, nature_travaux, montant_estime, region,
                           resultat, raison_resultat, note_technique, note_prix,
                           doc.embedding <=> tdoc.embedding AS distance
                    FROM historical_tenders ht
                    JOIN historical_tender_documents doc ON doc.tender_id = ht.id
                    JOIN tender_documents tdoc ON tdoc.tender_id = :tid
                    WHERE tdoc.embedding IS NOT NULL AND doc.embedding IS NOT NULL
                    ORDER BY doc.embedding <=> tdoc.embedding
                    LIMIT 5
                """),
                {"tid": tender_uuid},
            )
            if hist_results:
                hists = []
                won = 0
                for h in hist_results:
                    hd = dict(h._mapping)
                    hd["similarity"] = round(1 - float(hd.pop("distance", 1)), 3)
                    if hd.get("montant_estime"):
                        hd["montant_estime"] = float(hd["montant_estime"])
                    if hd.get("note_technique"):
                        hd["note_technique"] = float(hd["note_technique"])
                    if hd.get("note_prix"):
                        hd["note_prix"] = float(hd["note_prix"])
                    if hd.get("resultat") == "gagne":
                        won += 1
                    hists.append(hd)
                win_rate = (won / len(hists) * 100) if hists else 0
                steps.append({"step_name": "retrieve_historical_tenders", "agent_name": "rag-agent", "status": "completed",
                              "output_data": {"success": True, "historical_tenders": hists,
                                              "total_found": len(hists), "win_rate_percentage": win_rate}})
        except Exception as e:
            logger.debug(f"Could not query historical_tenders: {e}")

        # 5. Capabilities step
        try:
            cap_results = await run_db_query(
                text("""
                    SELECT name, category, valid_until, region, availability
                    FROM company_capabilities
                    ORDER BY created_at DESC LIMIT 10
                """),
                {},
            )
            if cap_results:
                caps = []
                for c in cap_results:
                    cd = dict(c._mapping)
                    for k, v in cd.items():
                        if hasattr(v, 'isoformat'):
                            cd[k] = v.isoformat()
                    caps.append(cd)
                categories = list(set(c.get("category", "autre") for c in caps))
                steps.append({"step_name": "retrieve_capabilities", "agent_name": "rag-agent", "status": "completed",
                              "output_data": {"success": True, "capabilities": caps,
                                              "total_found": len(caps), "categories_found": categories}})
        except Exception as e:
            logger.debug(f"Could not query company_capabilities: {e}")

        # 6. Decision step
        steps.append({"step_name": "decision", "agent_name": "tenders", "status": "completed",
                       "output_data": {"recommendation": recommendation, "confidence": confidence,
                                       "reasoning": reasoning[:500]}})

        processing_steps = json.dumps(steps)

        # Compute actual processing time
        processing_time_ms = int((_time.time() - _start_time) * 1000)

        # UPDATE tender status, processed_at, and processing steps in metadata
        logger.info(f"Updating tender {tender_id} (uuid={tender_uuid}) status to '{new_status}'")
        rows_updated = await run_db_execute(
            text("""
                UPDATE tenders SET
                    status = :status,
                    processed_at = NOW(),
                    total_processing_time_ms = :processing_time_ms,
                    metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('processing_steps', CAST(:steps AS jsonb))
                WHERE id = :tender_uuid
            """),
            {"status": new_status, "tender_uuid": tender_uuid, "steps": processing_steps,
             "processing_time_ms": processing_time_ms},
        )
        logger.info(f"UPDATE tenders: {rows_updated} row(s) affected for {tender_id}")
        logger.info(f"Decision saved for {tender_id}: {recommendation} (confidence={confidence}, embedding={embedding_status}, time={processing_time_ms}ms)")

        return json.dumps({
            "success": True,
            "tender_number": tender_id.strip(),
            "recommendation": recommendation,
            "confidence": confidence,
            "status": new_status,
            "embedding": embedding_status,
        })

    except Exception as e:
        logger.error(f"Error saving tender decision: {e}", exc_info=True)
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
    logger.info("Tools: list_tenders, get_tender, get_tender_documents, get_tender_statistics, analyze_tender, save_tender_decision")

    uvicorn.run(app, host=host, port=port)
