#!/usr/bin/env python3
"""
Data initialization script for multi-agents platform.

Downloads PDFs from GitHub, uploads to OGX Files API,
and processes 10 claims + 10 tenders via MCP server tools
(OCR + decision saving with embeddings), then embeds the reference data searched
by the RAG tools. On initialized data it only retries missing OCR texts and
embeddings.

Usage:
    python init_data.py

Environment variables:
    OGX_ENDPOINT: OGX API URL (default: http://ogx-service:8321)
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

from init_data.decisions import CLAIM_DECISIONS, TENDER_DECISIONS, RECLAMATION_DECISIONS

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("init_data")

# Configuration
OGX_ENDPOINT = os.getenv("OGX_ENDPOINT", "http://ogx-service:8321")
OCR_SERVER_URL = os.getenv("OCR_SERVER_URL", "http://ocr-server:8080")
CLAIMS_SERVER_URL = os.getenv("CLAIMS_SERVER_URL", "http://claims-server:8080")
TENDERS_SERVER_URL = os.getenv("TENDERS_SERVER_URL", "http://tenders-server:8080")
POSTAL_SERVER_URL = os.getenv("POSTAL_SERVER_URL", "http://postal-server:8080")
DOCUMENTS_ARCHIVE_URL = os.getenv("DOCUMENTS_ARCHIVE_URL", "")
FORCE_REINIT = os.getenv("FORCE_REINIT", "false").lower() == "true"

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


async def wait_for_ogx():
    """Wait for OGX to be healthy."""
    for i in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{OGX_ENDPOINT}/v1/health")
                if resp.status_code == 200:
                    logger.info("OGX is ready")
                    return
        except Exception as e:
            logger.info(f"Waiting for OGX ({i + 1}/{MAX_RETRIES}): {e}")
        await asyncio.sleep(RETRY_INTERVAL)
    raise RuntimeError("OGX not available after retries")


async def wait_for_mcp_servers():
    """Wait for all MCP servers to be healthy."""
    servers = {
        "ocr-server": OCR_SERVER_URL,
        "claims-server": CLAIMS_SERVER_URL,
        "tenders-server": TENDERS_SERVER_URL,
        "postal-server": POSTAL_SERVER_URL,
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

    Checks if document_path values have been replaced with OGX file IDs.
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


def reset_for_reinit():
    """Reset DB state so init_data can re-process all documents from scratch.

    Called when FORCE_REINIT=true. Restores original document_path values,
    resets statuses, and deletes all OCR/decision/processing data.
    """
    logger.info("FORCE_REINIT: Resetting database for re-initialization...")
    conn = get_pg_conn()
    conn.autocommit = True
    cur = conn.cursor()

    try:
        # --- Claims ---
        # Rebuild document_path from claim_type for standard claims (CLM-2024-*)
        cur.execute("""
            UPDATE claims c SET
                document_path = sub.new_path,
                status = 'pending',
                processed_at = NULL,
                total_processing_time_ms = NULL
            FROM (
                SELECT claim_number,
                       'claims/claim_' ||
                       CASE claim_type
                           WHEN 'Medical' THEN 'medical'
                           WHEN 'Auto' THEN 'auto'
                           WHEN 'Home' THEN 'home'
                           WHEN 'Life' THEN 'life'
                           ELSE LOWER(REPLACE(claim_type, ' ', '_'))
                       END || '_' ||
                       LPAD(
                           (ROW_NUMBER() OVER (
                               PARTITION BY claim_type ORDER BY claim_number
                           ))::text, 3, '0'
                       ) || '.pdf' AS new_path
                FROM claims
                WHERE claim_number LIKE 'CLM-2024-%%'
            ) sub
            WHERE c.claim_number = sub.claim_number
        """)
        logger.info(f"  Reset {cur.rowcount} standard claims (document_path + status)")

        # Reset cross-domain claim (CLM-ENT-001)
        cur.execute("""
            UPDATE claims SET
                document_path = 'claims/clm-ent-001-sinistre.pdf',
                status = 'pending',
                processed_at = NULL,
                total_processing_time_ms = NULL
            WHERE claim_number = 'CLM-ENT-001'
        """)

        # Delete claim-related data
        cur.execute("DELETE FROM claim_documents")
        logger.info(f"  Deleted {cur.rowcount} claim_documents")
        cur.execute("DELETE FROM claim_decisions")
        logger.info(f"  Deleted {cur.rowcount} claim_decisions")
        cur.execute("DELETE FROM processing_logs")
        logger.info(f"  Deleted {cur.rowcount} processing_logs")

        # --- Tenders ---
        # Rebuild document_path from tender_number for standard tenders (AO-2026-*)
        cur.execute("""
            UPDATE tenders SET
                document_path = 'tenders/' || LOWER(REPLACE(tender_number, '-', '_')) || '.pdf',
                status = 'pending',
                processed_at = NULL,
                total_processing_time_ms = NULL
            WHERE tender_number LIKE 'AO-2026-%%'
        """)
        logger.info(f"  Reset {cur.rowcount} standard tenders (document_path + status)")

        # Reset cross-domain tender (AO-2025-IDF-003)
        cur.execute("""
            UPDATE tenders SET
                document_path = 'tenders/ao-2025-idf-003-dce.pdf',
                status = 'pending',
                processed_at = NULL,
                total_processing_time_ms = NULL
            WHERE tender_number = 'AO-2025-IDF-003'
        """)

        # Delete tender-related data
        cur.execute("DELETE FROM tender_documents")
        logger.info(f"  Deleted {cur.rowcount} tender_documents")
        cur.execute("DELETE FROM tender_decisions")
        logger.info(f"  Deleted {cur.rowcount} tender_decisions")

        # --- Reclamations ---
        # Reset document_path for reclamations (restore original paths)
        cur.execute("""
            UPDATE reclamations r SET
                document_path = sub.new_path
            FROM (
                SELECT reclamation_number,
                       'reclamations/reclamation_' ||
                       reclamation_type || '_' ||
                       LPAD(
                           (ROW_NUMBER() OVER (
                               PARTITION BY reclamation_type ORDER BY reclamation_number
                           ))::text, 3, '0'
                       ) || '.pdf' AS new_path
                FROM reclamations
                WHERE document_path LIKE 'file-%%'
            ) sub
            WHERE r.reclamation_number = sub.reclamation_number
        """)
        logger.info(f"  Reset {cur.rowcount} reclamation document_paths")

        # Delete reclamation-related data (but NOT decisions/logs from seed)
        cur.execute("DELETE FROM reclamation_documents")
        logger.info(f"  Deleted {cur.rowcount} reclamation_documents")

        logger.info("FORCE_REINIT: Database reset complete")

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
            for subdir in ["claims", "tenders", "reclamations"]:
                src = os.path.join("/documents", subdir)
                if os.path.isdir(src):
                    subprocess.run(["cp", "-r", src, dest_dir], check=True)
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

    # Copy claims/, tenders/, and reclamations/ to dest_dir
    for subdir in ["claims", "tenders", "reclamations"]:
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
# OGX Files API upload
# ============================================================================

async def upload_pdf_to_ogx(filepath: str, purpose: str = "assistants") -> str:
    """Upload a single PDF to OGX Files API. Returns file ID."""
    filename = os.path.basename(filepath)
    async with httpx.AsyncClient(timeout=60) as client:
        with open(filepath, "rb") as f:
            resp = await client.post(
                f"{OGX_ENDPOINT}/v1/files",
                files={"file": (filename, f, "application/pdf")},
                data={"purpose": purpose},
            )
            resp.raise_for_status()
            result = resp.json()
            file_id = result.get("id", result.get("file_id"))
            logger.debug(f"Uploaded {filename} -> {file_id}")
            return file_id


def link_file(cur, table: str, doc_path: str, file_id: str) -> None:
    """Point the rows using this PDF to its OGX file ID.

    The French document is the row's document_path; the English one is referenced by
    metadata.document_path_en, which is kept and completed with document_file_id_en.
    """
    cur.execute(f"UPDATE {table} SET document_path = %s WHERE document_path = %s", (file_id, doc_path))
    cur.execute(
        f"UPDATE {table} SET metadata = metadata || jsonb_build_object('document_file_id_en', %s::text) "
        "WHERE metadata->>'document_path_en' = %s",
        (file_id, doc_path),
    )


def missing_english_documents() -> list:
    """(table, document_path_en) of English PDFs not linked to an OGX file yet."""
    conn = get_pg_conn()
    cur = conn.cursor()
    missing = []
    try:
        for table in ("claims", "tenders", "reclamations"):
            cur.execute(
                f"SELECT DISTINCT metadata->>'document_path_en' FROM {table} "
                "WHERE metadata ? 'document_path_en' AND NOT metadata ? 'document_file_id_en'"
            )
            missing += [(table, row[0]) for row in cur.fetchall() if row[0]]
    finally:
        conn.close()
    return missing


async def link_english_documents(missing: list, documents_dir: str = DOCUMENTS_DIR):
    """Upload the English PDFs of an already initialized database (idempotent catch-up)."""
    conn = get_pg_conn()
    conn.autocommit = True
    cur = conn.cursor()
    linked = 0
    try:
        for table, doc_path in missing:
            filepath = os.path.join(documents_dir, doc_path)
            if not os.path.exists(filepath):
                logger.warning(f"English document not found: {doc_path}")
                continue
            try:
                link_file(cur, table, doc_path, await upload_pdf_to_ogx(filepath))
                linked += 1
            except Exception as e:
                logger.error(f"Failed to upload {filepath}: {e}")
    finally:
        conn.close()
    logger.info(f"Linked {linked}/{len(missing)} English documents")


async def upload_all_pdfs_to_ogx(documents_dir: str = DOCUMENTS_DIR):
    """Upload all PDFs from documents_dir to OGX and update DB with file IDs."""
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
                file_id = await upload_pdf_to_ogx(filepath)
                link_file(cur, "claims", doc_path, file_id)
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
                file_id = await upload_pdf_to_ogx(filepath)
                link_file(cur, "tenders", doc_path, file_id)
                tender_count += 1
                logger.info(f"Tender {doc_path} -> {file_id}")
            except Exception as e:
                logger.error(f"Failed to upload {filepath}: {e}")

    # Upload reclamations
    reclamations_dir = os.path.join(documents_dir, "reclamations")
    reclamation_count = 0
    if os.path.isdir(reclamations_dir):
        for filepath in sorted(glob.glob(os.path.join(reclamations_dir, "*.pdf"))):
            filename = os.path.basename(filepath)
            doc_path = f"reclamations/{filename}"
            try:
                file_id = await upload_pdf_to_ogx(filepath)
                link_file(cur, "reclamations", doc_path, file_id)
                reclamation_count += 1
                logger.info(f"Reclamation {doc_path} -> {file_id}")
            except Exception as e:
                logger.error(f"Failed to upload {filepath}: {e}")

    conn.close()
    logger.info(
        f"Uploaded {claim_count} claim PDFs, {tender_count} tender PDFs, "
        f"and {reclamation_count} reclamation PDFs to OGX"
    )


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


async def process_reclamations(decisions: list[dict]):
    """Process 10 reclamations: OCR + save decision."""
    logger.info(f"Processing {len(decisions)} reclamations...")

    for i, decision in enumerate(decisions):
        reclamation_number = decision["reclamation_number"]
        logger.info(f"[{i + 1}/{len(decisions)}] Processing reclamation {reclamation_number}...")

        # Step 1: OCR
        try:
            logger.info(f"  OCR {reclamation_number}...")
            start = time.time()
            ocr_result = await call_mcp_tool(
                OCR_SERVER_URL,
                "ocr_document",
                {"document_id": reclamation_number},
                timeout=120.0,
            )
            elapsed = time.time() - start
            success = ocr_result.get("success", False)
            logger.info(f"  OCR {reclamation_number}: success={success} ({elapsed:.1f}s)")
            if not success:
                logger.warning(f"  OCR failed for {reclamation_number}: {ocr_result.get('error')}")
        except Exception as e:
            logger.error(f"  OCR error for {reclamation_number}: {e}")

        # Step 2: Save decision
        try:
            logger.info(f"  Decision {reclamation_number}: {decision['recommendation']}...")
            result = await call_mcp_tool(
                POSTAL_SERVER_URL,
                "save_reclamation_decision",
                {
                    "reclamation_id": reclamation_number,
                    "recommendation": decision["recommendation"],
                    "confidence": decision["confidence"],
                    "reasoning": decision["reasoning"],
                },
                timeout=60.0,
            )
            success = result.get("success", False)
            embedding = result.get("embedding", "unknown")
            logger.info(f"  Decision {reclamation_number}: success={success}, embedding={embedding}")
        except Exception as e:
            logger.error(f"  Decision error for {reclamation_number}: {e}")

    logger.info(f"Processed {len(decisions)} reclamations")


# ============================================================================
# Catch-up: precedent OCR texts and embeddings (also run on initialized data)
# ============================================================================

# Text embedded for each table searched by the RAG tools (rag_server); the MCP servers
# embed the first 2000 characters of a document's OCR text with the same model.
EMBEDDING_SOURCES = {
    "company_references": "concat_ws(E'\\n', project_name, nature_travaux, maitre_ouvrage, region, description)",
    "historical_tenders": "concat_ws(E'\\n', nature_travaux, maitre_ouvrage, region, description, raison_resultat)",
    "company_capabilities": "concat_ws(E'\\n', category, name, description, details)",
    "knowledge_base": "concat_ws(E'\\n\\n', title, content)",
    "courrier_knowledge_base": "concat_ws(E'\\n\\n', title, content)",
    "user_contracts": "concat_ws(E'\\n', contract_type, full_text)",
    "claim_documents": "raw_ocr_text",
    "tender_documents": "raw_ocr_text",
    "reclamation_documents": "raw_ocr_text",
}
EMBED_BATCH = 16  # the MaaS rejects large embedding batches (413)
EMBED_MAX_CHARS = 2000
OCR_CONCURRENCY = 3


def precedents_without_ocr() -> list:
    """Claim and tender numbers of the seeded precedents that have no OCR text yet
    (e.g. the vision model was unreachable during the first init)."""
    conn = get_pg_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT c.claim_number FROM claims c WHERE c.claim_number = ANY(%s) AND NOT EXISTS
               (SELECT 1 FROM claim_documents d WHERE d.claim_id = c.id AND d.raw_ocr_text <> '')""",
            ([d["claim_number"] for d in CLAIM_DECISIONS],),
        )
        missing = [r[0] for r in cur.fetchall()]
        cur.execute(
            """SELECT t.tender_number FROM tenders t WHERE t.tender_number = ANY(%s) AND NOT EXISTS
               (SELECT 1 FROM tender_documents d WHERE d.tender_id = t.id AND d.raw_ocr_text <> '')""",
            ([d["tender_number"] for d in TENDER_DECISIONS],),
        )
        return missing + [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


async def ocr_precedents(numbers: list):
    """OCR the given claims/tenders (the OCR server stores the text in *_documents)."""
    semaphore = asyncio.Semaphore(OCR_CONCURRENCY)

    async def ocr(number: str):
        async with semaphore:
            try:
                start = time.time()
                result = await call_mcp_tool(OCR_SERVER_URL, "ocr_document", {"document_id": number}, timeout=180.0)
                logger.info(f"  OCR {number}: success={result.get('success', False)} ({time.time() - start:.1f}s)")
            except Exception as e:
                logger.error(f"  OCR error for {number}: {e}")

    await asyncio.gather(*(ocr(n) for n in numbers))


async def backfill_embeddings():
    """Embed every RAG row that has text but no embedding (idempotent)."""
    model = os.getenv("EMBEDDING_MODEL", "")
    if not model:
        logger.warning("EMBEDDING_MODEL is not set: embeddings not generated")
        return
    conn = get_pg_conn()
    conn.autocommit = True
    try:
        cur = conn.cursor()
        async with httpx.AsyncClient(timeout=60) as client:
            for table, source in EMBEDDING_SOURCES.items():
                cur.execute(
                    f"SELECT id, LEFT({source}, %s) FROM {table} "
                    f"WHERE embedding IS NULL AND COALESCE({source}, '') <> ''",
                    (EMBED_MAX_CHARS,),
                )
                rows = cur.fetchall()
                done = 0
                for i in range(0, len(rows), EMBED_BATCH):
                    batch = rows[i:i + EMBED_BATCH]
                    try:
                        resp = await client.post(
                            f"{OGX_ENDPOINT}/v1/embeddings",
                            json={"model": model, "input": [text.strip() for _, text in batch]},
                        )
                        resp.raise_for_status()
                        vectors = [d["embedding"] for d in sorted(resp.json()["data"], key=lambda d: d["index"])]
                    except Exception as e:
                        logger.error(f"  Embeddings for {table} failed: {e}")
                        break
                    for (row_id, _), vector in zip(batch, vectors):
                        cur.execute(
                            f"UPDATE {table} SET embedding = CAST(%s AS vector) WHERE id = %s",
                            ("[" + ",".join(map(str, vector)) + "]", row_id),
                        )
                    done += len(batch)
                if rows:
                    logger.info(f"  {table}: {done}/{len(rows)} embeddings created")
    finally:
        conn.close()


async def catch_up():
    """Complete an existing initialization: OCR of the precedents, then embeddings."""
    missing = precedents_without_ocr()
    if missing:
        logger.info(f"{len(missing)} precedents have no OCR text: {', '.join(missing)}")
        await wait_for_mcp_servers()
        await ocr_precedents(missing)
    logger.info("Generating missing embeddings...")
    await backfill_embeddings()


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

        cur.execute("SELECT status::text, COUNT(*) FROM reclamations GROUP BY status ORDER BY status")
        reclamation_stats = cur.fetchall()
        logger.info("=== Reclamations by status ===")
        for status, count in reclamation_stats:
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

        cur.execute("SELECT COUNT(*) FROM reclamations WHERE document_path LIKE 'file-%%'")
        recl_uploaded = cur.fetchone()[0]
        logger.info(f"=== Reclamation docs uploaded: {recl_uploaded} ===")

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
    await wait_for_ogx()

    # Step 2: Check idempotency (or force reinit)
    logger.info("Step 2: Checking if already initialized...")
    if FORCE_REINIT:
        logger.info("FORCE_REINIT is enabled — resetting data for re-processing")
        reset_for_reinit()
    elif check_already_initialized():
        missing = missing_english_documents()
        if missing:
            logger.info(f"Already initialized, but {len(missing)} English documents are not linked yet")
            download_documents(DOCUMENTS_ARCHIVE_URL)
            await link_english_documents(missing)
        await catch_up()
        logger.info("Already initialized: catch-up done. Exiting.")
        return

    # Step 3: Wait for MCP servers
    logger.info("Step 3: Waiting for MCP servers...")
    await wait_for_mcp_servers()

    # Step 4: Download PDFs from GitHub (or use local mount)
    logger.info("Step 4: Downloading PDFs...")
    download_documents(DOCUMENTS_ARCHIVE_URL)

    # Step 5: Upload to OGX Files API
    logger.info("Step 5: Uploading PDFs to OGX Files API...")
    await upload_all_pdfs_to_ogx()

    # Step 6: Process 10 claims (OCR + decision)
    logger.info("Step 6: Processing 10 claims (OCR + decision)...")
    await process_claims(CLAIM_DECISIONS)

    # Step 7: Process 10 tenders (OCR + decision)
    logger.info("Step 7: Processing 10 tenders (OCR + decision)...")
    await process_tenders(TENDER_DECISIONS)

    # Step 8: Process 10 reclamations (OCR + decision)
    logger.info("Step 8: Processing 10 reclamations (OCR + decision)...")
    await process_reclamations(RECLAMATION_DECISIONS)

    # Step 9: OCR retries and embeddings of the reference data (references, capabilities,
    # knowledge bases, contracts) searched by the RAG tools
    logger.info("Step 9: Catch-up (OCR retries, embeddings)...")
    await catch_up()

    # Step 10: Summary
    total_elapsed = time.time() - total_start
    logger.info("=" * 60)
    logger.info(f"DATA INITIALIZATION COMPLETED in {total_elapsed:.0f}s")
    logger.info("=" * 60)
    log_summary()


if __name__ == "__main__":
    asyncio.run(main())
