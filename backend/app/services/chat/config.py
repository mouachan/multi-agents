"""The chat's texts and suggested actions: helm/multi-agents/files/prompts/backend/chat-config.yaml
(described at the top of that file), mounted in the backend (settings.chat_config_file)."""
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional

import yaml

from app.agents import AgentProfile
from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def chat_config() -> Dict[str, Any]:
    try:
        with open(settings.chat_config_file, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except OSError as e:
        logger.error("Chat configuration %s not found (%s): no welcome texts nor suggestions", settings.chat_config_file, e)
        return {}


def _for_language(texts: Dict[str, Any], language: str) -> Any:
    return texts.get(language) or texts.get("fr")


def detect_language(message: str) -> str:
    """"fr" when the message contains enough French words, else "en"."""
    rules = chat_config().get("language_detection", {})
    french = set(rules.get("fr_words", []))
    return "fr" if len(set(message.lower().split()) & french) >= rules.get("min_match_count", 1) else "en"


def welcome_message(profile: Optional[AgentProfile], language: str) -> str:
    texts = _for_language(chat_config().get("welcome_messages", {}), language) or {}
    if profile is None:
        return texts.get("orchestrator", "")
    name = profile.name_fr if language == "fr" else profile.name
    return texts.get("agent", "{agent_name}").format(agent_name=name)


def suggested_actions(profile_id: Optional[str], language: str) -> List[Dict[str, Any]]:
    """Buttons proposed when a message is routed to a profile ("general" without one)."""
    actions = chat_config().get("suggested_actions", {})
    return _for_language(actions.get(profile_id or "general") or actions.get("general", {}), language) or []


def follow_up_actions(profile_id: Optional[str], answer: str, language: str) -> List[Dict[str, Any]]:
    """Buttons proposed after an agent's answer, depending on what the answer says."""
    rules = chat_config().get("follow_up_actions", {}).get(profile_id or "")
    if not answer or not rules:
        return suggested_actions(None, language) if answer else []
    text = answer.lower()
    actions: List[Dict[str, Any]] = []
    if any(word in text for word in rules.get("go_keywords", [])):
        label = _for_language(rules.get("go_action", {}), language)
        if label:
            actions.append({"label": label, "action": "chat", "params": {}})
    if any(word in text for word in rules.get("result_keywords", [])):
        actions += _for_language(rules.get("result_actions", {}), language) or []
    return actions + (_for_language(rules.get("common", {}), language) or [])


def tool_display() -> Dict[str, Any]:
    """Labels and colors of the MCP tools and servers in the chat UI."""
    return chat_config().get("tool_display", {})
