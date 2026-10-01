"""Unit tests for PrimeKGWorkerAgent (DOC-01, DOC-03)."""

from __future__ import annotations

import pytest

from adk.agent import PrimeKGWorkerAgent


@pytest.mark.asyncio
async def test_primekg_worker_agent_pathways():
    """Verify worker agent coordinates GQL and SQL tools for pathway exploration."""
    agent = PrimeKGWorkerAgent(use_mock=True)
    result = await agent.explore_gene_disease_pathways(
        gene_symbol="EGFR",
        disease_name="Non-small cell lung carcinoma",
        max_hops=2,
    )
    assert len(result.nodes) > 0
    assert len(result.edges) > 0
    assert "EGFR" in result.summary
    assert result.hops_traversed == 2


@pytest.mark.asyncio
async def test_primekg_worker_agent_repurposing():
    """Verify worker agent identifies drug repurposing candidates."""
    agent = PrimeKGWorkerAgent(use_mock=True)
    candidates = await agent.find_drug_repurposing_candidates(
        disease_name="Non-small cell lung carcinoma",
        limit=5,
    )
    assert len(candidates) >= 1
    assert candidates[0]["target_gene"] == "EGFR"


@pytest.mark.asyncio
async def test_primekg_worker_agent_target_validation():
    """Verify worker agent performs oncological target validation."""
    agent = PrimeKGWorkerAgent(use_mock=True)
    result = await agent.query_target_validation(gene_symbol="TP53", limit=10)
    assert len(result.nodes) > 0
    assert result.query_target == "TP53"
    assert "TP53" in result.summary
