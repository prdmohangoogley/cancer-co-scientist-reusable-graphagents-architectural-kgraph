"""Unit tests for BigQuery Omics Analytics Tool (DOC-01, DOC-09)."""

from __future__ import annotations

import pytest

from adk.traversal import GraphNode
from tools.sql_tools import BigQueryAnalyticsTool


@pytest.mark.asyncio
async def test_bigquery_analytics_tool_mock_enrichment():
    """Verify BigQueryAnalyticsTool enriches biomedical nodes with omics features."""
    tool = BigQueryAnalyticsTool(use_mock=True)

    nodes = [
        GraphNode(id="NCBI:7157", label="Gene", name="TP53"),
        GraphNode(id="DRUGBANK:DB00530", label="Drug", name="Erlotinib"),
        GraphNode(id="MONDO:0005070", label="Disease", name="Lung Neoplasm"),
    ]

    enriched = await tool.enrich_node_metrics(nodes)
    assert len(enriched) == 3

    gene_node = next(n for n in enriched if n.label == "Gene")
    assert "depmap_dependency_score" in gene_node.properties
    assert "cancer_hallmark" in gene_node.properties

    drug_node = next(n for n in enriched if n.label == "Drug")
    assert "indication" in drug_node.properties
    assert "molecular_weight" in drug_node.properties

    disease_node = next(n for n in enriched if n.label == "Disease")
    assert "clinical_description" in disease_node.properties
