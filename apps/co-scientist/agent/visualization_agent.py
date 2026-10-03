"""Graph Visualization Specialist Agent for Cancer Co-Scientist (Spec 08).

Adheres to:
- DOC-01: AI Agent Quality Engineering & Observability
- DOC-02: Zero Ambient Authority & Non-Executable Payload Safety
- DOC-03: Open AI Agent Protocol Stack (A2UI Declarative Interfaces)
- DOC-08: Progressive Disclosure for Visual Payloads

Transforms typed AlgorithmResult outputs from the 15-algorithm matrix into
an interactive, declarative InteractiveGraphExplorer A2UI AST payload.
"""

from __future__ import annotations

import logging
import math
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

try:
    import networkx as nx
except ImportError:
    nx = None

try:
    from graphagent.observability.telemetry import trace_span
except ImportError:
    try:
        from observability.telemetry import trace_span
    except ImportError:
        from contextlib import contextmanager

        @contextmanager
        def trace_span(*args, **kwargs):
            yield None

logger = logging.getLogger("visualization_agent")


# Color palette for precision oncology entity types (DOC-03 certified)
ENTITY_COLORS: Dict[str, str] = {
    "Gene": "#38bdf8",         # Bright Sky Blue
    "Disease": "#f43f5e",      # Vibrant Rose / Crimson
    "Drug": "#10b981",         # Emerald Green
    "Pathway": "#a855f7",      # Purple / Amethyst
    "Phenotype": "#f59e0b",    # Amber / Gold
    "BiologicalProcess": "#6366f1",
    "MolecularFunction": "#ec4899",
    "CellularComponent": "#14b8a6",
    "Ligand": "#06b6d4",
    "Default": "#94a3b8",      # Slate Gray
}


class VisualNode(BaseModel):
    id: str
    name: str
    label: str
    x: float
    y: float
    radius: float = 24.0
    color: str = "#38bdf8"
    is_hub: bool = False
    is_gatekeeper: bool = False
    is_source: bool = False
    is_target: bool = False
    community_id: Optional[int] = None
    pagerank_score: Optional[float] = None
    degree: int = 1
    details: Dict[str, Any] = Field(default_factory=dict)


class VisualEdge(BaseModel):
    source_id: str
    target_id: str
    relationship: str
    confidence: float = 1.0
    is_shortest_path: bool = False
    is_bridge: bool = False
    style: str = "solid"  # solid, dashed, animated-flow


class InteractiveGraphExplorerPayload(BaseModel):
    component: str = "InteractiveGraphExplorer"
    id: str = Field(default_factory=lambda: f"graph_exp_{uuid.uuid4().hex[:8]}")
    props: Dict[str, Any]


class GraphVisualizationAgent:
    """Specialist agent producing declarative interactive visual graph ASTs."""

    def __init__(self, view_width: int = 860, view_height: int = 520) -> None:
        self.view_width = view_width
        self.view_height = view_height

    def create_interactive_visualization(
        self,
        algorithm_result: Any,
        title: Optional[str] = None,
        source_entity: Optional[str] = None,
        target_entity: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convert an AlgorithmResult into an InteractiveGraphExplorer A2UI payload."""
        algo_name = getattr(algorithm_result, "algorithm_name", "graph_traversal")
        nodes_raw = getattr(algorithm_result, "nodes", []) or []
        edges_raw = getattr(algorithm_result, "edges", []) or []
        metrics = getattr(algorithm_result, "metrics", {}) or {}
        paths = getattr(algorithm_result, "paths", []) or []

        with trace_span(
            name="agent.visualization_generation",
            workflow_type="Visualization",
            attributes={
                "graphagent.algorithm_name": algo_name,
                "graphagent.node_count": len(nodes_raw),
                "graphagent.edge_count": len(edges_raw),
            },
        ):
            # 1. Deduplicate & Build Adjacency Graph
            node_ids = list(dict.fromkeys(nodes_raw))
            if not node_ids and edges_raw:
                for e in edges_raw:
                    s = e.get("source_id") or e.get("source")
                    t = e.get("target_id") or e.get("target")
                    if s and s not in node_ids:
                        node_ids.append(s)
                    if t and t not in node_ids:
                        node_ids.append(t)

            # 2. Compute Layout Coordinates (Force-directed / Spring layout)
            coords = self._compute_layout(node_ids, edges_raw, algo_name)

            # 3. Detect Hubs, Gatekeepers, and Shortest Paths
            hubs = set(metrics.get("hub_proteins", []))
            gatekeepers = set(metrics.get("gatekeepers", []))
            shortest_path_edges = self._extract_shortest_path_edges(paths)

            # 4. Construct Visual Nodes
            visual_nodes: List[Dict[str, Any]] = []
            for nid in node_ids:
                label = self._infer_entity_label(nid)
                name = nid.split(":")[-1] if ":" in nid else nid
                pos = coords.get(nid, (self.view_width / 2, self.view_height / 2))
                is_source = (source_entity and (name.lower() == source_entity.lower() or nid == source_entity))
                is_target = (target_entity and (name.lower() == target_entity.lower() or nid == target_entity))
                is_hub = nid in hubs or name in hubs
                is_gatekeeper = nid in gatekeepers or name in gatekeepers

                # Centrality radius scaling (18px to 38px)
                radius = 24.0
                if is_hub:
                    radius = 34.0
                elif is_gatekeeper:
                    radius = 30.0
                elif is_source or is_target:
                    radius = 28.0

                visual_nodes.append({
                    "id": nid,
                    "name": name,
                    "label": label,
                    "x": round(pos[0], 1),
                    "y": round(pos[1], 1),
                    "radius": radius,
                    "color": ENTITY_COLORS.get(label, ENTITY_COLORS["Default"]),
                    "is_hub": bool(is_hub),
                    "is_gatekeeper": bool(is_gatekeeper),
                    "is_source": bool(is_source),
                    "is_target": bool(is_target),
                    "community_id": metrics.get("communities", {}).get(nid),
                    "degree": metrics.get("degrees", {}).get(nid, 1),
                    "details": {
                        "canonical_id": nid,
                        "entity_type": label,
                        "algorithm_role": "Hub" if is_hub else ("Gatekeeper" if is_gatekeeper else ("Focal Endpoint" if (is_source or is_target) else "Interacting Member")),
                    },
                })

            # 5. Construct Visual Edges
            visual_edges: List[Dict[str, Any]] = []
            for e in edges_raw:
                s = e.get("source_id") or e.get("source") or ""
                t = e.get("target_id") or e.get("target") or ""
                rel = e.get("relationship") or e.get("rel") or "INTERACTS_WITH"
                conf = float(e.get("confidence", 0.95))
                is_sp = (s, t) in shortest_path_edges or (t, s) in shortest_path_edges

                visual_edges.append({
                    "source_id": s,
                    "target_id": t,
                    "relationship": rel,
                    "confidence": conf,
                    "is_shortest_path": is_sp,
                    "style": "animated-flow" if is_sp else "solid",
                })

            # 6. Title and Layout Mode
            display_title = title or f"Interactive Topological Traversal: {algo_name.replace('_', ' ').title()}"
            layout_mode = "force-directed"
            if "topological" in algo_name.lower():
                layout_mode = "hierarchical-dag"
            elif "ego" in algo_name.lower() or "reachability" in algo_name.lower():
                layout_mode = "radial-ego"

            # 7. Build Declarative A2UI Component (DOC-03 compliant)
            return {
                "component": "InteractiveGraphExplorer",
                "id": f"graph_exp_{uuid.uuid4().hex[:8]}",
                "props": {
                    "title": display_title,
                    "algorithm_applied": algo_name,
                    "layout_mode": layout_mode,
                    "node_count": len(visual_nodes),
                    "edge_count": len(visual_edges),
                    "view_box": {
                        "width": self.view_width,
                        "height": self.view_height,
                    },
                    "nodes": visual_nodes,
                    "edges": visual_edges,
                    "metrics_summary": {
                        "density": metrics.get("density", 0.0),
                        "diameter": metrics.get("diameter"),
                        "hub_count": len(hubs),
                        "gatekeeper_count": len(gatekeepers),
                        "shortest_path_hops": len(paths[0]) - 1 if paths else 0,
                    },
                    "interactive_actions": [
                        "ZOOM_PAN",
                        "NODE_DRAG",
                        "CLICK_INSPECT",
                        "EXPAND_NEIGHBORHOOD",
                        "FILTER_RELATION",
                    ],
                },
            }

    def _compute_layout(
        self,
        node_ids: List[str],
        edges: List[Dict[str, Any]],
        algo_name: str,
    ) -> Dict[str, tuple[float, float]]:
        """Compute 2D coordinates scaled to view bounds."""
        margin_x = 80
        margin_y = 60
        w = self.view_width - (margin_x * 2)
        h = self.view_height - (margin_y * 2)

        if not node_ids:
            return {}

        n_nodes = len(node_ids)

        # Use NetworkX spring layout if available
        if nx and n_nodes > 1:
            g = nx.Graph()
            for nid in node_ids:
                g.add_node(nid)
            for e in edges:
                s = e.get("source_id") or e.get("source")
                t = e.get("target_id") or e.get("target")
                if s in g and t in g:
                    g.add_edge(s, t)

            pos = nx.spring_layout(g, seed=42, k=1.8 / math.sqrt(n_nodes), iterations=50)
            coords = {}
            for nid, (nx_x, nx_y) in pos.items():
                screen_x = margin_x + ((nx_x + 1.0) / 2.0) * w
                screen_y = margin_y + ((nx_y + 1.0) / 2.0) * h
                coords[nid] = (screen_x, screen_y)
            return coords

        # Fallback: Deterministic Radial / Circular placement
        coords = {}
        for i, nid in enumerate(node_ids):
            angle = (2 * math.pi * i) / n_nodes
            rad = min(w, h) * 0.42
            screen_x = (self.view_width / 2) + rad * math.cos(angle)
            screen_y = (self.view_height / 2) + rad * math.sin(angle)
            coords[nid] = (screen_x, screen_y)
        return coords

    def _infer_entity_label(self, entity_id: str) -> str:
        """Infer PrimeKG label from entity prefix or symbol."""
        eid_lower = entity_id.lower()
        if "drug" in eid_lower or "db:" in eid_lower or "chembl" in eid_lower:
            return "Drug"
        if "cancer" in eid_lower or "carcinoma" in eid_lower or "mondo:" in eid_lower or "disease" in eid_lower:
            return "Disease"
        if "reactome:" in eid_lower or "pathway" in eid_lower or "signaling" in eid_lower:
            return "Pathway"
        if "hp:" in eid_lower or "phenotype" in eid_lower:
            return "Phenotype"
        return "Gene"

    def _extract_shortest_path_edges(self, paths: List[List[str]]) -> Set[Tuple[str, str]]:
        """Extract edge pairs that are part of the shortest path."""
        pairs: Set[Tuple[str, str]] = set()
        if not paths:
            return pairs
        for p in paths:
            for i in range(len(p) - 1):
                pairs.add((p[i], p[i + 1]))
        return pairs
