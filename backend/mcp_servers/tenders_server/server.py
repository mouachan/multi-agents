"""MCP server of the construction tenders (appels d'offres): read the tenders.

A tender's details (title, client, budget, region, lots, award criteria...) are in its metadata.
The decisions are not written here: the backend saves them (backend/app/services/decisions.py).
"""
from typing import Any, Dict, Optional

from shared.cases import TENDERS, case_documents, case_statistics, get_case, list_cases
from shared.server import create_mcp, serve
from shared.tools import tool

mcp = create_mcp("tenders-server")


@tool(mcp)
async def list_tenders(status: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    List tenders (appels d'offres), the most recent first, with their details and current decision. "matching" is the number of
    tenders with this status (the answer to "how many"); the list holds the most recent ones.

    Args:
        status: Optional status filter (pending, processing, completed, manual_review, declined, failed)
        limit: Maximum number of tenders (default 10, at most 100)
    """
    return await list_cases(TENDERS, status, limit)


@tool(mcp)
async def get_tender(tender_id: str) -> Dict[str, Any]:
    """
    Get a tender: number, type, status, dates, metadata (titre, maitre_ouvrage, montant_estime,
    region, lots, criteres_attribution, date_limite_remise...) and its current decision.
    If has_document is true, ocr_document(document_id=<tender number>) reads its document.

    Args:
        tender_id: The tender number (e.g. AO-2026-IDF-001)
    """
    return await get_case(TENDERS, tender_id)


@tool(mcp)
async def get_tender_documents(tender_id: str) -> Dict[str, Any]:
    """
    Get the documents of a tender with the beginning of their OCR text (empty until ocr_document
    has read them).

    Args:
        tender_id: The tender number (e.g. AO-2026-IDF-001)
    """
    return await case_documents(TENDERS, tender_id)


@tool(mcp)
async def get_tender_statistics() -> Dict[str, Any]:
    """Get statistics of the tenders: count by status, processing times, current decisions."""
    return await case_statistics(TENDERS)


if __name__ == "__main__":
    serve(mcp)
