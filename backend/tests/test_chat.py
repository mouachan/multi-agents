"""The chat (app/services/chat): conversations, routing, the streamed answer, the saved messages."""
import json

from conftest import API


async def send(client, session_id: str, message: str):
    """Send a message; returns the server-sent events of the answer."""
    response = await client.post(f"{API}/chat/sessions/{session_id}/messages", json={"message": message})
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


async def test_new_conversation_has_a_welcome_message(client):
    session = (await client.post(f"{API}/chat/sessions", json={"locale": "en"})).json()
    assert session["welcome_message"].startswith("Welcome")
    messages = (await client.get(f"{API}/chat/sessions/{session['session_id']}/messages")).json()
    assert [m["role"] for m in messages] == ["assistant"]


async def test_message_is_routed_and_the_answer_saved(client, agent):
    agent.answer.update(output="Claim CLM-2024-0011 is pending.", tool_calls=[{"name": "get_claim"}],
                        usage={"input_tokens": 10, "output_tokens": 5}, model="maas/llama-scout-17b")
    session = (await client.post(f"{API}/chat/sessions", json={"locale": "fr"})).json()

    events = await send(client, session["session_id"], "Quel est le statut du sinistre CLM-2024-0011 ?")
    types = [event["type"] for event in events]
    assert types[0] == "routing" and events[0]["agent_id"] == "claims"
    assert "agent_resolved" in types and "text_delta" in types and types[-1] == "done"
    done = events[-1]
    assert done["usage"] == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    assert done["model_id"] == "llama-scout-17b"

    sent = agent.requests[-1]["metadata"]
    assert sent["mode"] == "chat" and sent["language"] == "fr"
    messages = (await client.get(f"{API}/chat/sessions/{session['session_id']}/messages")).json()
    assert [m["role"] for m in messages] == ["assistant", "user", "assistant"]
    assert messages[-1]["content"] == "Claim CLM-2024-0011 is pending."


async def test_json_blocks_are_not_shown_to_the_reader(client, agent):
    agent.answer.update(output='Done.\n```json\n{"recommendation": "approve"}\n```')
    session = (await client.post(f"{API}/chat/sessions", json={})).json()
    events = await send(client, session["session_id"], "Traiter le sinistre CLM-2024-0011")
    assert events[-1]["type"] == "done"
    replaced = [e for e in events if e["type"] == "text_replace"]
    assert replaced and replaced[-1]["text"] == "Done."


async def test_answers_are_masked_when_the_guardrails_could_not_check(client, agent):
    agent.answer.update(output="Write to jean.dupont@example.com",
                        guardrails={"output": {"status": "error"}})
    session = (await client.post(f"{API}/chat/sessions", json={})).json()
    events = await send(client, session["session_id"], "Contact du sinistre CLM-2024-0011")
    assert [e for e in events if e["type"] == "text_replace"][-1]["text"] == "Write to [EMAIL_ADDRESS]"


async def test_conversations_are_listed_and_deleted(client, agent):
    created = (await client.post(f"{API}/chat/sessions", json={})).json()["session_id"]
    listed = {s["session_id"] for s in (await client.get(f"{API}/chat/sessions")).json()}
    assert created in listed
    await client.delete(f"{API}/chat/sessions/{created}")
    assert (await client.get(f"{API}/chat/sessions/{created}/messages")).status_code == 404


def test_a_message_naming_one_domain_stays_in_it():
    from app.services.chat.routing import named_domain
    assert named_domain("Liste les appels d'offres en revue manuelle") == "tenders"
    assert named_domain("Où est mon colis 6C123456789FR ?") == "postal"
    assert named_domain("Détail du sinistre CLM-2024-0011") == "claims"
    assert named_domain("Combien de dossiers en attente ?") is None             # no domain named
    assert named_domain("Sinistres et réclamations en attente") is None         # several domains
