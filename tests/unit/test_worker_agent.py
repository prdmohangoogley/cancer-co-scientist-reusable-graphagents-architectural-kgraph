"""Unit tests for PrimeKGWorkerAgent (DOC-01, DOC-03)."""

from __future__ import annotations

import pytest

from adk.agent import PrimeKGWorkerAgent


@pytest.mark.asyncio
async def test_primekg_worker_agent_pathways():
    """Verify worker agent coordinates GQL and SQL tools for pathway exploration."""
    agent = PrimeKGWorkerAgent(use_mock=True)
    result = await agent.explore_gene_disease_pathways(
        gene_symbol="EGFR",
        disease_name="Non-small cell lung carcinoma",
        max_hops=2,
    )
    assert len(result.nodes) > 0
    assert len(result.edges) > 0
    assert "EGFR" in result.summary
    assert result.hops_traversed == 2


@pytest.mark.asyncio
async def test_primekg_worker_agent_repurposing():
    """Verify worker agent identifies drug repurposing candidates."""
    agent = PrimeKGWorkerAgent(use_mock=True)
    candidates = await agent.find_drug_repurposing_candidates(
        disease_name="Non-small cell lung carcinoma",
        limit=5,
    )
    assert len(candidates) >= 1
    assert candidates[0]["target_gene"] == "EGFR"


@pytest.mark.asyncio
async def test_primekg_worker_agent_target_validation():
    """Verify worker agent performs oncological target validation."""
    agent = PrimeKGWorkerAgent(use_mock=True)
    result = await agent.query_target_validation(gene_symbol="TP53", limit=10)
    assert len(result.nodes) > 0
    assert result.query_target == "TP53"
    assert "TP53" in result.summary


# =============================================================================
# Worker Tier 15-Algorithm Matrix Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_worker_run_discrete_algorithms():
    """Verify worker executes all discrete graph algorithms from the 15-algorithm matrix."""
    agent = PrimeKGWorkerAgent(use_mock=True)

    # 1. BFS / DFS
    bfs_res = await agent.run_discrete_algorithm("bfs", source_entity="EGFR", max_depth=2)
    assert bfs_res.workflow_type == "Discrete"
    assert bfs_res.metrics["mode"] == "BFS"
    assert len(bfs_res.nodes) >= 2
    assert "latency_ms" in bfs_res.metrics

    dfs_res = await agent.run_discrete_algorithm("dfs", source_entity="EGFR", max_depth=2)
    assert dfs_res.metrics["mode"] == "DFS"

    # 2. Dijkstra / Shortest Path
    dijkstra_res = await agent.run_discrete_algorithm("dijkstra", source_entity="EGFR", target_entity="BRAF")
    assert dijkstra_res.workflow_type == "Discrete"
    assert dijkstra_res.algorithm_name == "Dijkstra"
    assert len(dijkstra_res.paths[0]) >= 2

    # 3. D* Lite Incremental Replanning
    dstar_res = await agent.run_discrete_algorithm(
        "d_star_lite",
        source_entity="EGFR",
        target_entity="KRAS",
        initial_path=["EGFR", "GRB2", "SOS1", "KRAS"],
        mutated_edges={("GRB2", "SOS1"): 999.0},
    )
    assert dstar_res.algorithm_name == "D*_Lite_Incremental"
    assert dstar_res.metrics["original_path_invalidated"] is True

    # 4. Connected Components
    cc_res = await agent.run_discrete_algorithm("connected_components", source_entity="EGFR")
    assert cc_res.algorithm_name == "ConnectedComponents_WCC_SCC"
    assert cc_res.metrics["wcc_count"] >= 1

    # 5. Topological Sort
    topo_res = await agent.run_discrete_algorithm("topological_sort", source_entity="EGFR")
    assert topo_res.algorithm_name == "TopologicalSort"
    assert topo_res.metrics["is_dag"] is True

    # 6. Transitive Closure Reachability
    reach_res = await agent.run_discrete_algorithm("transitive_closure", source_entity="EGFR")
    assert reach_res.algorithm_name == "TransitiveClosureReachability"
    assert reach_res.metrics["reachable_count"] >= 1

    # 7. Community Detection (Label Propagation)
    comm_res = await agent.run_discrete_algorithm("community_detection", source_entity="EGFR")
    assert comm_res.algorithm_name == "CommunityDetection_LabelPropagation"
    assert comm_res.metrics["community_count"] >= 1

    # 8. Ego-Network Inspection
    ego_res = await agent.run_discrete_algorithm("ego_network", source_entity="EGFR", k_hops=1)
    assert ego_res.algorithm_name == "EgoNetworkInspection"
    assert len(ego_res.nodes) >= 2

    # Invalid algorithm name handling
    with pytest.raises(ValueError, match="Unknown discrete algorithm"):
        await agent.run_discrete_algorithm("invalid_algo", source_entity="EGFR")


@pytest.mark.asyncio
async def test_worker_run_structural_analytics():
    """Verify worker executes structural and node-level analytics."""
    agent = PrimeKGWorkerAgent(use_mock=True)

    # 9. Hub Proteins Centrality & PageRank
    hub_res = await agent.run_structural_analytics("hub_proteins", target_entity="TP53")
    assert hub_res.workflow_type == "Structural"
    assert hub_res.metrics["is_hub"] is True
    assert hub_res.metrics["degree_centrality"] > 50
    assert "latency_ms" in hub_res.metrics

    # 10. Subgraph Statistics (Density & Bridges)
    stats_res = await agent.run_structural_analytics("subgraph_statistics", target_entity="EGFR")
    assert stats_res.workflow_type == "Structural"
    assert stats_res.algorithm_name == "SubgraphStructuralStatistics"
    assert stats_res.metrics["density"] > 0
    assert stats_res.metrics["bridge_count"] >= 1

    # Invalid algorithm name handling
    with pytest.raises(ValueError, match="Unknown structural analytics algorithm"):
        await agent.run_structural_analytics("invalid_structural", target_entity="EGFR")


@pytest.mark.asyncio
async def test_worker_run_continuous_simulation():
    """Verify worker executes continuous simulation with graceful resilient fallback."""
    agent = PrimeKGWorkerAgent(use_mock=True)

    # 11. AlphaFold RRT* Docking
    af_res = await agent.run_continuous_simulation(
        "alphafold",
        protein_id="P00533",
        ligand_smiles="COCCOC1=C",
        num_samples=250,
    )
    assert af_res.workflow_type == "Continuous"
    assert af_res.simulation_payload is not None
    assert af_res.simulation_payload["engine"] == "OMPL-RRT*"
    assert af_res.simulation_payload["sampling_budget"] == 250
    assert af_res.metrics["fallback_applied"] is True
    assert "heuristic_binding_affinity_kcal_mol" in af_res.metrics
    assert "latency_ms" in af_res.metrics

    # 12. PhysiCell Swarming Simulation
    pc_res = await agent.run_continuous_simulation(
        "physicell",
        tumor_type="Glioblastoma",
        num_cells=5000,
    )
    assert pc_res.workflow_type == "Continuous"
    assert pc_res.simulation_payload is not None
    assert pc_res.simulation_payload["engine"] == "PhysiCell-AgentBased"
    assert pc_res.metrics["fallback_applied"] is True
    assert "heuristic_tumor_density" in pc_res.metrics
    assert "latency_ms" in pc_res.metrics

    # Invalid algorithm name handling
    with pytest.raises(ValueError, match="Unknown continuous simulation algorithm"):
        await agent.run_continuous_simulation("invalid_sim")


@pytest.mark.asyncio
async def test_worker_run_temporal_tracking():
    """Verify worker executes temporal tracking and AST visualization generator."""
    agent = PrimeKGWorkerAgent(use_mock=True)

    # 13. Temporal Edge Filtering
    filter_res = await agent.run_temporal_tracking(
        "temporal_edge_filtering",
        source_entity="EGFR",
        target_timestamp="2025-08-15",
    )
    assert filter_res.workflow_type == "Temporal"
    assert filter_res.algorithm_name == "TemporalEdgeFiltering"
    assert filter_res.metrics["active_edge_count"] >= 1
    assert "latency_ms" in filter_res.metrics

    # 14. Temporal Metric Profiling (Algebraic Connectivity)
    prof_res = await agent.run_temporal_tracking("temporal_metric_profiling")
    assert prof_res.workflow_type == "Temporal"
    assert prof_res.algorithm_name == "TemporalMetricProfiling_AlgebraicConnectivity"
    assert prof_res.metrics["algebraic_connectivity_lambda_2"] > 0

    # 15. Visualization AST Generator
    vis_res = await agent.run_temporal_tracking(
        "visualization_ast",
        nodes=["EGFR", "KRAS", "BRAF"],
        edges=[("EGFR", "KRAS"), ("KRAS", "BRAF")],
    )
    assert vis_res.workflow_type == "Temporal"
    assert vis_res.algorithm_name == "VisualizationDataGenerator"
    assert vis_res.visualization_ast is not None
    assert vis_res.visualization_ast["type"] == "A2UI_GRAPH_AST"
    assert len(vis_res.visualization_ast["nodes"]) == 3

    # Invalid algorithm name handling
    with pytest.raises(ValueError, match="Unknown temporal tracking algorithm"):
        await agent.run_temporal_tracking("invalid_temporal")
