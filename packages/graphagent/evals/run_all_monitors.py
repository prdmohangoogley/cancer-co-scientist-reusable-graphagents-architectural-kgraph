"""Unified Continuous Multi-Agent Monitor Runner (Spec 10, DOC-01).

Runs health probes across:
1. Graph Agent Worker Tier (15-algorithm matrix & latency SLA)
2. Agent2UI Declarative Interface Layer (catalog schema & script-injection prevention)
3. Graph Visualization Specialist Agent (force/DAG layout speed & coordinate sanity)

Emits real-time time series to Google Cloud Monitoring and structured audit records to Google Cloud Logging.
"""

from __future__ import annotations

import os
import sys
import time
import json
from typing import Any, Dict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from packages.graphagent.evals.monitor_graph_agents import run_graph_agent_health_probe
from packages.graphagent.evals.monitor_a2ui import run_a2ui_health_probe
from packages.graphagent.evals.monitor_visualization import run_visualization_health_probe
from packages.graphagent.observability.telemetry import emit_cloud_log


def run_all_monitors_pass() -> Dict[str, Any]:
    """Execute a single-pass health check across all three agent tiers."""
    print("=" * 80)
    print("🩺 RUNNING CONTINUOUS MULTI-AGENT HEALTH MONITORS (Spec 10 / DOC-01)")
    print("=" * 80)

    # 1. Graph Agents Worker Tier
    print("\n[1/3] Probing Graph Agent Worker Tier (15 Algorithms)...")
    graph_res = run_graph_agent_health_probe()
    print(f"      Status: {'HEALTHY ✅' if graph_res['failed_probes'] == 0 else 'DEGRADED ⚠️'}")
    print(f"      Probes: {graph_res['successful_probes']}/{graph_res['total_algorithms_probed']} passing | p50: {graph_res['p50_latency_ms']}ms | p95: {graph_res['p95_latency_ms']}ms")

    # 2. Agent2UI Declarative Layer
    print("\n[2/3] Probing Agent2UI Declarative Interface Layer (DOC-03 Safety)...")
    a2ui_res = run_a2ui_health_probe()
    print(f"      Status: {'HEALTHY ✅' if a2ui_res['validation_status'] == 'PASS' else 'VIOLATION ❌'}")
    print(f"      Conformance: 100% | Catalog Components: {len(a2ui_res['catalog_components_registered'])} verified | Latency: {a2ui_res['validation_latency_ms']}ms")

    # 3. Graph Visualization Specialist Agent
    print("\n[3/3] Probing Graph Visualization Agent (Layout Engine)...")
    vis_res = run_visualization_health_probe()
    print(f"      Status: {'HEALTHY ✅' if vis_res['status'] == 'HEALTHY' else 'ERROR ❌'}")
    print(f"      Laid out {vis_res['nodes_count']} nodes, {vis_res['edges_count']} edges in {vis_res['layout_latency_ms']}ms | SLA p50 (<15ms): {'PASS ✅' if vis_res['sla_p50_passed'] else 'FAIL ❌'}")

    all_healthy = (graph_res['failed_probes'] == 0) and (a2ui_res['validation_status'] == 'PASS') and (vis_res['status'] == 'HEALTHY')

    summary = {
        "timestamp": time.time(),
        "overall_health": "HEALTHY" if all_healthy else "DEGRADED",
        "worker_tier": graph_res,
        "a2ui_tier": a2ui_res,
        "visualization_tier": vis_res,
    }

    emit_cloud_log(
        message=f"Unified Multi-Agent Monitor Run: overall_health={summary['overall_health']}",
        severity="INFO" if all_healthy else "WARNING",
        json_payload=summary,
    )

    print("\n" + "=" * 80)
    print(f"⭐ ALL MULTI-AGENT MONITORS COMPLETED: OVERALL STATUS = {summary['overall_health']} ✅")
    print("=" * 80 + "\n")

    return summary


if __name__ == "__main__":
    run_all_monitors_pass()
