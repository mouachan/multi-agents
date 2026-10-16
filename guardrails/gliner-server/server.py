"""Finds people's names (and other personal data) in six languages, for NeMo Guardrails.

NeMo's built-in detector (Presidio) runs an English model: it misses French names and takes French
words for names. This server runs GLiNER (urchade/gliner_multi_pii-v1: en, fr, de, es, it, pt) for the
rails "gliner mask pii on input / output" (helm/multi-agents/templates/guardrails/nemo-configmap.yaml),
with the API that nemoguardrails/library/gliner expects:

    POST /v1/extract  {"text", "labels"?, "threshold", "chunk_length", "overlap", "flat_ner"}
                   -> {"entities": [{"value", "suggested_label", "start_position", "end_position", "score"}],
                       "total_entities", "tagged_text"}
    GET  /health      503 until the model is loaded

NeMo replaces each entity by its label in capitals: "person" -> [PERSON]. The text is read in
overlapping chunks of CHUNK_CHARS characters, all in one batch (the model reads up to 384 words; NeMo's
default chunk_length, 384 characters, would cut a page in a dozen pieces); every occurrence of a name
is returned, and of two overlapping spans the best scored is kept.
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("gliner-server")

MODEL_NAME = os.getenv("MODEL_NAME", "urchade/gliner_multi_pii-v1")
DEFAULT_LABELS = os.getenv("DEFAULT_LABELS", "person").split(",")
CHUNK_CHARS = int(os.getenv("CHUNK_CHARS", "1500"))   # ~250 words, under the model's 384
# The model sometimes takes a personal pronoun for a person ("Je peux vous aider" -> "Je": 0.86)
PRONOUNS = {"je", "j", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles", "moi", "toi", "lui", "eux",
            "i", "you", "he", "she", "we", "they", "me", "him", "her", "us", "them"}

model = None


class ExtractRequest(BaseModel):
    text: str
    labels: Optional[List[str]] = None
    threshold: float = 0.5
    chunk_length: int = 384       # characters per chunk (at least CHUNK_CHARS are read)
    overlap: int = 128            # characters shared by two consecutive chunks
    flat_ner: bool = True


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global model
    from gliner import GLiNER       # heavy import (torch): only in the running server
    logger.info("Loading %s", MODEL_NAME)
    model = GLiNER.from_pretrained(MODEL_NAME)
    logger.info("Model loaded; default labels: %s", ", ".join(DEFAULT_LABELS))
    yield


app = FastAPI(title="GLiNER PII server", lifespan=lifespan)


@app.get("/health")
def health():
    if model is None:
        return JSONResponse({"status": "loading", "model": MODEL_NAME}, status_code=503)
    return {"status": "healthy", "model": MODEL_NAME}


@app.post("/v1/extract")
def extract(request: ExtractRequest) -> Dict[str, Any]:
    if model is None:
        raise HTTPException(status_code=503, detail="The model is loading")
    labels = request.labels or DEFAULT_LABELS
    pieces = list(chunks(request.text, max(request.chunk_length, CHUNK_CHARS), request.overlap))
    results = model.inference([chunk for _, chunk in pieces], labels, threshold=request.threshold,
                              flat_ner=request.flat_ner) if pieces else []
    found = [{"value": entity["text"], "suggested_label": entity["label"], "score": float(entity["score"]),
              "start_position": offset + entity["start"], "end_position": offset + entity["end"]}
             for (offset, _), chunk_entities in zip(pieces, results) for entity in chunk_entities]
    entities = without_overlaps([e for e in found if e["value"].strip(" '’").lower() not in PRONOUNS])
    return {"entities": entities, "total_entities": len(entities), "tagged_text": tagged(request.text, entities)}


def chunks(text: str, length: int, overlap: int):
    """(offset, chunk) pairs covering the text; a chunk ends at a space when it can, not in a word."""
    start = 0
    while start < len(text):
        end = min(start + length, len(text))
        if end < len(text) and " " in text[start + overlap:end]:
            end = text.rindex(" ", start + overlap, end)
        yield start, text[start:end]
        if end == len(text):
            return
        start = max(end - overlap, start + 1)


def without_overlaps(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every entity once: of overlapping spans (two chunks saw the same name), the best scored stays."""
    kept: List[Dict[str, Any]] = []
    for entity in sorted(entities, key=lambda e: -e["score"]):
        if all(entity["end_position"] <= k["start_position"] or entity["start_position"] >= k["end_position"] for k in kept):
            kept.append(entity)
    return sorted(kept, key=lambda e: e["start_position"])


def tagged(text: str, entities: List[Dict[str, Any]]) -> str:
    """The text with each entity written [value](label)."""
    for entity in reversed(entities):
        start, end = entity["start_position"], entity["end_position"]
        text = f"{text[:start]}[{text[start:end]}]({entity['suggested_label']}){text[end:]}"
    return text


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
