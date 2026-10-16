"""The agent's answer, streamed to the caller as the A2A "response" artifact.

With the output rails on (NeMo Guardrails, GUARDRAILS_BUFFER_OUTPUT), the text is checked sentence by
sentence before it is sent: personal data is masked and no unmasked sentence ever leaves the agent.
A blocked sentence stops the stream (the executor then replaces the answer with a refusal).
"""
import re
from typing import Any, Dict, List, Optional

from a2a.helpers.proto_helpers import new_text_part
from a2a.server.tasks import TaskUpdater

from .guardrails import Guardrails

# End of a sentence: punctuation (or a newline) followed by whitespace
SENTENCE_END = re.compile(r"[.!?:;\n](?=\s)")


class AnswerStream:
    def __init__(self, updater: TaskUpdater, guardrails: Guardrails, check_sentences: bool, show: bool = True):
        self.updater = updater
        self.guardrails = guardrails
        self.check_sentences = guardrails.enabled and check_sentences
        self.show = show                  # False: nothing is sent (steps of the guided processing)
        self.sent: List[str] = []
        self.pending = ""                 # text received, not sent yet (an unfinished sentence)
        self.verdict: Dict[str, Any] = {"allowed": True, "status": "passed", "rail": None, "error": None}

    @property
    def text(self) -> str:
        return "".join(self.sent)

    async def add(self, delta: str) -> None:
        """Text from the model: sent at once, or sentence by sentence when the sentences are checked."""
        self.pending += delta
        if not self.check_sentences:
            await self._send(self.pending)
            self.pending = ""
            return
        ends = list(SENTENCE_END.finditer(self.pending))
        if ends:
            cut = ends[-1].end()
            sentences, self.pending = self.pending[:cut], self.pending[cut:]
            await self._send(sentences)

    async def finish(self, full_output: str) -> None:
        """End of the response: the last sentence, or the whole output when nothing was streamed."""
        await self._send(self.pending)
        self.pending = ""
        if not self.sent and full_output:
            await self._send(full_output)

    async def _send(self, chunk: str) -> None:
        if not chunk or not self.show or not self.verdict["allowed"]:
            return
        if self.check_sentences and chunk.strip():
            chunk = await self._checked(chunk)
            if chunk is None:
                return
        await self.updater.add_artifact([new_text_part(chunk)], artifact_id="response", name="response",
                                        append=bool(self.sent))
        self.sent.append(chunk)

    async def _checked(self, chunk: str) -> Optional[str]:
        """The chunk after the output rails (masked), None when blocked. Keeps the surrounding spaces."""
        lead = chunk[:len(chunk) - len(chunk.lstrip())]
        trail = chunk[len(chunk.rstrip()):]
        result = await self.guardrails.check_output(chunk.strip())
        if not result.allowed:
            self.verdict.update(allowed=False, status="blocked", rail=result.rail)
            return None
        if result.status == "modified":
            self.verdict.update(status="modified", rail=result.rail)
        elif result.status == "error" and self.verdict["status"] == "passed":
            self.verdict.update(status="error", error=result.error)
        return lead + result.text + trail
