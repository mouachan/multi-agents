"""
MCP Tracking Server - Parcel tracking timeline and status queries via PostgreSQL.

Simple CRUD operations on tracking_events and reclamations tables.
FastMCP implementation with Streamable HTTP transport (SSE).
"""

import json
import logging
import os

from mcp.server.fastmcp import FastMCP
from sqlalchemy import text
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse

from shared.db import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB,
    check_database_connection, run_db_query, run_db_query_one, run_db_execute,
)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP(
    "tracking-server",
    stateless_http=True,
    json_response=True
)


# =============================================================================
# MCP Tools - Tracking
# =============================================================================

@mcp.tool()
async def get_tracking(numero_suivi: str) -> str:
    """
    Get the complete tracking timeline for a parcel.

    Returns the full list of tracking events ordered chronologically,
    whether the parcel has been delivered, the last event details,
    and the related reclamation if one exists.

    Args:
        numero_suivi: The parcel tracking number (e.g., TRACK-2024-00001)

    Returns:
        JSON with keys: numero_suivi, events, is_delivered, last_event, reclamation
    """
    logger.info(f"Getting tracking timeline: {numero_suivi}")

    if not numero_suivi or not numero_suivi.strip():
        return json.dumps({"success": False, "error": "numero_suivi is required"})

    numero_suivi = numero_suivi.strip()

    try:
        # Get all tracking events ordered chronologically
        events_query = text("""
            SELECT
                id, numero_suivi, event_date, event_type::text AS event_type,
                location, detail, code_postal, is_final
            FROM tracking_events
            WHERE numero_suivi = :numero_suivi
            ORDER BY event_date ASC
        """)
        events_results = await run_db_query(events_query, {"numero_suivi": numero_suivi})

        events = []
        is_delivered = False
        last_event = None

        for row in events_results:
            event = dict(row._mapping)
            event['id'] = str(event['id'])
            for key, value in event.items():
                if hasattr(value, 'isoformat'):
                    event[key] = value.isoformat()
            events.append(event)

            # Check delivery status
            if event.get('event_type') in ('livre',) or event.get('is_final'):
                is_delivered = True

        # Last event is the most recent one
        if events:
            last_event = events[-1]

        # Get related reclamation if any
        reclamation_query = text("""
            SELECT
                id, reclamation_number, numero_suivi, client_nom, client_email,
                reclamation_type::text AS reclamation_type, description,
                status::text AS status, created_at, updated_at
            FROM reclamations
            WHERE numero_suivi = :numero_suivi
        """)
        reclamation_result = await run_db_query_one(reclamation_query, {"numero_suivi": numero_suivi})

        reclamation = None
        if reclamation_result:
            reclamation = dict(reclamation_result._mapping)
            reclamation['id'] = str(reclamation['id'])
            for key, value in reclamation.items():
                if hasattr(value, 'isoformat'):
                    reclamation[key] = value.isoformat()

        logger.info(f"Found {len(events)} tracking events for {numero_suivi} (delivered={is_delivered})")

        return json.dumps({
            "success": True,
            "numero_suivi": numero_suivi,
            "events": events,
            "total_events": len(events),
            "is_delivered": is_delivered,
            "last_event": last_event,
            "reclamation": reclamation
        }, default=str)

    except Exception as e:
        logger.error(f"Error getting tracking: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def search_tracking(client_email: str) -> str:
    """
    Search tracking information by client email.

    Finds all reclamations for the given email address and returns
    each parcel with its latest tracking status.

    Args:
        client_email: The client's email address

    Returns:
        JSON with list of parcels and their latest tracking status
    """
    logger.info(f"Searching tracking by email: {client_email}")

    if not client_email or not client_email.strip():
        return json.dumps({"success": False, "error": "client_email is required"})

    client_email = client_email.strip().lower()

    try:
        # Get all reclamations for this client
        reclamations_query = text("""
            SELECT
                id, reclamation_number, numero_suivi, client_nom, client_email,
                reclamation_type::text AS reclamation_type, description,
                status::text AS status, created_at
            FROM reclamations
            WHERE LOWER(client_email) = :email
            ORDER BY created_at DESC
        """)
        reclamations_results = await run_db_query(reclamations_query, {"email": client_email})

        parcels = []
        for row in reclamations_results:
            reclamation = dict(row._mapping)
            reclamation['id'] = str(reclamation['id'])
            for key, value in reclamation.items():
                if hasattr(value, 'isoformat'):
                    reclamation[key] = value.isoformat()

            # Get latest tracking event for this parcel
            latest_event_query = text("""
                SELECT
                    id, numero_suivi, event_date, event_type::text AS event_type,
                    location, detail, code_postal, is_final
                FROM tracking_events
                WHERE numero_suivi = :numero_suivi
                ORDER BY event_date DESC
                LIMIT 1
            """)
            latest_event_result = await run_db_query_one(
                latest_event_query, {"numero_suivi": reclamation['numero_suivi']}
            )

            latest_event = None
            if latest_event_result:
                latest_event = dict(latest_event_result._mapping)
                latest_event['id'] = str(latest_event['id'])
                for key, value in latest_event.items():
                    if hasattr(value, 'isoformat'):
                        latest_event[key] = value.isoformat()

            parcels.append({
                "reclamation": reclamation,
                "latest_tracking_event": latest_event
            })

        logger.info(f"Found {len(parcels)} parcels for {client_email}")

        return json.dumps({
            "success": True,
            "client_email": client_email,
            "parcels": parcels,
            "total_found": len(parcels)
        }, default=str)

    except Exception as e:
        logger.error(f"Error searching tracking: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


# =============================================================================
# Health Check
# =============================================================================

async def health_check(request):
    """Health check endpoint for liveness/readiness probes."""
    health_status = {
        "status": "healthy",
        "service": "tracking-server",
        "database_ready": False
    }

    try:
        await run_db_query_one(text("SELECT 1"), {})
        health_status["database_ready"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"

    return JSONResponse(health_status)


async def sse_options(request):
    """Handle OPTIONS requests for MCP SSE endpoint discovery."""
    return JSONResponse({
        "methods": ["GET", "POST", "OPTIONS"],
        "mcp_version": "0.1.0",
        "server_name": "tracking-server",
        "capabilities": {"tools": True, "streaming": True}
    })


# =============================================================================
# Starlette App
# =============================================================================

mcp_sse_app = mcp.sse_app()

app = Starlette(
    routes=[
        Route("/health", health_check),
        Route("/sse", sse_options, methods=["OPTIONS"]),
        Route("/", sse_options, methods=["OPTIONS"]),
        Mount("/", app=mcp_sse_app),
    ]
)


if __name__ == "__main__":
    import uvicorn

    try:
        check_database_connection()
    except Exception as e:
        logger.critical(f"Failed to connect to database: {e}")
        exit(1)

    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting MCP Tracking Server on {host}:{port}")
    logger.info(f"Database: {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    logger.info("Tools: get_tracking, search_tracking")

    uvicorn.run(app, host=host, port=port)
