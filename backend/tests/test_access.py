"""Access profiles (app/core/auth.py): what a user may see and do follows OpenShift RBAC.

OpenShift is replaced by a fake: the TokenReview gives the user, the SubjectAccessReview grants the
agents of the user's profile and the MCP tools it may call.
"""
import json

import pytest

from app.core import auth
from app.core.config import settings
from conftest import API

USERS = {  # token -> (user name, agents the profile gives, administrator, tools it may not call)
    "finance-token": ("demo-finance", {"claims"}, False, {"run_python"}),
    "admin-token": ("demo-admin", {"claims", "tenders", "postal"}, True, set()),
    "no-ocr-token": ("demo-intern", {"claims"}, False, {"run_python", "ocr_document"}),
}
AGENT_TOOLS = {"claims": ["get_claim", "ocr_document", "retrieve_user_info", "retrieve_similar_claims",
                          "compute_payout", "run_python"],
               "tenders": ["get_tender"], "postal": ["get_reclamation"]}


@pytest.fixture
def openshift(monkeypatch):
    async def review_token(token):
        if token not in USERS:
            return None
        return {"username": USERS[token][0], "groups": []}

    async def can(username, groups, verb, name, resource="services", api_group=""):
        _, agents, admin, denied = next(user for user in USERS.values() if user[0] == username)
        if verb == "call":
            return name not in denied
        return admin if verb == "admin" else name.removesuffix("-agent") in agents

    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_agent_tools", json.dumps(AGENT_TOOLS))
    monkeypatch.setattr(auth.kubernetes, "review_token", review_token)
    monkeypatch.setattr(auth.kubernetes, "can", can)
    auth._cache.clear()


def as_user(token: str):
    return {"Authorization": f"Bearer {token}"}


async def test_no_token_no_access(client, openshift):
    assert (await client.get(f"{API}/claims/")).status_code == 401


async def test_a_profile_only_reaches_its_domains(client, openshift):
    finance = as_user("finance-token")
    assert (await client.get(f"{API}/claims/", headers=finance)).status_code == 200
    assert (await client.get(f"{API}/tenders/", headers=finance)).status_code == 403
    assert (await client.post(f"{API}/admin/reset", headers=finance)).status_code == 403
    me = (await client.get(f"{API}/auth/me", headers=finance)).json()
    assert me["domains"] == ["claims"] and me["admin"] is False


async def test_chat_offers_only_the_profiles_agents(client, openshift):
    agents = (await client.get(f"{API}/chat/agents", headers=as_user("finance-token"))).json()
    assert [agent["id"] for agent in agents] == ["claims"]
    refused = await client.post(f"{API}/chat/sessions", json={"agent_id": "tenders"}, headers=as_user("finance-token"))
    assert refused.status_code == 403


async def test_review_is_limited_to_the_profiles_domains(client, openshift):
    tender = (await client.get(f"{API}/tenders/", headers=as_user("admin-token"))).json()["items"][0]
    response = await client.get(f"{API}/review/tenders/{tender['id']}", headers=as_user("finance-token"))
    assert response.status_code == 403


async def test_conversations_are_private(client, openshift, agent):
    session = (await client.post(f"{API}/chat/sessions", json={}, headers=as_user("admin-token"))).json()
    response = await client.get(f"{API}/chat/sessions/{session['session_id']}/messages",
                                headers=as_user("finance-token"))
    assert response.status_code == 404


async def test_the_agent_only_gets_the_tools_the_profile_allows(client, openshift, agent):
    me = (await client.get(f"{API}/auth/me", headers=as_user("finance-token"))).json()
    assert "run_python" not in me["tools"] and "get_claim" in me["tools"]
    assert "get_tender" not in me["tools"]                     # tools of an agent the profile does not give

    agent.answer = {**agent.answer, "output": "Voici le sinistre."}
    session = (await client.post(f"{API}/chat/sessions", json={}, headers=as_user("finance-token"))).json()
    await client.post(f"{API}/chat/sessions/{session['session_id']}/messages",
                      json={"message": "Montre-moi le sinistre CLM-2024-0001"}, headers=as_user("finance-token"))
    assert agent.requests[-1]["metadata"]["allowed_tools"] == me["tools"]


async def test_a_processing_needs_every_tool_of_its_workflow(client, openshift, agent):
    claim = (await client.get(f"{API}/claims/", headers=as_user("admin-token"))).json()["items"][0]
    refused = await client.post(f"{API}/claims/{claim['id']}/process", headers=as_user("no-ocr-token"))
    assert refused.status_code == 403 and "ocr_document" in refused.json()["detail"]
    assert agent.requests == []                                 # the agent was not asked
