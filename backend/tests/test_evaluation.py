"""Evaluation of the agents' decisions on the precedents (app/services/evaluation.py)."""
import asyncio
import json

from conftest import API
from app.core.config import settings


async def wait_for_evaluation(client):
    for _ in range(200):
        state = (await client.get(f"{API}/admin/evaluations/current")).json()
        if state["status"] != "running":
            return state
        await asyncio.sleep(0.05)
    raise TimeoutError


async def test_the_precedents_are_evaluated_without_saving_anything(client, agent, fresh_data):
    precedents = json.loads(open(settings.precedents_file, encoding="utf-8").read())
    before = (await client.get(f"{API}/claims/statistics")).json()
    agent.answer.update(decision={"recommendation": "approve", "confidence": 0.9}, tool_calls=[])

    started = (await client.post(f"{API}/admin/evaluations", json={"prompt_alias": "candidate"})).json()
    assert started["status"] == "running" and started["prompt_alias"] == "candidate"
    state = await wait_for_evaluation(client)

    assert state["status"] == "completed" and state["done"] == state["total"] == sum(
        len(precedents[key]) for key in ("claims", "tenders", "reclamations"))
    approved = [p for p in precedents["claims"] if p["recommendation"] == "approve"]
    assert state["metrics"]["accuracy_claims"] == round(len(approved) / len(precedents["claims"]), 3)
    assert all(m["metadata"]["prompt_alias"] == "candidate" for m in agent.requests)    # the version asked
    assert (await client.get(f"{API}/claims/statistics")).json() == before               # nothing saved
