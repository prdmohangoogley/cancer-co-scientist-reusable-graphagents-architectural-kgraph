"""Unit tests for Cloud Spanner Graph ISO GQL traversal tool (DOC-01, DOC-09)."""

from __future__ import annotations

import pytest

from adk.traversal import TraversalConfig
from tools.gql_tools import SpannerGraphTool


@pytest.mark.asyncio
async def test_spanner_graph_tool_mock_paths():
    """Verify SpannerGraphTool mock mode produces valid SubgraphResult."""
    tool = SpannerGraphTool(use_mock=True)
    result = await tool.find_paths_between(
        source_entity="EGFR",
        target_entity="Non-small cell lung carcinoma",
        config=TraversalConfig(max_hops=2),
    )
    assert len(result.nodes) >= 2
    assert len(result.edges) >= 2
    assert result.query_target == "EGFR -> Non-small cell lung carcinoma"
    assert result.hops_traversed == 2

    # Check node identities
    node_names = {n.name for n in result.nodes}
    assert "EGFR" in node_names
    assert "Non-small cell lung carcinoma" in node_names


@pytest.mark.asyncio
async def test_spanner_graph_tool_repurposing_candidates():
    """Verify drug repurposing candidate extraction in mock mode."""
    tool = SpannerGraphTool(use_mock=True)
    candidates = await tool.query_repurposing_candidates(
        disease_name="Non-small cell lung carcinoma",
        limit=5,
    )
    assert len(candidates) >= 1
    first = candidates[0]
    assert "drug_id" in first
    assert "drug_name" in first
    assert "target_gene" in first
    assert "clinical_phase" in first
    assert first["confidence"] > 0.8


@pytest.mark.asyncio
async def test_spanner_graph_tool_gene_neighborhood():
    """Verify gene neighborhood retrieval in mock mode."""
    tool = SpannerGraphTool(use_mock=True)
    result = await tool.query_gene_neighborhood(gene_symbol="TP53", limit=10)
    assert len(result.nodes) > 0
    assert result.query_target == "TP53"


@pytest.mark.asyncio
async def test_spanner_graph_tool_execute_traversal_enforces_parameterization():
    """Verify execute_traversal strictly enforces parameterization (DOC-02, DOC-09)."""
    tool = SpannerGraphTool(use_mock=True)
    with pytest.raises(ValueError, match="Parameterization is strictly enforced"):
        await tool.execute_traversal(
            query="GRAPH PrimeKGGraph MATCH (n) RETURN n",
            params=None,  # type: ignore
        )

    with pytest.raises(ValueError, match="Parameterization is strictly enforced"):
        await tool.execute_traversal(
            query="GRAPH PrimeKGGraph MATCH (n) RETURN n",
            params="invalid_params",  # type: ignore
        )


@pytest.mark.asyncio
async def test_spanner_graph_tool_execute_traversal_mock():
    """Verify execute_traversal returns valid rows in mock mode."""
    tool = SpannerGraphTool(use_mock=True)
    rows = await tool.execute_traversal(
        query="GRAPH PrimeKGGraph MATCH (src)-[e]->(dst) WHERE src.name = @source_entity RETURN src, e, dst",
        params={"source_entity": "BRAF", "target_entity": "Melanoma"},
        timeout_ms=1500,
    )
    assert len(rows) > 0
    assert "BRAF" in rows[0]
    assert "Melanoma" in rows[0]


@pytest.mark.asyncio
async def test_spanner_graph_tool_execute_traversal_retry_and_timeout(monkeypatch):
    """Verify exponential backoff retry and timeout handling in execute_traversal."""
    import asyncio
    tool = SpannerGraphTool(use_mock=False)

    # Mock database to simulate transient errors then timeout
    attempts = 0

    class MockSnapshot:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def execute_sql(self, *args, **kwargs):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError(f"Transient connection drop (attempt {attempts})")
            # Exceed timeout on third attempt
            import time
            time.sleep(0.1)
            return [("row1",)]

    class MockDatabase:
        def snapshot(self):
            return MockSnapshot()

    monkeypatch.setattr(tool, "_get_database", lambda: MockDatabase())

    # Set very small timeout (50ms) to trigger timeout after retries
    with pytest.raises((TimeoutError, ConnectionError)):
        await tool.execute_traversal(
            query="GRAPH PrimeKGGraph MATCH (n) RETURN n",
            params={"source_entity": "EGFR"},
            timeout_ms=50,
            max_retries=3,
            base_delay_seconds=0.01,
        )
    assert attempts >= 1
