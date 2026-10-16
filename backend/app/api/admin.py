"""Administration API (administrator profile only, see app/main.py).

    POST /api/v1/admin/reset                   back to the demo data of the installation (app/services/demo_reset.py)
    GET  /api/v1/admin/overview                what the database holds: cases per domain and status, embeddings
    GET  /api/v1/admin/users                   users and their access profiles (app/services/access_profiles.py)
    PUT  /api/v1/admin/users/<name>/profiles   give a user exactly these profiles   {profiles}
"""
import logging
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User, require_admin
from app.core.config import settings
from app.core.database import get_db
from app.domains import all_domains
from app.services import access_profiles
from app.services.demo_reset import REFERENCE_KEYS, reset_demo_data

logger = logging.getLogger(__name__)
router = APIRouter()


class ProfilesUpdate(BaseModel):
    profiles: List[str]


@router.post("/reset")
async def reset(db: AsyncSession = Depends(get_db)):
    """Reload the demo data, keeping the OCR texts, embeddings, PDF links and the installation
    precedents, so the similarity searches work right away. Conversations are kept."""
    logger.warning("Demo data reset requested")
    try:
        return await reset_demo_data(db)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Seed file missing: {e.filename}")


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    domains = []
    for spec in all_domains():
        rows = (await db.execute(select(spec.model.status, func.count()).group_by(spec.model.status))).all()
        documents, embedded = (await db.execute(
            select(func.count(), func.count(spec.document_model.embedding)))).one()
        domains.append({"domain": spec.name,
                        "by_status": {getattr(status, "value", status): count for status, count in rows},
                        "documents": documents, "documents_with_embedding": embedded})
    references = {}
    for table in REFERENCE_KEYS:   # reference data searched by the RAG tools
        total, embedded = (await db.execute(text(f"SELECT COUNT(*), COUNT(embedding) FROM {table}"))).one()
        references[table] = {"rows": total, "with_embedding": embedded}
    return {"domains": domains, "references": references}


def _profiles_enabled() -> None:
    if not settings.auth_enabled:
        raise HTTPException(status_code=409, detail="Authentication is disabled: no access profiles to manage")


@router.get("/users")
async def list_users():
    _profiles_enabled()
    try:
        return await access_profiles.list_users()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"OpenShift API: {access_profiles.api_error(e)}")


@router.put("/users/{username}/profiles")
async def set_user_profiles(username: str, update: ProfilesUpdate, admin: User = Depends(require_admin)):
    _profiles_enabled()
    try:
        return await access_profiles.set_profiles(username, set(update.profiles), admin)
    except access_profiles.ProfileError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"OpenShift API: {access_profiles.api_error(e)}")
