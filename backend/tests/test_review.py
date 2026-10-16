"""Human review (app/services/review.py): inbox, brief with evidence, questions to the agent, decision."""
from conftest import API, first_case, tool_call, wait_for_jobs

PAYOUT = {"success": True, "covered": True, "claimed_amount": 6200.0, "payout": 5850.0, "currency": "USD",
          "contract": {"number": "CNT-2024-0039", "type": "Home Insurance", "franchise": 350.0,
                       "coverage_amount": 260000.0},
          "sandbox_run": {"success": True}}
SIMILAR = {"success": True, "similar_claims": [
    {"claim_number": "CLM-2024-0007", "claim_type": "Home", "decision": "deny", "similarity_score": 0.888}]}


async def handed_over_claim(client, agent):
    """A claim the agent hands over to a human, leaning to deny."""
    claim = await first_case(client, "claims")
    agent.answer.update(
        output="needs a human",
        decision={"recommendation": "manual_review", "confidence": 0.55, "reasoning": "Amount close to the limit",
                  "review": {"reasons": ["The closest precedent was denied"], "checks": ["Check the invoice"],
                             "suggestion": "deny"}},
        tool_calls=[tool_call("compute_payout", PAYOUT), tool_call("retrieve_similar_claims", SIMILAR)],
    )
    await client.post(f"{API}/claims/{claim['id']}/process")
    await wait_for_jobs()
    return claim


async def test_inbox_lists_the_handed_over_cases(client, agent, fresh_data):
    claim = await handed_over_claim(client, agent)
    inbox = (await client.get(f"{API}/review/inbox")).json()
    entry = next(item for item in inbox if item["id"] == claim["id"])
    assert entry == {**entry, "domain": "claims", "suggestion": "deny", "reason": "The closest precedent was denied"}


async def test_brief_explains_why_and_shows_the_evidence(client, agent, fresh_data):
    claim = await handed_over_claim(client, agent)
    brief = (await client.get(f"{API}/review/claims/{claim['id']}")).json()

    assert brief["awaiting_review"] is True
    assert brief["choices"] == [{"decision": "approve", "status": "completed"}, {"decision": "deny", "status": "denied"}]
    assert brief["agent"]["suggestion"] == "deny"
    assert brief["agent"]["checks"] == ["Check the invoice"]
    payout = next(section for section in brief["case"]["evidence"] if section["key"] == "payout")
    facts = {fact["key"]: fact["value"] for fact in payout["facts"]}
    assert facts["payout"] == 5850.0 and facts["franchise"] == 350.0 and facts["covered"] is True
    similar = next(section for section in brief["case"]["evidence"] if section["key"] == "similar_cases")
    assert similar["items"][0]["title"] == "CLM-2024-0007" and similar["items"][0]["badge"] == "deny"


async def test_question_goes_to_the_domain_agent_with_read_only_tools(client, agent, fresh_data):
    claim = await handed_over_claim(client, agent)
    agent.answer.update(output="The invoice shows 6200 USD.")
    answer = (await client.post(f"{API}/review/claims/{claim['id']}/questions",
                                json={"question": "What does the invoice say?", "language": "en"})).json()

    assert answer["answer"] == "The invoice shows 6200 USD."
    sent = agent.requests[-1]["metadata"]
    assert sent["mode"] == "chat" and sent["profile"] == "claims"
    assert not any(tool.startswith("save_") for tool in sent["tools"])
    journal = (await client.get(f"{API}/review/claims/{claim['id']}")).json()["journal"]
    assert journal[-1]["type"] == "question" and journal[-1]["question"] == "What does the invoice say?"


async def test_going_against_the_agent_needs_a_justification(client, agent, fresh_data):
    claim = await handed_over_claim(client, agent)
    refused = await client.post(f"{API}/review/claims/{claim['id']}/decision", json={"decision": "approve"})
    assert refused.status_code == 409 and "Explain why" in refused.json()["detail"]

    accepted = await client.post(f"{API}/review/claims/{claim['id']}/decision",
                                 json={"decision": "approve", "justification": "The invoice was checked"})
    decision = accepted.json()
    assert decision["decision"] == "approve" and decision["agent"]["decision"] == "manual_review"
    assert decision["reviewer"]["justification"] == "The invoice was checked"
    assert (await client.get(f"{API}/claims/{claim['id']}")).json()["status"] == "completed"
    inbox = (await client.get(f"{API}/review/inbox")).json()
    assert claim["id"] not in {item["id"] for item in inbox}


async def test_following_the_agent_needs_no_justification(client, agent, fresh_data):
    claim = await handed_over_claim(client, agent)
    response = await client.post(f"{API}/review/claims/{claim['id']}/decision", json={"decision": "deny"})
    assert response.status_code == 200
    assert (await client.get(f"{API}/claims/{claim['id']}")).json()["status"] == "denied"


async def test_a_no_go_tender_is_declined_not_failed(client, agent, fresh_data):
    tender = await first_case(client, "tenders")
    agent.answer.update(decision={"recommendation": "a_approfondir", "confidence": 0.6})
    await client.post(f"{API}/tenders/{tender['id']}/process")
    await wait_for_jobs()
    await client.post(f"{API}/review/tenders/{tender['id']}/decision",
                      json={"decision": "no_go", "justification": "Outside our region"})
    assert (await client.get(f"{API}/tenders/{tender['id']}")).json()["status"] == "declined"


async def test_unknown_choice_is_refused(client, agent, fresh_data):
    claim = await handed_over_claim(client, agent)
    response = await client.post(f"{API}/review/claims/{claim['id']}/decision", json={"decision": "go"})
    assert response.status_code == 409


async def test_the_decision_is_recorded_as_feedback_on_the_trace(client, agent, fresh_data, monkeypatch):
    feedback = []

    async def log_feedback(trace_id, name, value, source, rationale=None):
        feedback.append((name, value, source))
        return True
    monkeypatch.setattr("app.services.review.tracing.log_feedback", log_feedback)

    claim = await handed_over_claim(client, agent)           # the agent leans to "deny"
    await client.post(f"{API}/review/claims/{claim['id']}/decision",
                      json={"decision": "approve", "justification": "Invoice received"})
    assert ("reviewer_decision", "approve", "test-user") in [(n, v, "test-user") for n, v, _ in feedback]
    assert ("agent_correct", False) in [(n, v) for n, v, _ in feedback]
