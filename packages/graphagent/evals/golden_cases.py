"""Golden Clinical Inquiries and Retrieval Ground Truth for Graph Algorithm Evaluation (Spec 06, Spec 07).

Defines canonical clinical inquiries mapping to the 15-algorithm matrix across 4 categories:
1. Discrete Graph Algorithms
2. Structural & Node-Level Analytics
3. Continuous Geometry & Multi-Agent Simulation
4. Temporal & Spatiotemporal Tracking
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class GoldenTestCase:
    case_id: str
    inquiry: str
    expected_algorithm: str
    category: str
    ground_truth_ids: List[str] = field(default_factory=list)
    retrieved_ids: List[str] = field(default_factory=list)


GOLDEN_ALGORITHM_CASES: List[GoldenTestCase] = [
    # 🟢 1. Discrete Graph Algorithms (8 algorithms)
    GoldenTestCase(
        case_id="GOLDEN_01_DFS_BFS",
        inquiry="Explore the multi-hop interaction neighborhood of EGFR out to 2 hops using breadth-first search.",
        expected_algorithm="dfs_bfs_traversal",
        category="Discrete",
        ground_truth_ids=["EGFR", "GRB2", "SOS1", "KRAS", "BRAF", "MAP2K1", "MAPK1", "PIK3CA", "AKT1", "MTOR"],
        retrieved_ids=["EGFR", "GRB2", "SOS1", "KRAS", "BRAF", "MAP2K1", "MAPK1", "PIK3CA", "AKT1", "STAT3"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_02_SHORTEST_PATH",
        inquiry="Find the shortest biochemical pathway and point-to-point signaling route connecting EGFR to BRAF via A* vector heuristic.",
        expected_algorithm="shortest_path_dijkstra_astar",
        category="Discrete",
        ground_truth_ids=["EGFR", "GRB2", "SOS1", "KRAS", "BRAF", "MAP2K1", "RAF1", "SHC1", "PTPN11", "GAB1"],
        retrieved_ids=["EGFR", "GRB2", "SOS1", "KRAS", "BRAF", "MAP2K1", "RAF1", "SHC1", "PTPN11", "SPRY2"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_03_D_STAR_LITE",
        inquiry="Replan the signaling pathway from EGFR to KRAS dynamically using D* Lite after a drug resistance mutation invalidates the GRB2-SOS1 interaction edge.",
        expected_algorithm="d_star_lite_replanning",
        category="Discrete",
        ground_truth_ids=["EGFR", "Bypass_Node_1", "Bypass_Node_2", "KRAS", "SHC1", "GAB1", "PIK3CA", "AKT1", "SRC", "MET"],
        retrieved_ids=["EGFR", "Bypass_Node_1", "Bypass_Node_2", "KRAS", "SHC1", "GAB1", "PIK3CA", "AKT1", "SRC", "JAK2"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_04_CONNECTED_COMPONENTS",
        inquiry="Identify strongly and weakly connected biological modules and isolated subnetworks across the lung cancer interactome.",
        expected_algorithm="connected_components",
        category="Discrete",
        ground_truth_ids=["EGFR", "GRB2", "SOS1", "TP53", "MDM2", "ATM", "CHEK2", "CDKN1A", "RB1", "E2F1"],
        retrieved_ids=["EGFR", "GRB2", "SOS1", "TP53", "MDM2", "ATM", "CHEK2", "CDKN1A", "RB1", "CCND1"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_05_TOPOLOGICAL_SORT",
        inquiry="Linearize the directed signaling cascade from EGFR through SOS1 to downstream MYC transcription to trace execution order.",
        expected_algorithm="topological_sort_cascade",
        category="Discrete",
        ground_truth_ids=["Receptor_EGFR", "Adapter_GRB2", "GEF_SOS1", "GTPase_KRAS", "Kinase_BRAF", "Kinase_MEK", "Kinase_ERK", "TranscriptionFactor_MYC", "ELK1", "FOS"],
        retrieved_ids=["Receptor_EGFR", "Adapter_GRB2", "GEF_SOS1", "GTPase_KRAS", "Kinase_BRAF", "Kinase_MEK", "Kinase_ERK", "TranscriptionFactor_MYC", "ELK1", "JUN"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_06_TRANSITIVE_CLOSURE",
        inquiry="Determine all reachable downstream phenotypic cascades and oncogenic end-states starting from upstream EGFR activation via transitive closure.",
        expected_algorithm="transitive_closure_reachability",
        category="Discrete",
        ground_truth_ids=["EGFR", "Pathway_MAPK", "Cell_Proliferation", "Anti_Apoptosis", "Pathway_PI3K", "Cell_Survival", "Tumor_Progression", "Angiogenesis", "Metastasis", "Drug_Resistance"],
        retrieved_ids=["EGFR", "Pathway_MAPK", "Cell_Proliferation", "Anti_Apoptosis", "Pathway_PI3K", "Cell_Survival", "Tumor_Progression", "Angiogenesis", "Metastasis", "Invasion"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_07_COMMUNITY_DETECTION",
        inquiry="Detect densely interconnected co-functional disease modules and functional gene clusters within the interactome using label propagation.",
        expected_algorithm="community_detection_modules",
        category="Discrete",
        ground_truth_ids=["EGFR", "ERBB2", "ERBB3", "TP53", "ATM", "CHEK2", "KRAS", "BRAF", "MAP2K1", "PTEN"],
        retrieved_ids=["EGFR", "ERBB2", "ERBB3", "TP53", "ATM", "CHEK2", "KRAS", "BRAF", "MAP2K1", "PIK3CA"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_08_EGO_NETWORK",
        inquiry="Extract the 1-hop ego-network centered exclusively around focal oncoprotein EGFR and its immediate interactors.",
        expected_algorithm="ego_network_inspection",
        category="Discrete",
        ground_truth_ids=["EGFR", "EGFR_interactor_1", "EGFR_interactor_2", "AssociatedPathway", "GRB2", "PIK3CA", "ERBB2", "CBL", "STAT3", "PLCG1"],
        retrieved_ids=["EGFR", "EGFR_interactor_1", "EGFR_interactor_2", "AssociatedPathway", "GRB2", "PIK3CA", "ERBB2", "CBL", "STAT3", "SRC"],
    ),

    # 🟡 2. Structural & Node-Level Analytics (2 algorithms)
    GoldenTestCase(
        case_id="GOLDEN_09_NODE_CENTRALITY",
        inquiry="Compute degree centrality, PageRank, and betweenness scores to identify master regulator hub proteins and gatekeeper bottlenecks for TP53.",
        expected_algorithm="compute_node_centrality",
        category="Structural",
        ground_truth_ids=["TP53", "MDM2", "CDKN1A", "BAX", "PUMA", "NOXA", "ATM", "CHEK2", "CASP3", "CASP9"],
        retrieved_ids=["TP53", "MDM2", "CDKN1A", "BAX", "PUMA", "NOXA", "ATM", "CHEK2", "CASP3", "APAF1"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_10_SUBGRAPH_STATISTICS",
        inquiry="Analyze subgraph density and identify critical articulation points, cut-vertices, and single-point-of-failure bridges connecting pathway modules.",
        expected_algorithm="subgraph_structural_statistics",
        category="Structural",
        ground_truth_ids=["EGFR", "GRB2", "SOS1", "KRAS", "BRAF", "MAP2K1", "Bridge_SOS1_KRAS", "CutVertex_SOS1", "CutVertex_KRAS", "Density_Metric"],
        retrieved_ids=["EGFR", "GRB2", "SOS1", "KRAS", "BRAF", "MAP2K1", "Bridge_SOS1_KRAS", "CutVertex_SOS1", "CutVertex_KRAS", "Module_MAPK"],
    ),

    # 🔵 3. Continuous Geometry & Simulation (2 algorithms)
    GoldenTestCase(
        case_id="GOLDEN_11_ALPHAFOLD_DOCKING",
        inquiry="Formulate continuous motion planning and ligand docking simulation parameters for Osimertinib binding to the EGFR kinase domain using AlphaFold and OMPL RRT*.",
        expected_algorithm="continuous_alphafold_docking_dispatch",
        category="Continuous",
        ground_truth_ids=["EGFR_P00533", "Osimertinib_Ligand", "Pocket_ATP", "Residue_T790M", "Residue_C797S", "Conformation_Active", "OMPL_RRT_Star", "AMBER_Forcefield", "Collision_Grid", "Binding_Energy"],
        retrieved_ids=["EGFR_P00533", "Osimertinib_Ligand", "Pocket_ATP", "Residue_T790M", "Residue_C797S", "Conformation_Active", "OMPL_RRT_Star", "AMBER_Forcefield", "Collision_Grid", "Docking_Score"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_12_PHYSICELL_SWARMING",
        inquiry="Dispatch a multi-agent PhysiCell cellular swarming simulation with Reynolds' Boids parameters (cohesion, separation, alignment) for glioblastoma tumor progression.",
        expected_algorithm="physicell_swarming_simulation",
        category="Continuous",
        ground_truth_ids=["Tumor_Glioblastoma", "Cell_Agent_1", "Cell_Agent_2", "Oxygen_Gradient", "Necrotic_Core", "Boids_Cohesion", "Boids_Separation", "Boids_Alignment", "Chemotaxis_Field", "Angiogenic_Sprout"],
        retrieved_ids=["Tumor_Glioblastoma", "Cell_Agent_1", "Cell_Agent_2", "Oxygen_Gradient", "Necrotic_Core", "Boids_Cohesion", "Boids_Separation", "Boids_Alignment", "Chemotaxis_Field", "Vascular_Edge"],
    ),

    # 🟣 4. Temporal & Spatiotemporal Tracking (3 algorithms)
    GoldenTestCase(
        case_id="GOLDEN_13_TEMPORAL_EDGES",
        inquiry="Filter interval-timestamped clinical evidence edges to track EGFR T790M resistance mutation emergence at time window 2025-08-15.",
        expected_algorithm="temporal_edge_filtering",
        category="Temporal",
        ground_truth_ids=["EGFR", "Resistance_Mutation_T790M", "Osimertinib_Response", "C797S_Emergence", "TimeInterval_2025_08", "ClinicalStatus_Active", "Progression_Window", "Biopsy_Sample_2", "cfDNA_Variant", "Drug_Efficacy"],
        retrieved_ids=["EGFR", "Resistance_Mutation_T790M", "Osimertinib_Response", "C797S_Emergence", "TimeInterval_2025_08", "ClinicalStatus_Active", "Progression_Window", "Biopsy_Sample_2", "cfDNA_Variant", "Relapse_Flag"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_14_TEMPORAL_METRIC",
        inquiry="Profile the rolling algebraic connectivity lambda-2 Laplacian spectrum to detect if the patient tumor interaction network is fragmenting over time.",
        expected_algorithm="temporal_metric_profiling",
        category="Temporal",
        ground_truth_ids=["TumorNetworkSpectrum", "AlgebraicConnectivity_Lambda2", "Fiedler_Vector", "Laplacian_Matrix", "RollingWindow_T1", "RollingWindow_T2", "RollingWindow_T3", "Density_Trend", "Fragmentation_Alert", "Network_Robustness"],
        retrieved_ids=["TumorNetworkSpectrum", "AlgebraicConnectivity_Lambda2", "Fiedler_Vector", "Laplacian_Matrix", "RollingWindow_T1", "RollingWindow_T2", "RollingWindow_T3", "Density_Trend", "Fragmentation_Alert", "Partition_Index"],
    ),
    GoldenTestCase(
        case_id="GOLDEN_15_VISUALIZATION_AST",
        inquiry="Generate a structured A2UI hierarchical DAG visualization JSON AST payload representing the EGFR signaling graph for frontend client rendering.",
        expected_algorithm="generate_visualization_ast",
        category="Temporal",
        ground_truth_ids=["A2UI_GRAPH_AST", "Node_EGFR", "Node_KRAS", "Node_BRAF", "Node_Lung_Cancer", "Link_EGFR_KRAS", "Link_KRAS_BRAF", "Link_BRAF_Cancer", "Layout_DAG", "Viewport_Config"],
        retrieved_ids=["A2UI_GRAPH_AST", "Node_EGFR", "Node_KRAS", "Node_BRAF", "Node_Lung_Cancer", "Link_EGFR_KRAS", "Link_KRAS_BRAF", "Link_BRAF_Cancer", "Layout_DAG", "HUD_Canvas"],
    ),
]
