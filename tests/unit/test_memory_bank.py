"""Unit tests for Enterprise Memory Bank and Session Persistence (PAT-MEM-BANK / DOC-08 / DOC-09)."""

from __future__ import annotations

import sys
from pathlib import Path

# Add apps/co-scientist to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "co-scientist"))

from agent.memory_bank import (
    ChatMessage,
    ChatSession,
    MemoryBankEngine,
    MemoryEntity,
    MemoryHypothesis,
)


def test_session_lifecycle():
    """Verify session creation, retrieval, and user filtering."""
    engine = MemoryBankEngine(use_mock=True)

    session = engine.create_session(
        user_id="usr_oncologist_101",
        title="EGFR Mutation Analysis",
        metadata={"patient_cohort": "Cohort_A"},
    )
    assert session.session_id is not None
    assert session.user_id == "usr_oncologist_101"
    assert session.title == "EGFR Mutation Analysis"
    assert session.metadata_json["patient_cohort"] == "Cohort_A"

    # Retrieve session
    retrieved = engine.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id

    # List sessions by user
    user_sessions = engine.list_sessions(user_id="usr_oncologist_101")
    assert len(user_sessions) >= 1
    assert user_sessions[0].session_id == session.session_id

    # Filter by different user
    empty_sessions = engine.list_sessions(user_id="usr_other_999")
    assert len(empty_sessions) == 0


def test_message_persistence_and_history():
    """Verify conversation turns are persisted and retrieved chronologically."""
    engine = MemoryBankEngine(use_mock=True)
    session = engine.create_session(user_id="usr_test_user")
    sid = session.session_id

    # User message
    msg_user = engine.save_message(
        session_id=sid,
        role="user",
        content="What treatments exist for EGFR T790M in lung cancer?",
        token_count=15,
    )
    assert msg_user.role == "user"
    assert msg_user.token_count == 15

    # Assistant message with A2UI payload
    a2ui_mock = {"type": "A2UI_SURFACE", "components": [{"component": "InsightCard"}]}
    msg_asst = engine.save_message(
        session_id=sid,
        role="assistant",
        content="Osimertinib is a third-generation TKI targeting EGFR T790M resistance.",
        a2ui_payload=a2ui_mock,
        token_count=25,
    )
    assert msg_asst.role == "assistant"
    assert msg_asst.a2ui_payload_json == a2ui_mock

    # Retrieve history
    history = engine.get_session_history(session_id=sid, limit=10)
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"


def test_clinical_entity_and_hypothesis_extraction():
    """Verify factual entity extraction across mutations, drugs, genes, diseases, and hypotheses."""
    engine = MemoryBankEngine(use_mock=True)
    session = engine.create_session(user_id="usr_clinician_42")
    sid = session.session_id

    user_query = "The patient presents with NSCLC harboring an EGFR T790M mutation and PD-L1 positivity."
    agent_response = (
        "We recommend initiating Osimertinib therapy. "
        "Osimertinib overcomes resistance conferred by EGFR T790M and exhibits synthetic lethality in vitro. "
        "Secondary analysis suggests MET amplification may emerge as an alternate escape mechanism."
    )

    entities, hypotheses = engine.extract_and_consolidate(
        session_id=sid,
        user_query=user_query,
        agent_response=agent_response,
    )

    # Verify extracted entities
    ent_names = [e.entity_name for e in entities]
    assert any("EGFR T790M" in name for name in ent_names)
    assert any("EGFR" in name for name in ent_names)
    assert any("Osimertinib" in name for name in ent_names)
    assert any("Non-small cell lung carcinoma" in name for name in ent_names)
    assert any("PD-L1" in name for name in ent_names)
    assert any("MET" in name for name in ent_names)

    # Verify extracted hypothesis
    assert len(hypotheses) >= 1
    hyp_statements = [h.statement for h in hypotheses]
    assert any("overcomes resistance" in s or "synthetic lethality" in s for s in hyp_statements)
    assert hypotheses[0].evidence_level == "Level_B"
    assert hypotheses[0].status == "formulated"

    # Verify de-duplication: extracting identical text again does not create duplicate entities
    entities_round2, _ = engine.extract_and_consolidate(
        session_id=sid,
        user_query=user_query,
        agent_response=agent_response,
    )
    assert len(entities_round2) == 0  # No duplicate entities added


def test_progressive_semantic_recall():
    """Verify progressive disclosure retrieves only relevant past entities for the inquiry."""
    engine = MemoryBankEngine(use_mock=True)
    session = engine.create_session(user_id="usr_clinician_77")
    sid = session.session_id

    # Seed Memory Bank with two separate clinical contexts
    engine.extract_and_consolidate(
        session_id=sid,
        user_query="Patient 1 has EGFR T790M in lung cancer treated with Osimertinib.",
        agent_response="Osimertinib successfully targets EGFR T790M.",
    )
    engine.extract_and_consolidate(
        session_id=sid,
        user_query="Patient 2 has BRAF V600E melanoma treated with Dabrafenib.",
        agent_response="Dabrafenib combined with Trametinib inhibits BRAF V600E signaling.",
    )

    # Query focusing specifically on EGFR and Osimertinib resistance
    egfr_recall = engine.semantic_recall(
        session_id=sid,
        current_query="What alternative inhibitors overcome Osimertinib resistance in EGFR?",
        top_k=3,
    )
    recalled_names = [e.entity_name for e in egfr_recall]

    # Should recall EGFR-related entities first
    assert any("EGFR" in name for name in recalled_names)
    assert any("Osimertinib" in name for name in recalled_names)

    # Top-K constraint respected
    assert len(egfr_recall) <= 3


def test_get_session_memory():
    """Verify complete snapshot retrieval of session memory bank."""
    engine = MemoryBankEngine(use_mock=True)
    session = engine.create_session(user_id="usr_audit")
    sid = session.session_id

    engine.extract_and_consolidate(
        session_id=sid,
        user_query="Investigating KRAS G12C in colorectal cancer.",
        agent_response="Sotorasib inhibits KRAS G12C activity.",
    )

    mem = engine.get_session_memory(sid)
    assert mem["session_id"] == sid
    assert mem["entity_count"] > 0
    assert len(mem["entities"]) == mem["entity_count"]
    assert "hypotheses" in mem
