"""Test fixtures.

The application runs against the PostgreSQL of tests/compose.yaml (same schema and seed as the cluster
database), without authentication (every request is a local administrator) unless a test enables it.
The A2A agents are replaced by FakeAgent, which records what it is asked and answers what the test sets.
"""
import asyncio
import json
from typing import Any, Dict, List

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import AsyncSessionLocal
from app.domains import all_domains
from app.main import app
from app.services import background
from app.services.demo_reset import reset_demo_data

API = "/api/v1"


class FakeAgent:
    """Stands for the A2A agents (app/services/a2a_client.py)."""

    def __init__(self) -> None:
        self.requests: List[Dict[str, Any]] = []
        self.answer: Dict[str, Any] = {"output": "", "decision": {}, "tool_calls": [], "model": "maas/test-model"}
        self.fail = False

    def _record(self, base_url, message, context_id, metadata) -> None:
        self.requests.append({"url": base_url, "message": message, "context_id": context_id, "metadata": metadata or {}})
        if self.fail:
            raise RuntimeError("agent unavailable")

    async def send(self, base_url, message, context_id=None, metadata=None):
        self._record(base_url, message, context_id, metadata)
        return {"status": "completed", **self.answer}

    async def stream(self, base_url, message, context_id=None, metadata=None):
        self._record(base_url, message, context_id, metadata)
        for word in self.answer.get("output", "").split(" "):
            yield {"type": "text_delta", "delta": word + " "}
        yield {"type": "done", "status": "completed", **self.answer}


@pytest.fixture
def agent(monkeypatch) -> FakeAgent:
    fake = FakeAgent()
    for module in ("app.services.processing", "app.services.review", "app.services.chat.turn"):
        monkeypatch.setattr(f"{module}.get_a2a_client", lambda: fake)
    return fake


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http


@pytest.fixture
async def fresh_data():
    """The demo data of the installation, for tests that change cases."""
    async with AsyncSessionLocal() as db:
        await reset_demo_data(db)


async def wait_for_jobs() -> None:
    """Wait for the processing jobs started in the background (app/services/background.py)."""
    while background._tasks:
        await asyncio.gather(*list(background._tasks), return_exceptions=True)


def tool_call(name: str, output: Dict[str, Any]) -> Dict[str, Any]:
    """A tool call as the agent reports it (its output is a JSON string)."""
    return {"name": name, "arguments": "{}", "output": json.dumps(output), "server": "mcp-gateway"}


@pytest.fixture(params=[spec.name for spec in all_domains()])
def domain(request):
    """Run a test once per domain."""
    from app.domains import get_domain
    return get_domain(request.param)


async def first_case(client: AsyncClient, domain: str, status: str = "pending") -> Dict[str, Any]:
    cases = (await client.get(f"{API}/{domain}/")).json()["items"]
    return next(case for case in cases if case["status"] == status)
