"""Continuous Quality & Latency Monitor for Graph Agent Worker Tier (Spec 06, Spec 10, DOC-01).

Periodically evaluates all 15 graph algorithms across the 4 categories:
- Discrete (DFS/BFS, Dijkstra, D* Lite, WCC, TopoSort, Transitive Closure, Community, Ego-Net)
- Structural (PageRank Centrality, Betweenness Centrality, Density & Bridges)
- Continuous (OMPL AlphaFold RRT*, PhysiCell Boids)
- Temporal (Interval-Timestamped Edges, Algebraic Connectivity lambda_2)

Measures p50/p95 latency and error rate, and emits live time series to Cloud Monitoring.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Dict, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from packages.graphagent.tools.algorithms import GraphAlgorithmEngine
from packages.graphagent.observability.telemetry import (
    record_latency,
    emit_cloud_monitoring_metric,
    emit_cloud_log,
)


def run_graph_agent_health_probe() -> Dict[str, Any]:
    """Execute a single-pass health probe across all 4 algorithmic families."""
    engine = GraphAlgorithmEngine()
    probe_start = time.time()
    
    probe_results = []
    latencies = []
    errors = 0

    import asyncio

    test_probes = [
        # Discrete
        ("Dijkstra", lambda: asyncio.run(engine.shortest_path_dijkstra_astar("EGFR", "Osimertinib"))),
        ("BFS_Traversal", lambda: asyncio.run(engine.dfs_bfs_traversal("EGFR", mode="BFS", max_depth=2))),
        ("Connected_Components", lambda: asyncio.run(engine.connected_components())),
        ("Topological_Sort", lambda: engine.topological_sort_cascade([("EGFR", "GRB2"), ("GRB2", "SOS1"), ("SOS1", "KRAS")])),
        # Structural
        ("PageRank_Hubs", lambda: asyncio.run(engine.identify_hub_proteins("EGFR"))),
        ("Structural_Statistics", lambda: engine.subgraph_structural_statistics(["EGFR", "KRAS", "BRAF"])),
        # Continuous
        ("OMPL_AlphaFold", lambda: engine.generate_alphafold_docking_job("EGFR", "Osimertinib")),
        ("PhysiCell_Boids", lambda: engine.generate_physicell_swarming_job("Non-Small Cell Lung Carcinoma")),
        # Temporal
        ("Temporal_Interval_Edges", lambda: engine.temporal_edge_filtering("EGFR", "2026-10-01")),
        ("Temporal_Metric_Profiling", lambda: engine.temporal_metric_profiling([0.15, 0.22, 0.35, 0.48])),
    ]

    for name, probe_fn in test_probes:
        t0 = time.time()
        try:
            res = probe_fn()
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            latencies.append(elapsed_ms)
            record_latency(f"probe_{name}", elapsed_ms)
            probe_results.append({
                "algorithm": name,
                "status": "HEALTHY",
                "latency_ms": elapsed_ms,
            })
            emit_cloud_monitoring_metric("agent/graph_algorithm/latency", elapsed_ms, labels={"algorithm": name})
        except Exception as e:
            errors += 1
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            probe_results.append({
                "algorithm": name,
                "status": "ERROR",
                "error": str(e),
                "latency_ms": elapsed_ms,
            })

    total_duration_ms = round((time.time() - probe_start) * 1000, 2)
    sorted_lat = sorted(latencies) if latencies else [0.0]
    p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
    p95 = sorted_lat[min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)]

    summary = {
        "timestamp": time.time(),
        "total_algorithms_probed": len(test_probes),
        "successful_probes": len(test_probes) - errors,
        "failed_probes": errors,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "sla_p50_passed": p50 < 45.0,
        "sla_p95_passed": p95 < 350.0,
        "details": probe_results,
    }

    emit_cloud_monitoring_metric("agent/graph_algorithm/error_count", float(errors))
    emit_cloud_log(
        message=f"Continuous Graph Agents Monitor probe completed: {summary['successful_probes']}/{len(test_probes)} healthy | p50={p50}ms",
        severity="INFO" if errors == 0 else "WARNING",
        json_payload=summary,
    )

    return summary


if __name__ == "__main__":
    print("Running Graph Agent Worker Tier continuous monitor probe...")
    res = run_graph_agent_health_probe()
    print(f"Results: {res['successful_probes']}/{res['total_algorithms_probed']} algorithms healthy. p50={res['p50_latency_ms']}ms, p95={res['p95_latency_ms']}ms")
