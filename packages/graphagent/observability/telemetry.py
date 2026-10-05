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

try:
    from packages.graphagent.observability.pii_scrubber import scrub_pii
except (ImportError, ModuleNotFoundError):
    try:
        from observability.pii_scrubber import scrub_pii
    except (ImportError, ModuleNotFoundError):
        def scrub_pii(data: Any) -> Any:
            return data

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

# OpenTelemetry GenAI Semantic Conventions (ADK >= v2.6.0 compliance)
_GENAI_TOKEN_USAGE_HISTOGRAM = _METER.create_histogram(
    name="gen_ai.client.token.usage",
    unit="{token}",
    description="Measures token usage of GenAI operations",
)
_GENAI_OPERATION_DURATION = _METER.create_histogram(
    name="gen_ai.client.operation.duration",
    unit="s",
    description="Measures the duration of GenAI client operations",
)
_GENAI_SERVER_REQUEST_DURATION = _METER.create_histogram(
    name="gen_ai.server.request.duration",
    unit="s",
    description="Measures incoming server request duration in seconds",
)
_GENAI_TOOL_DURATION = _METER.create_histogram(
    name="gen_ai.tool.duration",
    unit="s",
    description="Duration of tool execution in seconds",
)
_GENAI_TOOL_CALL_COUNT = _METER.create_counter(
    name="gen_ai.tool.call_count",
    unit="{call}",
    description="Total tool call invocations",
)
_AGENT_INVOCATIONS_COUNTER = _METER.create_counter(
    name="agent.invocations",
    unit="{invocation}",
    description="Total agent query invocations",
)
_AGENT_SESSIONS_COUNTER = _METER.create_counter(
    name="agent.sessions",
    unit="{session}",
    description="Total conversational sessions",
)
_AGENT_TURNS_COUNTER = _METER.create_counter(
    name="agent.turns",
    unit="{turn}",
    description="Total conversation turns",
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


def init_telemetry(service_name: str = "cancer-co-scientist-lead-orchestrator") -> Tracer:
    """Initialize OpenTelemetry tracer and meter providers with cloud-ready GCP ReasoningEngine metadata."""
    global _TRACER_INITIALIZED

    if not _TRACER_INITIALIZED:
        project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "fivedaysai-prd-sandbox-317383"
        project_number = os.getenv("GCP_PROJECT_NUMBER", "301802433103")
        reasoning_engine_id = os.getenv("GEA_REASONING_ENGINE_ID", "4359942935643422720")
        region = os.getenv("GEA_REGION", "us-east1")

        resource = Resource.create({
            "service.name": service_name,
            "service.namespace": "vertex-agent-engine",
            "service.version": "2.6.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "production"),
            "cloud.provider": "gcp",
            "cloud.platform": "gcp_vertex_ai",
            "cloud.region": region,
            "gcp.project_id": project_id,
            "gcp.resource_container": f"projects/{project_number}",
            "gcp.resource_type": "aiplatform.googleapis.com/ReasoningEngine",
            "aiplatform.googleapis.com/reasoning_engine_id": reasoning_engine_id,
            "aiplatform.googleapis.com/location": region,
            "aiplatform.googleapis.com/ReasoningEngine": f"projects/{project_number}/locations/{region}/reasoningEngines/{reasoning_engine_id}",
            "reasoning_engine_id": reasoning_engine_id,
            "gen_ai.system": "vertexai",
            "gen_ai.request.model": "gemini-2.5-flash",
        })

        provider = TracerProvider(resource=resource)

        # In GCP environments, attach CloudTraceSpanExporter
        if os.getenv("ENABLE_GCP_TRACE", "true").lower() == "true":
            try:
                from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
                cloud_trace_exporter = CloudTraceSpanExporter(project_id=project_id)
                provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
                logger.info(f"OpenTelemetry CloudTraceSpanExporter attached for project {project_id}")
            except Exception as e:
                logger.warning(f"Could not attach CloudTraceSpanExporter: {e}")

        # In dev/test environments, export to console if enabled
        if os.getenv("OTEL_EXPORTER_CONSOLE", "false").lower() == "true":
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(provider)

        # Attach CloudMonitoringMetricsExporter if available
        try:
            from opentelemetry.exporter.gcp_monitoring import CloudMonitoringMetricsExporter
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            metric_reader = PeriodicExportingMetricReader(
                CloudMonitoringMetricsExporter(project_id=project_id),
                export_interval_millis=5000,
            )
            meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
            metrics.set_meter_provider(meter_provider)
            logger.info(f"OpenTelemetry CloudMonitoringMetricsExporter attached for {project_id}")
        except Exception as e:
            logger.warning(f"Could not attach CloudMonitoringMetricsExporter: {e}")
            metrics.set_meter_provider(MeterProvider(resource=resource))

        _TRACER_INITIALIZED = True
        logger.info(f"OpenTelemetry initialized for {service_name} with ReasoningEngine {reasoning_engine_id}")

    return trace.get_tracer(_TRACER_NAME)


# Google Cloud Monitoring Metrics Client
_MONITORING_CLIENT = None

def get_monitoring_client():
    """Retrieve or initialize singleton Google Cloud Monitoring MetricServiceClient."""
    global _MONITORING_CLIENT
    if _MONITORING_CLIENT is None:
        try:
            from google.cloud import monitoring_v3
            _MONITORING_CLIENT = monitoring_v3.MetricServiceClient()
        except Exception as e:
            logger.warning(f"Could not initialize Google Cloud Monitoring client: {e}")
            _MONITORING_CLIENT = False
    return _MONITORING_CLIENT if _MONITORING_CLIENT is not False else None


def emit_cloud_monitoring_metric(
    metric_type: str,
    value: float,
    metric_kind: str = "GAUGE",
    labels: Optional[dict[str, str]] = None,
) -> bool:
    """Emit custom metric time series point to Google Cloud Monitoring.
    
    Metric type e.g.: 'custom.googleapis.com/agent/orchestrator/latency'
    """
    client = get_monitoring_client()
    if not client:
        return False

    project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "fivedaysai-prd-sandbox-317383"
    project_name = f"projects/{project_id}"
    reasoning_engine_id = os.getenv("GEA_REASONING_ENGINE_ID", "4359942935643422720")
    region = os.getenv("GEA_REGION", "us-east1")

    try:
        from google.cloud import monitoring_v3
        from google.protobuf import timestamp_pb2

        series = monitoring_v3.TimeSeries()
        series.metric.type = metric_type if metric_type.startswith("custom.googleapis.com/") else f"custom.googleapis.com/{metric_type}"
        metric_labels = {
            "reasoning_engine_id": reasoning_engine_id,
            "location": region,
            "project_id": project_id,
            "model": "gemini-2.5-flash",
        }
        if labels:
            metric_labels.update(labels)
        for k, v in metric_labels.items():
            series.metric.labels[k] = str(v)

        series.resource.type = "global"
        series.resource.labels["project_id"] = project_id

        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10**9)
        interval = monitoring_v3.TimeInterval(
            end_time=timestamp_pb2.Timestamp(seconds=seconds, nanos=nanos)
        )

        point = monitoring_v3.Point(
            interval=interval,
            value=monitoring_v3.TypedValue(double_value=float(value)),
        )
        series.points = [point]

        client.create_time_series(name=project_name, time_series=[series])
        return True
    except Exception as e:
        logger.debug(f"Cloud Monitoring metric emission failed for {metric_type}: {e}")
        return False


# Google Cloud Logging Client
_LOGGING_CLIENT = None
_CLOUD_LOGGER = None

def get_cloud_logger():
    """Retrieve or initialize singleton Google Cloud Logging Logger."""
    global _LOGGING_CLIENT, _CLOUD_LOGGER
    if _CLOUD_LOGGER is None:
        try:
            from google.cloud import logging as gcp_logging
            project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "fivedaysai-prd-sandbox-317383"
            _LOGGING_CLIENT = gcp_logging.Client(project=project_id)
            _CLOUD_LOGGER = _LOGGING_CLIENT.logger("aiplatform.googleapis.com/reasoning_engine")
        except Exception as e:
            logger.warning(f"Could not initialize Cloud Logging client: {e}")
            _CLOUD_LOGGER = False
    return _CLOUD_LOGGER if _CLOUD_LOGGER is not False else None


def emit_cloud_log(
    message: str,
    severity: str = "INFO",
    json_payload: Optional[dict[str, Any]] = None,
    **kwargs: Any,
) -> bool:
    """Emit structured log message directly to Google Cloud Logging with PII/PHI de-identification."""
    cloud_logger = get_cloud_logger()
    if not cloud_logger:
        return False

    try:
        # Gracefully handle swapped arguments e.g. emit_cloud_log("INFO", "msg", ...)
        log_levels = {"INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG", "DEFAULT"}
        if message.upper() in log_levels and isinstance(severity, str) and severity.upper() not in log_levels:
            actual_severity = message.upper()
            actual_message = severity
        else:
            actual_message = message
            actual_severity = severity.upper() if isinstance(severity, str) else "INFO"

        sanitized_message = scrub_pii(actual_message)
        payload = {
            "message": sanitized_message,
            "agent": "cancer-co-scientist-lead-orchestrator",
            "reasoning_engine_id": os.getenv("GEA_REASONING_ENGINE_ID", "4359942935643422720"),
            "region": os.getenv("GEA_REGION", "us-east1"),
            "timestamp": time.time(),
        }
        if json_payload:
            payload.update(scrub_pii(json_payload))
        if kwargs:
            payload.update(scrub_pii(kwargs))

        cloud_logger.log_struct(payload, severity=actual_severity)
        return True
    except Exception as e:
        logger.debug(f"Cloud Logging emission failed: {e}")
        return False


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


def record_genai_metrics(
    model_name: str = "gemini-1.5-pro",
    duration_s: float = 0.5,
    prompt_tokens: int = 150,
    completion_tokens: int = 80,
    cached_tokens: int = 0,
    session_id: str = "default_session",
    agent_name: str = "cancer-co-scientist-lead-orchestrator",
) -> None:
    """Record GenAI Semantic Conventions metrics to OTel instruments and Cloud Monitoring."""
    record_token_consumption(prompt_tokens, completion_tokens, cached_tokens)

    # 1. OpenTelemetry GenAI Semantic Histograms
    try:
        attrs = {
            "gen_ai.system": "vertexai",
            "gen_ai.request.model": model_name,
            "gen_ai.response.model": model_name,
            "agent.name": agent_name,
        }
        _GENAI_OPERATION_DURATION.record(duration_s, attributes=attrs)
        _GENAI_TOKEN_USAGE_HISTOGRAM.record(prompt_tokens, attributes={**attrs, "gen_ai.token.type": "input"})
        _GENAI_TOKEN_USAGE_HISTOGRAM.record(completion_tokens, attributes={**attrs, "gen_ai.token.type": "output"})
        if cached_tokens > 0:
            _GENAI_TOKEN_USAGE_HISTOGRAM.record(cached_tokens, attributes={**attrs, "gen_ai.token.type": "cache_read"})

        _AGENT_INVOCATIONS_COUNTER.add(1, attributes={"agent.name": agent_name, "status": "success"})
        _AGENT_TURNS_COUNTER.add(1, attributes={"session.id": session_id, "agent.name": agent_name})
    except Exception as e:
        logger.debug(f"Failed to record OTel GenAI instruments: {e}")

    # 2. Cloud Monitoring direct time-series emission
    try:
        emit_cloud_monitoring_metric("agent/orchestrator/latency", duration_s * 1000.0, labels={"model": model_name})
        emit_cloud_monitoring_metric("agent/orchestrator/invocations", 1.0, labels={"agent": agent_name})
        emit_cloud_monitoring_metric("agent/orchestrator/tokens_consumed", float(prompt_tokens + completion_tokens), labels={"model": model_name})
        emit_cloud_monitoring_metric("agent/model/calls", 1.0, labels={"model": model_name})
        emit_cloud_monitoring_metric("agent/model/duration_ms", duration_s * 1000.0, labels={"model": model_name})
        emit_cloud_monitoring_metric("agent/tokens/input", float(prompt_tokens), labels={"model": model_name})
        emit_cloud_monitoring_metric("agent/tokens/output", float(completion_tokens), labels={"model": model_name})
        emit_cloud_monitoring_metric("agent/sessions/active", 1.0, labels={"session_id": session_id})
    except Exception as e:
        logger.debug(f"Failed to emit Cloud Monitoring GenAI time series: {e}")



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
        project_number = os.getenv("GCP_PROJECT_NUMBER", "301802433103")
        reasoning_engine_id = os.getenv("GEA_REASONING_ENGINE_ID", "4359942935643422720")
        region = os.getenv("GEA_REGION", "us-east1")

        span.set_attribute("gcp.vertex.agent.workflow_type", workflow_type)
        span.set_attribute("aiplatform.googleapis.com/ReasoningEngine", f"projects/{project_number}/locations/{region}/reasoningEngines/{reasoning_engine_id}")
        span.set_attribute("reasoning_engine_id", reasoning_engine_id)
        span.set_attribute("gen_ai.system", "gemini")
        span.set_attribute("gen_ai.request.model", "gemini-2.5-flash")
        span.set_attribute("gen_ai.tool.name", name)
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
            sanitized_attrs = scrub_pii(attributes)
            for k, v in sanitized_attrs.items():
                if v is not None:
                    span.set_attribute(k, str(v) if not isinstance(v, (int, float, bool)) else v)

        t0 = time.time()
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_attribute("error", True)
            span.set_attribute("error.message", scrub_pii(str(exc)))
            raise
        finally:
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            span.set_attribute("graphagent.latency_ms", elapsed_ms)
            span.set_attribute("telemetry.latency_ms", elapsed_ms)
            span.set_attribute("gen_ai.tool.duration", elapsed_ms / 1000.0)

            # Automatically record latency to histogram and summary buffer
            rec_attrs = dict(attributes or {})
            rec_attrs["workflow_type"] = workflow_type
            rec_attrs["gen_ai.tool.name"] = name
            rec_attrs["reasoning_engine_id"] = reasoning_engine_id
            if db_target:
                rec_attrs["db_target"] = db_target
            if trace_id:
                rec_attrs["trace_id"] = trace_id
            if session_id:
                rec_attrs["session_id"] = session_id
            record_latency(name, elapsed_ms, attributes=rec_attrs)


def record_tool_metrics(tool_name: str, duration_s: float, status: str = "success") -> None:
    """Record tool duration and call count to OTel and Cloud Monitoring."""
    attrs = {
        "gen_ai.tool.name": tool_name,
        "gen_ai.system": "vertexai",
        "status": status,
    }
    try:
        _GENAI_TOOL_DURATION.record(duration_s, attributes=attrs)
        _GENAI_TOOL_CALL_COUNT.add(1, attributes=attrs)
    except Exception as e:
        logger.debug(f"Failed to record tool OTel metric: {e}")

    try:
        emit_cloud_monitoring_metric(
            f"agent/tool/{tool_name}/duration_ms",
            duration_s * 1000.0,
            labels={"tool_name": tool_name, "status": status},
        )
        emit_cloud_monitoring_metric(
            f"agent/tool/{tool_name}/calls",
            1.0,
            labels={"tool_name": tool_name, "status": status},
        )
    except Exception as e:
        logger.debug(f"Failed to emit Cloud Monitoring tool metrics: {e}")


def trace_tool(
    tool_name_or_func: Any = None,
    name: Optional[str] = None,
    workflow_type: str = "Discrete",
    db_target: Optional[str] = None,
) -> Callable:
    """Decorator to trace tool execution creating standard gen_ai.tool.{tool_name} span."""
    def make_decorator(tool_identifier: str) -> Callable:
        span_name = f"gen_ai.tool.{tool_identifier}" if not tool_identifier.startswith("gen_ai.tool.") else tool_identifier

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = get_tracer()
                t0 = time.time()
                with tracer.start_as_current_span(
                    span_name,
                    attributes={
                        "gen_ai.tool.name": tool_identifier,
                        "gen_ai.system": "vertexai",
                        "gcp.vertex.agent.workflow_type": workflow_type,
                    },
                ) as span:
                    try:
                        res = await func(*args, **kwargs)
                        span.set_attribute("gen_ai.tool.status", "success")
                        elapsed_s = max(0.001, time.time() - t0)
                        elapsed_ms = round(elapsed_s * 1000.0, 2)
                        span.set_attribute("gen_ai.tool.duration", elapsed_s)
                        span.set_attribute("telemetry.algorithm.latency_ms", elapsed_ms)
                        record_latency(
                            tool_identifier,
                            elapsed_ms,
                            attributes={
                                "workflow_type": workflow_type,
                                "db_target": db_target or "unknown",
                                "gen_ai.tool.name": tool_identifier,
                            },
                        )
                        record_tool_metrics(tool_identifier, elapsed_s, status="success")
                        if hasattr(res, "metrics") and isinstance(res.metrics, dict):
                            if "latency_ms" not in res.metrics:
                                res.metrics["latency_ms"] = elapsed_ms
                        return res
                    except Exception as e:
                        span.set_attribute("gen_ai.tool.status", "error")
                        span.record_exception(e)
                        elapsed_s = max(0.001, time.time() - t0)
                        elapsed_ms = round(elapsed_s * 1000.0, 2)
                        record_latency(
                            tool_identifier,
                            elapsed_ms,
                            attributes={
                                "workflow_type": workflow_type,
                                "db_target": db_target or "unknown",
                                "gen_ai.tool.name": tool_identifier,
                                "error": True,
                            },
                        )
                        record_tool_metrics(tool_identifier, elapsed_s, status="error")
                        raise

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                tracer = get_tracer()
                t0 = time.time()
                with tracer.start_as_current_span(
                    span_name,
                    attributes={
                        "gen_ai.tool.name": tool_identifier,
                        "gen_ai.system": "vertexai",
                        "gcp.vertex.agent.workflow_type": workflow_type,
                    },
                ) as span:
                    try:
                        res = func(*args, **kwargs)
                        span.set_attribute("gen_ai.tool.status", "success")
                        elapsed_s = max(0.001, time.time() - t0)
                        elapsed_ms = round(elapsed_s * 1000.0, 2)
                        span.set_attribute("gen_ai.tool.duration", elapsed_s)
                        span.set_attribute("telemetry.algorithm.latency_ms", elapsed_ms)
                        record_latency(
                            tool_identifier,
                            elapsed_ms,
                            attributes={
                                "workflow_type": workflow_type,
                                "db_target": db_target or "unknown",
                                "gen_ai.tool.name": tool_identifier,
                            },
                        )
                        record_tool_metrics(tool_identifier, elapsed_s, status="success")
                        if hasattr(res, "metrics") and isinstance(res.metrics, dict):
                            if "latency_ms" not in res.metrics:
                                res.metrics["latency_ms"] = elapsed_ms
                        return res
                    except Exception as e:
                        span.set_attribute("gen_ai.tool.status", "error")
                        span.record_exception(e)
                        elapsed_s = max(0.001, time.time() - t0)
                        elapsed_ms = round(elapsed_s * 1000.0, 2)
                        record_latency(
                            tool_identifier,
                            elapsed_ms,
                            attributes={
                                "workflow_type": workflow_type,
                                "db_target": db_target or "unknown",
                                "gen_ai.tool.name": tool_identifier,
                                "error": True,
                            },
                        )
                        record_tool_metrics(tool_identifier, elapsed_s, status="error")
                        raise

            if asyncio_iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator

    if callable(tool_name_or_func):
        return make_decorator(tool_name_or_func.__name__)(tool_name_or_func)

    chosen_name = name or tool_name_or_func or "tool"
    return make_decorator(str(chosen_name))


def asyncio_iscoroutinefunction(func: Any) -> bool:
    """Check if function is an asyncio coroutine function."""
    import inspect
    return inspect.iscoroutinefunction(func)
