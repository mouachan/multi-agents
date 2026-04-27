"""
MLflow tracing for agentic LLM calls.
Only active when MLFLOW_TRACKING_URI is configured.
"""
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

_mlflow_enabled = False
_mlflow = None

def init_mlflow():
    """Initialize MLflow if tracking URI is configured."""
    global _mlflow_enabled, _mlflow
    if not settings.mlflow_tracking_uri:
        logger.info("MLflow tracing disabled (MLFLOW_TRACKING_URI not set)")
        return
    try:
        import os
        import mlflow
        # Set tracking token for RHOAI Kubernetes auth (bearer token via Route)
        if settings.mlflow_tracking_token:
            os.environ["MLFLOW_TRACKING_TOKEN"] = settings.mlflow_tracking_token
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment(settings.mlflow_experiment_name)
        _mlflow = mlflow
        _mlflow_enabled = True
        logger.info(f"MLflow tracing enabled: {settings.mlflow_tracking_uri}")
    except ImportError:
        logger.warning("mlflow package not installed, tracing disabled")
    except Exception as e:
        logger.warning(f"Failed to initialize MLflow: {e}")

def is_enabled() -> bool:
    return _mlflow_enabled

def start_span(name: str, attributes: Optional[dict] = None):
    """Start an MLflow span. Returns span context or None."""
    if not _mlflow_enabled:
        return None
    try:
        span = _mlflow.start_span(name=name)
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, str(v))
        return span
    except Exception as e:
        logger.debug(f"MLflow span error: {e}")
        return None

def end_span(span, status: str = "OK", attributes: Optional[dict] = None):
    """End an MLflow span."""
    if span is None:
        return
    try:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, str(v))
        span.set_status(status)
        span.end()
    except Exception as e:
        logger.debug(f"MLflow end span error: {e}")

def log_llm_call(agent_id: str, model: str, input_text: str, output_text: str,
                  tool_calls: int = 0, usage: Optional[dict] = None,
                  duration_ms: Optional[int] = None, stream: bool = False):
    """Log an LLM agent call as an MLflow run."""
    if not _mlflow_enabled:
        return
    try:
        with _mlflow.start_run(run_name=f"agent-{agent_id}", nested=True):
            _mlflow.log_params({
                "agent_id": agent_id,
                "model": model,
                "stream": str(stream),
            })
            metrics = {"tool_calls": tool_calls}
            if duration_ms is not None:
                metrics["duration_ms"] = duration_ms
            if usage:
                if "input_tokens" in usage:
                    metrics["input_tokens"] = usage["input_tokens"]
                if "output_tokens" in usage:
                    metrics["output_tokens"] = usage["output_tokens"]
                if "total_tokens" in usage:
                    metrics["total_tokens"] = usage["total_tokens"]
            _mlflow.log_metrics(metrics)
            # Log input/output as text artifacts (truncated)
            _mlflow.log_text(str(input_text)[:5000], "input.txt")
            _mlflow.log_text(str(output_text)[:5000], "output.txt")
    except Exception as e:
        logger.debug(f"MLflow log error: {e}")
