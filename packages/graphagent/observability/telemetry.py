"""OpenTelemetry instrumentation and observability for GraphAgent Worker Tier.

Adheres to:
- DOC-01: AI Agent Quality Engineering & Observability
- DOC-02: Zero Ambient Authority & Auditable Operation Logs
- Spec 06: OpenTelemetry Bindings & Latency Breakdown
"""

from __future__ import annotations

import functools
import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Span, Tracer

logger = logging.getLogger("graphagent_telemetry")

_TRACER_INITIALIZED = False
_TRACER_NAME = "graphagent.worker.tracer"


def init_telemetry(service_name: str = "graphagent-worker") -> Tracer:
    """Initialize OpenTelemetry tracer provider with cloud-ready resource metadata."""
    global _TRACER_INITIALIZED

    if not _TRACER_INITIALIZED:
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "0.1.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "dev"),
            "cloud.provider": "gcp",
        })

        provider = TracerProvider(resource=resource)

        # In dev/test environments, export to console or in-memory
        if os.getenv("OTEL_EXPORTER_CONSOLE", "false").lower() == "true":
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(provider)
        _TRACER_INITIALIZED = True
        logger.info(f"OpenTelemetry initialized for {service_name}")

    return trace.get_tracer(_TRACER_NAME)


def get_tracer() -> Tracer:
    """Retrieve global tracer instance."""
    return trace.get_tracer(_TRACER_NAME)


@contextmanager
def trace_span(
    name: str,
    workflow_type: str = "Discrete",
    db_target: Optional[str] = None,
    attributes: Optional[dict[str, Any]] = None,
) -> Iterator[Span]:
    """Context manager creating an instrumented OpenTelemetry span.

    Injects canonical enterprise attributes:
    - gcp.vertex.agent.workflow_type (Discrete, Continuous, Temporal, Structural)
    - gcp.vertex.agent.db_target (Spanner, BigQuery, GKE)
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        span.set_attribute("gcp.vertex.agent.workflow_type", workflow_type)
        if db_target:
            span.set_attribute("gcp.vertex.agent.db_target", db_target)

        if attributes:
            for k, v in attributes.items():
                if v is not None:
                    span.set_attribute(k, str(v) if not isinstance(v, (int, float, bool)) else v)

        t0 = time.time()
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(exc))
            raise
        finally:
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            span.set_attribute("graphagent.latency_ms", elapsed_ms)


def trace_tool(
    name: Optional[str] = None,
    workflow_type: str = "Discrete",
    db_target: Optional[str] = None,
) -> Callable:
    """Decorator to trace tool and agent method executions with standard GenAI conventions."""
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            with trace_span(span_name, workflow_type=workflow_type, db_target=db_target) as span:
                span.set_attribute("gen_ai.tool.name", span_name)
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with trace_span(span_name, workflow_type=workflow_type, db_target=db_target) as span:
                span.set_attribute("gen_ai.tool.name", span_name)
                return func(*args, **kwargs)

        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def asyncio_iscoroutinefunction(func: Any) -> bool:
    """Check if function is an asyncio coroutine function."""
    import inspect
    return inspect.iscoroutinefunction(func)
