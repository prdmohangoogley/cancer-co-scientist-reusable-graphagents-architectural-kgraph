"""Unit tests for GraphAlgorithmEngine (Spec 06)."""

from __future__ import annotations

import pytest

from tools.algorithms import GraphAlgorithmEngine


@pytest.mark.asyncio
async def test_ego_network_inspection():
    """Verify ego-network extraction around a focal gene node."""
    engine = GraphAlgorithmEngine(use_mock=True)
    result = await engine.ego_network_inspection(focal_node="EGFR", k_hops=1, limit=10)
    assert result.algorithm_name == "EgoNetworkInspection"
    assert result.workflow_type == "Discrete"
    assert result.target_entity == "EGFR"
    assert len(result.paths) > 0
    assert result.metrics["node_count"] > 1


@pytest.mark.asyncio
async def test_hub_centrality_analysis():
    """Verify hub centrality identification flags key oncogenes."""
    engine = GraphAlgorithmEngine(use_mock=True)
    res_tp53 = await engine.identify_hub_proteins(gene_symbol="TP53")
    assert res_tp53.metrics["is_hub"] is True
    assert res_tp53.metrics["degree_centrality"] > 50
    assert res_tp53.metrics["bottleneck_gatekeeper"] is True


def test_continuous_alphafold_docking_dispatch():
    """Verify continuous motion planning parameter generator for AlphaFold."""
    engine = GraphAlgorithmEngine(use_mock=True)
    result = engine.generate_alphafold_docking_job(
        protein_id="P00533",
        ligand_smiles="COCCOC1=C",
        num_samples=500,
    )
    assert result.workflow_type == "Continuous"
    assert result.simulation_payload is not None
    assert result.simulation_payload["engine"] == "OMPL-RRT*"
    assert result.simulation_payload["sampling_budget"] == 500


def test_physicell_swarming_simulation():
    """Verify PhysiCell agent-based microenvironment simulation parameter generation."""
    engine = GraphAlgorithmEngine(use_mock=True)
    result = engine.generate_physicell_simulation_job(
        tumor_type="Glioblastoma",
        num_cells=10000,
    )
    assert result.workflow_type == "Continuous"
    assert result.simulation_payload["engine"] == "PhysiCell-AgentBased"
    assert result.simulation_payload["initial_cell_count"] == 10000
