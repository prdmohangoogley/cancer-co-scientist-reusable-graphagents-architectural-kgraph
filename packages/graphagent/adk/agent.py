"""PrimeKG Worker Agent implementation for multi-hop graph reasoning.

Adheres strictly to the worker tier pattern (DOC-03):
- Headless operation without raw HTML/JS rendering.
- Parameterized ISO GQL queries over Cloud Spanner Graph (DOC-09).
- BigQuery omics analytics enrichment.
- Typed Pydantic outputs passed back to the Lead Orchestrator.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .traversal import GraphEdge, GraphNode, SubgraphResult, TraversalConfig

try:
    from tools.algorithms import AlgorithmResult, GraphAlgorithmEngine
    from tools.gql_tools import SpannerGraphTool
    from tools.sql_tools import BigQueryAnalyticsTool
except ImportError:
    from ..tools.algorithms import AlgorithmResult, GraphAlgorithmEngine
    from ..tools.gql_tools import SpannerGraphTool
    from ..tools.sql_tools import BigQueryAnalyticsTool

try:
    from observability.telemetry import trace_span
except ImportError:
    try:
        from packages.graphagent.observability.telemetry import trace_span
    except ImportError:
        from contextlib import contextmanager
        @contextmanager
        def trace_span(name: str, **kwargs):
            yield None

logger = logging.getLogger("primekg_worker_agent")


class PrimeKGWorkerAgent:
    """Specialized Worker Agent for precision oncology knowledge graph traversals."""

    def __init__(
        self,
        project_id: str = "fivedaysai-prd-sandbox-317383",
        instance_id: str = "primekg-instance-dev",
        database_id: str = "primekg-database",
        bq_dataset_id: str = "primekg_analytics_dev",
        use_mock: bool = False,
    ) -> None:
        self.project_id = project_id
        self.instance_id = instance_id
        self.database_id = database_id
        self.bq_dataset_id = bq_dataset_id
        self.use_mock = use_mock

        self.gql_tool = SpannerGraphTool(
            project_id=project_id,
            instance_id=instance_id,
            database_id=database_id,
            use_mock=use_mock,
        )
        self.sql_tool = BigQueryAnalyticsTool(
            project_id=project_id,
            dataset_id=bq_dataset_id,
            use_mock=use_mock,
        )
        self.algo_engine = GraphAlgorithmEngine(
            gql_tool=self.gql_tool,
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
        gene_symbol: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Identify candidate therapeutics targeting pathways dysregulated in the specified disease."""
        return await self.gql_tool.query_repurposing_candidates(
            disease_name=disease_name,
            gene_symbol=gene_symbol,
            limit=limit,
        )

    async def query_target_validation(
        self,
        gene_symbol: str,
        limit: int = 15,
    ) -> SubgraphResult:
        """Validate an oncological target by extracting its interactome and targeting drugs."""
        logger.info(f"Worker validating target {gene_symbol}")
        neighborhood = await self.gql_tool.query_gene_neighborhood(gene_symbol=gene_symbol, limit=limit)
        enriched_nodes = await self.sql_tool.enrich_node_metrics(neighborhood.nodes)

        return SubgraphResult(
            nodes=enriched_nodes,
            edges=neighborhood.edges,
            query_target=gene_symbol,
            hops_traversed=1,
            summary=f"Target validation for {gene_symbol}: {len(enriched_nodes)} connected entities and {len(neighborhood.edges)} interactions discovered.",
        )

    async def run_discrete_algorithm(
        self,
        algorithm_name: str,
        source_entity: str,
        target_entity: Optional[str] = None,
        **kwargs: Any,
    ) -> AlgorithmResult:
        """Execute a discrete graph algorithm from the 15-algorithm matrix.

        Supported algorithms:
        - DFS/BFS ('dfs', 'bfs', 'dfs_bfs_traversal')
        - Dijkstra/A* ('dijkstra', 'astar', 'shortest_path')
        - D* Lite ('d_star_lite', 'dstar', 'replanning')
        - Connected Components ('connected_components', 'wcc', 'scc')
        - Topological Sort ('topological_sort', 'signaling_cascade')
        - Transitive Closure ('transitive_closure', 'reachability')
        - Community Detection ('community_detection', 'label_propagation')
        - Ego Network ('ego_network', 'ego_network_inspection')
        """
        key = algorithm_name.strip().lower().replace("-", "_").replace(" ", "_")

        with trace_span(f"worker_discrete_{key}", workflow_type="Discrete", db_target="SpannerGraph"):
            if key in ("bfs", "dfs", "dfs_bfs", "dfs_bfs_traversal"):
                mode = "DFS" if "dfs" in key and "bfs" not in key else kwargs.pop("mode", "BFS")
                return await self.algo_engine.dfs_bfs_traversal(
                    source_entity=source_entity,
                    mode=mode,
                    **kwargs,
                )
            elif key in ("dijkstra", "astar", "a_star", "shortest_path", "shortest_path_dijkstra_astar"):
                dst = target_entity or kwargs.pop("target_entity", "Neoplasm")
                return await self.algo_engine.shortest_path_dijkstra_astar(
                    source_entity=source_entity,
                    target_entity=dst,
                    **kwargs,
                )
            elif key in ("d_star_lite", "dstar", "d_star", "d_star_lite_replanning", "replanning"):
                dst = target_entity or kwargs.pop("target_entity", "Target")
                initial_path = kwargs.pop("initial_path", [source_entity, dst])
                mutated_edges = kwargs.pop("mutated_edges", {})
                return self.algo_engine.d_star_lite_replanning(
                    source_entity=source_entity,
                    target_entity=dst,
                    initial_path=initial_path,
                    mutated_edges=mutated_edges,
                    **kwargs,
                )
            elif key in ("connected_components", "wcc", "scc", "connectedcomponents_wcc_scc"):
                return await self.algo_engine.connected_components(**kwargs)
            elif key in ("topological_sort", "topological_sort_cascade", "topological", "signaling_cascade"):
                return self.algo_engine.topological_sort_cascade(**kwargs)
            elif key in ("transitive_closure", "transitive_closure_reachability", "reachability"):
                return self.algo_engine.transitive_closure_reachability(
                    source_gene=source_entity,
                    **kwargs,
                )
            elif key in ("community_detection", "community_detection_modules", "label_propagation"):
                return self.algo_engine.community_detection_modules(**kwargs)
            elif key in ("ego_network", "ego_network_inspection", "ego"):
                return await self.algo_engine.ego_network_inspection(
                    focal_node=source_entity,
                    **kwargs,
                )
            else:
                raise ValueError(
                    f"Unknown discrete algorithm: '{algorithm_name}'. "
                    "Supported: dfs_bfs_traversal, shortest_path_dijkstra_astar, d_star_lite_replanning, "
                    "connected_components, topological_sort_cascade, transitive_closure_reachability, "
                    "community_detection_modules, ego_network_inspection."
                )

    async def run_structural_analytics(
        self,
        algorithm_name: str,
        target_entity: str,
        **kwargs: Any,
    ) -> AlgorithmResult:
        """Execute structural or node-level analytics from the 15-algorithm matrix.

        Supported algorithms:
        - Node Centrality / PageRank / Betweenness ('hub_proteins', 'identify_hub_proteins', 'pagerank', 'betweenness')
        - Subgraph Structural Statistics ('subgraph_statistics', 'subgraph_structural_statistics', 'density', 'bridges')
        """
        key = algorithm_name.strip().lower().replace("-", "_").replace(" ", "_")

        with trace_span(f"worker_structural_{key}", workflow_type="Structural", db_target="SpannerGraph"):
            if key in ("identify_hub_proteins", "hub_proteins", "node_centrality", "pagerank", "betweenness"):
                return await self.algo_engine.identify_hub_proteins(
                    gene_symbol=target_entity,
                    **kwargs,
                )
            elif key in ("subgraph_structural_statistics", "subgraph_statistics", "density", "bridges", "cut_vertices"):
                return self.algo_engine.subgraph_structural_statistics(**kwargs)
            else:
                raise ValueError(
                    f"Unknown structural analytics algorithm: '{algorithm_name}'. "
                    "Supported: identify_hub_proteins, subgraph_structural_statistics."
                )

    async def run_continuous_simulation(
        self,
        algorithm_name: str,
        **kwargs: Any,
    ) -> AlgorithmResult:
        """Execute continuous simulation delegation (GKE delegated with heuristic fallback).

        Supported algorithms:
        - AlphaFold RRT* Docking ('alphafold', 'alphafold_docking', 'rrt_star', 'generate_alphafold_docking_job')
        - PhysiCell Swarming ('physicell', 'physicell_swarming', 'boids', 'generate_physicell_swarming_job')
        """
        key = algorithm_name.strip().lower().replace("-", "_").replace(" ", "_")

        with trace_span(f"worker_continuous_{key}", workflow_type="Continuous", db_target="GKE"):
            if key in ("alphafold", "alphafold_docking", "rrt", "rrt_star", "generate_alphafold_docking_job", "ompl"):
                protein_id = kwargs.pop("protein_id", kwargs.pop("target_entity", "P00533"))
                ligand_smiles = kwargs.pop("ligand_smiles", "COCCOC1=C")
                return self.algo_engine.generate_alphafold_docking_job(
                    protein_id=protein_id,
                    ligand_smiles=ligand_smiles,
                    **kwargs,
                )
            elif key in (
                "physicell",
                "physicell_swarming",
                "physicell_boids",
                "generate_physicell_swarming_job",
                "generate_physicell_simulation_job",
                "boids",
                "swarming",
            ):
                tumor_type = kwargs.pop("tumor_type", kwargs.pop("target_entity", "Glioblastoma"))
                return self.algo_engine.generate_physicell_swarming_job(
                    tumor_type=tumor_type,
                    **kwargs,
                )
            else:
                raise ValueError(
                    f"Unknown continuous simulation algorithm: '{algorithm_name}'. "
                    "Supported: generate_alphafold_docking_job, generate_physicell_swarming_job."
                )

    async def run_temporal_tracking(
        self,
        algorithm_name: str,
        **kwargs: Any,
    ) -> AlgorithmResult:
        """Execute temporal tracking, metric profiling, or visualization AST generation.

        Supported algorithms:
        - Temporal Edge Filtering ('temporal_edge_filtering', 'edge_filtering', 'temporal_tracking')
        - Temporal Metric Profiling ('temporal_metric_profiling', 'algebraic_connectivity', 'lambda_2')
        - Visualization AST Generator ('generate_visualization_ast', 'visualization_ast', 'a2ui_ast')
        """
        key = algorithm_name.strip().lower().replace("-", "_").replace(" ", "_")

        with trace_span(f"worker_temporal_{key}", workflow_type="Temporal", db_target="BigQuery"):
            if key in ("temporal_edge_filtering", "edge_filtering", "temporal_tracking", "temporal_edges", "interval_edges"):
                source_entity = kwargs.pop("source_entity", kwargs.pop("target_entity", "EGFR"))
                target_timestamp = kwargs.pop("target_timestamp", "2025-06-01")
                return self.algo_engine.temporal_edge_filtering(
                    source_entity=source_entity,
                    target_timestamp=target_timestamp,
                    **kwargs,
                )
            elif key in ("temporal_metric_profiling", "algebraic_connectivity", "lambda_2", "spectral"):
                return self.algo_engine.temporal_metric_profiling(**kwargs)
            elif key in ("generate_visualization_ast", "visualization_ast", "visualization", "a2ui_ast"):
                nodes = kwargs.pop("nodes", ["EGFR", "KRAS", "BRAF"])
                edges = kwargs.pop("edges", [("EGFR", "KRAS"), ("KRAS", "BRAF")])
                return self.algo_engine.generate_visualization_ast(
                    nodes=nodes,
                    edges=edges,
                    **kwargs,
                )
            else:
                raise ValueError(
                    f"Unknown temporal tracking algorithm: '{algorithm_name}'. "
                    "Supported: temporal_edge_filtering, temporal_metric_profiling, generate_visualization_ast."
                )
