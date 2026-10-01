"""Unit tests for Lead Orchestrator IntentRouter (DOC-03)."""

from __future__ import annotations

import sys
from pathlib import Path

# Add apps/co-scientist to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "co-scientist"))

from agent.router import IntentRouter, IntentType


def test_intent_router_drug_repurposing():
    """Verify router classifies therapeutic and repurposing queries."""
    router = IntentRouter()
    decision = router.route_query("What drugs or inhibitors can target EGFR in lung cancer?")
    assert decision.intent == IntentType.DRUG_REPURPOSING
    assert "EGFR" in decision.extracted_genes
    assert "Non-small cell lung carcinoma" in decision.extracted_diseases


def test_intent_router_pathway_analysis():
    """Verify router classifies biochemical cascade queries."""
    router = IntentRouter()
    decision = router.route_query("What signaling pathways and interactions connect TP53 and ovarian cancer?")
    assert decision.intent == IntentType.PATHWAY_ANALYSIS
    assert "TP53" in decision.extracted_genes
    assert "Ovarian Carcinoma" in decision.extracted_diseases


def test_intent_router_target_validation():
    """Verify router classifies oncogene target vulnerability queries."""
    router = IntentRouter()
    decision = router.route_query("Validate KRAS as an oncogene target in pancreatic cancer")
    assert decision.intent == IntentType.TARGET_VALIDATION
    assert "KRAS" in decision.extracted_genes
    assert "Pancreatic Ductal Adenocarcinoma" in decision.extracted_diseases
