"""Demo reset (app/services/demo_reset.py): the cases are back to their installation state."""
from conftest import API, first_case, wait_for_jobs


async def test_reset_brings_processed_cases_back(client, agent, fresh_data):
    claim = await first_case(client, "claims")
    agent.answer.update(decision={"recommendation": "approve", "confidence": 0.9})
    await client.post(f"{API}/claims/{claim['id']}/process")
    await wait_for_jobs()
    assert (await client.get(f"{API}/claims/{claim['id']}")).json()["status"] == "completed"

    result = (await client.post(f"{API}/admin/reset")).json()
    assert result["loaded"]["claims"] > 0

    reloaded = next(c for c in (await client.get(f"{API}/claims/")).json()["items"] if c["number"] == claim["number"])
    assert reloaded["status"] == "pending"


async def test_overview_counts_every_domain(client):
    overview = (await client.get(f"{API}/admin/overview")).json()
    assert {d["domain"] for d in overview["domains"]} == {"claims", "tenders", "postal"}
    assert "knowledge_base" in overview["references"]
