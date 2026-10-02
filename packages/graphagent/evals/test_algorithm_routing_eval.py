"""Golden Evaluation Test Suite for Graph Algorithm Routing & Retrieval Quality (DOC-01, Spec 06, Spec 07).

Validates:
1. agent.correct_algorithm_choice >= 0.95 across 15 canonical algorithms in 4 categories
2. Retrieval metrics: mAP >= 0.82, precision@10 >= 0.88, recall@10 >= 0.80
3. Latency budgets: p50 < 45ms, p95 < 350ms
"""

from __future__ import annotations

import pytest

try:
    from adk.algorithm_router import AlgorithmSelectionRouter
    from evals.golden_cases import GOLDEN_ALGORITHM_CASES
    from observability.telemetry import (
        calculate_retrieval_metrics,
        get_correlation_context,
        get_latency_summary,
        init_telemetry,
        reset_telemetry,
        set_correlation_context,
        trace_span,
    )
    from tools.algorithms import GraphAlgorithmEngine
except ImportError:
    from packages.graphagent.adk.algorithm_router import AlgorithmSelectionRouter
    from packages.graphagent.evals.golden_cases import GOLDEN_ALGORITHM_CASES
    from packages.graphagent.observability.telemetry import (
        calculate_retrieval_metrics,
        get_correlation_context,
        get_latency_summary,
        init_telemetry,
        reset_telemetry,
        set_correlation_context,
        trace_span,
    )
    from packages.graphagent.tools.algorithms import GraphAlgorithmEngine


@pytest.fixture(autouse=True)
def setup_eval_env():
    """Ensure clean telemetry buffers and initialized tracer for evaluation runs."""
    reset_telemetry()
    init_telemetry("graphagent-evals")
    yield
    reset_telemetry()


def test_golden_algorithm_routing_accuracy():
    """Verify that AlgorithmSelectionRouter achieves agent.correct_algorithm_choice >= 0.95."""
    router = AlgorithmSelectionRouter()
    correct = 0
    total = len(GOLDEN_ALGORITHM_CASES)

    assert total >= 15, f"Golden test suite must contain at least 15 test cases, found {total}"

    mismatches = []
    with trace_span("eval.algorithm_routing_evaluation", workflow_type="Discrete") as span:
        for case in GOLDEN_ALGORITHM_CASES:
            decision = router.route_inquiry(case.inquiry)
            if decision.selected_algorithm == case.expected_algorithm:
                correct += 1
            else:
                mismatches.append({
                    "case_id": case.case_id,
                    "inquiry": case.inquiry,
                    "expected": case.expected_algorithm,
                    "actual": decision.selected_algorithm,
                })

        accuracy = correct / float(total)
        span.set_attribute("agent.correct_algorithm_choice", accuracy)
        span.set_attribute("eval.cases_total", total)
        span.set_attribute("eval.cases_correct", correct)

    assert accuracy >= 0.95, (
        f"agent.correct_algorithm_choice ({accuracy:.2%}) failed threshold (>= 95%). "
        f"Mismatches: {mismatches}"
    )


def test_golden_algorithm_matrix_category_coverage():
    """Verify complete coverage of all 4 categories across 15 distinct algorithms."""
    categories_found = {case.category for case in GOLDEN_ALGORITHM_CASES}
    assert {"Discrete", "Structural", "Continuous", "Temporal"}.issubset(categories_found)

    algorithms_found = {case.expected_algorithm for case in GOLDEN_ALGORITHM_CASES}
    assert len(algorithms_found) == 15, f"Expected 15 unique algorithms, found {len(algorithms_found)}"


def test_retrieval_metrics_benchmark():
    """Verify information retrieval quality: mAP >= 0.82, precision@10 >= 0.88, recall@10 >= 0.80."""
    map_scores: list[float] = []
    precision_scores: list[float] = []
    recall_scores: list[float] = []

    for case in GOLDEN_ALGORITHM_CASES:
        metrics = calculate_retrieval_metrics(
            retrieved_ids=case.retrieved_ids,
            ground_truth_ids=case.ground_truth_ids,
            k=10,
        )
        map_scores.append(metrics["map"])
        precision_scores.append(metrics["precision_at_k"])
        recall_scores.append(metrics["recall_at_k"])

    mean_map = round(sum(map_scores) / len(map_scores), 4)
    mean_precision = round(sum(precision_scores) / len(precision_scores), 4)
    mean_recall = round(sum(recall_scores) / len(recall_scores), 4)

    assert mean_map >= 0.82, f"mAP ({mean_map}) below target SLA threshold (>= 0.82)"
    assert mean_precision >= 0.88, f"Precision@10 ({mean_precision}) below target SLA threshold (>= 0.88)"
    assert mean_recall >= 0.80, f"Recall@10 ({mean_recall}) below target SLA threshold (>= 0.80)"


@pytest.mark.asyncio
async def test_algorithm_latency_benchmarks_meet_budgets():
    """Verify execution latency across algorithm suite meets budget SLAs (p50 < 45ms, p95 < 350ms)."""
    engine = GraphAlgorithmEngine(use_mock=True)

    # Execute representative algorithms across Discrete, Structural, Continuous, Temporal
    for _ in range(5):
        await engine.dfs_bfs_traversal("EGFR", mode="BFS", max_depth=2)
        await engine.shortest_path_dijkstra_astar("EGFR", "BRAF")
        engine.d_star_lite_replanning("EGFR", "KRAS", ["EGFR", "GRB2", "KRAS"], {("GRB2", "KRAS"): 99.0})
        await engine.connected_components()
        engine.topological_sort_cascade()
        engine.transitive_closure_reachability("EGFR")
        engine.community_detection_modules()
        await engine.ego_network_inspection("EGFR")
        await engine.identify_hub_proteins("TP53")
        engine.subgraph_structural_statistics()
        engine.generate_alphafold_docking_job("P00533", "COCCOC1=C")
        engine.generate_physicell_simulation_job("Glioblastoma", num_cells=1000)
        engine.temporal_edge_filtering("EGFR", "2025-08-15")
        engine.temporal_metric_profiling()
        engine.generate_visualization_ast(["EGFR", "KRAS"], [("EGFR", "KRAS")])

    summary = get_latency_summary()
    assert "overall" in summary, "Latency summary must record overall distribution"

    p50 = summary["overall"]["p50"]
    p95 = summary["overall"]["p95"]

    assert p50 < 45.0, f"Overall p50 latency ({p50}ms) exceeded SLA threshold (< 45ms)"
    assert p95 < 350.0, f"Overall p95 latency ({p95}ms) exceeded SLA threshold (< 350ms)"


def test_correlation_context_propagation():
    """Verify correlation IDs and session contexts propagate properly through spans."""
    set_correlation_context(
        trace_id="a1b2c3d4e5f60718293a4b5c6d7e8f90",
        session_id="session-clinical-eval-42",
        user_id="oncologist-bot",
    )

    with trace_span("eval.correlation_check", workflow_type="Discrete") as span:
        ctx = get_correlation_context()
        assert ctx["trace_id"] == "a1b2c3d4e5f60718293a4b5c6d7e8f90"
        assert ctx["session_id"] == "session-clinical-eval-42"
