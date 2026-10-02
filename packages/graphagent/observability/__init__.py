"""Observability and OpenTelemetry package for GraphAgent."""

from .telemetry import (
    calculate_retrieval_metrics,
    get_correlation_context,
    get_latency_summary,
    get_token_summary,
    get_tracer,
    init_telemetry,
    record_latency,
    record_token_consumption,
    reset_telemetry,
    set_correlation_context,
    trace_span,
    trace_tool,
)

__all__ = [
    "get_tracer",
    "init_telemetry",
    "trace_span",
    "trace_tool",
    "record_latency",
    "get_latency_summary",
    "record_token_consumption",
    "get_token_summary",
    "set_correlation_context",
    "get_correlation_context",
    "calculate_retrieval_metrics",
    "reset_telemetry",
]
