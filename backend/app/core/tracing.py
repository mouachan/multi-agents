"""
MLflow Tracing module -- conditional instrumentation for agent observability.

Activation via MLFLOW_TRACING_ENABLED (default: false).
Uses mlflow-tracing SDK with manual @mlflow.trace decorators.
Lazy imports to avoid errors when mlflow-tracing is not installed.
"""

import asyncio
import functools
import inspect
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_tracing() -> None:
    """Initialize MLflow tracing at application startup.

    Configures tracking URI and experiment name. No-op when disabled.
    """
    if not settings.mlflow_tracing_enabled:
        logger.info("MLflow Tracing is disabled")
        return

    try:
        import mlflow

        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment(settings.mlflow_experiment_name)
        logger.info(
            "MLflow Tracing enabled: uri=%s, experiment=%s",
            settings.mlflow_tracking_uri,
            settings.mlflow_experiment_name,
        )
    except ImportError:
        logger.warning(
            "mlflow-tracing package not installed -- tracing disabled. "
            "Install with: pip install mlflow-tracing"
        )
    except Exception as e:
        logger.error("Failed to initialize MLflow Tracing: %s", e)


def trace(name: str, span_type: Optional[str] = None):
    """Conditional tracing decorator.

    When MLflow tracing is enabled, wraps the function with @mlflow.trace.
    When disabled, returns the function unchanged (zero overhead).

    Args:
        name: Span name for the trace.
        span_type: MLflow span type (e.g. "LLM", "AGENT").
    """
    def decorator(func):
        if not settings.mlflow_tracing_enabled:
            return func

        try:
            import mlflow

            kwargs = {"name": name}
            if span_type:
                kwargs["span_type"] = span_type

            # Async generators (yield-based) cannot be wrapped with @mlflow.trace
            # directly. Use manual span management instead.
            if inspect.isasyncgenfunction(func):
                @functools.wraps(func)
                async def async_gen_wrapper(*args, **kw):
                    with mlflow.start_span(name=name, span_type=span_type or "UNKNOWN"):
                        async for item in func(*args, **kw):
                            yield item
                return async_gen_wrapper

            @mlflow.trace(**kwargs)
            @functools.wraps(func)
            async def async_wrapper(*args, **kw):
                return await func(*args, **kw)

            @mlflow.trace(**kwargs)
            @functools.wraps(func)
            def sync_wrapper(*args, **kw):
                return func(*args, **kw)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        except ImportError:
            return func

    return decorator


def enrich_span(attributes: dict) -> None:
    """Add attributes to the current active MLflow span.

    No-op when tracing is disabled or no active span exists.

    Args:
        attributes: Key-value pairs to attach to the current span.
    """
    if not settings.mlflow_tracing_enabled:
        return

    try:
        import mlflow

        span = mlflow.get_current_active_span()
        if span:
            span.set_attributes(attributes)
    except (ImportError, Exception):
        pass
