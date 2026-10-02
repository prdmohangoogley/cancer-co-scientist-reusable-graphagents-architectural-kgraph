"""Unit tests for OpenTelemetry observability bindings (DOC-01, Spec 06)."""

from __future__ import annotations

import pytest

try:
    from observability.telemetry import (
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
except ImportError:
    from packages.graphagent.observability.telemetry import (
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


@pytest.fixture(autouse=True)
def clean_telemetry():
    """Reset telemetry buffers before and after every test."""
    reset_telemetry()
    yield
    reset_telemetry()


def test_init_telemetry():
    """Verify tracer initialization and retrieval."""
    tracer = init_telemetry("test-service")
    assert tracer is not None
    assert get_tracer() is not None


def test_trace_span_context_manager():
    """Verify custom span injection with workflow and target attributes."""
    with trace_span("test.operation", workflow_type="Discrete", db_target="Spanner") as span:
        assert span is not None
    
    summary = get_latency_summary()
    assert "test.operation" in summary
    assert summary["test.operation"]["p50"] >= 0.0


@pytest.mark.asyncio
async def test_trace_tool_decorator_async():
    """Verify @trace_tool decorator wraps async functions and records latency."""

    @trace_tool(name="test_async_tool", workflow_type="Structural", db_target="BigQuery")
    async def sample_async_task(val: int) -> int:
        return val * 2

    result = await sample_async_task(21)
    assert result == 42

    summary = get_latency_summary()
    assert "test_async_tool" in summary
    assert summary["test_async_tool"]["p50"] >= 0.0


def test_trace_tool_decorator_sync():
    """Verify @trace_tool decorator wraps sync functions and records latency."""

    @trace_tool(name="test_sync_tool", workflow_type="Continuous", db_target="GKE")
    def sample_sync_task(msg: str) -> str:
        return f"Echo: {msg}"

    result = sample_sync_task("hello")
    assert result == "Echo: hello"

    summary = get_latency_summary()
    assert "test_sync_tool" in summary
    assert summary["test_sync_tool"]["p50"] >= 0.0


def test_latency_recorder_and_percentiles():
    """Verify record_latency and p50, p95, p99 percentiles calculation."""
    for lat in [10.0, 20.0, 30.0, 40.0, 50.0]:
        record_latency("algo_dfs", lat, attributes={"workflow": "Discrete"})

    for lat in [100.0, 200.0, 300.0]:
        record_latency("algo_alphafold", lat, attributes={"workflow": "Continuous"})

    summary = get_latency_summary()
    assert "algo_dfs" in summary
    assert summary["algo_dfs"]["p50"] == 30.0
    assert summary["algo_dfs"]["p95"] == 48.0
    assert summary["algo_dfs"]["p99"] == 49.6

    assert "algo_alphafold" in summary
    assert summary["algo_alphafold"]["p50"] == 200.0

    assert "overall" in summary
    assert summary["overall"]["p50"] > 0.0


def test_token_consumption_counters():
    """Verify token recording and cache hit rate calculation."""
    record_token_consumption(prompt_tokens=1000, completion_tokens=250, cached_tokens=700)
    summary = get_token_summary()

    assert summary["prompt_tokens"] == 1000
    assert summary["completion_tokens"] == 250
    assert summary["cached_tokens"] == 700
    assert summary["cache_hit_rate_pct"] == 70.0

    # Accumulate more tokens
    record_token_consumption(prompt_tokens=500, completion_tokens=100, cached_tokens=300)
    updated = get_token_summary()
    assert updated["prompt_tokens"] == 1500
    assert updated["completion_tokens"] == 350
    assert updated["cached_tokens"] == 1000
    assert updated["cache_hit_rate_pct"] == 66.67


def test_correlation_id_context():
    """Verify correlation ID context storage and propagation."""
    set_correlation_context(
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
        session_id="session-user-9912",
        user_id="oncologist-dr-smith",
    )
    ctx = get_correlation_context()
    assert ctx["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert ctx["session_id"] == "session-user-9912"
    assert ctx["user_id"] == "oncologist-dr-smith"

    # Verify context injection in span
    with trace_span("correlated_operation") as span:
        assert span is not None


def test_calculate_retrieval_metrics():
    """Verify mAP, precision@k, and recall@k calculation."""
    ground_truth = ["GENE_A", "GENE_B", "GENE_C", "GENE_D", "GENE_E"]
    retrieved = ["GENE_A", "GENE_B", "OTHER_1", "GENE_C", "GENE_D", "OTHER_2", "GENE_E"]

    metrics = calculate_retrieval_metrics(retrieved, ground_truth, k=5)
    # At k=5: retrieved are GENE_A, GENE_B, OTHER_1, GENE_C, GENE_D (4 relevant out of 5)
    # Precision@5 = 4 / 5 = 0.80
    assert metrics["precision_at_k"] == 0.80
    # Recall@5 = 4 / 5 = 0.80
    assert metrics["recall_at_k"] == 0.80
    # AP: rank1=1/1, rank2=2/2, rank4=3/4, rank5=4/5 -> sum = 1 + 1 + 0.75 + 0.80 = 3.55 / 5 = 0.71
    assert metrics["map"] == 0.71


def test_calculate_retrieval_metrics_edge_cases():
    """Verify retrieval metric calculations on empty inputs."""
    res_empty = calculate_retrieval_metrics([], ["A", "B"], k=10)
    assert res_empty == {"map": 0.0, "precision_at_k": 0.0, "recall_at_k": 0.0}

    res_no_gt = calculate_retrieval_metrics(["A", "B"], [], k=10)
    assert res_no_gt == {"map": 0.0, "precision_at_k": 0.0, "recall_at_k": 0.0}
