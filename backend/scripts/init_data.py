#!/usr/bin/env python3
"""
Data initialization script for multi-agents platform.

Downloads PDFs from GitHub, uploads to LlamaStack Files API,
and processes 10 claims + 10 tenders via MCP server tools
(OCR + decision saving with embeddings).

Usage:
    python init_data.py

Environment variables:
    LLAMASTACK_ENDPOINT: LlamaStack API URL (default: http://llamastack:8321)
    OCR_SERVER_URL: OCR MCP server URL (default: http://ocr-server:8080)
    CLAIMS_SERVER_URL: Claims MCP server URL (default: http://claims-server:8080)
    TENDERS_SERVER_URL: Tenders MCP server URL (default: http://tenders-server:8080)
    DOCUMENTS_ARCHIVE_URL: URL of the tar.gz archive containing PDFs
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE, POSTGRES_USER, POSTGRES_PASSWORD
"""

import asyncio
import glob
import json
import logging
import os
import subprocess
import sys
import tarfile
import time

import httpx
import psycopg2

# Add parent dir to path for init_data package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from init_data.decisions import CLAIM_DECISIONS, TENDER_DECISIONS

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
DOCUMENTS_ARCHIVE_URL = os.getenv("DOCUMENTS_ARCHIVE_URL", "")

PG_HOST = os.getenv("POSTGRES_HOST", "postgresql")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB = os.getenv("POSTGRES_DATABASE", "multi_agent_db")
PG_USER = os.getenv("POSTGRES_USER", "multi_agent_user")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "multi_agents_pass")

DOCUMENTS_DIR = "/tmp/documents"
MAX_RETRIES = 60
RETRY_INTERVAL = 10  # seconds


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
    """Check if data init has already been run (idempotent).

    Checks if document_path values have been replaced with LlamaStack file IDs.
    """
    conn = get_pg_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM claims WHERE document_path LIKE 'file-%%'"
        )
        count = cur.fetchone()[0]
        if count > 0:
            logger.info(f"Data already initialized ({count} claims with file IDs). Skipping.")
            return True
        return False
    finally:
        conn.close()


# ============================================================================
# Download PDFs from GitHub
# ============================================================================

def download_documents(archive_url: str, dest_dir: str = DOCUMENTS_DIR):
    """Download and extract PDF documents from a GitHub archive URL."""
    if not archive_url:
        # Fall back to local /documents mount (docker-compose)
        if os.path.isdir("/documents"):
            logger.info("Using locally mounted /documents directory")
            # Copy to dest_dir for consistency
            os.makedirs(dest_dir, exist_ok=True)
            subprocess.run(
                ["cp", "-r", "/documents/claims", "/documents/tenders", dest_dir],
                check=True,
            )
            return
        raise RuntimeError(
            "No DOCUMENTS_ARCHIVE_URL set and no /documents mount found"
        )

    logger.info(f"Downloading documents from {archive_url}")
    archive_path = "/tmp/repo.tar.gz"

    subprocess.run(
        ["curl", "-sL", archive_url, "-o", archive_path],
        check=True,
    )

    os.makedirs(dest_dir, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall("/tmp/repo_extract")

    # Find the extracted directory (e.g., multi-agents-main/)
    extracted_dirs = os.listdir("/tmp/repo_extract")
    if not extracted_dirs:
        raise RuntimeError("Archive extraction produced no directories")

    repo_dir = os.path.join("/tmp/repo_extract", extracted_dirs[0], "documents")
    if not os.path.isdir(repo_dir):
        raise RuntimeError(f"No documents/ directory found in archive at {repo_dir}")

    # Copy claims/ and tenders/ to dest_dir
    for subdir in ["claims", "tenders"]:
        src = os.path.join(repo_dir, subdir)
        dst = os.path.join(dest_dir, subdir)
        if os.path.isdir(src):
            subprocess.run(["cp", "-r", src, dst], check=True)
            pdf_count = len(glob.glob(os.path.join(dst, "*.pdf")))
            logger.info(f"Extracted {pdf_count} PDFs to {dst}")

    # Cleanup
    os.remove(archive_path)
    subprocess.run(["rm", "-rf", "/tmp/repo_extract"], check=False)


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


async def upload_all_pdfs_to_llamastack(documents_dir: str = DOCUMENTS_DIR):
    """Upload all PDFs from documents_dir to LlamaStack and update DB with file IDs."""
    conn = get_pg_conn()
    conn.autocommit = True
    cur = conn.cursor()

    claims_dir = os.path.join(documents_dir, "claims")
    tenders_dir = os.path.join(documents_dir, "tenders")

    claim_count = 0
    tender_count = 0

    # Upload claims
    if os.path.isdir(claims_dir):
        for filepath in sorted(glob.glob(os.path.join(claims_dir, "*.pdf"))):
            filename = os.path.basename(filepath)
            doc_path = f"claims/{filename}"
            try:
                file_id = await upload_pdf_to_llamastack(filepath)
                cur.execute(
                    "UPDATE claims SET document_path = %s WHERE document_path = %s",
                    (file_id, doc_path),
                )
                claim_count += 1
                logger.info(f"Claim {doc_path} -> {file_id}")
            except Exception as e:
                logger.error(f"Failed to upload {filepath}: {e}")

    # Upload tenders
    if os.path.isdir(tenders_dir):
        for filepath in sorted(glob.glob(os.path.join(tenders_dir, "*.pdf"))):
            filename = os.path.basename(filepath)
            doc_path = f"tenders/{filename}"
            try:
                file_id = await upload_pdf_to_llamastack(filepath)
                cur.execute(
                    "UPDATE tenders SET document_path = %s WHERE document_path = %s",
                    (file_id, doc_path),
                )
                tender_count += 1
                logger.info(f"Tender {doc_path} -> {file_id}")
            except Exception as e:
                logger.error(f"Failed to upload {filepath}: {e}")

    conn.close()
    logger.info(f"Uploaded {claim_count} claim PDFs and {tender_count} tender PDFs to LlamaStack")


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

    # Step 4: Download PDFs from GitHub (or use local mount)
    logger.info("Step 4: Downloading PDFs...")
    download_documents(DOCUMENTS_ARCHIVE_URL)

    # Step 5: Upload to LlamaStack Files API
    logger.info("Step 5: Uploading PDFs to LlamaStack Files API...")
    await upload_all_pdfs_to_llamastack()

    # Step 6: Process 10 claims (OCR + decision)
    logger.info("Step 6: Processing 10 claims (OCR + decision)...")
    await process_claims(CLAIM_DECISIONS)

    # Step 7: Process 10 tenders (OCR + decision)
    logger.info("Step 7: Processing 10 tenders (OCR + decision)...")
    await process_tenders(TENDER_DECISIONS)

    # Step 8: Summary
    total_elapsed = time.time() - total_start
    logger.info("=" * 60)
    logger.info(f"DATA INITIALIZATION COMPLETED in {total_elapsed:.0f}s")
    logger.info("=" * 60)
    log_summary()


if __name__ == "__main__":
    asyncio.run(main())
