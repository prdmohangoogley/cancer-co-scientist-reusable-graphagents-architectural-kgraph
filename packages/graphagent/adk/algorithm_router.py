"""Algorithm selection router for the 15-algorithm matrix across 4 categories (Spec 06, Spec 07).

Categories:
1. Discrete Graph Algorithms:
   - dfs_bfs_traversal (BFS / DFS Traversal)
   - shortest_path_dijkstra_astar (Dijkstra / A* Shortest Path)
   - d_star_lite_replanning (D* Lite Dynamic Replanning)
   - connected_components (Connected Components WCC / SCC)
   - topological_sort_cascade (Topological Sort Signaling Cascade)
   - transitive_closure_reachability (Transitive Closure Reachability)
   - community_detection_modules (Community Detection / Label Propagation)
   - ego_network_inspection (Ego-Network Inspection)
2. Structural & Node-Level Analytics:
   - compute_node_centrality (Degree, PageRank Hubs, Betweenness Gatekeepers)
   - subgraph_structural_statistics (Graph Density, Bridges, Cut-Vertices)
3. Continuous Geometry & Simulation:
   - continuous_alphafold_docking_dispatch (AlphaFold RRT* Motion Planning)
   - physicell_swarming_simulation (PhysiCell Reynolds' Boids Swarming)
4. Temporal & Spatiotemporal Tracking:
   - temporal_edge_filtering (Interval-Timestamped Edges)
   - temporal_metric_profiling (Rolling Algebraic Connectivity λ2)
   - generate_visualization_ast (A2UI / JSON AST Graph Visualization)
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class GraphAlgorithmCategory(str, Enum):
    DISCRETE = "Discrete"
    STRUCTURAL = "Structural"
    CONTINUOUS = "Continuous"
    TEMPORAL = "Temporal"


class AlgorithmRoutingDecision(BaseModel):
    """Encapsulates selected algorithm, category, confidence score, and rationale."""
    selected_algorithm: str
    category: str
    confidence: float = 1.0
    reasoning: str = ""
    target_entities: List[str] = Field(default_factory=list)


class AlgorithmSelectionRouter:
    """Classifies clinical inquiry queries into optimal graph algorithms from the 15-algorithm matrix."""

    KNOWN_GENES = {
        "TP53", "EGFR", "KRAS", "BRCA1", "BRCA2", "PIK3CA",
        "BRAF", "MYC", "PTEN", "ERBB2", "ERBB3", "ALK", "MET",
        "GRB2", "SOS1", "MAP2K1", "MAPK1", "AKT1", "MTOR",
    }

    def route_inquiry(self, inquiry: str) -> AlgorithmRoutingDecision:
        """Route clinical query to one of the 15 canonical graph algorithms."""
        q = inquiry.lower()

        # Extract target entities (genes / proteins)
        extracted: list[str] = []
        for word in re.findall(r"\b[A-Za-z0-9_-]+\b", inquiry):
            upper_word = word.upper()
            if upper_word in self.KNOWN_GENES and upper_word not in extracted:
                extracted.append(upper_word)

        # ---------------------------------------------------------------------
        # 3. Continuous Geometry & Simulation (GKE Delegated)
        # ---------------------------------------------------------------------
        if any(w in q for w in ["alphafold", "ompl", "rrt*", "rrt", "docking", "ligand binding", "conformation planning"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="continuous_alphafold_docking_dispatch",
                category=GraphAlgorithmCategory.CONTINUOUS.value,
                confidence=0.98,
                reasoning="Inquiry involves continuous conformational motion planning or ligand docking.",
                target_entities=extracted or ["EGFR"],
            )

        if any(w in q for w in ["physicell", "boids", "swarming", "reynolds", "microenvironment simulation", "flocking"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="physicell_swarming_simulation",
                category=GraphAlgorithmCategory.CONTINUOUS.value,
                confidence=0.98,
                reasoning="Inquiry models agent-based cell swarming and flocking in tumor microenvironments.",
                target_entities=extracted,
            )

        # ---------------------------------------------------------------------
        # 4. Temporal & Spatiotemporal Tracking
        # ---------------------------------------------------------------------
        if any(w in q for w in ["visualization ast", "a2ui visualization", "json ast", "hierarchical dag visualization", "canvas rendering", "client rendering ast"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="generate_visualization_ast",
                category=GraphAlgorithmCategory.TEMPORAL.value,
                confidence=0.98,
                reasoning="Inquiry requests declarative graph AST / A2UI payload generation for client rendering.",
                target_entities=extracted,
            )

        if any(w in q for w in ["algebraic connectivity", "lambda_2", "lambda-2", "fiedler", "laplacian spectrum", "network fragmenting", "temporal metric", "collapsing"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="temporal_metric_profiling",
                category=GraphAlgorithmCategory.TEMPORAL.value,
                confidence=0.98,
                reasoning="Inquiry profiles dynamic graph stability and Laplacian algebraic connectivity over time.",
                target_entities=extracted,
            )

        if any(w in q for w in ["temporal edge", "timestamped", "interval-timestamped", "valid_from", "valid_to", "time window", "progression over time"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="temporal_edge_filtering",
                category=GraphAlgorithmCategory.TEMPORAL.value,
                confidence=0.98,
                reasoning="Inquiry requires interval-timestamped edge filtering across longitudinal windows.",
                target_entities=extracted or ["EGFR"],
            )

        # ---------------------------------------------------------------------
        # 2. Structural & Node-Level Analytics
        # ---------------------------------------------------------------------
        if any(w in q for w in ["subgraph density", "bridges", "cut-vertices", "cut vertices", "articulation points", "single point of failure", "graph density"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="subgraph_structural_statistics",
                category=GraphAlgorithmCategory.STRUCTURAL.value,
                confidence=0.97,
                reasoning="Inquiry analyzes network density and critical vulnerability bridges or cut-vertices.",
                target_entities=extracted,
            )

        if any(w in q for w in ["centrality", "pagerank", "betweenness", "hub protein", "gatekeeper", "bottleneck gatekeeper", "degree centrality", "master regulator"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="compute_node_centrality",
                category=GraphAlgorithmCategory.STRUCTURAL.value,
                confidence=0.98,
                reasoning="Inquiry evaluates degree centrality, PageRank hubs, or betweenness gatekeepers.",
                target_entities=extracted or ["TP53"],
            )

        # ---------------------------------------------------------------------
        # 1. Discrete Graph Algorithms (Spanner GQL / In-Memory Topology)
        # ---------------------------------------------------------------------
        if any(w in q for w in ["d* lite", "d*lite", "d-star", "replanning", "replan", "mutation invalidat", "resistance barrier", "dynamically reroute"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="d_star_lite_replanning",
                category=GraphAlgorithmCategory.DISCRETE.value,
                confidence=0.98,
                reasoning="Inquiry requires real-time incremental path replanning around mutated or impassable edges.",
                target_entities=extracted or ["EGFR"],
            )

        if any(w in q for w in ["topological sort", "linearize", "signaling cascade", "execution order", "linear ordering", "dag order", "linearization"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="topological_sort_cascade",
                category=GraphAlgorithmCategory.DISCRETE.value,
                confidence=0.97,
                reasoning="Inquiry resolves the execution sequence of a directed acyclic signaling cascade.",
                target_entities=extracted,
            )

        if any(w in q for w in ["transitive closure", "reachability", "reachable downstream", "phenotypic end-states", "all downstream targets"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="transitive_closure_reachability",
                category=GraphAlgorithmCategory.DISCRETE.value,
                confidence=0.98,
                reasoning="Inquiry queries downstream phenotypic reachability and transitive closure.",
                target_entities=extracted or ["EGFR"],
            )

        if any(w in q for w in ["community detection", "label propagation", "dense functional modules", "gene clusters", "co-functional", "clustering modules"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="community_detection_modules",
                category=GraphAlgorithmCategory.DISCRETE.value,
                confidence=0.97,
                reasoning="Inquiry clusters interactome entities into co-functional biological modules.",
                target_entities=extracted,
            )

        if any(w in q for w in ["connected components", "scc", "wcc", "weakly connected", "strongly connected", "isolated subnetworks", "sub-networks"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="connected_components",
                category=GraphAlgorithmCategory.DISCRETE.value,
                confidence=0.98,
                reasoning="Inquiry identifies connected graph modules and isolated component subgraphs.",
                target_entities=extracted,
            )

        if any(w in q for w in ["ego-network", "ego network", "focal node", "focal protein", "1-hop ego", "ego-net"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="ego_network_inspection",
                category=GraphAlgorithmCategory.DISCRETE.value,
                confidence=0.97,
                reasoning="Inquiry inspects the localized k-hop ego-network around a focal target entity.",
                target_entities=extracted or ["EGFR"],
            )

        if any(w in q for w in ["shortest path", "dijkstra", "a*", "a-star", "point-to-point", "point to point", "least cost path", "fastest pathway route"]):
            return AlgorithmRoutingDecision(
                selected_algorithm="shortest_path_dijkstra_astar",
                category=GraphAlgorithmCategory.DISCRETE.value,
                confidence=0.98,
                reasoning="Inquiry requires point-to-point shortest path finding via Dijkstra or A*.",
                target_entities=extracted or ["EGFR", "BRAF"],
            )

        # Default fallback: DFS/BFS Traversal
        return AlgorithmRoutingDecision(
            selected_algorithm="dfs_bfs_traversal",
            category=GraphAlgorithmCategory.DISCRETE.value,
            confidence=0.95,
            reasoning="Inquiry explores multi-hop interaction paths via Breadth-First or Depth-First traversal.",
            target_entities=extracted or ["EGFR"],
        )
