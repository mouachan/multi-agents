"""
MCP OCR Server - Extract text from documents using a vision model served by OGX
(default: llama-scout-17b via MaaS).
FastMCP server exposing Streamable HTTP (/mcp) and legacy SSE (/sse).

SIMPLE TOOL: Returns raw OCR text only.
The calling agent handles all LLM analysis and structuring.

Document retrieval: accepts claim/tender number, resolves the OGX file ID
via a DB lookup (document_path stores file-xxx), then fetches content from
the OGX Files API.

OCR: converts PDF pages to images, sends them to the vision model via the OGX
/v1/chat/completions API for text extraction. Zero local GPU/memory overhead.
"""

import asyncio
import contextlib
import base64
import io
import json
import logging
import os
import time
from pathlib import Path
from typing import Tuple

import httpx
import psycopg2
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pdf2image import convert_from_bytes
from PIL import Image
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# OGX / inference config
OGX_ENDPOINT = os.getenv("OGX_ENDPOINT", "").rstrip("/")
VISION_MODEL = os.getenv("OGX_VISION_MODEL", "llama-scout-17b")
VISION_MAX_TOKENS = int(os.getenv("VISION_MAX_TOKENS", "2048"))

# PostgreSQL configuration (for resolving claim/tender number → OGX file ID)
PG_HOST = os.getenv("POSTGRES_HOST", "postgresql")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB = os.getenv("POSTGRES_DATABASE", "multi_agent_db")
PG_USER = os.getenv("POSTGRES_USER", "multi_agent_user")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "")

# Create FastMCP server
# DNS-rebinding protection disabled explicitly: requests arrive through the
# Service name or the MCP Gateway internal hostname (FastMCP would answer 421).
mcp = FastMCP(
    "ocr-server",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

# Health check endpoint for Kubernetes probes
async def health_check(request):
    """Simple health check endpoint for liveness/readiness probes"""
    return JSONResponse({
        "status": "healthy",
        "service": "ocr-server",
        "vision_model": VISION_MODEL,
    })


# OPTIONS endpoint for MCP transport discovery
async def sse_options(request):
    """Handle OPTIONS requests for MCP endpoint discovery"""
    return JSONResponse({
        "methods": ["GET", "POST", "OPTIONS"],
        "server_name": "ocr-server",
        "transports": {"streamable_http": "/mcp", "sse": "/sse"},
        "capabilities": {
            "tools": True,
            "streaming": True
        }
    })


# The streamable HTTP session manager must run in the parent app lifespan
# (lifespans of mounted sub-apps are not executed).
@contextlib.asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield


# /mcp (Streamable HTTP), /sse (legacy SSE), /health
app = Starlette(
    routes=[
        Route("/health", health_check),
        *mcp.streamable_http_app().routes,
        Route("/sse", sse_options, methods=["OPTIONS"]),
        Route("/", sse_options, methods=["OPTIONS"]),
        Mount("/", app=mcp.sse_app()),
    ],
    lifespan=lifespan,
)

# Configuration
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "50"))
PDF_DPI = int(os.getenv("PDF_DPI", "200"))

# Supported file extensions
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}
SUPPORTED_PDF_EXTENSIONS = {'.pdf'}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS

OCR_PROMPT = (
    "Extract ALL text from this document image exactly as it appears. "
    "Preserve the layout and structure. Return only the extracted text."
)


# The cluster MaaS gateway does not pass request bodies much above ~128 KB (larger vision
# requests hang, then fail with HTTP 500): page images are sent as grayscale JPEG, shrunk
# until their base64 form fits (text stays readable: ~1000 chars per page at 850x1100).
MAX_IMAGE_B64_KB = int(os.getenv("OCR_MAX_IMAGE_B64_KB", "96"))


def _encode_image(image: Image.Image) -> str:
    img = image.convert("L")
    quality = 85
    while True:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        if len(b64) <= MAX_IMAGE_B64_KB * 1024 or min(img.size) < 400:
            return b64
        if quality > 60:
            quality -= 10
        else:
            img = img.resize((int(img.width * 0.8), int(img.height * 0.8)))


async def extract_text_with_vision(image: Image.Image) -> Tuple[str, float]:
    """Extract text from a PIL Image using the OGX vision model."""
    b64 = _encode_image(image)

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{OGX_ENDPOINT}/v1/chat/completions",
            json={
                "model": VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": OCR_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ]
                }],
                "max_tokens": VISION_MAX_TOKENS,
            },
        )
        resp.raise_for_status()
        result = resp.json()

    text = result["choices"][0]["message"]["content"]
    # Vision models don't return per-word confidence; use 0.95 as default
    confidence = 0.95 if text.strip() else 0.0

    word_count = len(text.split()) if text else 0
    logger.info(f"Vision OCR extracted {word_count} words")
    return text.strip(), confidence


# ---------------------------------------------------------------------------
# Document retrieval: claim/tender number → DB lookup → OGX file ID
# ---------------------------------------------------------------------------

def _resolve_file_id(document_id: str) -> str:
    """
    Resolve a claim/tender number to its OGX file ID via DB lookup.

    The upload script stores the OGX-generated file ID (file-xxx) in
    the document_path column. This function looks it up.
    """
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB,
        user=PG_USER, password=PG_PASS
    )
    try:
        cur = conn.cursor()
        # Try claims first
        cur.execute(
            "SELECT document_path FROM claims WHERE claim_number = %s",
            (document_id,)
        )
        row = cur.fetchone()
        if row and row[0]:
            logger.info(f"Resolved {document_id} → {row[0]} (claim)")
            return row[0]

        # Try tenders
        cur.execute(
            "SELECT document_path FROM tenders WHERE tender_number = %s",
            (document_id,)
        )
        row = cur.fetchone()
        if row and row[0]:
            logger.info(f"Resolved {document_id} → {row[0]} (tender)")
            return row[0]

        raise ValueError(f"No document found for {document_id} in claims or tenders")
    finally:
        conn.close()


async def fetch_file_content(document_id: str) -> bytes:
    """
    Fetch file content from the OGX Files API.

    Resolves claim/tender number → OGX file ID via DB, then fetches
    the content from the Files API.
    """
    if not OGX_ENDPOINT:
        raise ValueError("OGX_ENDPOINT not configured")

    # Resolve claim/tender number to OGX file ID
    file_id = await asyncio.to_thread(_resolve_file_id, document_id)

    url = f"{OGX_ENDPOINT}/v1/files/{file_id}/content"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        logger.info(f"Fetched {len(resp.content)} bytes from OGX: {document_id} (file_id={file_id})")
        return resp.content


async def ocr_from_bytes(content: bytes, filename: str = "") -> Tuple[str, float]:
    """Run OCR on raw file bytes (PDF or image) using vision model."""
    ext = Path(filename).suffix.lower() if filename else ""

    # Detect type from content magic bytes if no extension
    if not ext:
        if content[:4] == b'%PDF':
            ext = '.pdf'
        elif content[:2] == b'\xff\xd8':
            ext = '.jpg'
        elif content[:8] == b'\x89PNG\r\n\x1a\n':
            ext = '.png'
        else:
            ext = '.pdf'  # default assumption

    if ext in SUPPORTED_PDF_EXTENSIONS:
        images = await asyncio.to_thread(
            convert_from_bytes, content, dpi=PDF_DPI, first_page=1, last_page=MAX_PDF_PAGES
        )
        logger.info(f"PDF converted to {len(images)} pages")

        all_text = []
        all_confidences = []
        for i, image in enumerate(images):
            text, confidence = await extract_text_with_vision(image)
            if text:
                all_text.append(f"[Page {i + 1}]\n{text}")
                all_confidences.append(confidence)
            else:
                all_text.append(f"[Page {i + 1}]\n(No text detected)")

        combined = "\n\n--- Page Break ---\n\n".join(all_text)
        avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
        return combined, avg_conf

    elif ext in SUPPORTED_IMAGE_EXTENSIONS:
        image = Image.open(io.BytesIO(content))
        return await extract_text_with_vision(image)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


async def _save_ocr_result(document_id: str, raw_text: str, confidence: float):
    """Persist OCR result in claim_documents or tender_documents."""
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, dbname=PG_DB,
            user=PG_USER, password=PG_PASS
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Try claim first
        cur.execute("SELECT id, document_path FROM claims WHERE claim_number = %s", (document_id,))
        row = cur.fetchone()
        if row:
            claim_id = row[0]
            file_path = row[1] or document_id
            # Upsert into claim_documents
            cur.execute("""
                INSERT INTO claim_documents (claim_id, file_path, raw_ocr_text, ocr_confidence, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (claim_id) DO UPDATE SET
                    raw_ocr_text = EXCLUDED.raw_ocr_text,
                    ocr_confidence = EXCLUDED.ocr_confidence
            """, (claim_id, file_path, raw_text, confidence))
            logger.info(f"OCR result saved to claim_documents for {document_id}")
            conn.close()
            return

        # Try tender
        cur.execute("SELECT id FROM tenders WHERE tender_number = %s", (document_id,))
        row = cur.fetchone()
        if row:
            tender_id = row[0]
            # Delete existing then insert (no unique constraint on tender_id)
            cur.execute("DELETE FROM tender_documents WHERE tender_id = %s", (tender_id,))
            cur.execute("""
                INSERT INTO tender_documents (tender_id, raw_ocr_text, ocr_confidence, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (tender_id, raw_text, confidence))
            logger.info(f"OCR result saved to tender_documents for {document_id}")

        conn.close()
    except Exception as e:
        logger.warning(f"Failed to persist OCR result for {document_id}: {e}")


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def ocr_document(
    document_id: str,
    document_type: str = "AUTO"
) -> str:
    """
    Extract text from a claim or tender document using OCR.

    Retrieves the document from OGX Files by claim/tender number,
    then extracts text using the vision model. Supports PDF and images.

    Args:
        document_id: The claim number (e.g. CLM-2024-0024) or tender number (e.g. AO-2026-0042).
        document_type: Type hint (AUTO, MEDICAL, HOME, etc.) — informational only.

    Returns:
        JSON with raw_text, confidence score, and processing time.
    """
    start_time = time.time()
    logger.info(f"OCR STARTED for document: {document_id} (type: {document_type})")

    if not document_id or not document_id.strip():
        return json.dumps({"success": False, "raw_text": None, "confidence": 0.0,
                           "error": "document_id is required"})

    document_id = document_id.strip()

    try:
        # Fetch content from OGX Files API
        content = await fetch_file_content(document_id)
        fetch_time = time.time() - start_time
        logger.info(f"File fetched in {fetch_time:.2f}s ({len(content)} bytes)")

        # OCR via vision model
        raw_text, confidence = await ocr_from_bytes(content)

        total_time = time.time() - start_time
        word_count = len(raw_text.split()) if raw_text else 0
        logger.info(f"OCR COMPLETED in {total_time:.2f}s (confidence: {confidence:.2f}, words: {word_count})")

        # Persist OCR result in claim_documents / tender_documents
        await _save_ocr_result(document_id, raw_text, confidence)

        return json.dumps({
            "success": True,
            "document_id": document_id,
            "raw_text": raw_text,
            "confidence": round(confidence, 4),
            "processing_time_seconds": round(total_time, 2),
            "statistics": {
                "word_count": word_count,
                "character_count": len(raw_text) if raw_text else 0
            }
        })

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"OCR failed after {total_time:.2f}s: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "document_id": document_id,
            "raw_text": None,
            "confidence": 0.0,
            "error": str(e),
            "processing_time_seconds": round(total_time, 2)
        })


@mcp.tool()
async def ocr_health_check() -> str:
    """
    Check OCR server health and readiness.

    Returns:
        JSON string with health status
    """
    health = {
        "status": "healthy",
        "checks": {},
        "config": {
            "vision_model": VISION_MODEL,
            "max_pdf_pages": MAX_PDF_PAGES,
            "pdf_dpi": PDF_DPI,
        }
    }

    # Test vision model availability
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{OGX_ENDPOINT}/v1/health")
            resp.raise_for_status()
            health["checks"]["ogx"] = "ok"
    except Exception as e:
        health["checks"]["ogx"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return json.dumps(health)


@mcp.tool()
async def list_supported_formats() -> str:
    """
    List all supported file formats for OCR.

    Returns:
        JSON string with supported formats
    """
    return json.dumps({
        "image_formats": sorted(list(SUPPORTED_IMAGE_EXTENSIONS)),
        "document_formats": sorted(list(SUPPORTED_PDF_EXTENSIONS)),
        "all_formats": sorted(list(SUPPORTED_EXTENSIONS)),
        "vision_model": VISION_MODEL,
    })


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting MCP OCR Server (Vision: {VISION_MODEL}) on {host}:{port}")
    logger.info(f"OGX endpoint: {OGX_ENDPOINT}")
    logger.info(f"Max PDF Pages: {MAX_PDF_PAGES}")
    logger.info(f"PDF DPI: {PDF_DPI}")

    logger.info(f"MCP endpoints: http://{host}:{port}/mcp (streamable HTTP), /sse (legacy)")
    logger.info("Tools:")
    logger.info("  - ocr_document: Extract raw text from documents by claim/tender number")
    logger.info("  - ocr_health_check: Check server health")
    logger.info("  - list_supported_formats: List supported file formats")

    uvicorn.run(app, host=host, port=port)
