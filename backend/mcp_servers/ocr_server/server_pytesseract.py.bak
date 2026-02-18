"""
MCP OCR Server - Extract text from documents using OCR and validate with LLM
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

import pytesseract
from fastapi import FastAPI, HTTPException
from PIL import Image
from pdf2image import convert_from_path
from pydantic import BaseModel, Field
import httpx

# Import prompts
from prompts import get_ocr_validation_prompt

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MCP OCR Server",
    description="OCR processing with LLM validation",
    version="1.0.0",
)

# LlamaStack configuration
LLAMASTACK_ENDPOINT = os.getenv("LLAMASTACK_ENDPOINT", "http://localhost:8090")


# Pydantic models
class OCRRequest(BaseModel):
    document_path: str = Field(..., description="Path to document image or PDF")
    document_type: str = Field(default="claim_form", description="Type of document")
    language: str = Field(default="eng", description="OCR language code")
    enhance_image: bool = Field(default=True, description="Apply image enhancement")


class OCRResponse(BaseModel):
    success: bool
    raw_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    errors: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    service: str


# Helper functions
async def extract_text_from_image(image_path: Path, language: str = "eng") -> tuple[str, float]:
    """Extract text from image using Tesseract OCR."""
    try:
        image = Image.open(image_path)

        # Get detailed OCR data including confidence
        ocr_data = pytesseract.image_to_data(
            image,
            lang=language,
            output_type=pytesseract.Output.DICT
        )

        # Extract text
        text = pytesseract.image_to_string(image, lang=language)

        # Calculate average confidence
        confidences = [int(conf) for conf in ocr_data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) / 100 if confidences else 0.0

        logger.info(f"Extracted text from {image_path.name}, confidence: {avg_confidence:.2f}")
        return text.strip(), avg_confidence

    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        raise


async def extract_text_from_pdf(pdf_path: Path, language: str = "eng") -> tuple[str, float]:
    """Extract text from PDF by converting to images first."""
    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path)

        all_text = []
        all_confidences = []

        for i, image in enumerate(images):
            # Save temp image
            temp_image_path = f"/tmp/page_{i}.png"
            image.save(temp_image_path, "PNG")

            # Extract text from page
            text, confidence = await extract_text_from_image(
                Path(temp_image_path),
                language
            )
            all_text.append(text)
            all_confidences.append(confidence)

            # Clean up temp file
            os.remove(temp_image_path)

        # Combine all pages
        combined_text = "\n\n--- Page Break ---\n\n".join(all_text)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        logger.info(f"Extracted text from PDF with {len(images)} pages, confidence: {avg_confidence:.2f}")
        return combined_text, avg_confidence

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise


async def validate_with_llm(raw_text: str, document_type: str) -> Dict[str, Any]:
    """Validate and structure OCR text using LLM."""
    try:
        # Define expected fields based on document type
        field_mapping = {
            "claim_form": ["claim_number", "claimant_name", "date_of_service", "provider_name", "diagnosis", "amount"],
            "invoice": ["invoice_number", "date", "vendor_name", "total_amount", "line_items"],
            "medical_record": ["patient_name", "date_of_birth", "diagnosis", "treatment", "provider"],
            "id_card": ["name", "id_number", "date_of_birth", "address"],
            "other": ["key_information"]
        }

        expected_fields = field_mapping.get(document_type, field_mapping["other"])

        # Prepare LLM prompt using centralized prompts
        prompt = get_ocr_validation_prompt(raw_text, expected_fields)

        # Call LlamaStack
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{LLAMASTACK_ENDPOINT}/inference/generate",
                json={
                    "model": "llama-3.1-8b-instruct",
                    "prompt": prompt,
                    "temperature": 0.1,
                    "max_tokens": 1024,
                }
            )

            if response.status_code == 200:
                result = response.json()
                # Parse the generated text as JSON
                import json
                try:
                    structured_data = json.loads(result.get("generated_text", "{}"))
                    logger.info("Successfully validated OCR text with LLM")
                    return structured_data
                except json.JSONDecodeError:
                    logger.warning("LLM response was not valid JSON, returning raw text")
                    return {
                        "fields": {"raw_text": {"value": raw_text, "confidence": 0.5}},
                        "overall_confidence": 0.5,
                        "requires_manual_review": True,
                        "notes": "LLM validation failed to parse"
                    }
            else:
                logger.error(f"LlamaStack API error: {response.status_code}")
                return {
                    "fields": {"raw_text": {"value": raw_text, "confidence": 0.5}},
                    "overall_confidence": 0.5,
                    "requires_manual_review": True,
                    "notes": "LLM validation unavailable"
                }

    except Exception as e:
        logger.error(f"Error validating with LLM: {str(e)}")
        return {
            "fields": {"raw_text": {"value": raw_text, "confidence": 0.5}},
            "overall_confidence": 0.5,
            "requires_manual_review": True,
            "notes": f"Error: {str(e)}"
        }


# API Endpoints
@app.post("/ocr_document", response_model=OCRResponse)
async def ocr_document(request: OCRRequest) -> OCRResponse:
    """
    Extract text from a document using OCR and validate with LLM.

    MCP Tool: ocr_document
    """
    try:
        document_path = Path(request.document_path)

        # Check if file exists
        if not document_path.exists():
            logger.error(f"Document not found: {request.document_path}")
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {request.document_path}"
            )

        # Determine file type and extract text
        file_extension = document_path.suffix.lower()

        if file_extension in ['.pdf']:
            raw_text, confidence = await extract_text_from_pdf(document_path, request.language)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            raw_text, confidence = await extract_text_from_image(document_path, request.language)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}"
            )

        # Validate with LLM
        structured_data = await validate_with_llm(raw_text, request.document_type)

        return OCRResponse(
            success=True,
            raw_text=raw_text,
            structured_data=structured_data,
            confidence=confidence,
            errors=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing OCR request: {str(e)}")
        return OCRResponse(
            success=False,
            raw_text=None,
            structured_data=None,
            confidence=0.0,
            errors=[str(e)]
        )


@app.get("/health/live", response_model=HealthResponse)
async def liveness():
    """Liveness probe."""
    return HealthResponse(status="alive", service="mcp-ocr-server")


@app.get("/health/ready", response_model=HealthResponse)
async def readiness():
    """Readiness probe."""
    # Check if Tesseract is available
    try:
        pytesseract.get_tesseract_version()
        return HealthResponse(status="ready", service="mcp-ocr-server")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Tesseract not ready: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "MCP OCR Server",
        "version": "1.0.0",
        "status": "running",
        "tools": ["ocr_document"]
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
