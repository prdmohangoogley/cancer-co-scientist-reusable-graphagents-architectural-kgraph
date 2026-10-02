"""ADK (Agent Development Kit) module for PrimeKG graph reasoning."""

from __future__ import annotations

from .algorithm_router import (
    AlgorithmRoutingDecision,
    AlgorithmSelectionRouter,
    GraphAlgorithmCategory,
)
from .traversal import GraphEdge, GraphNode, SubgraphResult, TraversalConfig


def __getattr__(name: str):
    if name == "PrimeKGWorkerAgent":
        from .agent import PrimeKGWorkerAgent
        return PrimeKGWorkerAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "PrimeKGWorkerAgent",
    "TraversalConfig",
    "SubgraphResult",
    "GraphEdge",
    "GraphNode",
    "AlgorithmSelectionRouter",
    "AlgorithmRoutingDecision",
    "GraphAlgorithmCategory",
]
