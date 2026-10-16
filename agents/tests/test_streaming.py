"""The answer stream (shared/streaming.py): with the output rails on, no unmasked sentence leaves the agent."""
from shared.guardrails import GuardrailResult
from shared.streaming import AnswerStream


class Updater:
    """Collects what would be sent to the caller (the A2A "response" artifact)."""
    def __init__(self):
        self.chunks = []

    async def add_artifact(self, parts, **_):
        self.chunks.append(parts[0].text)


class Guardrails:
    """Masks e-mail addresses; blocks the word "secret"."""
    enabled = True

    def __init__(self):
        self.checked = []

    async def check_output(self, text):
        self.checked.append(text)
        if "secret" in text:
            return GuardrailResult(False, text, status="blocked", rail="self check output")
        if "@" in text:
            return GuardrailResult(True, "Write to [EMAIL_ADDRESS].", status="modified", rail="mask")
        return GuardrailResult(True, text)


async def test_sentences_are_checked_before_they_are_sent():
    updater, rails = Updater(), Guardrails()
    stream = AnswerStream(updater, rails, check_sentences=True)
    for delta in ["Hello. Write to ", "jo@example.com. ", "Bye"]:
        await stream.add(delta)
    await stream.finish("")

    assert rails.checked == ["Hello.", "Write to jo@example.com.", "Bye"]
    assert "jo@example.com" not in stream.text
    assert stream.text == "Hello. Write to [EMAIL_ADDRESS]. Bye"
    assert stream.verdict["status"] == "modified"


async def test_a_blocked_sentence_stops_the_answer():
    updater = Updater()
    stream = AnswerStream(updater, Guardrails(), check_sentences=True)
    await stream.add("First. The secret is 42. ")
    await stream.add("More text. ")
    await stream.finish("")
    assert updater.chunks == [] and stream.verdict["allowed"] is False


async def test_without_rails_the_text_is_sent_as_it_comes():
    rails = Guardrails()
    rails.enabled = False
    updater = Updater()
    stream = AnswerStream(updater, rails, check_sentences=True)
    await stream.add("Hel")
    await stream.add("lo")
    await stream.finish("")
    assert updater.chunks == ["Hel", "lo"] and rails.checked == []


async def test_a_hidden_step_sends_nothing():
    updater = Updater()
    stream = AnswerStream(updater, Guardrails(), check_sentences=True, show=False)
    await stream.add("Tool step. ")
    await stream.finish("Tool step.")
    assert updater.chunks == [] and stream.text == ""
