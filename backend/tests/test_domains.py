"""The business API of each domain (app/api/domains.py) and the processing by the agent
(app/services/processing.py). Every test runs for claims, tenders and postal."""
from conftest import API, first_case, tool_call, wait_for_jobs


async def test_list_and_read_cases(client, domain):
    listing = (await client.get(f"{API}/{domain.name}/")).json()
    assert listing["total"] == len(listing["items"]) > 0
    case = listing["items"][0]
    assert case["domain"] == domain.name and case["number"] == case[domain.number_field]

    read = (await client.get(f"{API}/{domain.name}/{case['id']}")).json()
    assert read["id"] == case["id"]


async def test_unknown_case_is_404(client, domain):
    response = await client.get(f"{API}/{domain.name}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


async def test_statistics_count_every_case(client, domain):
    stats = (await client.get(f"{API}/{domain.name}/statistics")).json()
    listing = (await client.get(f"{API}/{domain.name}/")).json()
    assert stats["total"] >= listing["total"]
    assert sum(stats["by_status"].values()) == stats["total"]


async def test_processing_saves_the_agent_decision(client, agent, fresh_data, domain):
    case = await first_case(client, domain.name)
    decision = domain.human_decisions[0]
    agent.answer.update(
        output="done",
        decision={"recommendation": decision, "confidence": 0.9, "reasoning": "Clear case"},
        tool_calls=[tool_call(domain.processing_tools[0], {"success": True, "processing_time_seconds": 1.5})],
    )

    response = await client.post(f"{API}/{domain.name}/{case['id']}/process")
    assert response.json()["status"] == "processing"
    await wait_for_jobs()

    # the agent got the guided workflow: its tools, in order, the decision values, and what a
    # reviewer could decide (for the brief it writes when it hands the case over)
    sent = agent.requests[-1]["metadata"]
    assert sent["mode"] == "process"
    assert sent["tools"] == domain.processing_tools
    assert sent["decision_values"] == domain.decision_values
    assert sent["review_decision"] == domain.review_decision
    assert sent["human_decisions"] == domain.human_decisions
    assert case["number"] in agent.requests[-1]["message"]

    processed = (await client.get(f"{API}/{domain.name}/{case['id']}")).json()
    assert processed["status"] == domain.status_after(decision)
    assert processed["processing_steps"][0] == {
        "step_name": domain.processing_tools[0], "status": "completed", "duration_ms": 1500,
        "output_data": {"success": True, "processing_time_seconds": 1.5}, "error_message": None,
    }
    saved = (await client.get(f"{API}/{domain.name}/{case['id']}/decision")).json()
    assert saved["decision"] == decision and saved["agent"]["reasoning"] == "Clear case"
    assert saved["reviewer"] is None and saved["llm_model"] == "test-model"


async def test_an_unknown_decision_goes_to_a_human(client, agent, fresh_data, domain):
    case = await first_case(client, domain.name)
    agent.answer.update(decision={"recommendation": "maybe", "confidence": 0.3})
    await client.post(f"{API}/{domain.name}/{case['id']}/process")
    await wait_for_jobs()
    assert (await client.get(f"{API}/{domain.name}/{case['id']}")).json()["status"] == domain.review_status


async def test_an_agent_failure_marks_the_case_failed(client, agent, fresh_data, domain):
    case = await first_case(client, domain.name)
    agent.fail = True
    await client.post(f"{API}/{domain.name}/{case['id']}/process")
    await wait_for_jobs()
    assert (await client.get(f"{API}/{domain.name}/{case['id']}")).json()["status"] == "failed"


async def test_a_case_processed_twice_shows_the_latest_decision(client, agent, fresh_data, domain):
    case = await first_case(client, domain.name)
    for decision in domain.human_decisions[:2]:
        agent.answer.update(decision={"recommendation": decision, "confidence": 0.8})
        await client.post(f"{API}/{domain.name}/{case['id']}/process")
        await wait_for_jobs()
    saved = (await client.get(f"{API}/{domain.name}/{case['id']}/decision")).json()
    assert saved["decision"] == domain.human_decisions[1]


async def test_postal_tracking_timeline(client):
    complaint = (await client.get(f"{API}/postal/")).json()["items"][0]
    events = (await client.get(f"{API}/postal/{complaint['id']}/tracking")).json()
    assert isinstance(events, list)
    dates = [event["event_date"] for event in events]
    assert dates == sorted(dates, reverse=True)


async def test_claims_personal_data_report(client):
    claim = (await client.get(f"{API}/claims/")).json()["items"][0]
    assert (await client.get(f"{API}/claims/{claim['id']}/personal-data")).status_code == 200
