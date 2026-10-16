"""MLflow tracing (OpenTelemetry): spans sent over OTLP/HTTP to the MLflow server of OpenShift AI.

Authentication with the pod's ServiceAccount token, TLS with the OpenShift service CA; active only
when MLFLOW_TRACKING_URI is set. The backend opens the root span of each chat turn or processing
(app/services/turn_trace.py); the agents' spans join the same trace (W3C traceparent in the A2A
request), so one turn is one MLflow trace in experiment MLFLOW_EXPERIMENT_NAME.
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


def mlflow_verify():
    """TLS verification for the MLflow API: the OpenShift service CA in the cluster."""
    return SERVICE_CA_PATH if os.path.exists(SERVICE_CA_PATH) else False


def mlflow_headers() -> Dict[str, str]:
    """Authentication to the MLflow API: the pod's ServiceAccount token, and the RHOAI workspace."""
    headers: Dict[str, str] = {}
    if os.path.exists(SA_TOKEN_PATH):
        with open(SA_TOKEN_PATH) as f:
            headers["Authorization"] = f"Bearer {f.read().strip()}"
    if settings.mlflow_rhoai_workspace:
        headers["X-Mlflow-Workspace"] = settings.mlflow_rhoai_workspace
    return headers


def _resolve_experiment_id(retries: int = 5, delay: float = 3.0) -> str:
    """Resolve MLflow experiment ID from name via REST API, with retries."""
    verify = mlflow_verify()
    url = (
        f"{settings.mlflow_tracking_uri.rstrip('/')}"
        f"/api/2.0/mlflow/experiments/get-by-name"
        f"?experiment_name={settings.mlflow_experiment_name}"
    )
    headers = mlflow_headers()

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

        otlp_headers = mlflow_headers()
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
