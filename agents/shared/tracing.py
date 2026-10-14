"""OpenTelemetry traces exported to the RHOAI MLflow OTLP endpoint (/v1/traces).

Span tree visible in MLflow "GenAI apps & agents":
    <agent>/<profile> | <message>   (AGENT, root)
    ├── guardrails                  (GUARDRAIL)
    ├── tool:<name>                 (TOOL, one per MCP call)
    └── llm-response                (CHAT_MODEL, token usage)
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

import httpx

from . import mlflow_auth
from .config import AgentSettings

logger = logging.getLogger(__name__)

_tracer = None


def _experiment_id(settings: AgentSettings, retries: int = 5) -> str:
    base = settings.mlflow_tracking_uri.rstrip("/")
    headers = mlflow_auth.headers(settings)
    verify = mlflow_auth.ca_bundle() or False
    name = settings.mlflow_experiment_name or f"agent-{settings.agent_id}"
    for attempt in range(1, retries + 1):
        try:
            r = httpx.get(f"{base}/api/2.0/mlflow/experiments/get-by-name",
                          params={"experiment_name": name}, headers=headers, verify=verify, timeout=10)
            if r.status_code == 200:
                return r.json()["experiment"]["experiment_id"]
            r = httpx.post(f"{base}/api/2.0/mlflow/experiments/create", json={"name": name},
                           headers=headers, verify=verify, timeout=10)
            if r.status_code == 200:
                return r.json()["experiment_id"]
            logger.warning("MLflow experiment '%s': HTTP %s %s", name, r.status_code, r.text[:200])
        except Exception as e:
            logger.warning("MLflow experiment resolution %d/%d: %s", attempt, retries, e)
        time.sleep(3)
    return ""


def init(settings: AgentSettings) -> None:
    global _tracer
    if not settings.mlflow_tracking_uri:
        logger.info("Tracing disabled (MLFLOW_TRACKING_URI not set)")
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        experiment_id = _experiment_id(settings)
        if not experiment_id:
            logger.warning("Tracing disabled: MLflow experiment unavailable")
            return
        headers = mlflow_auth.headers(settings)
        headers["x-mlflow-experiment-id"] = experiment_id
        # The OTLP receiver is mounted at the server root, not under the UI prefix (/mlflow on RHOAI)
        uri = urlsplit(settings.mlflow_tracking_uri)
        exporter = OTLPSpanExporter(
            endpoint=f"{uri.scheme}://{uri.netloc}/v1/traces",
            headers=headers,
            certificate_file=mlflow_auth.ca_bundle(),
            timeout=30,
        )
        provider = TracerProvider(resource=Resource.create({"service.name": f"{settings.agent_id}-agent"}))
        provider.add_span_processor(BatchSpanProcessor(exporter))
        # Private provider: only our explicit spans go to MLflow. As the global provider it
        # also exported library HTTP spans (probes, agent-card fetches), which flooded
        # the experiment with traces without inputs/outputs.
        _tracer = provider.get_tracer(f"{settings.agent_id}-agent")
        logger.info("Tracing enabled → MLflow experiment %s", experiment_id)
    except Exception as e:
        logger.warning("Tracing init failed: %s", e, exc_info=True)


def _j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def log_agent_trace(
    agent_id: str,
    profile: str,
    model: str,
    input_text: str,
    output_text: str,
    tool_calls: List[Dict[str, Any]],
    usage: Optional[Dict[str, Any]],
    response_id: Optional[str],
    duration_ms: int,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    if _tracer is None:
        return
    try:
        from opentelemetry.trace import StatusCode

        meta = metadata or {}
        prompt = meta.get("prompt") or {}
        name = f"{agent_id}/{profile} | {input_text[:80].replace(chr(10), ' ').strip()}"
        with _tracer.start_as_current_span(name, attributes={
            "mlflow.traceName": name,
            "mlflow.spanType": "AGENT",
            "session.id": str(meta.get("context_id") or ""),
            "agent.id": agent_id,
            "agent.profile": profile,
            "a2a.task_id": str(meta.get("task_id") or ""),
            "prompt.name": str(prompt.get("name") or ""),
            "prompt.version": str(prompt.get("version") or ""),
            "prompt.source": str(prompt.get("source") or ""),
            "response.id": response_id or "",
            "duration_ms": duration_ms,
        }) as root:
            root.set_attribute("mlflow.spanInputs", _j({"message": input_text[:4000], "profile": profile}))

            if meta.get("guardrails"):
                with _tracer.start_as_current_span("guardrails", attributes={"mlflow.spanType": "GUARDRAIL"}) as g:
                    g.set_attribute("mlflow.spanOutputs", _j(meta["guardrails"]))

            for i, tc in enumerate(tool_calls):
                tool = tc.get("name") or f"tool-{i}"
                with _tracer.start_as_current_span(f"tool:{tool}", attributes={
                    "mlflow.spanType": "TOOL", "tool.name": tool, "tool.server": str(tc.get("server") or ""),
                }) as span:
                    span.set_attribute("mlflow.spanInputs", _j({"arguments": tc.get("arguments", "")}))
                    span.set_attribute("mlflow.spanOutputs", _j({"output": str(tc.get("output") or "")[:4000],
                                                                 "error": tc.get("error")}))
                    if tc.get("error"):
                        span.set_status(StatusCode.ERROR, str(tc["error"]))

            with _tracer.start_as_current_span("llm-response", attributes={
                "mlflow.spanType": "CHAT_MODEL", "gen_ai.request.model": model, "gen_ai.response.model": model,
            }) as llm:
                u = usage or {}
                inp, out = int(u.get("input_tokens", 0) or 0), int(u.get("output_tokens", 0) or 0)
                llm.set_attribute("gen_ai.usage.input_tokens", inp)
                llm.set_attribute("gen_ai.usage.output_tokens", out)
                llm.set_attribute("mlflow.spanOutputs", _j({
                    "choices": [{"message": {"role": "assistant", "content": output_text[:4000]}}],
                    "usage": {"prompt_tokens": inp, "completion_tokens": out, "total_tokens": inp + out},
                }))

            root.set_attribute("mlflow.spanOutputs", _j({
                "response": output_text[:4000],
                "decision": meta.get("decision") or None,
                "tools_used": [tc.get("name") for tc in tool_calls],
                "prompt": prompt,
            }))
    except Exception as e:
        logger.warning("Tracing error: %s", e)
