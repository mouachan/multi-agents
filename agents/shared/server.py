import logging
from typing import Dict, List

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.fastapi_routes import add_a2a_routes_to_fastapi
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentProvider, AgentSkill
from fastapi import FastAPI

from . import spiffe_auth, tracing
from .config import AgentSettings
from .executor import DomainAgentExecutor, Profile

AGENT_VERSION = "3.5.0"


def create_app(name: str, description: str, profiles: Dict[str, Profile],
               skills: List[AgentSkill]) -> tuple[FastAPI, AgentSettings]:
    settings = AgentSettings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    tracing.init(settings)

    public_url = settings.agent_public_url or f"http://localhost:{settings.agent_port}"
    card = AgentCard(
        name=name,
        description=description,
        version=AGENT_VERSION,
        provider=AgentProvider(organization="multi-agents demo", url=public_url),
        supported_interfaces=[
            AgentInterface(url=public_url, protocol_binding="JSONRPC", protocol_version="1.0"),
        ],
        capabilities=AgentCapabilities(streaming=True, push_notifications=False),
        skills=skills,
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
    )

    executor = DomainAgentExecutor(settings, profiles)
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )

    app = FastAPI(title=name, version=AGENT_VERSION)
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
    )

    if spiffe_auth.enabled():
        app.add_middleware(
            spiffe_auth.SpiffeJwtMiddleware,
            audience=f"a2a:{settings.agent_id}-agent",
            allowed_paths=settings.spiffe_allowed_ids.split(","),
        )

    @app.get("/health")
    async def health():
        return {"status": "ok", "agent": settings.agent_id, "profiles": list(profiles)}

    return app, settings


def run(name: str, description: str, profiles: Dict[str, Profile], skills: List[AgentSkill]):
    app, settings = create_app(name, description, profiles, skills)
    uvicorn.run(app, host="0.0.0.0", port=settings.agent_port)
