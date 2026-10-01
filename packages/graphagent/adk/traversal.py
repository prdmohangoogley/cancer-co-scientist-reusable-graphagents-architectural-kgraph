"""Biomedical knowledge graph traversal definitions and algorithms."""

from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class TraversalConfig(BaseModel):
    """Configuration constraints for multi-hop graph traversal."""
    max_hops: int = Field(default=2, ge=1, le=5, description="Maximum traversal depth")
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum edge confidence score")
    allowed_edge_types: Optional[List[str]] = Field(
        default=None,
        description="Filter for relationship labels (e.g. TARGETS, INDICATION, INTERACTS_WITH)",
    )
    limit: int = Field(default=50, ge=1, le=500, description="Max entities to return")


class GraphNode(BaseModel):
    """Typed biomedical entity node."""
    id: str
    label: str  # Gene, Disease, Drug, Pathway
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Typed relationship connecting biomedical nodes."""
    source_id: str
    target_id: str
    relationship: str
    confidence: float = 1.0
    evidence_source: Optional[str] = None
    properties: dict[str, Any] = Field(default_factory=dict)


class SubgraphResult(BaseModel):
    """Encapsulates an extracted subgraph containing nodes, edges, and provenance."""
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    query_target: str
    hops_traversed: int
    summary: str = ""
