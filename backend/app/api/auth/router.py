"""The authenticated user, its access profiles and the agents it may use (app/core/auth.py)."""
from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.core.auth import User, current_user
from app.core.config import settings

router = APIRouter()


@router.get("/me")
async def me(user: User = Depends(current_user)) -> Dict[str, Any]:
    # authEnabled=false: local stack, every user is an administrator (no profiles to manage)
    return {**user.to_dict(), "authEnabled": settings.auth_enabled}
