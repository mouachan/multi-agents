"""
MCP Claims Server - CRUD operations on insurance claims via PostgreSQL.

Includes decision persistence with automatic embedding generation.
FastMCP server exposing Streamable HTTP (/mcp) and legacy SSE (/sse).
"""

import json
import logging
import os
import re
from typing import List, Optional, Tuple

from sqlalchemy import text
from starlette.responses import JSONResponse

from shared.db import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB,
    check_database_connection, run_db_query, run_db_query_one, run_db_execute,
)
from shared.mcp_app import build_app, create_mcp
from shared.ogx import generate_embedding, get_llm_model_name

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = create_mcp("claims-server")


# =============================================================================
# MCP Tools - Claims CRUD
# =============================================================================

@mcp.tool()
async def list_claims(
    status: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    List insurance claims with optional status filter.

    Args:
        status: Optional status filter (pending, processing, completed, failed, manual_review)
        limit: Maximum number of claims to return (default: 10)

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
                    c.document_path,
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
                    c.document_path,
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
            uuid_id = str(claim['id'])
            # Convert non-serializable types
            for key, value in claim.items():
                if hasattr(value, 'isoformat'):
                    claim[key] = value.isoformat()
                elif hasattr(value, '__float__'):
                    claim[key] = float(value)
            claim['id'] = uuid_id
            claim['has_document'] = bool(claim.get('document_path'))
            claim.pop('document_path', None)
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

    Returns: claim fields (number, type, status, dates, has_document), claimant info
    (name, email, phone, address), existing AI decision, and processing logs.
    If has_document is true, use ocr_document(document_id=claim_number) to extract text.

    Args:
        claim_id: The claim number (e.g., CLM-2024-0001)

    Returns:
        JSON with keys: claim, decision, processing_logs
    """
    logger.info(f"Getting claim details: {claim_id}")

    if not claim_id or not claim_id.strip():
        return json.dumps({"success": False, "error": "claim_id is required"})

    claim_id = claim_id.strip()

    try:
        # Get claim with user info — try claim_number first, fallback to UUID
        base_query = """
            SELECT
                c.id, c.claim_number, c.user_id, c.claim_type,
                c.document_path, c.status::text as status,
                c.submitted_at, c.processed_at,
                c.total_processing_time_ms, c.metadata,
                u.full_name as user_name, u.email as user_email,
                u.phone_number as user_phone, u.address as user_address
            FROM claims c
            LEFT JOIN users u ON c.user_id = u.user_id
        """
        result = await run_db_query_one(
            text(base_query + " WHERE c.claim_number = :claim_id"),
            {"claim_id": claim_id},
        )
        if not result:
            # Fallback: try as UUID
            try:
                result = await run_db_query_one(
                    text(base_query + " WHERE c.id = :claim_id::uuid"),
                    {"claim_id": claim_id},
                )
            except Exception:
                pass  # Not a valid UUID, ignore

        if not result:
            return json.dumps({"success": False, "error": f"Claim {claim_id} not found"})

        claim = dict(result._mapping)
        claim_uuid = claim['id']
        uuid_str = str(claim['id'])
        claim['id'] = uuid_str

        # Convert types
        for key, value in claim.items():
            if hasattr(value, 'isoformat'):
                claim[key] = value.isoformat()

        # Document availability flag (document_path is internal, not exposed to LLM)
        claim['has_document'] = bool(claim.get('document_path'))
        claim.pop('document_path', None)

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
    Get documents associated with a claim, including their OCR text.

    Returns the list of documents with their raw OCR text (truncated to 1000 chars),
    structured data, confidence score, and file metadata (file_path, mime_type, size).
    If no documents exist or OCR text is empty, use ocr_document(document_id=claim_number)
    to extract text first.

    Args:
        claim_id: The claim number (e.g., CLM-2024-0001)

    Returns:
        JSON with keys: claim_number, documents (list), total_documents
    """
    logger.info(f"Getting documents for claim: {claim_id}")

    if not claim_id or not claim_id.strip():
        return json.dumps({"success": False, "error": "claim_id is required"})

    try:
        cid = claim_id.strip()
        base_query = """
            SELECT
                cd.id, cd.document_type, cd.file_path, cd.file_size_bytes,
                cd.mime_type, cd.raw_ocr_text, cd.structured_data,
                cd.ocr_confidence, cd.ocr_processed_at, cd.page_count,
                cd.language
            FROM claim_documents cd
            JOIN claims c ON cd.claim_id = c.id
        """
        results = await run_db_query(
            text(base_query + " WHERE c.claim_number = :claim_id"), {"claim_id": cid}
        )
        if not results:
            try:
                results = await run_db_query(
                    text(base_query + " WHERE c.id = :claim_id::uuid"), {"claim_id": cid}
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
    Retrieve everything needed to evaluate a claim in a single call.

    Returns: claim details (type, status, claimant name/email), the full OCR text
    extracted from the claim document (if available), the claimant's active insurance
    contracts (coverage amounts, key terms, exclusions), and the existing AI decision
    (if one was already made). Use this instead of calling get_claim + get_claim_documents
    + retrieve_user_info separately.

    Args:
        claim_id: The claim number (e.g., CLM-2024-0001)

    Returns:
        JSON with keys: claim, ocr_data (raw_text + structured_data + confidence),
        user_contracts (list), existing_decision (decision + confidence + reasoning)
    """
    logger.info(f"Analyzing claim: {claim_id}")

    if not claim_id or not claim_id.strip():
        return json.dumps({"success": False, "error": "claim_id is required"})

    claim_id = claim_id.strip()

    try:
        # Get claim with user info — try claim_number first, fallback to UUID
        base_query = """
            SELECT
                c.id, c.claim_number, c.user_id, c.claim_type,
                c.document_path, c.status::text as status,
                c.submitted_at, c.processed_at, c.metadata,
                u.full_name as user_name, u.email as user_email
            FROM claims c
            LEFT JOIN users u ON c.user_id = u.user_id
        """
        claim_result = await run_db_query_one(
            text(base_query + " WHERE c.claim_number = :claim_id"),
            {"claim_id": claim_id},
        )
        if not claim_result:
            try:
                claim_result = await run_db_query_one(
                    text(base_query + " WHERE c.id = :claim_id::uuid"),
                    {"claim_id": claim_id},
                )
            except Exception:
                pass

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
# MCP Tools - Payout, computed in the OpenShell sandbox
# =============================================================================

# run_python tool of the sandbox MCP server (OpenShell); empty when the sandbox is not deployed
SANDBOX_MCP_URL = os.getenv("SANDBOX_MCP_URL", "")
# Claim type -> contract type that covers it
COVERING_CONTRACT = {
    "Auto": "Auto Insurance", "Home": "Home Insurance",
    "Medical": "Health Insurance", "Life": "Life Insurance",
}
# Amount labels of the claim documents, most specific first
AMOUNT_LABELS = ("Amount Claimed", "Estimated Repair Cost", "Capital Assur[eé]", "Total Charges")
AMOUNT = r"\s*:?\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)"
FORMULA = "payout = min(max(claimed - franchise, 0), ceiling); 0 without an active contract of the claim type"


def _claimed_amount(document_text: str) -> Tuple[Optional[float], Optional[str]]:
    """Amount claimed in the OCR text of the claim document, with the label it was read from."""
    for label in AMOUNT_LABELS:
        match = re.search(label + AMOUNT, document_text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", "")), match.group(0).split(":")[0].strip()
    return None, None


async def _payout_inputs(claim_number: str) -> dict:
    """Exact figures of a claim for its payout, and the code computing it."""
    claim = await run_db_query_one(text("""
        SELECT c.claim_number, c.claim_type, c.user_id,
               (SELECT cd.raw_ocr_text FROM claim_documents cd WHERE cd.claim_id = c.id
                AND cd.raw_ocr_text IS NOT NULL ORDER BY cd.created_at DESC LIMIT 1) AS document_text
        FROM claims c WHERE c.claim_number = :n
    """), {"n": claim_number})
    if not claim:
        return {"success": False, "error": f"Claim {claim_number} not found"}
    if claim.document_text is None:
        return {"success": False, "claim_number": claim.claim_number,
                "error": "No OCR text for this claim: call ocr_document first"}
    claimed, source = _claimed_amount(claim.document_text)
    contract_type = COVERING_CONTRACT.get(claim.claim_type)
    contract = await run_db_query_one(text("""
        SELECT contract_number, contract_type, coverage_amount, key_terms->>'franchise' AS franchise
        FROM user_contracts WHERE user_id = :u AND is_active AND contract_type = :t
        ORDER BY coverage_amount DESC LIMIT 1
    """), {"u": claim.user_id, "t": contract_type}) if contract_type else None

    covered = contract is not None
    deductible = float(contract.franchise or 0) if covered else 0.0
    ceiling = float(contract.coverage_amount) if covered else 0.0
    number = contract.contract_number if covered else "NONE"
    code = "\n".join([
        f"claim_type = '{claim.claim_type}'",
        f"contract = '{number}'",
        f"claimed = {claimed if claimed is not None else 0.0}",
        f"deductible = {deductible}",
        f"ceiling = {ceiling}",
        f"covered = {covered}",
        "payout = min(max(claimed - deductible, 0), ceiling) if covered else 0.0",
        *[f"print('{name}:', {name})" for name in ("claim_type", "contract", "claimed", "deductible", "ceiling", "payout")],
    ])
    return {
        "success": True,
        "claim_number": claim.claim_number,
        "claim_type": claim.claim_type,
        "covered": covered,
        "contract": {"number": number, "type": contract.contract_type, "coverage_amount": ceiling,
                     "franchise": deductible} if covered else None,
        "claimed_amount": claimed,
        "claimed_source": f"{source} (claim document)" if source else "not found in the claim document",
        "formula": FORMULA,
        "code": code,
    }


async def _run_in_sandbox(code: str) -> dict:
    """Execute code with the run_python tool of the sandbox MCP server."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(SANDBOX_MCP_URL, timeout=90) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("run_python", {"code": code, "timeout_s": 20})
            return json.loads(result.content[0].text)


def _printed_value(stdout: str, name: str) -> Optional[float]:
    match = re.search(rf"^{name}:\s*([-0-9.]+)\s*$", stdout or "", re.MULTILINE)
    return float(match.group(1)) if match else None


@mcp.tool()
async def compute_payout(claim_id: str) -> str:
    """
    Compute the payout of a claim (coverage check and amount) in the OpenShell sandbox.

    Reads the claim type, the claimant's ACTIVE contract matching that type (coverage
    ceiling, franchise) and the amount claimed in the claim document (OCR text: call
    ocr_document first if it is missing). The computation runs in an isolated OpenShell
    sandbox (no network, kernel-enforced policy). Report the returned figures as they are.

    Args:
        claim_id: The claim number (e.g., CLM-2024-0001)

    Returns:
        JSON with keys: claim_number, claim_type, covered, contract (number, type,
        coverage_amount, franchise) or null, claimed_amount, claimed_source, formula,
        payout, code, sandbox_run (exit code, output, sandbox name and timings)
    """
    if not claim_id or not claim_id.strip():
        return json.dumps({"success": False, "error": "claim_id is required"})
    try:
        inputs = await _payout_inputs(claim_id.strip())
    except Exception as e:
        logger.error(f"Error reading payout inputs for {claim_id}: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})
    if not inputs["success"]:
        return json.dumps(inputs)
    if not SANDBOX_MCP_URL:
        return json.dumps({**inputs, "success": False, "error": "The OpenShell sandbox is not deployed"})
    try:
        run = await _run_in_sandbox(inputs["code"])
    except Exception as e:
        logger.error(f"Sandbox execution failed for {claim_id}: {e}", exc_info=True)
        return json.dumps({**inputs, "success": False, "error": f"Sandbox execution failed: {e}"})
    payout = _printed_value(run.get("stdout", ""), "payout")
    logger.info(f"Payout of {claim_id}: {payout} (covered={inputs['covered']}, sandbox exit {run.get('exit_code')})")
    return json.dumps({**inputs, "success": bool(run.get("success")) and payout is not None,
                       "payout": payout, "sandbox_run": run})


@mcp.tool()
async def save_claim_decision(
    claim_id: str,
    recommendation: str,
    confidence: float,
    reasoning: str,
) -> str:
    """
    Save a claim decision (approve/deny/manual_review), update claim status,
    and generate an embedding for future similarity search.

    Args:
        claim_id: The claim number (e.g., CLM-2024-0001)
        recommendation: Decision - "approve", "deny", or "manual_review"
        confidence: Confidence score between 0.0 and 1.0
        reasoning: Explanation of the decision

    Returns:
        JSON string with save result
    """
    import time as _time
    _start_time = _time.time()
    logger.info(f"Saving claim decision: {claim_id} -> {recommendation} ({confidence})")

    if not claim_id or not claim_id.strip():
        return json.dumps({"success": False, "error": "claim_id is required"})

    valid_recommendations = {"approve", "deny", "manual_review"}
    if recommendation not in valid_recommendations:
        return json.dumps({"success": False, "error": f"recommendation must be one of: {valid_recommendations}"})

    confidence = max(0.0, min(1.0, confidence))

    try:
        # Lookup claim by claim_number to get UUID
        claim_result = await run_db_query_one(
            text("SELECT id FROM claims WHERE claim_number = :cn"),
            {"cn": claim_id.strip()},
        )
        if not claim_result:
            return json.dumps({"success": False, "error": f"Claim {claim_id} not found"})

        claim_uuid = claim_result.id

        # Map recommendation to status
        status_map = {"approve": "completed", "deny": "denied", "manual_review": "manual_review"}
        new_status = status_map[recommendation]

        # DELETE any previous decision for this claim (avoid duplicates)
        await run_db_execute(
            text("DELETE FROM claim_decisions WHERE claim_id = :claim_uuid"),
            {"claim_uuid": claim_uuid},
        )

        # Reasoning model name (OGX_DEFAULT_MODEL)
        llm_model = get_llm_model_name()

        # INSERT into claim_decisions
        await run_db_execute(
            text("""
                INSERT INTO claim_decisions (
                    claim_id, initial_decision, initial_confidence, initial_reasoning,
                    initial_decided_at, decision, confidence, reasoning, llm_model,
                    requires_manual_review
                ) VALUES (
                    :claim_uuid, :recommendation, :confidence, :reasoning,
                    NOW(), :recommendation, :confidence, :reasoning, :llm_model,
                    :requires_review
                )
            """),
            {
                "claim_uuid": claim_uuid,
                "recommendation": recommendation,
                "confidence": confidence,
                "reasoning": reasoning,
                "llm_model": llm_model,
                "requires_review": recommendation == "manual_review",
            },
        )

        # Build processing steps with real data from DB
        steps = []

        # 1. OCR step - get real OCR data if available
        ocr_result = await run_db_query_one(
            text("""
                SELECT raw_ocr_text, structured_data, ocr_confidence,
                       page_count, language
                FROM claim_documents WHERE claim_id = :cid
                ORDER BY created_at DESC LIMIT 1
            """),
            {"cid": claim_uuid},
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

        # 2. User info step - get user data and contracts
        user_result = await run_db_query_one(
            text("""
                SELECT c.user_id, u.full_name, u.email, u.phone_number, u.date_of_birth
                FROM claims c LEFT JOIN users u ON c.user_id = u.user_id
                WHERE c.id = :cid
            """),
            {"cid": claim_uuid},
        )
        if user_result and user_result.full_name:
            contracts_results = await run_db_query(
                text("""
                    SELECT contract_number, contract_type, coverage_amount, is_active
                    FROM user_contracts WHERE user_id = :uid AND is_active = true
                """),
                {"uid": user_result.user_id},
            )
            contracts = []
            for cr in contracts_results:
                c = dict(cr._mapping)
                if c.get("coverage_amount"):
                    c["coverage_amount"] = float(c["coverage_amount"])
                contracts.append(c)

            steps.append({"step_name": "retrieve_user_info", "agent_name": "rag-agent", "status": "completed",
                          "output_data": {
                              "success": True,
                              "user_info": {
                                  "user_id": user_result.user_id,
                                  "full_name": user_result.full_name,
                                  "email": user_result.email,
                              },
                              "contracts": contracts,
                          }})

        # 3. Ensure embedding exists BEFORE querying similar claims
        embedding_status = "skipped"
        doc_result = await run_db_query_one(
            text("""
                SELECT cd.id, cd.raw_ocr_text, cd.embedding IS NOT NULL as has_embedding
                FROM claim_documents cd WHERE cd.claim_id = :cid
                ORDER BY cd.created_at DESC LIMIT 1
            """),
            {"cid": claim_uuid},
        )
        if doc_result and not doc_result.has_embedding and doc_result.raw_ocr_text:
            embedding = await generate_embedding(doc_result.raw_ocr_text)
            if embedding:
                emb_str = '[' + ','.join(map(str, embedding)) + ']'
                await run_db_execute(
                    text("UPDATE claim_documents SET embedding = CAST(:emb AS vector) WHERE id = :doc_id"),
                    {"emb": emb_str, "doc_id": doc_result.id},
                )
                embedding_status = "created"
                logger.info(f"Embedding generated for {claim_id} (dim={len(embedding)})")
            else:
                embedding_status = "failed"
        elif doc_result and doc_result.has_embedding:
            embedding_status = "already_exists"

        # 4. Similar claims step - now embedding is guaranteed to exist
        try:
            similar_result = await run_db_query(
                text("""
                    SELECT c.claim_number, c.claim_type, cd.decision, cd.confidence,
                           1 - (doc.embedding <=> doc2.embedding) AS similarity
                    FROM claim_documents doc
                    JOIN claim_documents doc2 ON doc2.claim_id = :cid
                    JOIN claims c ON doc.claim_id = c.id
                    LEFT JOIN claim_decisions cd ON cd.claim_id = c.id
                    WHERE doc.embedding IS NOT NULL AND doc2.embedding IS NOT NULL
                    AND doc.claim_id != :cid
                    AND c.status IN ('completed', 'manual_review', 'denied')
                    ORDER BY doc.embedding <=> doc2.embedding
                    LIMIT 5
                """),
                {"cid": claim_uuid},
            )
            if similar_result:
                similar_claims = []
                for r in similar_result:
                    sc = dict(r._mapping)
                    if sc.get("confidence"):
                        sc["confidence"] = float(sc["confidence"])
                    if sc.get("similarity"):
                        sc["similarity_score"] = round(float(sc.pop("similarity")), 3)
                    similar_claims.append(sc)
                steps.append({"step_name": "retrieve_similar_claims", "agent_name": "rag-agent", "status": "completed",
                              "output_data": {"success": True, "claims": similar_claims, "total_found": len(similar_claims)}})
        except Exception as e:
            logger.debug(f"Could not query similar claims: {e}")

        # 5. Decision step
        steps.append({"step_name": "decision", "agent_name": "claims", "status": "completed",
                       "output_data": {"recommendation": recommendation, "confidence": confidence,
                                       "reasoning": reasoning[:500]}})

        processing_steps = json.dumps(steps)

        # Compute actual processing time
        processing_time_ms = int((_time.time() - _start_time) * 1000)

        # UPDATE claim status, processed_at, and processing steps in metadata
        logger.info(f"Updating claim {claim_id} (uuid={claim_uuid}) status to '{new_status}'")
        rows_updated = await run_db_execute(
            text("""
                UPDATE claims SET
                    status = :status,
                    processed_at = NOW(),
                    total_processing_time_ms = :processing_time_ms,
                    metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('processing_steps', CAST(:steps AS jsonb))
                WHERE id = :claim_uuid
            """),
            {"status": new_status, "claim_uuid": claim_uuid, "steps": processing_steps,
             "processing_time_ms": processing_time_ms},
        )
        logger.info(f"UPDATE claims: {rows_updated} row(s) affected for {claim_id}")
        logger.info(f"Decision saved for {claim_id}: {recommendation} (confidence={confidence}, embedding={embedding_status}, time={processing_time_ms}ms)")

        return json.dumps({
            "success": True,
            "claim_number": claim_id.strip(),
            "recommendation": recommendation,
            "confidence": confidence,
            "status": new_status,
            "embedding": embedding_status,
        })

    except Exception as e:
        logger.error(f"Error saving claim decision: {e}", exc_info=True)
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


# =============================================================================
# Starlette App — /mcp (Streamable HTTP), /sse (legacy), /health
# =============================================================================

app = build_app(mcp, "claims-server", health_check)


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
    logger.info("Tools: list_claims, get_claim, get_claim_documents, get_claim_statistics, analyze_claim, save_claim_decision")

    uvicorn.run(app, host=host, port=port)
