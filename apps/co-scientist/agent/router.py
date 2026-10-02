"""Intent classification and worker agent delegation router supporting the full 15-algorithm matrix.

Adheres to:
- DOC-03: Multi-Agent Layer Separation Standards & Declarative Routing
- Spec 06 & Spec 07: 15-Algorithm Graph Matrix Routing & Selection Evaluation (agent.correct_algorithm_choice)
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Categorical classification of user clinical inquiries."""
    DRUG_REPURPOSING = "DRUG_REPURPOSING"
    PATHWAY_ANALYSIS = "PATHWAY_ANALYSIS"
    TARGET_VALIDATION = "TARGET_VALIDATION"
    CLINICAL_TRIALS = "CLINICAL_TRIALS"
    GENERAL_ONCOLOGY_QUERY = "GENERAL_ONCOLOGY_QUERY"
    STRUCTURAL_ANALYSIS = "STRUCTURAL_ANALYSIS"
    CONTINUOUS_SIMULATION = "CONTINUOUS_SIMULATION"
    TEMPORAL_TRACKING = "TEMPORAL_TRACKING"
    VISUALIZATION_AST = "VISUALIZATION_AST"


class RoutingDecision(BaseModel):
    """Encapsulates classified intent, extracted entities, delegated tasks, and optimal algorithm choice."""
    intent: IntentType
    extracted_genes: List[str] = Field(default_factory=list)
    extracted_diseases: List[str] = Field(default_factory=list)
    delegated_workers: List[str] = Field(default_factory=list)
    recommended_algorithm: str = "Dijkstra"
    algorithm_choice_confidence: float = 0.95
    reasoning: str = ""


class IntentRouter:
    """Classifies user queries and routes tasks to specialized Graph Agent Workers and Algorithms."""

    # Common oncogenes / tumor suppressors for rapid heuristic extraction
    KNOWN_GENES = {
        "TP53", "EGFR", "KRAS", "NRAS", "HRAS", "BRCA1", "BRCA2", "PIK3CA",
        "BRAF", "MYC", "PTEN", "ERBB2", "ALK", "MET", "ROS1", "RET",
        "CDK4", "CDK6", "RB1", "APC", "ATM", "ATR", "FGFR1", "FGFR2", "FGFR3",
    }
    
    # Common cancer types
    KNOWN_DISEASES = {
        "lung cancer": "Non-small cell lung carcinoma",
        "nsclc": "Non-small cell lung carcinoma",
        "sclc": "Small cell lung cancer",
        "ovarian cancer": "Ovarian Carcinoma",
        "breast cancer": "Invasive Breast Carcinoma",
        "melanoma": "Cutaneous Melanoma",
        "colorectal cancer": "Colorectal Adenocarcinoma",
        "pancreatic cancer": "Pancreatic Ductal Adenocarcinoma",
        "glioblastoma": "Glioblastoma Multiforme",
        "prostate cancer": "Prostate Adenocarcinoma",
    }

    # 15-Algorithm Matrix Metadata
    ALGORITHM_CATALOG = {
        # Discrete Graph Algorithms
        "Dijkstra": {"category": "Discrete", "description": "Point-to-point shortest path for direct therapeutic and interaction routes."},
        "A*_VectorHeuristic": {"category": "Discrete", "description": "Shortest path guided by vector embedding heuristics."},
        "D*_Lite_Incremental": {"category": "Discrete", "description": "Dynamic replanning when edge weights mutate due to resistance."},
        "BFS_DFS": {"category": "Discrete", "description": "Breadth-first / depth-first step-by-step traversal."},
        "ConnectedComponents_WCC_SCC": {"category": "Discrete", "description": "Weakly and strongly connected component detection."},
        "TopologicalSort": {"category": "Discrete", "description": "Linear ordering of biochemical cascades and DAG signaling paths."},
        "TransitiveClosureReachability": {"category": "Discrete", "description": "Reachability analysis to downstream phenotype targets."},
        "CommunityDetection_LabelPropagation": {"category": "Discrete", "description": "Functional module and disease target cluster identification."},
        "EgoNetworkInspection": {"category": "Discrete", "description": "Focal gene k-hop ego-network neighborhood scan."},
        # Structural Analytics
        "NodeCentrality_PageRank": {"category": "Structural", "description": "High degree centrality hubs and master regulator identification."},
        "NodeCentrality_Betweenness": {"category": "Structural", "description": "Gatekeepers, bottlenecks, and critical signaling chokepoints."},
        "SubgraphStructuralStatistics": {"category": "Structural", "description": "Density, bridges, cut-vertices, and structural vulnerability."},
        # Continuous Simulation
        "Continuous_AlphaFold_OMPL_RRT": {"category": "Continuous", "description": "Conformation planning and ligand docking continuous motion planning."},
        "Continuous_PhysiCell_Boids": {"category": "Continuous", "description": "Cellular swarming and agent-based tumor microenvironment simulation."},
        # Temporal Tracking
        "Temporal_IntervalEdges": {"category": "Temporal", "description": "Interval-timestamped edge filtering across clinical time windows."},
        "Temporal_AlgebraicConnectivity_Lambda2": {"category": "Temporal", "description": "Rolling Laplacian spectrum (λ2) profiling network fragmentation."},
        "Temporal_Visualization_AST": {"category": "Temporal", "description": "A2UI graph AST visualization layout generator."},
    }

    def route_query(self, user_query: str) -> RoutingDecision:
        """Classify inquiry intent, extract entities, and recommend the optimal graph algorithm."""
        query_lower = user_query.lower()

        # 1. Entity Extraction
        genes: list[str] = []
        for word in re.findall(r"\b[A-Za-z0-9_-]+\b", user_query):
            upper_word = word.upper()
            if upper_word in self.KNOWN_GENES and upper_word not in genes:
                genes.append(upper_word)

        diseases: list[str] = []
        for term, canonical in self.KNOWN_DISEASES.items():
            if term in query_lower and canonical not in diseases:
                diseases.append(canonical)

        # Defaults if not matched
        if not genes:
            genes = ["EGFR"]
        if not diseases:
            diseases = ["Non-small cell lung carcinoma"]

        # 2. 15-Algorithm Matrix Intent & Algorithm Matching

        def _matches(patterns: list[str]) -> bool:
            for pat in patterns:
                if re.search(r"\b" + re.escape(pat) + r"\b", query_lower, re.IGNORECASE):
                    return True
            return False

        # 🔵 Continuous Geometry & Multi-Agent Simulation
        if _matches(["alphafold", "docking", "conformation", "ompl", "rrt", "ligand binding"]):
            return RoutingDecision(
                intent=IntentType.CONTINUOUS_SIMULATION,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.generate_alphafold_docking_job"],
                recommended_algorithm="Continuous_AlphaFold_OMPL_RRT",
                algorithm_choice_confidence=0.98,
                reasoning="Continuous molecular docking conformation planning dispatched to GKE OMPL RRT* engine.",
            )

        if _matches(["swarming", "physicell", "boids", "microenvironment simulation", "spatial cell"]):
            return RoutingDecision(
                intent=IntentType.CONTINUOUS_SIMULATION,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.generate_physicell_simulation_job"],
                recommended_algorithm="Continuous_PhysiCell_Boids",
                algorithm_choice_confidence=0.98,
                reasoning="Agent-based tumor swarming simulation dispatched to PhysiCell Boids engine.",
            )

        # 🟣 Temporal & Spatiotemporal Tracking
        if _matches(["algebraic connectivity", "lambda 2", "lambda_2", "laplacian", "fragmentation", "collapse"]):
            return RoutingDecision(
                intent=IntentType.TEMPORAL_TRACKING,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.temporal_metric_profiling"],
                recommended_algorithm="Temporal_AlgebraicConnectivity_Lambda2",
                algorithm_choice_confidence=0.97,
                reasoning="Longitudinal network fragmentation tracked via rolling algebraic connectivity (λ2) Laplacian spectrum.",
            )

        if _matches(["temporal", "time window", "timestamp", "longitudinal", "interval edge", "over time"]):
            return RoutingDecision(
                intent=IntentType.TEMPORAL_TRACKING,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.temporal_edge_filtering"],
                recommended_algorithm="Temporal_IntervalEdges",
                algorithm_choice_confidence=0.96,
                reasoning="Interval-timestamped edge filtering applied across patient clinical progression windows.",
            )

        if _matches(["ast", "visualization ast", "visualization layout", "render graph", "hierarchical dag layout"]):
            return RoutingDecision(
                intent=IntentType.VISUALIZATION_AST,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.generate_visualization_ast"],
                recommended_algorithm="Temporal_Visualization_AST",
                algorithm_choice_confidence=0.95,
                reasoning="A2UI graph AST structure requested for hierarchical layout visualization.",
            )

        # 🟡 Structural & Node-Level Analytics
        if _matches(["gatekeeper", "betweenness", "bottleneck", "chokepoint"]):
            return RoutingDecision(
                intent=IntentType.STRUCTURAL_ANALYSIS,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.identify_hub_proteins"],
                recommended_algorithm="NodeCentrality_Betweenness",
                algorithm_choice_confidence=0.97,
                reasoning="Betweenness centrality computation identifying critical signaling gatekeepers and bottlenecks.",
            )

        if _matches(["hub", "hubs", "pagerank", "master regulator", "degree centrality"]):
            return RoutingDecision(
                intent=IntentType.STRUCTURAL_ANALYSIS,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.identify_hub_proteins"],
                recommended_algorithm="NodeCentrality_PageRank",
                algorithm_choice_confidence=0.96,
                reasoning="PageRank and degree centrality analysis identifying high-influence oncogenic hub proteins.",
            )

        if _matches(["density", "cut vertex", "cut-vertex", "bridges", "fragility"]):
            return RoutingDecision(
                intent=IntentType.STRUCTURAL_ANALYSIS,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.subgraph_structural_statistics"],
                recommended_algorithm="SubgraphStructuralStatistics",
                algorithm_choice_confidence=0.95,
                reasoning="Subgraph structural statistics evaluated for density, bridges, and cut-vertices.",
            )

        # 🟢 Discrete Graph Algorithms & Core Clinical Workflows
        if _matches(["replan", "d* lite", "d-star", "resistance mutation", "invalidated path"]):
            return RoutingDecision(
                intent=IntentType.TARGET_VALIDATION,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.d_star_lite_replanning"],
                recommended_algorithm="D*_Lite_Incremental",
                algorithm_choice_confidence=0.96,
                reasoning="Incremental D* Lite replanning routes around drug-resistant mutated edges.",
            )

        if _matches(["connected components", "wcc", "scc", "isolated component"]):
            return RoutingDecision(
                intent=IntentType.PATHWAY_ANALYSIS,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.connected_components"],
                recommended_algorithm="ConnectedComponents_WCC_SCC",
                algorithm_choice_confidence=0.95,
                reasoning="Connected component detection identifies weakly and strongly isolated functional subgraphs.",
            )

        if _matches(["topological", "kinase cascade", "linear cascade", "upstream downstream order"]):
            return RoutingDecision(
                intent=IntentType.PATHWAY_ANALYSIS,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.topological_sort_cascade"],
                recommended_algorithm="TopologicalSort",
                algorithm_choice_confidence=0.96,
                reasoning="Topological sort linearizes directed biochemical signaling cascades.",
            )

        if _matches(["transitive closure", "phenotype reachability", "downstream phenotype", "reachable"]):
            return RoutingDecision(
                intent=IntentType.TARGET_VALIDATION,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.transitive_closure_reachability"],
                recommended_algorithm="TransitiveClosureReachability",
                algorithm_choice_confidence=0.95,
                reasoning="Transitive closure calculates all reachable downstream disease phenotypes from oncogenic source.",
            )

        if _matches(["community", "label propagation", "target cluster", "functional module"]):
            return RoutingDecision(
                intent=IntentType.PATHWAY_ANALYSIS,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.community_detection_modules"],
                recommended_algorithm="CommunityDetection_LabelPropagation",
                algorithm_choice_confidence=0.96,
                reasoning="Label propagation community detection groups cohesive cancer hallmark modules.",
            )

        if _matches(["ego network", "ego-network", "focal node", "neighborhood scan"]):
            return RoutingDecision(
                intent=IntentType.GENERAL_ONCOLOGY_QUERY,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.ego_network_inspection"],
                recommended_algorithm="EgoNetworkInspection",
                algorithm_choice_confidence=0.95,
                reasoning="Ego-network extraction explores immediate multi-hop interaction perimeter around focal node.",
            )

        if _matches(["a*", "a-star", "vector heuristic", "embedding heuristic"]):
            return RoutingDecision(
                intent=IntentType.PATHWAY_ANALYSIS,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.shortest_path_dijkstra_astar"],
                recommended_algorithm="A*_VectorHeuristic",
                algorithm_choice_confidence=0.96,
                reasoning="A* shortest path guided by BigQuery vector embedding heuristics.",
            )

        if _matches(["bfs", "dfs", "breadth first", "depth first"]):
            return RoutingDecision(
                intent=IntentType.PATHWAY_ANALYSIS,
                extracted_genes=genes,
                extracted_diseases=diseases,
                delegated_workers=["PrimeKGWorkerAgent.dfs_bfs_traversal"],
                recommended_algorithm="BFS_DFS",
                algorithm_choice_confidence=0.95,
                reasoning="Systematic breadth-first / depth-first pathway traversal over biomedical graph.",
            )

        # Standard Clinical Inquiry Fallbacks
        if any(w in query_lower for w in ["drug", "repurpose", "repurposing", "inhibitor", "therapy", "treatment"]):
            intent = IntentType.DRUG_REPURPOSING
            delegated = ["PrimeKGWorkerAgent.find_drug_repurposing_candidates"]
            recommended_algo = "Dijkstra"
            confidence = 0.95
            reasoning = "Query focuses on therapeutic candidates and drug repurposing opportunities via Dijkstra shortest paths."
        elif any(w in query_lower for w in ["pathway", "signaling", "cascade", "mechanism", "interact"]):
            intent = IntentType.PATHWAY_ANALYSIS
            delegated = ["PrimeKGWorkerAgent.explore_gene_disease_pathways"]
            recommended_algo = "TopologicalSort"
            confidence = 0.95
            reasoning = "Query seeks biochemical signaling pathways; routed to cascade topological analysis."
        elif any(w in query_lower for w in ["target", "vulnerability", "oncogene", "mutation", "validat"]):
            intent = IntentType.TARGET_VALIDATION
            delegated = ["PrimeKGWorkerAgent.explore_gene_disease_pathways"]
            recommended_algo = "NodeCentrality_PageRank"
            confidence = 0.95
            reasoning = "Query targets oncogenic driver validation and tumor vulnerabilities via centrality profiling."
        else:
            intent = IntentType.GENERAL_ONCOLOGY_QUERY
            delegated = ["PrimeKGWorkerAgent.explore_gene_disease_pathways"]
            recommended_algo = "Dijkstra"
            confidence = 0.90
            reasoning = "General oncology query dispatched to standard graph traversal."

        return RoutingDecision(
            intent=intent,
            extracted_genes=genes,
            extracted_diseases=diseases,
            delegated_workers=delegated,
            recommended_algorithm=recommended_algo,
            algorithm_choice_confidence=confidence,
            reasoning=reasoning,
        )
