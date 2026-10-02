"""Unit tests for Lead Orchestrator IntentRouter and 15-Algorithm Matrix (DOC-03, Spec 06, Spec 07)."""

from __future__ import annotations

import sys
from pathlib import Path

# Add apps/co-scientist to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "co-scientist"))

from agent.router import IntentRouter, IntentType


def test_intent_router_drug_repurposing():
    """Verify router classifies therapeutic and repurposing queries."""
    router = IntentRouter()
    decision = router.route_query("What drugs or inhibitors can target EGFR in lung cancer?")
    assert decision.intent == IntentType.DRUG_REPURPOSING
    assert "EGFR" in decision.extracted_genes
    assert "Non-small cell lung carcinoma" in decision.extracted_diseases
    assert decision.recommended_algorithm == "Dijkstra"
    assert decision.algorithm_choice_confidence >= 0.90


def test_intent_router_pathway_analysis():
    """Verify router classifies biochemical cascade queries."""
    router = IntentRouter()
    decision = router.route_query("What signaling pathways and interactions connect TP53 and ovarian cancer?")
    assert decision.intent == IntentType.PATHWAY_ANALYSIS
    assert "TP53" in decision.extracted_genes
    assert "Ovarian Carcinoma" in decision.extracted_diseases
    assert decision.recommended_algorithm in ("TopologicalSort", "BFS_DFS", "Dijkstra")
    assert decision.algorithm_choice_confidence >= 0.90


def test_intent_router_target_validation():
    """Verify router classifies oncogene target vulnerability queries."""
    router = IntentRouter()
    decision = router.route_query("Validate KRAS as an oncogene target in pancreatic cancer")
    assert decision.intent == IntentType.TARGET_VALIDATION
    assert "KRAS" in decision.extracted_genes
    assert "Pancreatic Ductal Adenocarcinoma" in decision.extracted_diseases
    assert decision.recommended_algorithm in ("NodeCentrality_PageRank", "Dijkstra", "TransitiveClosureReachability")
    assert decision.algorithm_choice_confidence >= 0.90


# =============================================================================
# 🟢 1. Discrete Graph Algorithms Matrix Tests
# =============================================================================

def test_router_discrete_astar_vector_heuristic():
    """Verify routing to A* shortest path with vector heuristics."""
    router = IntentRouter()
    decision = router.route_query("Compute A* shortest path using vector heuristic embeddings between EGFR and BRAF")
    assert decision.recommended_algorithm == "A*_VectorHeuristic"
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_discrete_d_star_lite_replanning():
    """Verify routing to D* Lite incremental replanning for resistance mutations."""
    router = IntentRouter()
    decision = router.route_query("Perform dynamic replanning with D* Lite for resistance mutation edge invalidated path")
    assert decision.recommended_algorithm == "D*_Lite_Incremental"
    assert decision.intent == IntentType.TARGET_VALIDATION
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_discrete_bfs_dfs_traversal():
    """Verify routing to BFS/DFS systematic pathway traversal."""
    router = IntentRouter()
    decision = router.route_query("Run breadth first BFS traversal across the EGFR signaling cascade")
    assert decision.recommended_algorithm == "BFS_DFS"
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_discrete_connected_components():
    """Verify routing to WCC / SCC connected component detection."""
    router = IntentRouter()
    decision = router.route_query("Identify isolated component subgraphs and weakly connected components WCC")
    assert decision.recommended_algorithm == "ConnectedComponents_WCC_SCC"
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_discrete_topological_sort():
    """Verify routing to topological sort cascade ordering."""
    router = IntentRouter()
    decision = router.route_query("Determine upstream downstream order in kinase cascade via topological sort")
    assert decision.recommended_algorithm == "TopologicalSort"
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_discrete_transitive_closure():
    """Verify routing to transitive closure phenotype reachability."""
    router = IntentRouter()
    decision = router.route_query("Calculate transitive closure reachability to all downstream phenotype targets")
    assert decision.recommended_algorithm == "TransitiveClosureReachability"
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_discrete_community_detection():
    """Verify routing to label propagation community detection."""
    router = IntentRouter()
    decision = router.route_query("Discover functional module clusters using label propagation community detection")
    assert decision.recommended_algorithm == "CommunityDetection_LabelPropagation"
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_discrete_ego_network():
    """Verify routing to ego network neighborhood scan."""
    router = IntentRouter()
    decision = router.route_query("Perform an ego network neighborhood scan around focal node EGFR")
    assert decision.recommended_algorithm == "EgoNetworkInspection"
    assert decision.algorithm_choice_confidence >= 0.95


# =============================================================================
# 🟡 2. Structural & Node-Level Analytics Tests
# =============================================================================

def test_router_structural_pagerank_hubs():
    """Verify routing to PageRank hub protein identification."""
    router = IntentRouter()
    decision = router.route_query("Find master regulator hub proteins using PageRank and degree centrality")
    assert decision.recommended_algorithm == "NodeCentrality_PageRank"
    assert decision.intent == IntentType.STRUCTURAL_ANALYSIS
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_structural_betweenness_gatekeepers():
    """Verify routing to betweenness gatekeeper bottleneck identification."""
    router = IntentRouter()
    decision = router.route_query("Identify critical signaling chokepoint bottleneck and gatekeeper proteins using betweenness")
    assert decision.recommended_algorithm == "NodeCentrality_Betweenness"
    assert decision.intent == IntentType.STRUCTURAL_ANALYSIS
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_structural_subgraph_statistics():
    """Verify routing to subgraph density and bridge detection."""
    router = IntentRouter()
    decision = router.route_query("Evaluate network density cut vertex and bridges for structural fragility")
    assert decision.recommended_algorithm == "SubgraphStructuralStatistics"
    assert decision.intent == IntentType.STRUCTURAL_ANALYSIS
    assert decision.algorithm_choice_confidence >= 0.95


# =============================================================================
# 🔵 3. Continuous Geometry & Simulation Tests
# =============================================================================

def test_router_continuous_alphafold_docking():
    """Verify routing to AlphaFold OMPL RRT* continuous docking simulation."""
    router = IntentRouter()
    decision = router.route_query("Generate AlphaFold ligand binding conformation docking trajectory with OMPL RRT*")
    assert decision.recommended_algorithm == "Continuous_AlphaFold_OMPL_RRT"
    assert decision.intent == IntentType.CONTINUOUS_SIMULATION
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_continuous_physicell_swarming():
    """Verify routing to PhysiCell Boids agent-based swarming simulation."""
    router = IntentRouter()
    decision = router.route_query("Simulate tumor microenvironment cell swarming dynamics using PhysiCell Boids")
    assert decision.recommended_algorithm == "Continuous_PhysiCell_Boids"
    assert decision.intent == IntentType.CONTINUOUS_SIMULATION
    assert decision.algorithm_choice_confidence >= 0.95


# =============================================================================
# 🟣 4. Temporal & Spatiotemporal Tracking Tests
# =============================================================================

def test_router_temporal_algebraic_connectivity():
    """Verify routing to rolling Laplacian λ2 algebraic connectivity profiling."""
    router = IntentRouter()
    decision = router.route_query("Analyze algebraic connectivity lambda 2 spectrum for network fragmentation and collapse")
    assert decision.recommended_algorithm == "Temporal_AlgebraicConnectivity_Lambda2"
    assert decision.intent == IntentType.TEMPORAL_TRACKING
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_temporal_interval_edges():
    """Verify routing to interval-timestamped edge filtering over clinical time."""
    router = IntentRouter()
    decision = router.route_query("Filter longitudinal temporal edge changes across patient time window progression")
    assert decision.recommended_algorithm == "Temporal_IntervalEdges"
    assert decision.intent == IntentType.TEMPORAL_TRACKING
    assert decision.algorithm_choice_confidence >= 0.95


def test_router_temporal_visualization_ast():
    """Verify routing to A2UI hierarchical visualization AST generator."""
    router = IntentRouter()
    decision = router.route_query("Generate A2UI graph visualization AST with hierarchical DAG layout")
    assert decision.recommended_algorithm == "Temporal_Visualization_AST"
    assert decision.intent == IntentType.VISUALIZATION_AST
    assert decision.algorithm_choice_confidence >= 0.95
