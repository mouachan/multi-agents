"""The authenticated user, its access profiles and the agents it may use (app/core/auth.py)."""
from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.core.auth import User, current_user

router = APIRouter()


@router.get("/me")
async def me(user: User = Depends(current_user)) -> Dict[str, Any]:
    return user.to_dict()
