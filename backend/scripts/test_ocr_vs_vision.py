"""
Test script: Compare OCR approaches for document text extraction.

1. EasyOCR (current) — via MCP OCR server
2. Scout Vision (proposed) — LlamaStack Files API + multimodal inference

Measures: time (seconds), tokens consumed, text quality.

Usage: python backend/scripts/test_ocr_vs_vision.py
"""
import asyncio
import base64
import httpx
import json
import time
import sys
from pathlib import Path

LLAMASTACK = "http://localhost:8321"
MINIO_URL = "http://localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "minioadmin123"
SCOUT_MODEL = "litemaas/Llama-4-Scout-17B-16E-W4A16"

# Local document path (same files mounted in containers)
DOC_PATH = Path(__file__).parent.parent.parent / "documents" / "claims" / "claim_auto_011.pdf"


async def test_1_ocr_server():
    """Test 1: Call OCR MCP server (EasyOCR) via the running container."""
    print("\n" + "=" * 60)
    print("TEST 1: EasyOCR via MCP OCR Server")
    print("=" * 60)

    # Call the OCR server directly (MCP over HTTP)
    # The OCR server expects the path as seen from inside the container
    async with httpx.AsyncClient(timeout=60) as client:
        start = time.time()

        # Call via the backend's MCP proxy or directly
        # OCR server is on port 8081 locally
        try:
            # Use MCP tool call format
            resp = await client.post(
                "http://localhost:8081/messages/",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "ocr_document",
                        "arguments": {
                            "document_path": "/documents/claims/claim_auto_011.pdf",
                            "language": "eng",
                            "document_type": "AUTO"
                        }
                    }
                }
            )
            elapsed = time.time() - start

            if resp.status_code == 200:
                result = resp.json()
                # MCP response format
                content = result.get("result", {}).get("content", [])
                if content:
                    text_data = json.loads(content[0].get("text", "{}"))
                    raw_text = text_data.get("raw_text", "")
                    confidence = text_data.get("confidence", 0)
                    print(f"  Time: {elapsed:.2f}s")
                    print(f"  Confidence: {confidence:.2%}")
                    print(f"  Text length: {len(raw_text)} chars")
                    print(f"  Tokens: ~{len(raw_text) // 4} (text only, no LLM call)")
                    print(f"  Preview: {raw_text[:200]}...")
                    return raw_text
                else:
                    print(f"  Empty response: {result}")
            else:
                print(f"  HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"  Error: {e}")
            print("  (OCR server might not be reachable on localhost:8081)")

        elapsed = time.time() - start
        print(f"  Time: {elapsed:.2f}s")
    return None


async def test_2_llamastack_files_upload():
    """Test 2a: Upload document to LlamaStack Files API."""
    print("\n" + "=" * 60)
    print("TEST 2a: Upload PDF to LlamaStack Files API")
    print("=" * 60)

    if not DOC_PATH.exists():
        print(f"  File not found: {DOC_PATH}")
        return None

    async with httpx.AsyncClient(timeout=30) as client:
        start = time.time()

        # Upload file to LlamaStack Files API
        with open(DOC_PATH, "rb") as f:
            resp = await client.post(
                f"{LLAMASTACK}/v1/files",
                files={"file": (DOC_PATH.name, f, "application/pdf")},
                data={"purpose": "assistants"}
            )

        elapsed = time.time() - start

        if resp.status_code == 200:
            result = resp.json()
            file_id = result.get("id")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  File ID: {file_id}")
            print(f"  Response: {json.dumps(result, indent=2)[:300]}")
            return file_id
        else:
            print(f"  HTTP {resp.status_code}: {resp.text[:300]}")
            return None


async def test_2b_llamastack_files_retrieve(file_id: str):
    """Test 2b: Retrieve file content from LlamaStack Files API."""
    print("\n" + "=" * 60)
    print("TEST 2b: Retrieve file from LlamaStack Files API")
    print("=" * 60)

    if not file_id:
        print("  Skipped (no file_id)")
        return None

    async with httpx.AsyncClient(timeout=30) as client:
        start = time.time()

        resp = await client.get(f"{LLAMASTACK}/v1/files/{file_id}/content")

        elapsed = time.time() - start

        if resp.status_code == 200:
            content = resp.content
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Content size: {len(content)} bytes")
            print(f"  Content type: {resp.headers.get('content-type', 'unknown')}")
            return content
        else:
            print(f"  HTTP {resp.status_code}: {resp.text[:300]}")
            return None


async def test_3_vision_direct():
    """Test 3: Send document image directly to Scout vision model."""
    print("\n" + "=" * 60)
    print("TEST 3: Scout Vision (PDF → image → LLM)")
    print("=" * 60)

    if not DOC_PATH.exists():
        print(f"  File not found: {DOC_PATH}")
        return None

    # Convert PDF to image
    try:
        from pdf2image import convert_from_path
        print("  Converting PDF to image...")
        start_convert = time.time()
        images = convert_from_path(str(DOC_PATH), dpi=150, first_page=1, last_page=1)
        convert_time = time.time() - start_convert
        print(f"  PDF→image: {convert_time:.2f}s ({len(images)} page(s))")
    except ImportError:
        print("  pdf2image not installed, trying Pillow with raw bytes...")
        # Fallback: just send the PDF bytes as-is (some models handle it)
        images = None
    except Exception as e:
        print(f"  PDF conversion error: {e}")
        print("  Trying to send raw PDF to model...")
        images = None

    # Encode image to base64
    if images:
        import io
        img = images[0]
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        img_bytes = buf.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode()
        print(f"  Image size: {len(img_bytes)} bytes ({len(img_b64)} base64 chars)")
    else:
        # Fallback: send PDF as base64
        img_bytes = DOC_PATH.read_bytes()
        img_b64 = base64.b64encode(img_bytes).decode()
        print(f"  PDF size: {len(img_bytes)} bytes")

    # Call Scout vision via LlamaStack
    async with httpx.AsyncClient(timeout=120) as client:
        start = time.time()

        payload = {
            "model": SCOUT_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract ALL text from this document image. Return only the raw text, no commentary."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2048,
            "stream": False
        }

        print(f"  Calling Scout vision...")
        resp = await client.post(
            f"{LLAMASTACK}/v1/chat/completions",
            json=payload
        )

        elapsed = time.time() - start

        if resp.status_code == 200:
            result = resp.json()
            usage = result.get("usage", {})
            choices = result.get("choices", [])
            text = choices[0]["message"]["content"] if choices else ""

            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            print(f"  Time: {elapsed:.2f}s (convert: {convert_time:.2f}s + inference: {elapsed - convert_time:.2f}s)" if images else f"  Time: {elapsed:.2f}s")
            print(f"  Tokens: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens}")
            print(f"  Text length: {len(text)} chars")
            print(f"  Preview: {text[:300]}...")
            return text, usage
        else:
            print(f"  HTTP {resp.status_code}")
            try:
                error = resp.json()
                print(f"  Error: {json.dumps(error, indent=2)[:500]}")
            except Exception:
                print(f"  Response: {resp.text[:500]}")
            return None, {}


async def test_4_minio_direct():
    """Test 4: Fetch document directly from MinIO S3 API."""
    print("\n" + "=" * 60)
    print("TEST 4: Direct MinIO S3 fetch")
    print("=" * 60)

    # MinIO S3-compatible GET
    s3_key = "claims/claim_auto_011.pdf"
    url = f"{MINIO_URL}/{s3_key}"

    async with httpx.AsyncClient(timeout=10) as client:
        start = time.time()

        # Anonymous GET (MinIO might need auth)
        resp = await client.get(url)
        elapsed = time.time() - start

        if resp.status_code == 200:
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Size: {len(resp.content)} bytes")
            print(f"  Content-Type: {resp.headers.get('content-type', 'unknown')}")
            return True
        elif resp.status_code == 403:
            print(f"  403 Forbidden (need auth)")
            # Try with presigned or basic auth header
            import hashlib, hmac, datetime
            print(f"  Trying with credentials...")
            # Simple approach: use MinIO mc-style auth headers
            # For demo, just note it needs auth
            return False
        else:
            print(f"  HTTP {resp.status_code}: {resp.text[:200]}")
            return False


async def main():
    print("=" * 60)
    print("OCR vs Vision Benchmark")
    print(f"Document: {DOC_PATH.name}")
    print(f"LlamaStack: {LLAMASTACK}")
    print(f"Model: {SCOUT_MODEL}")
    print("=" * 60)

    # Check document exists
    if DOC_PATH.exists():
        print(f"Local file: {DOC_PATH.stat().st_size} bytes")
    else:
        print(f"WARNING: Local file not found: {DOC_PATH}")

    # Test 1: EasyOCR via MCP server
    ocr_text = await test_1_ocr_server()

    # Test 2: LlamaStack Files API
    file_id = await test_2_llamastack_files_upload()
    if file_id:
        file_content = await test_2b_llamastack_files_retrieve(file_id)

    # Test 3: Scout Vision
    vision_result = await test_3_vision_direct()

    # Test 4: MinIO direct fetch
    await test_4_minio_direct()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if ocr_text:
        print(f"  EasyOCR: {len(ocr_text)} chars, ~{len(ocr_text)//4} tokens (text only)")
    if vision_result and vision_result[0]:
        text, usage = vision_result
        print(f"  Vision:  {len(text)} chars, {usage.get('total_tokens', '?')} tokens (prompt+completion)")
        print(f"           prompt_tokens={usage.get('prompt_tokens', '?')} (includes image)")


if __name__ == "__main__":
    asyncio.run(main())
