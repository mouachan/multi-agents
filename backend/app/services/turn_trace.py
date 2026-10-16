"""Trace of one chat turn or business processing, recorded once for two destinations.

- Application trace (PostgreSQL): the events streamed to the UI (routing, A2A, guardrails,
  MCP tools, sandbox runs), each with its offset from the start of the turn ("t", in ms).
  It is saved with the assistant message at the end of the turn (no added latency) and the
  UI replays it through the same reducer as the live stream (frontend/src/hooks/useChat.ts).
- Observability trace (MLflow): spans built from the same events, one trace per turn:

      <turn>                 root: input message and answer, session id, user
      ├── routing            agent, method, score, candidates
      └── a2a:<agent>        agent card, authentication, task id and states, SPIFFE caller
          └── <agent spans>  guardrails, MCP tools (sandbox), LLM: emitted by the agent
                             under the W3C traceparent sent in the A2A metadata

The application trace keeps the MLflow trace id, so the UI can link to it.
"""
import json
import time
from typing import Any, Dict, List, Optional

from app.core import tracing
from app.core.auth import current_username
from app.core.config import settings

# Events kept in the application trace (text deltas and heartbeats are not)
TRACE_EVENTS = {"routing", "agent_resolved", "a2a", "guardrails", "governance", "tool_call", "tool_result", "error"}
TEXT_EVENTS = {"text_delta", "text_replace"}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


class TurnTrace:
    def __init__(self, name: str, inputs: Dict[str, Any], session_id: str = "") -> None:
        self._t0 = time.monotonic()
        self._t0_ns = time.time_ns()
        self.events: List[Dict[str, Any]] = []
        self.first_text_ms: Optional[int] = None
        self._error: Optional[str] = None
        self._finished = False
        self._a2a = None
        self._root = tracing.start_span(name, attributes={
            "mlflow.traceName": name, "mlflow.spanType": "AGENT", "session.id": session_id,
            "user.id": current_username(),  # MLflow trace user (None without authentication)
            "mlflow.spanInputs": _json(inputs),
        })
        self.mlflow_trace_id = tracing.mlflow_trace_id(self._root)

    def _elapsed_ms(self) -> int:
        return int((time.monotonic() - self._t0) * 1000)

    def _ns(self, ms: float) -> int:
        return self._t0_ns + int(ms * 1_000_000)

    def link(self) -> Dict[str, Optional[str]]:
        """MLflow trace id and UI link, sent to the UI in the done event."""
        experiment = tracing.experiment_id()
        url = None
        if self.mlflow_trace_id and experiment and settings.mlflow_ui_url:
            url = (f"{settings.mlflow_ui_url.rstrip('/')}/#/experiments/{experiment}/traces"
                   f"?selectedEvaluationId={self.mlflow_trace_id}")
        return {"mlflow_trace_id": self.mlflow_trace_id, "mlflow_url": url}

    def start_a2a(self, agent_id: str) -> Optional[str]:
        """Open the span of the A2A call; returns the traceparent to send to the agent."""
        self._a2a = tracing.start_span(f"a2a:{agent_id}", parent=self._root, attributes={
            "mlflow.spanType": "AGENT", "agent.id": agent_id})
        return tracing.traceparent(self._a2a)

    def add(self, event: Dict[str, Any]) -> None:
        """Record a streamed event (application trace) and mirror it in the spans."""
        etype = event.get("type")
        t = self._elapsed_ms()
        if etype in TEXT_EVENTS:
            if self.first_text_ms is None:
                self.first_text_ms = t
            return
        if etype not in TRACE_EVENTS:
            return
        self.events.append({**event, "t": t})

        if etype == "routing":
            span = tracing.start_span("routing", parent=self._root, start_ns=self._ns(t - event.get("duration_ms", 0)),
                                      attributes={
                                          "mlflow.spanType": "CHAIN",
                                          "routing.agent_id": event.get("agent_id"),
                                          "routing.method": event.get("method"),
                                          "routing.score": event.get("score"),
                                          "mlflow.spanOutputs": _json({"agent_id": event.get("agent_id"),
                                                                       "candidates": event.get("candidates")}),
                                      })
            tracing.end_span(span, end_ns=self._ns(t))
        elif etype == "a2a" and event.get("phase") == "request":
            agent = event.get("agent") or {}
            auth = event.get("auth") or {}
            tracing.set_attributes(self._a2a, {
                "a2a.method": event.get("method"), "a2a.profile": event.get("profile"),
                "agent.name": agent.get("name"), "agent.version": agent.get("version"), "agent.url": agent.get("url"),
                "auth.scheme": auth.get("scheme"), "auth.audience": auth.get("audience"),
            })
        elif etype == "a2a":
            tracing.add_event(self._a2a, f"task {event.get('state')}", {
                "a2a.task_id": event.get("task_id"), "a2a.context_id": event.get("context_id")}, at_ns=self._ns(t))
        elif etype == "guardrails":
            tracing.add_event(self._a2a or self._root, f"guardrails {event.get('stage')}: {event.get('status')}",
                              {"rail": event.get("rail")}, at_ns=self._ns(t))
        elif etype == "governance":
            tracing.add_event(self._a2a or self._root, "tools withheld by the user's profile",
                              {"tools": ", ".join(event.get("withheld_tools") or [])}, at_ns=self._ns(t))
        elif etype == "error":
            self._error = str(event.get("message") or "error")

    def finish(self, output: str, done: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """End the spans; returns the application trace saved with the assistant message."""
        if not self._finished:
            self._finished = True
            summary = (done or {}).get("a2a") or {}
            prompt = summary.get("prompt") or {}
            tracing.set_attributes(self._a2a, {
                "a2a.task_id": summary.get("task_id"), "a2a.state": summary.get("state"),
                "spiffe.caller": summary.get("caller"), "agent.duration_ms": summary.get("agent_duration_ms"),
                "prompt.name": prompt.get("name"), "prompt.version": prompt.get("version"),
            })
            tracing.end_span(self._a2a, error=self._error)
            tracing.set_attributes(self._root, {
                "agent.id": (done or {}).get("agent_id"),
                "mlflow.spanOutputs": _json({"response": output[:4000], "agent": (done or {}).get("agent_id"),
                                             "tools": [e.get("name") for e in self.events if e["type"] == "tool_result"]}),
            })
            tracing.end_span(self._root, error=self._error)
        return {
            "events": self.events,
            "first_text_ms": self.first_text_ms,
            "duration_ms": self._elapsed_ms(),
            "done": done,
            **self.link(),
        }

    def close(self) -> None:
        """End the spans of a turn that stopped early (no answer saved)."""
        if not self._finished:
            self.finish("")
