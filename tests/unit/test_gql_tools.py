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
