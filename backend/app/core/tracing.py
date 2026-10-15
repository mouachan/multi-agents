"""
OpenTelemetry-based tracing for the multi-agent orchestrator.

Sends traces via OTLP/HTTP to MLflow RHOAI endpoint (/v1/traces).
Auth via pod ServiceAccount token, TLS via OpenShift service-ca.crt.

Only active when MLFLOW_TRACKING_URI is configured.
Reusable: any future separated agent just needs OTel SDK + env vars.

Span hierarchy visible in MLflow "GenAI apps & agents":
    {agent_id} | {message}       (root)
    └── agent-{agent_id}         (agent)
        ├── tool:{tool_name}     (tool per call)
        └── llm-response         (LLM)
"""
import json
import logging
import os
from urllib.parse import urlsplit
import time
from typing import Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_enabled = False
_tracer = None
_provider = None
_experiment_id: Optional[str] = None

SA_TOKEN_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/token"
SERVICE_CA_PATH = "/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt"


def _build_auth_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if os.path.exists(SA_TOKEN_PATH):
        with open(SA_TOKEN_PATH) as f:
            headers["Authorization"] = f"Bearer {f.read().strip()}"
    if settings.mlflow_rhoai_workspace:
        headers["X-Mlflow-Workspace"] = settings.mlflow_rhoai_workspace
    return headers


def _resolve_experiment_id(retries: int = 5, delay: float = 3.0) -> str:
    """Resolve MLflow experiment ID from name via REST API, with retries."""
    verify = SERVICE_CA_PATH if os.path.exists(SERVICE_CA_PATH) else False
    url = (
        f"{settings.mlflow_tracking_uri.rstrip('/')}"
        f"/api/2.0/mlflow/experiments/get-by-name"
        f"?experiment_name={settings.mlflow_experiment_name}"
    )
    headers = _build_auth_headers()

    for attempt in range(1, retries + 1):
        try:
            resp = httpx.get(url, headers=headers, verify=verify, timeout=10)
            if resp.status_code == 200:
                eid = resp.json()["experiment"]["experiment_id"]
                logger.info(f"Resolved experiment '{settings.mlflow_experiment_name}' → ID {eid}")
                return eid
            if resp.status_code == 404:
                logger.warning(f"Experiment '{settings.mlflow_experiment_name}' not found, creating it")
                return _create_experiment(headers, verify)
        except Exception as e:
            logger.warning(f"Experiment resolution attempt {attempt}/{retries}: {e}")
        if attempt < retries:
            time.sleep(delay)

    logger.error("All experiment resolution attempts failed — tracing will be disabled")
    return ""


def _create_experiment(headers: Dict[str, str], verify) -> str:
    """Create the MLflow experiment if it doesn't exist."""
    url = f"{settings.mlflow_tracking_uri.rstrip('/')}/api/2.0/mlflow/experiments/create"
    try:
        resp = httpx.post(
            url, headers={**headers, "Content-Type": "application/json"},
            json={"name": settings.mlflow_experiment_name},
            verify=verify, timeout=10,
        )
        if resp.status_code == 200:
            eid = resp.json()["experiment_id"]
            logger.info(f"Created experiment '{settings.mlflow_experiment_name}' → ID {eid}")
            return eid
    except Exception as e:
        logger.warning(f"Could not create experiment: {e}")
    return ""


def init_mlflow():
    """Initialize OpenTelemetry tracing with OTLP exporter → MLflow."""
    global _enabled, _tracer, _provider, _experiment_id

    if not settings.mlflow_tracking_uri:
        logger.info("Tracing disabled (MLFLOW_TRACKING_URI not set)")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        experiment_id = _resolve_experiment_id()
        if not experiment_id:
            logger.warning("Tracing disabled: could not resolve or create MLflow experiment")
            return
        _experiment_id = experiment_id

        # The OTLP receiver is mounted at the server root, not under the UI prefix (/mlflow on RHOAI)
        uri = urlsplit(settings.mlflow_tracking_uri)
        endpoint = f"{uri.scheme}://{uri.netloc}/v1/traces"

        otlp_headers = _build_auth_headers()
        otlp_headers["x-mlflow-experiment-id"] = experiment_id

        cert_file = SERVICE_CA_PATH if os.path.exists(SERVICE_CA_PATH) else None

        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=otlp_headers,
            certificate_file=cert_file,
            timeout=30,
        )

        resource = Resource.create({"service.name": "multi-agent-orchestrator"})
        _provider = TracerProvider(resource=resource)
        _provider.add_span_processor(BatchSpanProcessor(exporter))
        # Private provider: only our explicit spans go to MLflow (a global provider would
        # also export library HTTP spans without inputs/outputs)

        _tracer = _provider.get_tracer("multi-agent-orchestrator")
        _enabled = True
        logger.info(
            f"OTel tracing enabled → {endpoint} (experiment={experiment_id})"
        )
    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed: {e}")
    except Exception as e:
        logger.warning(f"Failed to initialize tracing: {e}", exc_info=True)


def shutdown_tracing():
    """Flush pending spans and shut down the TracerProvider."""
    global _provider
    if _provider:
        try:
            _provider.force_flush(timeout_millis=5000)
            _provider.shutdown()
            logger.info("OTel TracerProvider shut down, pending spans flushed")
        except Exception as e:
            logger.warning(f"Error shutting down tracing: {e}")


def is_enabled() -> bool:
    return _enabled


def log_agent_trace(
    agent_id: str,
    model: str,
    input_text: str,
    output_text: str,
    tool_calls: Optional[List[Dict]] = None,
    usage: Optional[dict] = None,
    stream: bool = False,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    response_id: Optional[str] = None,
    metadata: Optional[Dict] = None,
):
    """Log an agentic call as an OTel trace exported to MLflow."""
    if not _enabled:
        return
    try:
        from opentelemetry.trace import StatusCode

        tool_calls = tool_calls or []
        model_short = model.split("/")[-1] if "/" in model else model
        short_msg = input_text[:80].replace("\n", " ").strip()
        trace_name = f"{agent_id} | {short_msg}"

        meta = metadata or {}

        # Root span — orchestrator level
        with _tracer.start_as_current_span(
            name=trace_name,
            attributes={
                "mlflow.traceName": trace_name,
                "mlflow.spanType": "AGENT",
                "session.id": session_id or "",
                "user.id": user_id or "",
                "response.id": response_id or "",
                "stream": stream,
            },
        ) as root:
            root.set_attribute(
                "mlflow.spanInputs", json.dumps({"message": input_text[:2000]})
            )

            # Agent span
            with _tracer.start_as_current_span(
                name=f"agent-{agent_id}",
                attributes={
                    "mlflow.spanType": "AGENT",
                    "agent.id": agent_id,
                    "gen_ai.request.model": model_short,
                    "response.id": response_id or "",
                },
            ) as agent_span:
                agent_span.set_attribute(
                    "mlflow.spanInputs",
                    json.dumps({"agent_id": agent_id, "model": model_short}),
                )

                # Tool spans
                for i, tc in enumerate(tool_calls):
                    tool_name = tc.get("name") or f"tool-{i}"
                    server = str(tc.get("server_label") or tc.get("server") or "")
                    with _tracer.start_as_current_span(
                        name=f"tool:{tool_name}",
                        attributes={
                            "mlflow.spanType": "TOOL",
                            "tool.name": tool_name,
                            "tool.server": server,
                        },
                    ) as tool_span:
                        tool_span.set_attribute(
                            "mlflow.spanInputs",
                            json.dumps({"tool": tool_name, "server": server}),
                        )
                        tool_output = str(tc.get("output") or "")[:2000]
                        tool_error = tc.get("error")
                        result = {"status": tc.get("status", "unknown"), "output": tool_output}
                        if tool_error:
                            result["error"] = str(tool_error)
                            tool_span.set_status(StatusCode.ERROR, str(tool_error))
                        tool_span.set_attribute("mlflow.spanOutputs", json.dumps(result))

                # LLM response span
                with _tracer.start_as_current_span(
                    name="llm-response",
                    attributes={
                        "mlflow.spanType": "CHAT_MODEL",
                        "gen_ai.request.model": model_short,
                        "gen_ai.response.model": model_short,
                    },
                ) as llm_span:
                    llm_span.set_attribute(
                        "mlflow.spanInputs",
                        json.dumps({
                            "messages": [{"role": "user", "content": input_text[:2000]}],
                            "model": model_short,
                        }),
                    )
                    llm_outputs: Dict = {
                        "choices": [{"message": {"role": "assistant", "content": output_text[:2000]}}],
                        "model": model_short,
                    }
                    if usage:
                        input_tokens = usage.get("input_tokens", 0) or 0
                        output_tokens = usage.get("output_tokens", 0) or 0
                        total_tokens = input_tokens + output_tokens
                        llm_outputs["usage"] = {
                            "prompt_tokens": input_tokens,
                            "completion_tokens": output_tokens,
                            "total_tokens": total_tokens,
                        }
                        llm_span.set_attribute("llm.token_usage.input_tokens", input_tokens)
                        llm_span.set_attribute("llm.token_usage.output_tokens", output_tokens)
                        llm_span.set_attribute("llm.token_usage.total_tokens", total_tokens)
                        llm_span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
                        llm_span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
                    llm_span.set_attribute("mlflow.spanOutputs", json.dumps(llm_outputs))

                # Agent span outputs
                agent_outputs: Dict = {
                    "response": output_text[:2000],
                    "tool_count": len(tool_calls),
                    "tools_used": [tc.get("name", "") for tc in tool_calls],
                }
                if response_id:
                    agent_outputs["response_id"] = response_id
                if meta.get("decision"):
                    agent_outputs["decision"] = meta["decision"]
                agent_span.set_attribute("mlflow.spanOutputs", json.dumps(agent_outputs))

            # Root span outputs
            root_outputs: Dict = {
                "agent": agent_id,
                "model": model_short,
                "response": output_text[:2000],
                "tools_used": [tc.get("name", "") for tc in tool_calls],
                "total_tokens": (usage.get("total_tokens", 0) or 0) if usage else 0,
            }
            if response_id:
                root_outputs["response_id"] = response_id
            if meta.get("decision"):
                root_outputs["decision"] = meta["decision"]
            if meta.get("recommendation"):
                root_outputs["recommendation"] = meta["recommendation"]
            root.set_attribute("mlflow.spanOutputs", json.dumps(root_outputs))

        logger.info(f"OTel trace sent: agent={agent_id}, tools={len(tool_calls)}")
    except Exception as e:
        logger.warning(f"Tracing error: {e}", exc_info=True)


# ---------------------------------------------------------------------------
# Spans with an explicit parent, for the A2A path (see app/services/agents/turn_trace.py).
# A chat turn runs in an async generator, where attaching a "current" context across yields
# is not safe: spans are linked to their parent explicitly and ended explicitly. Every
# helper is a no-op on None (tracing disabled).
# ---------------------------------------------------------------------------
def _attributes(values: Dict) -> Dict:
    """OTel attribute values are primitives: drop None, serialize the rest as JSON."""
    out = {}
    for key, value in values.items():
        if value is None:
            continue
        out[key] = value if isinstance(value, (str, bool, int, float)) else json.dumps(value, ensure_ascii=False, default=str)
    return out


def start_span(name: str, parent=None, attributes: Optional[Dict] = None, start_ns: Optional[int] = None):
    """Start a span, child of parent when given; None when tracing is disabled."""
    if not _enabled:
        return None
    from opentelemetry import trace
    context = trace.set_span_in_context(parent) if parent is not None else None
    return _tracer.start_span(name, context=context, attributes=_attributes(attributes or {}), start_time=start_ns)


def set_attributes(span, attributes: Dict) -> None:
    if span is not None:
        span.set_attributes(_attributes(attributes))


def add_event(span, name: str, attributes: Optional[Dict] = None, at_ns: Optional[int] = None) -> None:
    if span is not None:
        span.add_event(name, attributes=_attributes(attributes or {}), timestamp=at_ns)


def end_span(span, error: Optional[str] = None, end_ns: Optional[int] = None) -> None:
    if span is None:
        return
    if error:
        from opentelemetry.trace import Status, StatusCode
        span.set_status(Status(StatusCode.ERROR, error[:500]))
    span.end(end_time=end_ns)


def traceparent(span) -> Optional[str]:
    """W3C traceparent of a span: sent to an agent so that its spans join the trace."""
    if span is None:
        return None
    from opentelemetry import trace
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
    carrier: Dict[str, str] = {}
    TraceContextTextMapPropagator().inject(carrier, context=trace.set_span_in_context(span))
    return carrier.get("traceparent")


def mlflow_trace_id(span) -> Optional[str]:
    """MLflow id of the trace of a span ("tr-" + the OTel trace id in hex)."""
    if span is None:
        return None
    return "tr-" + format(span.get_span_context().trace_id, "032x")


def experiment_id() -> Optional[str]:
    return _experiment_id
