"""
MCP OCR Server - Extract text from documents using EasyOCR
FastMCP implementation with Streamable HTTP transport

SIMPLE TOOL: Returns raw OCR text only.
The LlamaStack agent handles all LLM analysis and structuring.

FIXES APPLIED:
- Async execution of blocking OCR operations using asyncio.to_thread()
- Secure temporary file handling with tempfile
- Proper cleanup with try/finally
- Input validation
- Better error handling
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Tuple

import easyocr
from mcp.server.fastmcp import FastMCP
from pdf2image import convert_from_path
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP server with Streamable HTTP configuration (recommended)
# stateless_http=True: server doesn't maintain session state
# json_response=True: tools return JSON strings (optimal for scalability)
mcp = FastMCP(
    "ocr-server",
    stateless_http=True,
    json_response=True
)

# Health check endpoint for Kubernetes probes
async def health_check(request):
    """Simple health check endpoint for liveness/readiness probes"""
    return JSONResponse({
        "status": "healthy",
        "service": "ocr-server",
        "ocr_ready": _ocr_reader is not None
    })


# OPTIONS endpoint for MCP discovery (required by LlamaStack)
async def sse_options(request):
    """Handle OPTIONS requests for MCP SSE endpoint discovery"""
    return JSONResponse({
        "methods": ["GET", "POST", "OPTIONS"],
        "mcp_version": "0.1.0",
        "server_name": "ocr-server",
        "capabilities": {
            "tools": True,
            "streaming": True
        }
    })


# Create wrapper app with health check and MCP SSE server
mcp_sse_app = mcp.sse_app()

app = Starlette(
    routes=[
        Route("/health", health_check),
        Route("/sse", sse_options, methods=["OPTIONS"]),
        Route("/", sse_options, methods=["OPTIONS"]),
        Mount("/", app=mcp_sse_app),
    ]
)

# Configuration
OCR_LANGUAGES = os.getenv("OCR_LANGUAGES", "en,fr").split(",")
OCR_GPU_ENABLED = os.getenv("OCR_GPU_ENABLED", "false").lower() == "true"
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "50"))
PDF_DPI = int(os.getenv("PDF_DPI", "200"))

# Supported file extensions
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}
SUPPORTED_PDF_EXTENSIONS = {'.pdf'}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS

# Initialize EasyOCR reader (lazy loading on first use)
_ocr_reader = None
_ocr_reader_lock = asyncio.Lock()


async def get_ocr_reader() -> easyocr.Reader:
    """
    Get or create EasyOCR reader instance (singleton with async lock).
    
    Returns:
        EasyOCR Reader instance
    """
    global _ocr_reader
    
    async with _ocr_reader_lock:
        if _ocr_reader is None:
            logger.info(f"Initializing EasyOCR reader with languages: {OCR_LANGUAGES}")
            logger.info(f"GPU enabled: {OCR_GPU_ENABLED}")
            
            # Initialize in thread pool (blocking operation)
            _ocr_reader = await asyncio.to_thread(
                easyocr.Reader,
                OCR_LANGUAGES,
                gpu=OCR_GPU_ENABLED
            )
            
            logger.info("✅ EasyOCR reader initialized successfully")
        
        return _ocr_reader


async def extract_text_with_easyocr(image_path: Path) -> Tuple[str, float]:
    """
    Extract text from image using EasyOCR.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (extracted_text, average_confidence)
    """
    try:
        reader = await get_ocr_reader()

        # Run OCR in thread pool (blocking operation)
        result = await asyncio.to_thread(reader.readtext, str(image_path))

        if not result:
            logger.warning(f"No text detected in {image_path.name}")
            return "", 0.0

        # Combine all detected text blocks
        text_blocks = []
        confidences = []

        for bbox, text, confidence in result:
            if text.strip():  # Only include non-empty text
                text_blocks.append(text.strip())
                confidences.append(confidence)

        extracted_text = " ".join(text_blocks)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        logger.info(f"Extracted {len(text_blocks)} text blocks from {image_path.name} (confidence: {avg_confidence:.2f})")
        return extracted_text.strip(), avg_confidence

    except Exception as e:
        logger.error(f"Error extracting text with EasyOCR from {image_path}: {str(e)}")
        raise


async def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, float]:
    """
    Extract text from PDF by converting to images and using EasyOCR.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Tuple of (extracted_text, average_confidence)
    """
    temp_files = []  # Track temp files for cleanup
    
    try:
        # Convert PDF to images in thread pool (blocking operation)
        logger.info(f"Converting PDF to images: {pdf_path.name}")
        images = await asyncio.to_thread(
            convert_from_path,
            pdf_path,
            dpi=PDF_DPI,
            first_page=1,
            last_page=MAX_PDF_PAGES
        )
        
        logger.info(f"PDF converted to {len(images)} pages")

        all_text = []
        all_confidences = []

        for i, image in enumerate(images):
            # Create secure temporary file
            with tempfile.NamedTemporaryFile(
                suffix=".jpg",
                delete=False,
                prefix=f"ocr_page_{i}_"
            ) as tmp:
                temp_image_path = Path(tmp.name)
                temp_files.append(temp_image_path)

            try:
                # Save image to temp file
                await asyncio.to_thread(
                    image.save,
                    temp_image_path,
                    "JPEG",
                    quality=90
                )

                # Extract text from page
                text, confidence = await extract_text_with_easyocr(temp_image_path)
                
                if text:  # Only include pages with detected text
                    all_text.append(f"[Page {i + 1}]\n{text}")
                    all_confidences.append(confidence)
                else:
                    all_text.append(f"[Page {i + 1}]\n(No text detected)")
                    
            finally:
                # Clean up temp file immediately after processing
                try:
                    temp_image_path.unlink(missing_ok=True)
                    temp_files.remove(temp_image_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp file {temp_image_path}: {e}")

        combined_text = "\n\n--- Page Break ---\n\n".join(all_text)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        logger.info(f"Extracted text from PDF ({len(images)} pages, confidence: {avg_confidence:.2f})")
        return combined_text, avg_confidence

    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        raise
        
    finally:
        # Cleanup any remaining temp files
        for temp_file in temp_files:
            try:
                temp_file.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")


def validate_file_path(document_path: str) -> Tuple[bool, str, Path]:
    """
    Validate the document path.
    
    Args:
        document_path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message, Path object)
    """
    if not document_path or not document_path.strip():
        return False, "Document path is required", Path()
    
    doc_path = Path(document_path.strip())
    
    if not doc_path.exists():
        return False, f"Document not found: {document_path}", doc_path
    
    if not doc_path.is_file():
        return False, f"Path is not a file: {document_path}", doc_path
    
    file_extension = doc_path.suffix.lower()
    if file_extension not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type: {file_extension}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}", doc_path
    
    # Check file size (max 100MB)
    max_size = 100 * 1024 * 1024  # 100MB
    if doc_path.stat().st_size > max_size:
        return False, f"File too large. Maximum size: 100MB", doc_path
    
    return True, "", doc_path


@mcp.tool()
async def ocr_document(
    document_path: str,
    language: str = "eng",
    document_type: str = "AUTO",
    extract_structured: str = "false"
) -> str:
    """
    Extract raw text from document using OCR (EasyOCR).

    This tool performs ONLY text extraction. No LLM analysis or structuring.
    The LlamaStack agent will analyze and structure the extracted text.

    Supports PDF, JPG, PNG, TIFF, BMP, and WebP formats.
    Fast extraction: 2-4 seconds per page.

    Args:
        document_path: Path to the document file (PDF, image, etc.)
        language: OCR language code (eng, fra, deu, etc.)
                 Note: Language is configured at server startup via OCR_LANGUAGES env var
        document_type: Type hint for the document (MEDICAL, AUTO, HOME, etc.) - informational only
        extract_structured: Whether to extract structured data - not used, always returns raw text

    Returns:
        JSON string with raw extracted text and confidence score
    """
    start_time = time.time()
    logger.info(f"⏱️  OCR STARTED for document: {document_path} (type: {document_type})")

    # Validate input
    is_valid, error_msg, doc_path = validate_file_path(document_path)
    if not is_valid:
        logger.error(error_msg)
        return json.dumps({
            "success": False,
            "raw_text": None,
            "confidence": 0.0,
            "error": error_msg
        })

    try:
        file_extension = doc_path.suffix.lower()

        # Extract text based on file type
        if file_extension in SUPPORTED_PDF_EXTENSIONS:
            raw_text, confidence = await extract_text_from_pdf(doc_path)
        elif file_extension in SUPPORTED_IMAGE_EXTENSIONS:
            raw_text, confidence = await extract_text_with_easyocr(doc_path)
        else:
            # This shouldn't happen due to validation, but just in case
            return json.dumps({
                "success": False,
                "raw_text": None,
                "confidence": 0.0,
                "error": f"Unsupported file type: {file_extension}"
            })

        total_time = time.time() - start_time
        logger.info(f"⏱️  OCR COMPLETED in {total_time:.2f}s (confidence: {confidence:.2f})")

        if total_time > 25.0:
            logger.warning(f"⚠️  OCR took longer than expected: {total_time:.2f}s")

        # Calculate text statistics
        word_count = len(raw_text.split()) if raw_text else 0
        char_count = len(raw_text) if raw_text else 0

        return json.dumps({
            "success": True,
            "raw_text": raw_text,
            "confidence": round(confidence, 4),
            "processing_time_seconds": round(total_time, 2),
            "statistics": {
                "word_count": word_count,
                "character_count": char_count
            },
            "file_info": {
                "name": doc_path.name,
                "extension": file_extension,
                "size_bytes": doc_path.stat().st_size
            }
        })

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Error processing OCR request after {total_time:.2f}s: {str(e)}", exc_info=True)
        return json.dumps({
            "success": False,
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
            "languages": OCR_LANGUAGES,
            "gpu_enabled": OCR_GPU_ENABLED,
            "max_pdf_pages": MAX_PDF_PAGES,
            "pdf_dpi": PDF_DPI
        }
    }
    
    # Check EasyOCR reader
    try:
        reader = await get_ocr_reader()
        health["checks"]["easyocr"] = "ok"
        health["checks"]["easyocr_languages"] = OCR_LANGUAGES
    except Exception as e:
        health["checks"]["easyocr"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
    
    # Check temp directory
    try:
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            health["checks"]["temp_directory"] = "ok"
    except Exception as e:
        health["checks"]["temp_directory"] = f"error: {str(e)}"
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
        "languages": OCR_LANGUAGES
    })


if __name__ == "__main__":
    import asyncio
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting MCP OCR Server (FastMCP SSE) on {host}:{port}")
    logger.info(f"OCR Languages: {OCR_LANGUAGES}")
    logger.info(f"GPU Enabled: {OCR_GPU_ENABLED}")
    logger.info(f"Max PDF Pages: {MAX_PDF_PAGES}")

    # Pre-initialize EasyOCR before starting server (ensures readiness)
    logger.info("Pre-initializing EasyOCR reader...")
    try:
        async def init_ocr():
            reader = await get_ocr_reader()
            logger.info("✅ EasyOCR reader pre-initialized and ready")
            return reader

        asyncio.run(init_ocr())
    except Exception as e:
        logger.error(f"Failed to initialize EasyOCR: {e}")
        raise

    logger.info(f"MCP SSE endpoint will be available at: http://{host}:{port}/sse")
    logger.info("Tools:")
    logger.info("  - ocr_document: Extract raw text from documents")
    logger.info("  - ocr_health_check: Check server health")
    logger.info("  - list_supported_formats: List supported file formats")

    # Run uvicorn with FastMCP SSE app
    uvicorn.run(app, host=host, port=port)