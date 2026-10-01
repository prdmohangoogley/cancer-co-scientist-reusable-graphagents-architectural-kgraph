"""Performance and latency evaluation benchmark for GraphAgent (DOC-01, Spec 06).

Measures traversal latency, telemetry span creation, and bottleneck detection.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

try:
    from adk.agent import PrimeKGWorkerAgent
    from observability.telemetry import init_telemetry, trace_span
    from tools.algorithms import GraphAlgorithmEngine
except ImportError:
    from ..adk.agent import PrimeKGWorkerAgent
    from ..observability.telemetry import init_telemetry, trace_span
    from ..tools.algorithms import GraphAlgorithmEngine

logger = logging.getLogger("graphagent_evals")



class GraphAgentBenchmark:
    """Latency and quality benchmark suite for graph operations."""

    def __init__(self, use_mock: bool = True) -> None:
        self.tracer = init_telemetry(service_name="graphagent-evals")
        self.worker = PrimeKGWorkerAgent(use_mock=use_mock)
        self.algo_engine = GraphAlgorithmEngine(use_mock=use_mock)

    async def benchmark_traversal_latency(self, iterations: int = 10) -> dict[str, Any]:
        """Measure average latency for standard PrimeKG multi-hop traversals."""
        latencies: list[float] = []

        for i in range(iterations):
            t0 = time.time()
            with trace_span("benchmark.traversal_iteration", workflow_type="Discrete", db_target="Spanner") as span:
                span.set_attribute("benchmark.iteration", i)
                await self.worker.explore_gene_disease_pathways(
                    gene_symbol="EGFR",
                    disease_name="Non-small cell lung carcinoma",
                    max_hops=2,
                )
            latencies.append((time.time() - t0) * 1000)

        avg_latency = round(sum(latencies) / len(latencies), 2)
        p95_latency = round(sorted(latencies)[int(len(latencies) * 0.95)], 2)
        min_latency = round(min(latencies), 2)
        max_latency = round(max(latencies), 2)

        return {
            "test": "multi_hop_traversal",
            "iterations": iterations,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "min_latency_ms": min_latency,
            "max_latency_ms": max_latency,
            "budget_met": avg_latency < 100.0,
        }

    async def benchmark_simulation_dispatch(self) -> dict[str, Any]:
        """Measure latency of continuous simulation dispatch parameter formulation."""
        t0 = time.time()
        with trace_span("benchmark.simulation_dispatch", workflow_type="Continuous", db_target="GKE"):
            res = self.algo_engine.generate_alphafold_docking_job(
                protein_id="P00533",
                ligand_smiles="COCCOC1=C(C=C2C(=C1)C(=NC=N2)NC3=CC=CC(=C3)C#C)OCCOC",
            )
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        return {
            "test": "simulation_dispatch",
            "elapsed_ms": elapsed_ms,
            "status": res.metrics.get("status"),
            "budget_met": elapsed_ms < 50.0,
        }

    async def run_all_benchmarks(self) -> dict[str, Any]:
        """Run full evaluation suite."""
        traversal = await self.benchmark_traversal_latency(iterations=5)
        simulation = await self.benchmark_simulation_dispatch()
        return {
            "status": "completed",
            "traversal_benchmarks": traversal,
            "simulation_benchmarks": simulation,
        }


if __name__ == "__main__":
    benchmark = GraphAgentBenchmark(use_mock=True)
    results = asyncio.run(benchmark.run_all_benchmarks())
    print("\n=== GraphAgent Evaluation Benchmark Results ===")
    print(f"Traversal Avg Latency: {results['traversal_benchmarks']['avg_latency_ms']}ms (Budget Met: {results['traversal_benchmarks']['budget_met']})")
    print(f"Simulation Dispatch:   {results['simulation_benchmarks']['elapsed_ms']}ms (Budget Met: {results['simulation_benchmarks']['budget_met']})")
