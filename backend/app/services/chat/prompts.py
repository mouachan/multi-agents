"""The prompt editor of the chat: the system prompt the agent profile runs, and a per-conversation override.

The prompt shown is the one the agent really uses: version "@production" of the profile's prompt in
the MLflow Prompt Registry (the agents load it the same way, agents/shared/prompts.py). An override is
kept in the conversation (metadata "custom_prompt") and sent to the agent with each message
("instructions_override", app/services/chat/turn.py).
"""
import logging
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import get_profile
from app.core.config import settings
from app.core.tracing import mlflow_headers, mlflow_verify
from app.models.conversation import ChatSession

logger = logging.getLogger(__name__)

PROMPT_ALIAS = "production"
PROMPT_TEXT_TAG = "mlflow.prompt.text"


async def registry_prompt(name: str) -> Optional[Dict[str, Any]]:
    """Text and version of prompt `name`@production in MLflow (None when unavailable)."""
    if not settings.mlflow_tracking_uri:
        return None
    url = f"{settings.mlflow_tracking_uri.rstrip('/')}/api/2.0/mlflow/registered-models/alias"
    try:
        async with httpx.AsyncClient(verify=mlflow_verify(), timeout=10) as client:
            resp = await client.get(url, params={"name": name, "alias": PROMPT_ALIAS}, headers=mlflow_headers())
            resp.raise_for_status()
            version = resp.json()["model_version"]
    except Exception as e:
        logger.warning("Prompt %s@%s unavailable in MLflow: %s", name, PROMPT_ALIAS, e)
        return None
    tags = {tag["key"]: tag["value"] for tag in version.get("tags", [])}
    return {"name": name, "version": version.get("version"), "text": tags.get(PROMPT_TEXT_TAG, "")}


async def session_prompt(session: ChatSession) -> Dict[str, Any]:
    """The prompt of the conversation's profile: its override, or the MLflow version the agent runs."""
    custom = (session.session_metadata or {}).get("custom_prompt")
    profile = get_profile(session.agent_id)
    if custom:
        return {"prompt": custom, "is_custom": True, "agent_id": session.agent_id}
    if profile is None:   # no agent yet: the router picks one with the first message
        return {"prompt": "", "is_custom": False, "agent_id": None}
    stored = await registry_prompt(profile.prompt)
    return {"prompt": stored["text"] if stored else "", "is_custom": False, "agent_id": profile.id,
            "name": profile.prompt, "version": stored["version"] if stored else None}


async def set_session_prompt(db: AsyncSession, session: ChatSession, prompt: Optional[str]) -> Dict[str, Any]:
    """Override the profile's prompt in this conversation (None: back to the MLflow version)."""
    metadata = dict(session.session_metadata or {})
    if prompt:
        metadata["custom_prompt"] = prompt
    else:
        metadata.pop("custom_prompt", None)
    session.session_metadata = metadata
    await db.commit()
    return await session_prompt(session)
