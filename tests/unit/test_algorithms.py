"""Comprehensive unit test suite for all Phase 6.1 Graph Algorithms (Spec 06)."""

from __future__ import annotations

import pytest

from tools.algorithms import GraphAlgorithmEngine


# =============================================================================
# 🟢 1. Discrete Graph Algorithms Tests
# =============================================================================

@pytest.mark.asyncio
async def test_dfs_bfs_traversal():
    """Verify DFS and BFS graph traversals."""
    engine = GraphAlgorithmEngine(use_mock=True)

    bfs_res = await engine.dfs_bfs_traversal("EGFR", mode="BFS", max_depth=2)
    assert bfs_res.workflow_type == "Discrete"
    assert bfs_res.metrics["mode"] == "BFS"
    assert len(bfs_res.visited_entities() if hasattr(bfs_res, "visited_entities") else bfs_res.nodes) >= 2

    dfs_res = await engine.dfs_bfs_traversal("EGFR", mode="DFS", max_depth=2)
    assert dfs_res.metrics["mode"] == "DFS"
    assert len(dfs_res.nodes) >= 2


@pytest.mark.asyncio
async def test_shortest_path_dijkstra_astar():
    """Verify point-to-point shortest path via Dijkstra and A* with vector heuristic."""
    engine = GraphAlgorithmEngine(use_mock=True)

    # Dijkstra
    dijkstra_res = await engine.shortest_path_dijkstra_astar("EGFR", "BRAF")
    assert dijkstra_res.algorithm_name == "Dijkstra"
    assert len(dijkstra_res.paths[0]) >= 2
    assert dijkstra_res.metrics["total_path_weight"] > 0

    # A* with mock vector embeddings
    vectors = {
        "EGFR": [1.0, 0.0, 0.0],
        "GRB2": [0.8, 0.2, 0.0],
        "SOS1": [0.6, 0.4, 0.0],
        "KRAS": [0.4, 0.6, 0.0],
        "BRAF": [0.2, 0.8, 0.0],
    }
    astar_res = await engine.shortest_path_dijkstra_astar("EGFR", "BRAF", heuristic_vectors=vectors)
    assert astar_res.algorithm_name == "A*_VectorHeuristic"
    assert len(astar_res.paths[0]) >= 2


def test_d_star_lite_replanning():
    """Verify incremental replanning when edge interaction weights mutate."""
    engine = GraphAlgorithmEngine(use_mock=True)
    initial_path = ["EGFR", "GRB2", "SOS1", "KRAS"]

    # Drug resistance mutation makes GRB2 -> SOS1 impassable
    mutations = {("GRB2", "SOS1"): 999.0}
    replanned = engine.d_star_lite_replanning("EGFR", "KRAS", initial_path, mutations)
    assert replanned.algorithm_name == "D*_Lite_Incremental"
    assert replanned.metrics["original_path_invalidated"] is True
    # Verify rerouted path does not use the mutated edge
    repaired_path = replanned.paths[0]
    assert ("GRB2", "SOS1") not in zip(repaired_path[:-1], repaired_path[1:])


@pytest.mark.asyncio
async def test_connected_components():
    """Verify Weakly (WCC) and Strongly (SCC) Connected Component detection."""
    engine = GraphAlgorithmEngine(use_mock=True)
    res = await engine.connected_components()
    assert res.algorithm_name == "ConnectedComponents_WCC_SCC"
    assert res.metrics["wcc_count"] >= 2
    assert res.metrics["scc_count"] >= 2


def test_topological_sort_cascade():
    """Verify topological linearization of directed biochemical cascades."""
    engine = GraphAlgorithmEngine(use_mock=True)
    res = engine.topological_sort_cascade()
    assert res.algorithm_name == "TopologicalSort"
    assert res.metrics["is_dag"] is True
    assert res.nodes[0] == "Receptor_EGFR"
    assert res.nodes[-1] == "TranscriptionFactor_MYC"


def test_transitive_closure_reachability():
    """Verify transitive closure reachability to downstream phenotype targets."""
    engine = GraphAlgorithmEngine(use_mock=True)
    res = engine.transitive_closure_reachability(source_gene="EGFR")
    assert res.algorithm_name == "TransitiveClosureReachability"
    assert res.metrics["reachable_count"] >= 4
    assert "Tumor_Progression" in res.nodes


def test_community_detection_modules():
    """Verify Label Propagation community detection discovers functional modules."""
    engine = GraphAlgorithmEngine(use_mock=True)
    res = engine.community_detection_modules()
    assert res.algorithm_name == "CommunityDetection_LabelPropagation"
    assert res.metrics["community_count"] >= 2


@pytest.mark.asyncio
async def test_ego_network_inspection():
    """Verify ego-network extraction around a focal gene node."""
    engine = GraphAlgorithmEngine(use_mock=True)
    result = await engine.ego_network_inspection(focal_node="EGFR", k_hops=1, limit=10)
    assert result.algorithm_name == "EgoNetworkInspection"
    assert result.workflow_type == "Discrete"
    assert result.target_entity == "EGFR"
    assert len(result.paths) > 0
    assert result.metrics["node_count"] > 1


# =============================================================================
# 🟡 2. Structural & Node-Level Analytics Tests
# =============================================================================

@pytest.mark.asyncio
async def test_compute_node_centrality():
    """Verify PageRank and Betweenness centrality identify Hubs and Gatekeepers."""
    engine = GraphAlgorithmEngine(use_mock=True)
    res_tp53 = await engine.identify_hub_proteins(gene_symbol="TP53")
    assert res_tp53.algorithm_name == "NodeCentrality_PageRank_Betweenness"
    assert res_tp53.metrics["is_hub"] is True
    assert res_tp53.metrics["degree_centrality"] > 50
    assert res_tp53.metrics["bottleneck_gatekeeper"] is True
    assert res_tp53.metrics["pagerank_score"] > 0


def test_subgraph_structural_statistics():
    """Verify density computation and bridge/cut-vertex identification."""
    engine = GraphAlgorithmEngine(use_mock=True)
    res = engine.subgraph_structural_statistics()
    assert res.algorithm_name == "SubgraphStructuralStatistics"
    assert res.metrics["density"] > 0
    assert res.metrics["bridge_count"] >= 1
    assert res.metrics["cut_vertex_count"] >= 1
    assert "SOS1<->KRAS" in res.metrics["bridges"]


# =============================================================================
# 🔵 3. Continuous Geometry & Simulation Delegation Tests
# =============================================================================

def test_continuous_alphafold_docking_dispatch():
    """Verify continuous motion planning parameter generator for AlphaFold."""
    engine = GraphAlgorithmEngine(use_mock=True)
    result = engine.generate_alphafold_docking_job(
        protein_id="P00533",
        ligand_smiles="COCCOC1=C",
        num_samples=500,
    )
    assert result.workflow_type == "Continuous"
    assert result.simulation_payload is not None
    assert result.simulation_payload["engine"] == "OMPL-RRT*"
    assert result.simulation_payload["sampling_budget"] == 500


def test_physicell_swarming_simulation():
    """Verify PhysiCell agent-based microenvironment simulation parameter generation."""
    engine = GraphAlgorithmEngine(use_mock=True)
    result = engine.generate_physicell_simulation_job(
        tumor_type="Glioblastoma",
        num_cells=10000,
    )
    assert result.workflow_type == "Continuous"
    assert result.simulation_payload["engine"] == "PhysiCell-AgentBased"
    assert result.simulation_payload["initial_cell_count"] == 10000


# =============================================================================
# 🟣 4. Temporal & Spatiotemporal Tracking Tests
# =============================================================================

def test_temporal_edge_filtering():
    """Verify interval-timestamped edge filtering over clinical time windows."""
    engine = GraphAlgorithmEngine(use_mock=True)
    res = engine.temporal_edge_filtering(source_entity="EGFR", target_timestamp="2025-08-15")
    assert res.algorithm_name == "TemporalEdgeFiltering"
    assert res.metrics["active_edge_count"] == 1
    assert "Osimertinib_Response" in res.nodes


def test_temporal_metric_profiling():
    """Verify rolling algebraic connectivity (λ2) Laplacian spectrum profiling."""
    engine = GraphAlgorithmEngine(use_mock=True)
    res = engine.temporal_metric_profiling(slice_densities=[0.5, 0.45, 0.35, 0.20, 0.15])
    assert res.algorithm_name == "TemporalMetricProfiling_AlgebraicConnectivity"
    assert res.metrics["algebraic_connectivity_lambda_2"] > 0
    assert res.metrics["network_fragmenting"] is True
    assert res.metrics["warning_level"] == "CRITICAL_COLLAPSE"


def test_generate_visualization_ast():
    """Verify A2UI / JSON AST graph visualization generation."""
    engine = GraphAlgorithmEngine(use_mock=True)
    nodes = ["EGFR", "KRAS", "BRAF", "Lung_Cancer"]
    edges = [("EGFR", "KRAS"), ("KRAS", "BRAF"), ("BRAF", "Lung_Cancer")]
    res = engine.generate_visualization_ast(nodes, edges, layout="hierarchical_dag")
    assert res.algorithm_name == "VisualizationDataGenerator"
    assert res.visualization_ast is not None
    assert res.visualization_ast["type"] == "A2UI_GRAPH_AST"
    assert len(res.visualization_ast["nodes"]) == 4
    assert len(res.visualization_ast["links"]) == 3
