"""Unit tests for biomedical traversal models (DOC-01, DOC-03)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from adk.traversal import GraphEdge, GraphNode, SubgraphResult, TraversalConfig


def test_traversal_config_defaults():
    """Verify default traversal constraints."""
    config = TraversalConfig()
    assert config.max_hops == 2
    assert config.min_confidence == 0.7
    assert config.limit == 50
    assert config.allowed_edge_types is None


def test_traversal_config_validation():
    """Verify bounds enforcement on traversal configuration."""
    with pytest.raises(ValidationError):
        TraversalConfig(max_hops=10)  # max is 5

    with pytest.raises(ValidationError):
        TraversalConfig(min_confidence=-0.1)  # ge=0.0


def test_graph_node_serialization():
    """Verify GraphNode model serialization and properties."""
    node = GraphNode(
        id="NCBI:7157",
        label="Gene",
        name="TP53",
        properties={"cancer_hallmark": "Genome Instability", "druggability": "High"},
    )
    dumped = node.model_dump()
    assert dumped["id"] == "NCBI:7157"
    assert dumped["label"] == "Gene"
    assert dumped["name"] == "TP53"
    assert dumped["properties"]["druggability"] == "High"


def test_graph_edge_serialization():
    """Verify GraphEdge serialization and default confidence."""
    edge = GraphEdge(
        source_id="NCBI:7157",
        target_id="MONDO:18513",
        relationship="ASSOCIATED_WITH",
        evidence_source="DisGeNET",
    )
    assert edge.confidence == 1.0
    assert edge.relationship == "ASSOCIATED_WITH"
    assert edge.evidence_source == "DisGeNET"


def test_subgraph_result_assembly():
    """Verify SubgraphResult holds nodes, edges, and provenance."""
    node_a = GraphNode(id="A", label="Gene", name="GeneA")
    node_b = GraphNode(id="B", label="Disease", name="DiseaseB")
    edge = GraphEdge(source_id="A", target_id="B", relationship="TARGETS")

    result = SubgraphResult(
        nodes=[node_a, node_b],
        edges=[edge],
        query_target="GeneA -> DiseaseB",
        hops_traversed=1,
        summary="Found 1 direct targeting edge linking GeneA to DiseaseB.",
    )
    assert len(result.nodes) == 2
    assert len(result.edges) == 1
    assert result.hops_traversed == 1
    assert "GeneA" in result.summary

