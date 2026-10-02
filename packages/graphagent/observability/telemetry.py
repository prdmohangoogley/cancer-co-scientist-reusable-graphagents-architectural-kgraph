"""OpenTelemetry instrumentation and observability for GraphAgent Worker Tier.

Adheres to:
- DOC-01: AI Agent Quality Engineering & Observability
- DOC-02: Zero Ambient Authority & Auditable Operation Logs
- Spec 06: OpenTelemetry Bindings & Latency Breakdown
"""

from __future__ import annotations

import collections
import contextvars
import functools
import logging
import math
import os
import sys
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional

# Ensure singleton module identity across different sys.path import roots
if __name__ == "observability.telemetry":
    sys.modules.setdefault("packages.graphagent.observability.telemetry", sys.modules[__name__])
elif __name__ == "packages.graphagent.observability.telemetry":
    sys.modules.setdefault("observability.telemetry", sys.modules[__name__])

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Span, Tracer

logger = logging.getLogger("graphagent_telemetry")

_TRACER_INITIALIZED = False
_TRACER_NAME = "graphagent.worker.tracer"
_METER_NAME = "graphagent.worker.meter"

# OpenTelemetry Metrics Instruments
_METER = metrics.get_meter(_METER_NAME)
_LATENCY_HISTOGRAM = _METER.create_histogram(
    name="telemetry.algorithm.latency",
    unit="ms",
    description="Execution latency of graph algorithms and tools",
)
_PROMPT_TOKENS_COUNTER = _METER.create_counter(
    name="llm.tokens.prompt",
    unit="tokens",
    description="Number of prompt tokens consumed",
)
_COMPLETION_TOKENS_COUNTER = _METER.create_counter(
    name="llm.tokens.completion",
    unit="tokens",
    description="Number of completion tokens generated",
)
_CACHED_TOKENS_COUNTER = _METER.create_counter(
    name="llm.tokens.cached",
    unit="tokens",
    description="Number of cached context tokens",
)

# In-memory storage for metrics analysis and summaries
_LATENCY_RECORDS: dict[str, list[float]] = collections.defaultdict(list)
_TOKEN_STATE: dict[str, int] = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "cached_tokens": 0,
}

# Correlation Context storage (trace_id, session_id, user_id)
_CORRELATION_CONTEXT: contextvars.ContextVar[dict[str, str]] = contextvars.ContextVar(
    "correlation_context",
    default={
        "trace_id": "",
        "session_id": "",
        "user_id": "",
    },
)


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
        metrics.set_meter_provider(MeterProvider(resource=resource))
        _TRACER_INITIALIZED = True
        logger.info(f"OpenTelemetry initialized for {service_name}")

    return trace.get_tracer(_TRACER_NAME)


def get_tracer() -> Tracer:
    """Retrieve global tracer instance."""
    return trace.get_tracer(_TRACER_NAME)


# =============================================================================
# Correlation Context Management
# =============================================================================

def set_correlation_context(trace_id: str, session_id: str, user_id: str = "") -> None:
    """Set correlation IDs in thread/asyncio context."""
    _CORRELATION_CONTEXT.set({
        "trace_id": trace_id,
        "session_id": session_id,
        "user_id": user_id,
    })


def get_correlation_context() -> dict[str, str]:
    """Retrieve active correlation IDs, falling back to active OTel span if needed."""
    ctx = dict(_CORRELATION_CONTEXT.get())
    if not ctx.get("trace_id"):
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().is_valid:
            ctx["trace_id"] = format(current_span.get_span_context().trace_id, "032x")
    return ctx


# =============================================================================
# Latency Histogram / Recorder
# =============================================================================

def record_latency(name: str, latency_ms: float, attributes: Optional[dict[str, Any]] = None) -> None:
    """Record execution latency for a tool or graph algorithm."""
    attrs = attributes or {}
    _LATENCY_RECORDS[name].append(float(latency_ms))
    try:
        _LATENCY_HISTOGRAM.record(latency_ms, attributes=attrs)
    except Exception as e:
        logger.debug(f"Failed to record OTel latency histogram: {e}")


def _calculate_percentile(data: list[float], percentile: float) -> float:
    """Compute percentile using linear interpolation between closest ranks."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    if len(sorted_data) == 1:
        return round(float(sorted_data[0]), 2)
    k = (len(sorted_data) - 1) * percentile
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return round(float(sorted_data[int(k)]), 2)
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return round(float(d0 + d1), 2)


def get_latency_summary() -> dict[str, dict[str, float]]:
    """Compute p50, p95, and p99 percentiles for recorded tools/algorithms."""
    summary: dict[str, dict[str, float]] = {}
    all_latencies: list[float] = []

    for name, latencies in _LATENCY_RECORDS.items():
        if not latencies:
            continue
        all_latencies.extend(latencies)
        summary[name] = {
            "p50": _calculate_percentile(latencies, 0.50),
            "p95": _calculate_percentile(latencies, 0.95),
            "p99": _calculate_percentile(latencies, 0.99),
        }

    if all_latencies:
        summary["overall"] = {
            "p50": _calculate_percentile(all_latencies, 0.50),
            "p95": _calculate_percentile(all_latencies, 0.95),
            "p99": _calculate_percentile(all_latencies, 0.99),
        }

    return summary


# =============================================================================
# Token Consumption Counters
# =============================================================================

def record_token_consumption(
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0,
) -> None:
    """Record LLM token usage and update cumulative state and OTel counters."""
    _TOKEN_STATE["prompt_tokens"] += prompt_tokens
    _TOKEN_STATE["completion_tokens"] += completion_tokens
    _TOKEN_STATE["cached_tokens"] += cached_tokens

    try:
        _PROMPT_TOKENS_COUNTER.add(prompt_tokens)
        _COMPLETION_TOKENS_COUNTER.add(completion_tokens)
        if cached_tokens > 0:
            _CACHED_TOKENS_COUNTER.add(cached_tokens)
    except Exception as e:
        logger.debug(f"Failed to record OTel token metrics: {e}")


def get_token_summary() -> dict[str, Any]:
    """Return prompt_tokens, completion_tokens, cached_tokens, and cache_hit_rate_pct."""
    prompt = _TOKEN_STATE["prompt_tokens"]
    completion = _TOKEN_STATE["completion_tokens"]
    cached = _TOKEN_STATE["cached_tokens"]
    cache_hit_rate = round((cached / prompt * 100), 2) if prompt > 0 else 0.0

    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "cached_tokens": cached,
        "cache_hit_rate_pct": cache_hit_rate,
    }


# =============================================================================
# Information Retrieval (IR) Evaluation Metrics
# =============================================================================

def calculate_retrieval_metrics(
    retrieved_ids: list[str],
    ground_truth_ids: list[str],
    k: int = 10,
) -> dict[str, float]:
    """Calculate Mean Average Precision (mAP), Precision@k, and Recall@k."""
    if not retrieved_ids or not ground_truth_ids or k <= 0:
        return {"map": 0.0, "precision_at_k": 0.0, "recall_at_k": 0.0}

    gt_set = set(ground_truth_ids)
    retrieved_k = retrieved_ids[:k]

    hits = 0
    sum_precisions = 0.0

    for rank, item_id in enumerate(retrieved_k, start=1):
        if item_id in gt_set:
            hits += 1
            sum_precisions += hits / rank

    precision_at_k = hits / float(k)
    recall_at_k = hits / float(len(gt_set)) if gt_set else 0.0
    denom = min(len(gt_set), k)
    map_score = sum_precisions / float(denom) if denom > 0 else 0.0

    return {
        "map": round(map_score, 4),
        "precision_at_k": round(precision_at_k, 4),
        "recall_at_k": round(recall_at_k, 4),
    }


def reset_telemetry() -> None:
    """Reset in-memory metric buffers and correlation context for clean test isolation."""
    _LATENCY_RECORDS.clear()
    _TOKEN_STATE["prompt_tokens"] = 0
    _TOKEN_STATE["completion_tokens"] = 0
    _TOKEN_STATE["cached_tokens"] = 0
    _CORRELATION_CONTEXT.set({"trace_id": "", "session_id": "", "user_id": ""})


# =============================================================================
# Tracing Instrumentation: Spans & Decorators
# =============================================================================

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
    - trace_id, session_id (Correlation Context)
    - graphagent.latency_ms (and records to latency histogram)
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        span.set_attribute("gcp.vertex.agent.workflow_type", workflow_type)
        if db_target:
            span.set_attribute("gcp.vertex.agent.db_target", db_target)

        # Correlation context injection
        corr = get_correlation_context()
        span_ctx = span.get_span_context()
        trace_id = corr.get("trace_id") or (
            format(span_ctx.trace_id, "032x") if span_ctx.is_valid else ""
        )
        session_id = corr.get("session_id") or ""
        user_id = corr.get("user_id") or ""

        if trace_id:
            span.set_attribute("trace_id", trace_id)
            span.set_attribute("gcp.trace.id", trace_id)
        if session_id:
            span.set_attribute("session_id", session_id)
        if user_id:
            span.set_attribute("user_id", user_id)

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
            span.set_attribute("telemetry.latency_ms", elapsed_ms)

            # Automatically record latency to histogram and summary buffer
            rec_attrs = dict(attributes or {})
            rec_attrs["workflow_type"] = workflow_type
            if db_target:
                rec_attrs["db_target"] = db_target
            if trace_id:
                rec_attrs["trace_id"] = trace_id
            if session_id:
                rec_attrs["session_id"] = session_id
            record_latency(name, elapsed_ms, attributes=rec_attrs)


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
            t0 = time.time()
            with trace_span(span_name, workflow_type=workflow_type, db_target=db_target) as span:
                span.set_attribute("gen_ai.tool.name", span_name)
                res = await func(*args, **kwargs)
                elapsed_ms = round((time.time() - t0) * 1000, 2)
                span.set_attribute("telemetry.algorithm.latency_ms", elapsed_ms)
                if hasattr(res, "metrics") and isinstance(res.metrics, dict):
                    if "latency_ms" not in res.metrics:
                        res.metrics["latency_ms"] = elapsed_ms
                return res

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            t0 = time.time()
            with trace_span(span_name, workflow_type=workflow_type, db_target=db_target) as span:
                span.set_attribute("gen_ai.tool.name", span_name)
                res = func(*args, **kwargs)
                elapsed_ms = round((time.time() - t0) * 1000, 2)
                span.set_attribute("telemetry.algorithm.latency_ms", elapsed_ms)
                if hasattr(res, "metrics") and isinstance(res.metrics, dict):
                    if "latency_ms" not in res.metrics:
                        res.metrics["latency_ms"] = elapsed_ms
                return res

        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def asyncio_iscoroutinefunction(func: Any) -> bool:
    """Check if function is an asyncio coroutine function."""
    import inspect
    return inspect.iscoroutinefunction(func)
