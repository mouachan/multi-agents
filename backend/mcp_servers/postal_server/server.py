"""MCP server of the postal complaints (réclamations): read the complaints and their parcel's tracking.

The decisions are not written here: the backend saves them (backend/app/services/decisions.py).
"""
from typing import Any, Dict, Optional

from shared.cases import COMPLAINTS, case_documents, case_statistics, get_case, list_cases
from shared.db import fetch_all
from shared.server import create_mcp, serve
from shared.tools import tool

mcp = create_mcp("postal-server")

TRACKING_EVENTS = 20


@tool(mcp)
async def list_reclamations(status: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    List postal complaints, the most recent first, with their current decision. "total" is the number of
    matching complaints (use it to answer "how many"), the list holds the most recent ones.

    Args:
        status: Optional status filter (pending, processing, completed, rejected, escalated, failed)
        limit: Maximum number of complaints (default 10, at most 100)
    """
    return await list_cases(COMPLAINTS, status, limit)


@tool(mcp)
async def get_reclamation(reclamation_id: str) -> Dict[str, Any]:
    """
    Get a postal complaint: number, type, status, parcel tracking number, declared value,
    description, the latest tracking events of the parcel, and its current decision.
    If has_document is true, ocr_document(document_id=<complaint number>) reads its document.

    Args:
        reclamation_id: The complaint number (e.g. RECL-2026-0001)
    """
    result = await get_case(COMPLAINTS, reclamation_id)
    result["tracking_events"] = await fetch_all("""
        SELECT event_type::text AS event_type, event_date, location, detail, code_postal, is_final
        FROM tracking_events WHERE numero_suivi = :parcel ORDER BY event_date DESC LIMIT :count""",
        parcel=result["reclamation"]["numero_suivi"], count=TRACKING_EVENTS)
    return result


@tool(mcp)
async def get_reclamation_documents(reclamation_id: str) -> Dict[str, Any]:
    """
    Get the documents of a postal complaint with the beginning of their OCR text (empty until
    ocr_document has read them).

    Args:
        reclamation_id: The complaint number (e.g. RECL-2026-0001)
    """
    return await case_documents(COMPLAINTS, reclamation_id)


@tool(mcp)
async def get_reclamation_statistics() -> Dict[str, Any]:
    """Get statistics of the postal complaints: count by status, processing times, current decisions."""
    return await case_statistics(COMPLAINTS)


if __name__ == "__main__":
    serve(mcp)
