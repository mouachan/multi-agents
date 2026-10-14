"""
A2A Client — streams tasks to the decoupled A2A agents (a2a-sdk 1.x, JSON-RPC binding).

Normalizes the A2A event stream into the same events as the Responses API stream:
    {"type": "tool_call",    "name", "server"}
    {"type": "tool_result",  "name", "server", "status"}
    {"type": "text_delta",   "delta"}
    {"type": "text_replace", "text"}     (agent re-sent a masked/redacted version)
    {"type": "done", "output", "tool_calls", "response_id", "model", "usage",
                     "decision", "prompt", "guardrails", "status"}
"""

import logging
import uuid
from typing import Any, AsyncGenerator, Dict, Optional

import httpx
from a2a.client import Client, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, SendMessageRequest, TaskState
from google.protobuf import json_format, struct_pb2

logger = logging.getLogger(__name__)

_TERMINAL_ERRORS = {
    TaskState.TASK_STATE_FAILED: "failed",
    TaskState.TASK_STATE_REJECTED: "rejected",
    TaskState.TASK_STATE_CANCELED: "canceled",
}


def _struct_to_dict(msg) -> Dict[str, Any]:
    if msg is None or not msg.HasField("metadata"):
        return {}
    return json_format.MessageToDict(msg.metadata)


def _text(parts) -> str:
    return "".join(p.text for p in parts if p.text)


class A2AClient:
    """Client for the A2A domain agents, with one cached SDK client per agent URL."""

    def __init__(self, timeout: float = 300.0):
        self.timeout = timeout
        from app.core.spiffe import add_a2a_auth

        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0),
            event_hooks={"request": [add_a2a_auth]},
        )
        self._factory = ClientFactory(ClientConfig(streaming=True, httpx_client=self._http))
        self._clients: Dict[str, Client] = {}

    async def _client(self, base_url: str) -> Client:
        client = self._clients.get(base_url)
        if client is None:
            client = await self._factory.create_from_url(base_url)
            self._clients[base_url] = client
            logger.info("Discovered A2A agent at %s", base_url)
        return client

    async def stream(
        self,
        base_url: str,
        message: str,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        msg = Message(
            message_id=uuid.uuid4().hex,
            role=Role.ROLE_USER,
            parts=[Part(text=message)],
            context_id=context_id or "",
        )
        if metadata:
            meta = struct_pb2.Struct()
            json_format.ParseDict({k: v for k, v in metadata.items() if v is not None}, meta)
            msg.metadata.CopyFrom(meta)

        try:
            client = await self._client(base_url)
        except Exception:
            self._clients.pop(base_url, None)
            raise

        text = ""
        final: Dict[str, Any] = {}
        status = "unknown"

        async for event in client.send_message(SendMessageRequest(message=msg)):
            if event.HasField("artifact_update"):
                upd = event.artifact_update
                chunk = _text(upd.artifact.parts)
                if upd.append:
                    text += chunk
                    yield {"type": "text_delta", "delta": chunk}
                elif text:
                    text = chunk
                    yield {"type": "text_replace", "text": chunk}
                else:
                    text = chunk
                    yield {"type": "text_delta", "delta": chunk}

            elif event.HasField("status_update"):
                st = event.status_update.status
                meta = _struct_to_dict(st.message) if st.HasField("message") else {}
                if st.state == TaskState.TASK_STATE_WORKING and meta.get("event") in ("tool_call", "tool_result"):
                    yield {
                        "type": meta["event"],
                        "name": meta.get("name", ""),
                        "server": meta.get("server", ""),
                        "status": meta.get("status", "in_progress"),
                    }
                elif st.state == TaskState.TASK_STATE_COMPLETED:
                    status, final = "completed", meta
                    if not final.get("output"):
                        final["output"] = _text(st.message.parts) or text
                elif st.state in _TERMINAL_ERRORS:
                    status = _TERMINAL_ERRORS[st.state]
                    final = meta or {}
                    final.setdefault("output", _text(st.message.parts))

            elif event.HasField("task"):
                # Non-streaming fallback: the whole task in one response
                task = event.task
                if task.status.state == TaskState.TASK_STATE_COMPLETED:
                    status = "completed"
                    final = _struct_to_dict(task.status.message)
                    final.setdefault("output", _text(task.status.message.parts)
                                     or "".join(_text(a.parts) for a in task.artifacts))
                elif task.status.state in _TERMINAL_ERRORS:
                    status = _TERMINAL_ERRORS[task.status.state]
                    final = {"output": _text(task.status.message.parts)}

        if status == "failed":
            raise RuntimeError(final.get("output") or "A2A agent task failed")

        yield {
            "type": "done",
            "status": status,
            "output": final.get("output", text),
            "tool_calls": final.get("tool_calls", []),
            "response_id": final.get("response_id"),
            "model": final.get("model", ""),
            "usage": final.get("usage", {}),
            "decision": final.get("decision", {}),
            "prompt": final.get("prompt", {}),
            "guardrails": final.get("guardrails", {}),
        }

    async def send(
        self,
        base_url: str,
        message: str,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a task to completion and return the final `done` payload."""
        result: Dict[str, Any] = {}
        async for event in self.stream(base_url, message, context_id, metadata):
            if event["type"] == "done":
                result = event
        return result


_shared_client: Optional[A2AClient] = None


def get_a2a_client() -> A2AClient:
    """Process-wide A2A client (shares the httpx pool and resolved agent cards)."""
    global _shared_client
    if _shared_client is None:
        from app.core.config import settings
        _shared_client = A2AClient(timeout=settings.ogx_timeout)
    return _shared_client
