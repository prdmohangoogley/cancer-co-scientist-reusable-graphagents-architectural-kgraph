"""Integration tests executing against live Cloud Spanner Graph and BigQuery (DOC-01, DOC-09)."""

from __future__ import annotations

import os
import pytest

from adk.agent import PrimeKGWorkerAgent
from adk.traversal import GraphNode
from tools.gql_tools import SpannerGraphTool
from tools.sql_tools import BigQueryAnalyticsTool

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "fivedaysai-prd-sandbox-317383")
SPANNER_INSTANCE = os.getenv("SPANNER_INSTANCE", "primekg-instance-dev")
SPANNER_DB = os.getenv("SPANNER_DATABASE", "primekg-database")
BQ_DATASET = os.getenv("BQ_DATASET", "primekg_analytics_dev")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_spanner_graph_query():
    """Verify live ISO GQL execution against PrimeKGGraph in Cloud Spanner."""
    tool = SpannerGraphTool(
        project_id=PROJECT_ID,
        instance_id=SPANNER_INSTANCE,
        database_id=SPANNER_DB,
        use_mock=False,
    )
    result = await tool.query_gene_neighborhood(gene_symbol="TP53", limit=5)
    assert len(result.nodes) > 0
    assert len(result.edges) > 0
    assert any(n.name == "TP53" for n in result.nodes)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_bigquery_enrichment():
    """Verify live BigQuery node enrichment against primekg_analytics_dev."""
    tool = BigQueryAnalyticsTool(
        project_id=PROJECT_ID,
        dataset_id=BQ_DATASET,
        use_mock=False,
    )
    nodes = [
        GraphNode(id="DRUGBANK:DB00530", label="Drug", name="Erlotinib"),
        GraphNode(id="NCBI:7157", label="Gene", name="TP53"),
    ]
    enriched = await tool.enrich_node_metrics(nodes)
    drug_node = next(n for n in enriched if n.name == "Erlotinib")
    assert "indication" in drug_node.properties or "molecular_weight" in drug_node.properties


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_worker_agent_end_to_end():
    """Verify full Worker Agent coordination over live Cloud Spanner and BigQuery."""
    worker = PrimeKGWorkerAgent(
        project_id=PROJECT_ID,
        instance_id=SPANNER_INSTANCE,
        database_id=SPANNER_DB,
        bq_dataset_id=BQ_DATASET,
        use_mock=False,
    )
    result = await worker.explore_gene_disease_pathways(
        gene_symbol="TP53",
        disease_name="colorectal cancer",
        max_hops=2,
    )
    assert len(result.nodes) > 0
    assert len(result.edges) > 0
    assert "TP53" in result.summary
