"""MCP server of the parcel tracking: the timeline of a parcel."""
from typing import Any, Dict

from shared.db import fetch_all, fetch_one
from shared.server import create_mcp, serve
from shared.tools import ToolError, required, tool

mcp = create_mcp("tracking-server")

EVENT_COLUMNS = "event_date, event_type::text AS event_type, location, detail, code_postal, is_final"
COMPLAINT_COLUMNS = ("reclamation_number, numero_suivi, client_nom, client_email, "
                     "reclamation_type::text AS reclamation_type, description, status::text AS status, created_at")


@tool(mcp)
async def get_tracking(numero_suivi: str) -> Dict[str, Any]:
    """
    Get the tracking timeline of a parcel: its events in chronological order, whether it was
    delivered, its last event, and the complaint about it if there is one.

    Args:
        numero_suivi: The parcel tracking number (e.g. 6C123456789FR)
    """
    parcel = required(numero_suivi, "numero_suivi")
    events = await fetch_all(f"SELECT {EVENT_COLUMNS} FROM tracking_events WHERE numero_suivi = :parcel "
                             "ORDER BY event_date", parcel=parcel)
    if not events:
        raise ToolError(f"No tracking events for parcel {parcel}")
    complaint = await fetch_one(f"SELECT {COMPLAINT_COLUMNS} FROM reclamations WHERE numero_suivi = :parcel",
                                parcel=parcel)
    return {
        "numero_suivi": parcel,
        "events": events,
        "total_events": len(events),
        "is_delivered": any(e["event_type"] == "livre" or e["is_final"] for e in events),
        "last_event": events[-1],
        "reclamation": complaint,
    }


if __name__ == "__main__":
    serve(mcp)
