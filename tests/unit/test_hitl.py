"""Unit tests for Human-in-the-Loop (HITL) Gatekeeper (DOC-02, DOC-03, Spec 15 §3)."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

# Add apps/co-scientist to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "co-scientist"))

from agent.hitl import (
    ActionType,
    ApprovalStatus,
    ClinicalAction,
    ClinicalActionApprovalManager,
    RiskLevel,
    clinical_approval_manager,
)
from agent.orchestrator import app, orchestrator
from agent.auth import UserProfile, create_access_token


@pytest.fixture(autouse=True)
def setup_mock_orchestrator():
    orchestrator.mcp_client.use_mock = True
    orchestrator.memory_bank.use_mock = True


@pytest.fixture
def auth_headers():
    user = UserProfile(
        user_id="dr_test_oncologist",
        email="dr_test@cancercenter.org",
        full_name="Dr. Test Oncologist",
        roles=["clinician"],
        tenant_id="mskcc_oncology",
    )
    token = create_access_token(user)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def test_hitl_manager_lifecycle():
    mgr = ClinicalActionApprovalManager()
    action = mgr.create_action(
        action_type=ActionType.OFF_LABEL_THERAPY_RECOMMENDATION.value,
        proposed_action="Administer Osimertinib + Savolitinib for MET amplification",
        clinical_rationale="Overcomes acquired resistance identified via multi-hop traversal",
        risk_level=RiskLevel.HIGH.value,
        session_id="test-session-123",
        parameters={"drug_a": "Osimertinib", "drug_b": "Savolitinib"},
    )

    assert action.action_id.startswith("act-")
    assert action.status == ApprovalStatus.PENDING
    assert action.session_id == "test-session-123"

    # Verify listing
    pending = mgr.list_pending("test-session-123")
    assert len(pending) == 1
    assert pending[0].action_id == action.action_id

    # Verify retrieval
    retrieved = mgr.get_action(action.action_id)
    assert retrieved is not None
    assert retrieved.action_id == action.action_id

    # Verify approval
    approved = mgr.approve_action(
        action_id=action.action_id,
        reviewer_id="reviewer@cancercenter.org",
        comments="Approved based on TATTON trial evidence",
    )
    assert approved.status == ApprovalStatus.APPROVED
    assert approved.reviewer_id == "reviewer@cancercenter.org"
    assert approved.resolved_at is not None

    # Cannot approve again
    with pytest.raises(ValueError):
        mgr.approve_action(action.action_id)


def test_hitl_manager_rejection():
    mgr = ClinicalActionApprovalManager()
    action = mgr.create_action(
        action_type=ActionType.HIGH_TOXICITY_REGIMEN_MODIFICATION.value,
        proposed_action="Triple combination with high hepatotoxicity risk",
        clinical_rationale="Experimental aggressive therapy",
        risk_level=RiskLevel.CRITICAL.value,
        session_id="test-session-456",
    )

    rejected = mgr.reject_action(
        action_id=action.action_id,
        reviewer_id="reviewer@cancercenter.org",
        comments="Excessive toxicity risk for frail patient",
    )
    assert rejected.status == ApprovalStatus.REJECTED
    assert rejected.reviewer_comments == "Excessive toxicity risk for frail patient"


def test_hitl_manager_expiration():
    mgr = ClinicalActionApprovalManager()
    action = mgr.create_action(
        action_type=ActionType.EXPENSIVE_CLUSTER_SIMULATION.value,
        proposed_action="100,000-cell 48-hour PhysiCell simulation",
        clinical_rationale="Tissue microenvironment modeling",
        session_id="test-session-789",
        expires_in_minutes=-1,  # Already expired
    )

    assert action.is_expired() is True
    pending = mgr.list_pending("test-session-789")
    assert len(pending) == 0

    with pytest.raises(ValueError, match="(?i)expired"):
        mgr.approve_action(action.action_id)


def test_hitl_a2ui_card_schema():
    mgr = ClinicalActionApprovalManager()
    action = mgr.create_action(
        action_type=ActionType.EXPERIMENTAL_CLINICAL_TRIAL_ENROLLMENT.value,
        proposed_action="Enroll patient in Phase 1 NCT04849203 investigational trial",
        clinical_rationale="Matches rare variant BRAF non-V600",
        risk_level=RiskLevel.HIGH.value,
        parameters={"nct_id": "NCT04849203"},
    )

    card = mgr.to_a2ui_card(action)
    assert card["type"] == "ConfirmationDialog"
    assert card["action_id"] == action.action_id
    assert card["risk_level"] == "HIGH"
    assert len(card["actions"]) == 2
    assert card["actions"][0]["action"] == "APPROVE"
    assert card["actions"][1]["action"] == "REJECT"


@pytest.mark.asyncio
async def test_hitl_api_endpoints(auth_headers):
    # Create action in singleton manager
    action = clinical_approval_manager.create_action(
        action_type=ActionType.OFF_LABEL_THERAPY_RECOMMENDATION.value,
        proposed_action="Test API therapy recommendation",
        clinical_rationale="API integration test rationale",
        session_id="sess_api_test",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. GET /api/actions/pending
        res = await client.get("/api/actions/pending?session_id=sess_api_test", headers=auth_headers)
        assert res.status_code == 200
        pending_list = res.json()
        assert any(a["action_id"] == action.action_id for a in pending_list)

        # 2. GET /api/actions/{action_id}
        res_get = await client.get(f"/api/actions/{action.action_id}", headers=auth_headers)
        assert res_get.status_code == 200
        assert res_get.json()["action_id"] == action.action_id

        # 3. POST /api/actions/{action_id}/approve
        res_approve = await client.post(
            f"/api/actions/{action.action_id}/approve",
            headers=auth_headers,
            json={"comments": "Approved via automated unit test"},
        )
        assert res_approve.status_code == 200
        assert res_approve.json()["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_chat_endpoint_hitl_trigger(auth_headers):
    # Query with high-stakes trigger keyword ("off-label")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/chat",
            headers=auth_headers,
            json={
                "query": "Recommend off-label combination therapy for EGFR T790M and MET amplification",
                "session_id": "sess_hitl_chat_test",
            },
        )
        assert res.status_code == 200
        payload = res.json()
        components = payload.get("components", [])

        # Verify that ConfirmationDialog card is injected
        confirmation_components = [c for c in components if c.get("component") == "ConfirmationDialog"]
        assert len(confirmation_components) >= 1
        card_props = confirmation_components[0]["props"]
        assert "Confirmation Required" in card_props.get("title", "")
        assert card_props.get("risk_level") in ("HIGH", "CRITICAL")
