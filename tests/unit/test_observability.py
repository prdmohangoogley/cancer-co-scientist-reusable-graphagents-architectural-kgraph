"""Unit tests for OpenTelemetry observability bindings (DOC-01, Spec 06)."""

from __future__ import annotations

import pytest

try:
    from observability.telemetry import (
        get_tracer,
        init_telemetry,
        trace_span,
        trace_tool,
    )
except ImportError:
    from packages.graphagent.observability.telemetry import (
        get_tracer,
        init_telemetry,
        trace_span,
        trace_tool,
    )



def test_init_telemetry():
    """Verify tracer initialization and retrieval."""
    tracer = init_telemetry("test-service")
    assert tracer is not None
    assert get_tracer() is not None


def test_trace_span_context_manager():
    """Verify custom span injection with workflow and target attributes."""
    with trace_span("test.operation", workflow_type="Discrete", db_target="Spanner") as span:
        assert span is not None


@pytest.mark.asyncio
async def test_trace_tool_decorator_async():
    """Verify @trace_tool decorator wraps async functions seamlessly."""

    @trace_tool(name="test_async_tool", workflow_type="Structural", db_target="BigQuery")
    async def sample_async_task(val: int) -> int:
        return val * 2

    result = await sample_async_task(21)
    assert result == 42


def test_trace_tool_decorator_sync():
    """Verify @trace_tool decorator wraps sync functions seamlessly."""

    @trace_tool(name="test_sync_tool", workflow_type="Continuous", db_target="GKE")
    def sample_sync_task(msg: str) -> str:
        return f"Echo: {msg}"

    result = sample_sync_task("hello")
    assert result == "Echo: hello"
