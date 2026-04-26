"""
Agent Registry - Central registry for all agents.

Each agent registers with: id, name, description, service_class,
tools, prompts, entity_type, color, icon.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


@dataclass
class AgentDefinition:
    """Definition of a registered agent."""
    id: str
    name: str
    description: str
    entity_type: str
    service_class: Type[Any]
    instructions: str
    user_message_template: str
    tools: List[str] = field(default_factory=list)
    color: str = "blue"
    icon: str = "document"
    api_prefix: str = ""
    decision_values: List[str] = field(default_factory=list)
    routing_keywords: List[str] = field(default_factory=list)
    model: Optional[str] = None
    frontend_path: Optional[str] = None
    name_fr: Optional[str] = None
    description_fr: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    """Central registry for all agents."""

    _agents: Dict[str, AgentDefinition] = {}

    @classmethod
    def register(cls, definition: AgentDefinition) -> None:
        """Register an agent definition."""
        if definition.id in cls._agents:
            logger.warning(f"Agent '{definition.id}' already registered, overwriting")
        cls._agents[definition.id] = definition
        logger.info(f"Registered agent: {definition.id} ({definition.name})")

    @classmethod
    def get(cls, agent_id: str) -> Optional[AgentDefinition]:
        """Get agent definition by ID."""
        return cls._agents.get(agent_id)

    @classmethod
    def get_by_entity_type(cls, entity_type: str) -> Optional[AgentDefinition]:
        """Get agent definition by entity_type (e.g. 'claim', 'tender')."""
        return next((a for a in cls._agents.values() if a.entity_type == entity_type), None)

    @classmethod
    def list_agents(cls) -> List[AgentDefinition]:
        """List all registered agents."""
        return list(cls._agents.values())

    @classmethod
    def to_api_list(cls) -> List[Dict[str, Any]]:
        """Return agent list formatted for API response."""
        return [
            {
                "id": a.id,
                "name": a.name,
                "name_fr": a.name_fr,
                "description": a.description,
                "description_fr": a.description_fr,
                "entity_type": a.entity_type,
                "path": a.frontend_path or f"/{a.entity_type}s",
                "api_prefix": a.api_prefix,
                "color": a.color,
                "icon": a.icon,
                "tools": a.tools,
                "decision_values": a.decision_values,
            }
            for a in cls._agents.values()
        ]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered agents (for testing)."""
        cls._agents.clear()
