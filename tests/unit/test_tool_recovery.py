"""Unit tests for Tool Docstrings and LLM Error Recovery Contracts (DOC-01, Spec 15 §2)."""

from __future__ import annotations

import inspect
import pytest

from tools.algorithms import AlgorithmResult, GraphAlgorithmEngine
import deploy.scripts.deploy_dual_gea_agents as deploy_tools


def test_algorithm_result_recoverable_error_contract():
    err_res = AlgorithmResult.recoverable_error(
        algorithm_name="Dijkstra",
        workflow_type="Discrete",
        target_entity="EGFR_T790M",
        error_type="EntityNotFoundException",
        error_message="Node 'EGFR_T790M' was not found in PrimeKGGraph.",
        recovery_instruction="Retry with canonical HGNC symbol 'EGFR' and filter relationships using biomarker='T790M'.",
    )
    assert err_res.status == "RECOVERABLE_ERROR"
    assert err_res.error_type == "EntityNotFoundException"
    assert "recovery_instruction" in AlgorithmResult.model_fields
    assert "Retry with canonical HGNC" in err_res.recovery_instruction
    assert "Recoverable error" in err_res.summary


def test_graph_algorithm_engine_docstrings_completeness():
    """All public methods of GraphAlgorithmEngine must contain exhaustive Args: and Returns: docstrings."""
    engine = GraphAlgorithmEngine(use_mock=True)
    methods = [
        engine.dfs_bfs_traversal,
        engine.shortest_path_dijkstra_astar,
        engine.d_star_lite_replanning,
        engine.connected_components,
        engine.topological_sort_cascade,
        engine.transitive_closure_reachability,
        engine.community_detection_modules,
        engine.ego_network_inspection,
        engine.identify_hub_proteins,
        engine.subgraph_structural_statistics,
        engine.generate_alphafold_docking_job,
        engine.generate_physicell_swarming_job,
        engine.temporal_edge_filtering,
        engine.temporal_metric_profiling,
        engine.generate_visualization_ast,
    ]

    for meth in methods:
        doc = inspect.getdoc(meth)
        name = meth.__name__
        assert doc is not None, f"Method {name} lacks a docstring."
        assert "Args:" in doc, f"Method {name} lacks 'Args:' section in docstring."
        assert "Returns:" in doc, f"Method {name} lacks 'Returns:' section in docstring."


@pytest.mark.asyncio
async def test_graph_algorithm_engine_recoverable_errors():
    engine = GraphAlgorithmEngine(use_mock=True)

    # Empty source_entity in dfs_bfs_traversal
    res1 = await engine.dfs_bfs_traversal(source_entity="", mode="BFS")
    assert res1.status == "RECOVERABLE_ERROR"
    assert res1.error_type == "EmptySourceEntityException"
    assert "HGNC" in res1.recovery_instruction

    # Invalid depth in dfs_bfs_traversal
    res2 = await engine.dfs_bfs_traversal(source_entity="EGFR", max_depth=10)
    assert res2.status == "RECOVERABLE_ERROR"
    assert res2.error_type == "DepthOutOfBoundsException"

    # Missing target in shortest_path
    res3 = await engine.shortest_path_dijkstra_astar(source_entity="EGFR", target_entity="")
    assert res3.status == "RECOVERABLE_ERROR"
    assert res3.error_type == "MissingEntityException"

    # Missing gene in transitive closure
    res4 = engine.transitive_closure_reachability(source_gene="")
    assert res4.status == "RECOVERABLE_ERROR"

    # Missing protein_id in AlphaFold
    res5 = engine.generate_alphafold_docking_job(protein_id="", ligand_smiles="CC")
    assert res5.status == "RECOVERABLE_ERROR"

    # Missing tumor_type in PhysiCell
    res6 = engine.generate_physicell_swarming_job(tumor_type="")
    assert res6.status == "RECOVERABLE_ERROR"

    # Missing source_entity in temporal edge filtering
    res7 = engine.temporal_edge_filtering(source_entity="", target_timestamp="2025-06-01")
    assert res7.status == "RECOVERABLE_ERROR"


def test_deploy_script_tools_docstrings():
    """All tools exposed in deploy_dual_gea_agents must contain exhaustive Args: and Returns: docstrings."""
    tools = [
        deploy_tools.query_primekg_graph,
        deploy_tools.execute_graph_algorithm,
        deploy_tools.execute_discrete_graph_algorithm,
        deploy_tools.explore_target_subgraph_neighborhood,
        deploy_tools.analyze_structural_centrality_gatekeepers,
        deploy_tools.validate_precision_oncology_pathway,
        deploy_tools.run_discrete_traversal,
        deploy_tools.run_structural_analytics,
        deploy_tools.run_continuous_simulation,
        deploy_tools.run_temporal_tracking,
        deploy_tools.delegate_to_graph_agent,
        deploy_tools.verify_oncology_guidelines,
        deploy_tools.inspect_memory_bank,
        deploy_tools.generate_a2ui_payload,
        deploy_tools.request_human_confirmation,
    ]

    for tool in tools:
        doc = inspect.getdoc(tool)
        name = tool.__name__
        assert doc is not None, f"Deploy tool {name} lacks a docstring."
        assert "Args:" in doc, f"Deploy tool {name} lacks 'Args:' section in docstring."
        assert "Returns:" in doc, f"Deploy tool {name} lacks 'Returns:' section in docstring."


def test_deploy_script_tool_recovery_contracts():
    # query_primekg_graph error handling
    res_err1 = deploy_tools.query_primekg_graph(source_entity="")
    assert res_err1["status"] == "RECOVERABLE_ERROR"
    assert "recovery_instruction" in res_err1

    res_err2 = deploy_tools.query_primekg_graph(source_entity="EGFR", depth=5)
    assert res_err2["status"] == "RECOVERABLE_ERROR"
    assert "recovery_instruction" in res_err2

    res_ok = deploy_tools.query_primekg_graph(source_entity="EGFR", depth=2)
    assert res_ok["status"] == "SUCCESS"

    # execute_graph_algorithm error handling
    res_algo_err = deploy_tools.execute_graph_algorithm(algorithm_name="nonexistent_quantum_super_algo")
    assert res_algo_err["status"] == "RECOVERABLE_ERROR"
    assert "recovery_instruction" in res_algo_err

    # validate_precision_oncology_pathway error handling
    res_pathway_err1 = deploy_tools.validate_precision_oncology_pathway(biomarker="", therapeutic_agent="Osimertinib")
    assert res_pathway_err1["status"] == "RECOVERABLE_ERROR"
    res_pathway_err2 = deploy_tools.validate_precision_oncology_pathway(biomarker="EGFR T790M", therapeutic_agent="")
    assert res_pathway_err2["status"] == "RECOVERABLE_ERROR"

    # request_human_confirmation error handling and success
    res_hitl_err = deploy_tools.request_human_confirmation(action_type="INVALID_UNKNOWN_ACTION")
    assert res_hitl_err["status"] == "RECOVERABLE_ERROR"
    assert "recovery_instruction" in res_hitl_err

    res_hitl_ok = deploy_tools.request_human_confirmation(
        action_type="OFF_LABEL_THERAPY_RECOMMENDATION",
        proposed_action="Osimertinib + Savolitinib",
        clinical_rationale="Overcoming secondary MET amplification",
        risk_level="HIGH",
    )
    assert res_hitl_ok["status"] == "PENDING_APPROVAL"
    assert "action_id" in res_hitl_ok
    assert res_hitl_ok["confirmation_card"]["component"] == "ConfirmationDialog"
    assert "recovery_instruction" in res_hitl_ok
