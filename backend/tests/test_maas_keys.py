"""The models are called as the user (app/services/maas_keys.py): the agent gets the user's MaaS key,
bound to the subscription of their access profile."""
import json

import pytest

from app.core.auth import User
from app.core.config import settings
from app.services import maas_keys
from conftest import API
from test_access import as_user, openshift  # noqa: F401  (fixture)

PROFILES = {
    "admin": {"group": "multi-agents-admins", "tokenQuota": {"limit": 3000000, "window": "1h", "priority": 9}},
    "finance": {"group": "multi-agents-finance", "tokenQuota": {"limit": 500000, "window": "1h", "priority": 8}},
    "guest": {"group": "multi-agents-guests"},
}


def user(*profiles):
    return User("someone", (), frozenset(), False, profiles)


@pytest.fixture
def maas(monkeypatch):
    """The MaaS API is replaced by a fake that mints a key named after its subscription."""
    minted = []

    async def mint(token, subscription):
        minted.append(subscription)
        return f"sk-oai-{subscription}"

    monkeypatch.setattr(settings, "auth_profiles", json.dumps(PROFILES))
    monkeypatch.setattr(settings, "maas_api_url", "https://maas.example.com/maas-api/v1")
    monkeypatch.setattr(maas_keys, "_mint", mint)
    maas_keys._keys.clear()
    return minted


def test_the_subscription_is_the_profiles_one_with_the_highest_priority(maas):
    assert maas_keys.subscription_of(user("finance")) == "multi-agents-finance"
    assert maas_keys.subscription_of(user("finance", "admin")) == "multi-agents-admin"
    assert maas_keys.subscription_of(user("guest")) == "multi-agents-users"     # no quota of its own


async def test_the_agent_gets_the_users_key_minted_once(client, openshift, agent, maas):  # noqa: F811
    agent.answer = {**agent.answer, "output": "Bonjour."}
    session = (await client.post(f"{API}/chat/sessions", json={}, headers=as_user("finance-token"))).json()
    for _ in range(2):
        await client.post(f"{API}/chat/sessions/{session['session_id']}/messages",
                          json={"message": "Montre-moi le sinistre CLM-2024-0001"}, headers=as_user("finance-token"))
    metadata = agent.requests[-1]["metadata"]
    assert metadata["user_token"] == "finance-token"
    assert metadata["model_key"] == "sk-oai-multi-agents-users"   # the fake user has no profile group
    assert maas == ["multi-agents-users"]                          # minted once, then reused


async def test_without_the_maas_api_the_platform_key_is_used(client, openshift, agent):  # noqa: F811
    agent.answer = {**agent.answer, "output": "Bonjour."}
    session = (await client.post(f"{API}/chat/sessions", json={}, headers=as_user("finance-token"))).json()
    await client.post(f"{API}/chat/sessions/{session['session_id']}/messages",
                      json={"message": "Montre-moi le sinistre CLM-2024-0001"}, headers=as_user("finance-token"))
    assert "model_key" not in agent.requests[-1]["metadata"]
