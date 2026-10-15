"""
Admin API endpoints for database management and demo utilities.
"""
import logging
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.auth import User, require_admin
from app.core.config import settings
from app.core.database import get_db
from app.services import access_profiles
from app.services.demo_reset import reset_demo_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reset-database")
async def reset_database(db: AsyncSession = Depends(get_db)):
    """
    Reset the demo data to its state after installation (seed reloaded).

    OCR texts, embeddings, links to the PDFs and the decisions of the installation precedents
    are kept, so the similarity searches work right away (see app/services/demo_reset.py).
    Chat sessions are not affected.
    """
    logger.warning("Demo data reset requested")
    try:
        result = await reset_demo_data(db)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Seed file missing: {e.filename}")
    except Exception as e:
        logger.error(f"Demo data reset failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database reset failed: {e}")
    return {"success": True, "message": "Database reset successfully", "data": result}


@router.get("/database-stats")
async def get_database_stats(db: AsyncSession = Depends(get_db)):
    """Get current database statistics."""
    try:
        stats = {}

        # Users
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        stats['users'] = result.scalar()

        # Contracts
        result = await db.execute(text("SELECT COUNT(*) FROM user_contracts"))
        stats['contracts'] = result.scalar()

        # Claims by status
        result = await db.execute(text("""
            SELECT status, COUNT(*)
            FROM claims
            GROUP BY status
        """))
        stats['claims_by_status'] = {row[0]: row[1] for row in result.fetchall()}

        # Total claims
        stats['claims_total'] = sum(stats['claims_by_status'].values())

        # Knowledge base
        result = await db.execute(text("SELECT COUNT(*) FROM knowledge_base"))
        stats['knowledge_base'] = result.scalar()

        # Embeddings
        result = await db.execute(text("""
            SELECT COUNT(*), COUNT(embedding)
            FROM knowledge_base
        """))
        kb_total, kb_with_emb = result.fetchone()
        stats['knowledge_base_embeddings'] = f"{kb_with_emb}/{kb_total}"

        result = await db.execute(text("""
            SELECT COUNT(*), COUNT(embedding)
            FROM claim_documents
        """))
        cd_total, cd_with_emb = result.fetchone()
        stats['claim_documents_embeddings'] = f"{cd_with_emb}/{cd_total}"

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get database stats: {str(e)}"
        )


# =============================================================================
# Users and access profiles (OpenShift groups)
# =============================================================================

class ProfilesUpdate(BaseModel):
    profiles: List[str]


def _profiles_enabled() -> None:
    if not settings.auth_enabled:
        raise HTTPException(status_code=409, detail="Authentication is disabled: no access profiles to manage")


@router.get("/users")
async def list_users():
    """Users (OpenShift users and members of the profile groups) and their access profiles."""
    _profiles_enabled()
    try:
        return await access_profiles.list_users()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"OpenShift API: {access_profiles.api_error(e)}")


@router.put("/users/{username}/profiles")
async def set_user_profiles(username: str, update: ProfilesUpdate, admin: User = Depends(require_admin)):
    """Give a user exactly these profiles (membership of the profile groups)."""
    _profiles_enabled()
    try:
        return await access_profiles.set_profiles(username, set(update.profiles), admin)
    except access_profiles.ProfileError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"OpenShift API: {access_profiles.api_error(e)}")
