#!/usr/bin/env python3
"""
Data initialization script for multi-agents platform.

Generates PDFs, uploads to LlamaStack, and processes 10 claims + 10 tenders
via MCP server tools (OCR + decision saving with embeddings).

Usage:
    python init_data.py

Environment variables:
    LLAMASTACK_ENDPOINT: LlamaStack API URL (default: http://llamastack:8321)
    OCR_SERVER_URL: OCR MCP server URL (default: http://ocr-server:8080)
    CLAIMS_SERVER_URL: Claims MCP server URL (default: http://claims-server:8080)
    TENDERS_SERVER_URL: Tenders MCP server URL (default: http://tenders-server:8080)
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE, POSTGRES_USER, POSTGRES_PASSWORD
"""

import asyncio
import json
import logging
import os
import sys
import time

import httpx
import psycopg2

# Add parent dir to path for init_data package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from init_data.decisions import CLAIM_DECISIONS, TENDER_DECISIONS
from init_data.pdf_generator import generate_all_pdfs

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("init_data")

# Configuration
LLAMASTACK_ENDPOINT = os.getenv("LLAMASTACK_ENDPOINT", "http://llamastack:8321")
OCR_SERVER_URL = os.getenv("OCR_SERVER_URL", "http://ocr-server:8080")
CLAIMS_SERVER_URL = os.getenv("CLAIMS_SERVER_URL", "http://claims-server:8080")
TENDERS_SERVER_URL = os.getenv("TENDERS_SERVER_URL", "http://tenders-server:8080")

PG_HOST = os.getenv("POSTGRES_HOST", "postgresql")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB = os.getenv("POSTGRES_DATABASE", "claims_db")
PG_USER = os.getenv("POSTGRES_USER", "claims_user")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "claims_pass")

MAX_RETRIES = 30
RETRY_INTERVAL = 5  # seconds


# ============================================================================
# Wait helpers
# ============================================================================

def get_pg_conn():
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB,
        user=PG_USER, password=PG_PASS,
    )


def wait_for_postgres():
    """Wait for PostgreSQL to be ready."""
    for i in range(MAX_RETRIES):
        try:
            conn = get_pg_conn()
            conn.close()
            logger.info("PostgreSQL is ready")
            return
        except Exception as e:
            logger.info(f"Waiting for PostgreSQL ({i + 1}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_INTERVAL)
    raise RuntimeError("PostgreSQL not available after retries")


async def wait_for_llamastack():
    """Wait for LlamaStack to be healthy."""
    for i in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{LLAMASTACK_ENDPOINT}/v1/health")
                if resp.status_code == 200:
                    logger.info("LlamaStack is ready")
                    return
        except Exception as e:
            logger.info(f"Waiting for LlamaStack ({i + 1}/{MAX_RETRIES}): {e}")
        await asyncio.sleep(RETRY_INTERVAL)
    raise RuntimeError("LlamaStack not available after retries")


async def wait_for_mcp_servers():
    """Wait for all MCP servers to be healthy."""
    servers = {
        "ocr-server": OCR_SERVER_URL,
        "claims-server": CLAIMS_SERVER_URL,
        "tenders-server": TENDERS_SERVER_URL,
    }
    for name, url in servers.items():
        for i in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(f"{url}/health")
                    if resp.status_code == 200:
                        logger.info(f"{name} is ready")
                        break
            except Exception as e:
                logger.info(f"Waiting for {name} ({i + 1}/{MAX_RETRIES}): {e}")
            await asyncio.sleep(RETRY_INTERVAL)
        else:
            raise RuntimeError(f"{name} not available after retries")


def check_already_initialized() -> bool:
    """Check if data init has already been run (idempotent)."""
    conn = get_pg_conn()
    try:
        cur = conn.cursor()
        # Check if any CLM-2024-* claim has been processed by data-init
        cur.execute(
            "SELECT COUNT(*) FROM claims WHERE claim_number LIKE 'CLM-2024-%%' AND status != 'pending'"
        )
        count = cur.fetchone()[0]
        if count > 0:
            logger.info(f"Data already initialized ({count} non-pending claims). Skipping.")
            return True
        return False
    finally:
        conn.close()


# ============================================================================
# Data loading from DB
# ============================================================================

def load_claims_data() -> list[dict]:
    """Load all claims with user info for PDF generation."""
    conn = get_pg_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.claim_number, c.claim_type, c.document_path, c.submitted_at,
                   u.full_name, u.address,
                   uc.contract_number
            FROM claims c
            LEFT JOIN users u ON c.user_id = u.user_id
            LEFT JOIN user_contracts uc ON c.user_id = uc.user_id
                AND uc.is_active = true
            ORDER BY c.claim_number
        """)
        rows = cur.fetchall()

        # Deduplicate by claim_number (user may have multiple contracts)
        seen = {}
        for row in rows:
            cn = row[0]
            if cn not in seen:
                address = row[5] if row[5] else {}
                city = address.get("city", "France") if isinstance(address, dict) else "France"
                seen[cn] = {
                    "claim_number": row[0],
                    "claim_type": row[1],
                    "document_path": row[2],
                    "submitted_at": str(row[3]) if row[3] else "2025-11-15",
                    "user_name": row[4] or "Assure",
                    "address": city,
                    "contract_number": row[6] or "N/A",
                }
        return list(seen.values())
    finally:
        conn.close()


def load_tenders_data() -> list[dict]:
    """Load all tenders for PDF generation."""
    conn = get_pg_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT tender_number, document_path, metadata
            FROM tenders
            ORDER BY tender_number
        """)
        results = []
        for row in cur.fetchall():
            metadata = row[2] if row[2] else {}
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            results.append({
                "tender_number": row[0],
                "document_path": row[1],
                "metadata": metadata,
            })
        return results
    finally:
        conn.close()


# ============================================================================
# LlamaStack Files API upload
# ============================================================================

async def upload_pdf_to_llamastack(filepath: str, purpose: str = "assistants") -> str:
    """Upload a single PDF to LlamaStack Files API. Returns file ID."""
    filename = os.path.basename(filepath)
    async with httpx.AsyncClient(timeout=60) as client:
        with open(filepath, "rb") as f:
            resp = await client.post(
                f"{LLAMASTACK_ENDPOINT}/v1/files",
                files={"file": (filename, f, "application/pdf")},
                data={"purpose": purpose},
            )
            resp.raise_for_status()
            result = resp.json()
            file_id = result.get("id", result.get("file_id"))
            logger.debug(f"Uploaded {filename} -> {file_id}")
            return file_id


async def upload_all_pdfs(claim_paths: list[str], tender_paths: list[str]):
    """Upload all PDFs to LlamaStack and update DB with file IDs."""
    conn = get_pg_conn()
    conn.autocommit = True
    cur = conn.cursor()

    # Upload claims
    for filepath in claim_paths:
        filename = os.path.basename(filepath)
        # Find matching document_path in DB
        doc_path = f"claims/{filename}"
        try:
            file_id = await upload_pdf_to_llamastack(filepath)
            cur.execute(
                "UPDATE claims SET document_path = %s WHERE document_path = %s",
                (file_id, doc_path),
            )
            logger.info(f"Claim {doc_path} -> {file_id}")
        except Exception as e:
            logger.error(f"Failed to upload {filepath}: {e}")

    # Upload tenders
    for filepath in tender_paths:
        filename = os.path.basename(filepath)
        doc_path = f"tenders/{filename}"
        try:
            file_id = await upload_pdf_to_llamastack(filepath)
            cur.execute(
                "UPDATE tenders SET document_path = %s WHERE document_path = %s",
                (file_id, doc_path),
            )
            logger.info(f"Tender {doc_path} -> {file_id}")
        except Exception as e:
            logger.error(f"Failed to upload {filepath}: {e}")

    conn.close()
    logger.info(f"Uploaded {len(claim_paths)} claim PDFs and {len(tender_paths)} tender PDFs")


# ============================================================================
# MCP tool calls via SSE (using MCP SDK client)
# ============================================================================

async def call_mcp_tool(server_url: str, tool_name: str, arguments: dict,
                        timeout: float = 300.0) -> dict:
    """
    Call an MCP tool via the SSE transport using the official MCP SDK client.
    Keeps the SSE stream open during the entire interaction.
    """
    from mcp.client.sse import sse_client
    from mcp import ClientSession

    sse_url = f"{server_url}/sse"
    async with sse_client(sse_url, timeout=timeout) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)

            if result.content:
                text = result.content[0].text
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"raw_text": text}

            return {}


# ============================================================================
# Processing logic
# ============================================================================

async def process_claims(decisions: list[dict]):
    """Process 10 claims: OCR + save decision."""
    logger.info(f"Processing {len(decisions)} claims...")

    for i, decision in enumerate(decisions):
        claim_number = decision["claim_number"]
        logger.info(f"[{i + 1}/{len(decisions)}] Processing claim {claim_number}...")

        # Step 1: OCR
        try:
            logger.info(f"  OCR {claim_number}...")
            start = time.time()
            ocr_result = await call_mcp_tool(
                OCR_SERVER_URL,
                "ocr_document",
                {"document_id": claim_number},
                timeout=120.0,
            )
            elapsed = time.time() - start
            success = ocr_result.get("success", False)
            logger.info(f"  OCR {claim_number}: success={success} ({elapsed:.1f}s)")
            if not success:
                logger.warning(f"  OCR failed for {claim_number}: {ocr_result.get('error')}")
        except Exception as e:
            logger.error(f"  OCR error for {claim_number}: {e}")

        # Step 2: Save decision
        try:
            logger.info(f"  Decision {claim_number}: {decision['recommendation']}...")
            result = await call_mcp_tool(
                CLAIMS_SERVER_URL,
                "save_claim_decision",
                {
                    "claim_id": claim_number,
                    "recommendation": decision["recommendation"],
                    "confidence": decision["confidence"],
                    "reasoning": decision["reasoning"],
                },
                timeout=60.0,
            )
            success = result.get("success", False)
            embedding = result.get("embedding", "unknown")
            logger.info(f"  Decision {claim_number}: success={success}, embedding={embedding}")
        except Exception as e:
            logger.error(f"  Decision error for {claim_number}: {e}")

    logger.info(f"Processed {len(decisions)} claims")


async def process_tenders(decisions: list[dict]):
    """Process 10 tenders: OCR + save decision."""
    logger.info(f"Processing {len(decisions)} tenders...")

    for i, decision in enumerate(decisions):
        tender_number = decision["tender_number"]
        logger.info(f"[{i + 1}/{len(decisions)}] Processing tender {tender_number}...")

        # Step 1: OCR
        try:
            logger.info(f"  OCR {tender_number}...")
            start = time.time()
            ocr_result = await call_mcp_tool(
                OCR_SERVER_URL,
                "ocr_document",
                {"document_id": tender_number},
                timeout=120.0,
            )
            elapsed = time.time() - start
            success = ocr_result.get("success", False)
            logger.info(f"  OCR {tender_number}: success={success} ({elapsed:.1f}s)")
            if not success:
                logger.warning(f"  OCR failed for {tender_number}: {ocr_result.get('error')}")
        except Exception as e:
            logger.error(f"  OCR error for {tender_number}: {e}")

        # Step 2: Save decision
        try:
            logger.info(f"  Decision {tender_number}: {decision['recommendation']}...")
            result = await call_mcp_tool(
                TENDERS_SERVER_URL,
                "save_tender_decision",
                {
                    "tender_id": tender_number,
                    "recommendation": decision["recommendation"],
                    "confidence": decision["confidence"],
                    "reasoning": decision["reasoning"],
                },
                timeout=60.0,
            )
            success = result.get("success", False)
            embedding = result.get("embedding", "unknown")
            logger.info(f"  Decision {tender_number}: success={success}, embedding={embedding}")
        except Exception as e:
            logger.error(f"  Decision error for {tender_number}: {e}")

    logger.info(f"Processed {len(decisions)} tenders")


def log_summary():
    """Print final summary of data state."""
    conn = get_pg_conn()
    try:
        cur = conn.cursor()

        cur.execute("SELECT status, COUNT(*) FROM claims GROUP BY status ORDER BY status")
        claim_stats = cur.fetchall()
        logger.info("=== Claims by status ===")
        for status, count in claim_stats:
            logger.info(f"  {status}: {count}")

        cur.execute("SELECT status, COUNT(*) FROM tenders GROUP BY status ORDER BY status")
        tender_stats = cur.fetchall()
        logger.info("=== Tenders by status ===")
        for status, count in tender_stats:
            logger.info(f"  {status}: {count}")

        cur.execute("SELECT COUNT(*) FROM claim_documents WHERE embedding IS NOT NULL")
        claim_emb = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tender_documents WHERE embedding IS NOT NULL")
        tender_emb = cur.fetchone()[0]
        logger.info(f"=== Embeddings: claims={claim_emb}, tenders={tender_emb} ===")

        cur.execute("SELECT COUNT(*) FROM claim_documents WHERE raw_ocr_text IS NOT NULL")
        claim_ocr = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tender_documents WHERE raw_ocr_text IS NOT NULL")
        tender_ocr = cur.fetchone()[0]
        logger.info(f"=== OCR texts: claims={claim_ocr}, tenders={tender_ocr} ===")

    finally:
        conn.close()


# ============================================================================
# Main
# ============================================================================

async def main():
    total_start = time.time()
    logger.info("=" * 60)
    logger.info("DATA INITIALIZATION STARTED")
    logger.info("=" * 60)

    # Step 1: Wait for services
    logger.info("Step 1: Waiting for services...")
    wait_for_postgres()
    await wait_for_llamastack()

    # Step 2: Check idempotency
    logger.info("Step 2: Checking if already initialized...")
    if check_already_initialized():
        logger.info("Skipping init (already done). Exiting.")
        return

    # Step 3: Wait for MCP servers
    logger.info("Step 3: Waiting for MCP servers...")
    await wait_for_mcp_servers()

    # Step 4: Load data from DB
    logger.info("Step 4: Loading data from DB...")
    claims_data = load_claims_data()
    tenders_data = load_tenders_data()
    logger.info(f"Loaded {len(claims_data)} claims and {len(tenders_data)} tenders")

    # Step 5: Generate PDFs
    logger.info("Step 5: Generating PDFs...")
    claim_paths, tender_paths = generate_all_pdfs(claims_data, tenders_data)

    # Step 6: Upload to LlamaStack
    logger.info("Step 6: Uploading PDFs to LlamaStack...")
    await upload_all_pdfs(claim_paths, tender_paths)

    # Step 7: Process 10 claims (OCR + decision)
    logger.info("Step 7: Processing 10 claims (OCR + decision)...")
    await process_claims(CLAIM_DECISIONS)

    # Step 8: Process 10 tenders (OCR + decision)
    logger.info("Step 8: Processing 10 tenders (OCR + decision)...")
    await process_tenders(TENDER_DECISIONS)

    # Step 9: Summary
    total_elapsed = time.time() - total_start
    logger.info("=" * 60)
    logger.info(f"DATA INITIALIZATION COMPLETED in {total_elapsed:.0f}s")
    logger.info("=" * 60)
    log_summary()


if __name__ == "__main__":
    asyncio.run(main())
