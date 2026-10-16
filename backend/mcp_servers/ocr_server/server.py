"""MCP server reading the document of a case (OCR) with a vision model served by OGX.

ocr_document(<case number>) finds the case's PDF in the OGX Files API (data-init stored its file id in
the case's document_path), turns each page into an image, has the vision model transcribe it, and
keeps the text in the case's documents table: the other tools (payout, similarity searches) read it
there. A document already read is not read again (the vision model takes ~10 s per page), unless
refresh=true.
"""
import asyncio
import base64
import io
import logging
import os
from typing import Any, Dict, List

import httpx
from pdf2image import convert_from_bytes
from PIL import Image

from shared.cases import CaseTable, domain_of, find_case
from shared.db import execute, fetch_one
from shared.server import create_mcp, serve
from shared.tools import ToolError, required, tool

logger = logging.getLogger(__name__)
mcp = create_mcp("ocr-server")

OGX_ENDPOINT = os.getenv("OGX_ENDPOINT", "").rstrip("/")
VISION_MODEL = os.getenv("OGX_VISION_MODEL", "llama-scout-17b")
VISION_MAX_TOKENS = int(os.getenv("VISION_MAX_TOKENS", "2048"))
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "50"))
PDF_DPI = int(os.getenv("PDF_DPI", "200"))
# The cluster MaaS gateway does not pass request bodies much above ~128 KB (larger vision requests
# hang, then fail with HTTP 500): page images are sent as grayscale JPEG, shrunk until their base64
# form fits (the text stays readable: ~1000 characters per page at 850x1100)
MAX_IMAGE_B64_KB = int(os.getenv("OCR_MAX_IMAGE_B64_KB", "60"))
VISION_TIMEOUT = 60   # seconds per page; the vision call sometimes hangs on the MaaS side
OCR_PROMPT = ("Extract ALL text from this document image exactly as it appears. "
              "Preserve the layout and structure. Return only the extracted text.")
PAGE_BREAK = "\n\n--- Page Break ---\n\n"


@tool(mcp)
async def ocr_document(document_id: str, refresh: bool = False) -> Dict[str, Any]:
    """
    Read the document of a claim, a tender or a postal complaint (OCR) and return its text.
    The text is kept: reading the same document again returns it at once.

    Args:
        document_id: The case number (e.g. CLM-2024-0024, AO-2026-IDF-001, RECL-2026-0001)
        refresh: true to read the document again even if it was already read
    """
    number = required(document_id, "document_id")
    domain = domain_of(number)
    if domain is None:
        raise ToolError(f"{number} is not a claim, tender or complaint number")
    case = await find_case(domain, number)
    file_id = (await fetch_one(f"SELECT document_path FROM {domain.table} WHERE id = CAST(:id AS uuid)",
                               id=case["id"]))["document_path"]
    if not file_id:
        raise ToolError(f"{domain.label} {number} has no document")

    if not refresh:
        known = await _stored_text(domain, case["id"], file_id)
        if known:
            return {"document_id": number, "raw_text": known["raw_ocr_text"], "confidence": known["ocr_confidence"],
                    "pages": known["page_count"], "already_read": True}

    pages = await _page_images(await _download(file_id))
    texts = [await _transcribe(page) for page in pages]
    text = PAGE_BREAK.join(f"[Page {i}]\n{page_text or '(No text detected)'}" for i, page_text in enumerate(texts, 1))
    confidence = 0.95 if any(texts) else 0.0   # vision models give no confidence: a fixed value when text was read
    await _store_text(domain, case["id"], file_id, text, confidence, len(pages))
    logger.info("OCR of %s: %d pages, %d words", number, len(pages), len(text.split()))
    return {"document_id": number, "raw_text": text, "confidence": confidence, "pages": len(pages),
            "already_read": False}


async def _download(file_id: str) -> bytes:
    if not OGX_ENDPOINT:
        raise ToolError("OGX_ENDPOINT is not configured")
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{OGX_ENDPOINT}/v1/files/{file_id}/content")
        response.raise_for_status()
    return response.content


async def _page_images(content: bytes) -> List[Image.Image]:
    """The pages of a PDF as images (or the image itself)."""
    if content[:4] == b"%PDF":
        return await asyncio.to_thread(convert_from_bytes, content, dpi=PDF_DPI, first_page=1, last_page=MAX_PDF_PAGES)
    return [Image.open(io.BytesIO(content))]


async def _transcribe(image: Image.Image) -> str:
    """The text of one page, by the vision model (one retry: the MaaS sometimes hangs)."""
    request = {
        "model": VISION_MODEL,
        "max_tokens": VISION_MAX_TOKENS,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": OCR_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{_jpeg_base64(image)}"}},
        ]}],
    }
    for attempt in (1, 2):
        try:
            async with httpx.AsyncClient(timeout=VISION_TIMEOUT) as client:
                response = await client.post(f"{OGX_ENDPOINT}/v1/chat/completions", json=request)
                response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            if attempt == 2:
                raise
            logger.warning("Vision call failed (attempt %d): %s", attempt, e)
    return ""


def _jpeg_base64(image: Image.Image) -> str:
    """The page as a grayscale JPEG in base64, small enough for the MaaS gateway."""
    image = image.convert("L")
    quality = 85
    while True:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode()
        if len(encoded) <= MAX_IMAGE_B64_KB * 1024 or min(image.size) < 400:
            return encoded
        if quality > 60:
            quality -= 10
        else:
            image = image.resize((int(image.width * 0.8), int(image.height * 0.8)))


async def _stored_text(domain: CaseTable, case_id: str, file_id: str):
    """The text already read from this file (metadata ocr_file_id of the case's document row)."""
    return await fetch_one(f"""
        SELECT raw_ocr_text, ocr_confidence, page_count FROM {domain.documents}
        WHERE {domain.fk} = CAST(:id AS uuid) AND metadata->>'ocr_file_id' = :file
          AND COALESCE(raw_ocr_text, '') <> ''
        ORDER BY created_at DESC LIMIT 1""", id=case_id, file=file_id)


async def _store_text(domain: CaseTable, case_id: str, file_id: str, text: str, confidence: float, pages: int) -> None:
    """The text goes in the case's latest document row (created if there is none). Its embedding is
    cleared: the backend embeds the new text after the processing (backend/app/services/embeddings.py)."""
    values = {"id": case_id, "file": file_id, "text": text, "confidence": confidence, "pages": pages}
    updated = await execute(f"""
        UPDATE {domain.documents} SET raw_ocr_text = :text, ocr_confidence = :confidence, page_count = :pages,
               ocr_processed_at = NOW(), embedding = NULL,
               metadata = COALESCE(metadata, '{{}}'::jsonb) || jsonb_build_object('ocr_file_id', CAST(:file AS text))
        WHERE id = (SELECT id FROM {domain.documents} WHERE {domain.fk} = CAST(:id AS uuid)
                    ORDER BY created_at DESC LIMIT 1)""", **values)
    if not updated:
        await execute(f"""
            INSERT INTO {domain.documents} ({domain.fk}, file_path, mime_type, raw_ocr_text, ocr_confidence,
                                            page_count, ocr_processed_at, metadata)
            VALUES (CAST(:id AS uuid), :file, 'application/pdf', :text, :confidence, :pages, NOW(),
                    jsonb_build_object('ocr_file_id', CAST(:file AS text)))""", **values)


if __name__ == "__main__":
    serve(mcp)
