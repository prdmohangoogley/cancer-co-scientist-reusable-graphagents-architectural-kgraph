"""PrimeKG Worker Agent implementation for multi-hop graph reasoning."""

from __future__ import annotations

import logging
from typing import Any, Optional
from pydantic import BaseModel

from .traversal import GraphEdge, GraphNode, SubgraphResult, TraversalConfig

try:
    from tools.gql_tools import SpannerGraphTool
    from tools.sql_tools import BigQueryAnalyticsTool
except ImportError:
    from ..tools.gql_tools import SpannerGraphTool
    from ..tools.sql_tools import BigQueryAnalyticsTool

logger = logging.getLogger("primekg_worker_agent")


class PrimeKGWorkerAgent:
    """Specialized Worker Agent for precision oncology knowledge graph traversals.

    Adheres strictly to the worker tier pattern (DOC-03):
    - Headless operation without raw HTML/JS rendering.
    - Parameterized ISO GQL queries over Cloud Spanner Graph.
    - Typed Pydantic outputs passed back to the Lead Orchestrator.
    """

    def __init__(
        self,
        project_id: str = "mock-project",
        instance_id: str = "primekg-instance",
        database_id: str = "primekg-db",
        use_mock: bool = True,
    ) -> None:
        self.project_id = project_id
        self.use_mock = use_mock
        self.gql_tool = SpannerGraphTool(
            project_id=project_id,
            instance_id=instance_id,
            database_id=database_id,
            use_mock=use_mock,
        )
        self.sql_tool = BigQueryAnalyticsTool(
            project_id=project_id,
            use_mock=use_mock,
        )

    async def explore_gene_disease_pathways(
        self,
        gene_symbol: str,
        disease_name: str,
        max_hops: int = 2,
    ) -> SubgraphResult:
        """Discover pathways, drug targets, and interactions connecting a gene to a cancer phenotype."""
        config = TraversalConfig(max_hops=max_hops)
        logger.info(f"Worker exploring pathways for {gene_symbol} -> {disease_name} (hops={max_hops})")

        # 1. Query ISO GQL via Spanner Graph
        graph_data = await self.gql_tool.find_paths_between(
            source_entity=gene_symbol,
            target_entity=disease_name,
            config=config,
        )

        # 2. Enrich with druggability and evidence metrics from BigQuery
        enriched_nodes = await self.sql_tool.enrich_node_metrics(graph_data.nodes)

        return SubgraphResult(
            nodes=enriched_nodes,
            edges=graph_data.edges,
            query_target=f"{gene_symbol} -> {disease_name}",
            hops_traversed=max_hops,
            summary=f"Extracted {len(enriched_nodes)} entities and {len(graph_data.edges)} interactions linking {gene_symbol} to {disease_name}.",
        )

    async def find_drug_repurposing_candidates(
        self,
        disease_name: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Identify candidate therapeutics targeting pathways dysregulated in the specified disease."""
        return await self.gql_tool.query_repurposing_candidates(disease_name=disease_name, limit=limit)
