"""Comprehensive unit tests for Cancer Co-Scientist Lead Orchestrator endpoints (DOC-01, DOC-02, DOC-03, DOC-08, DOC-09)."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

# Add apps/co-scientist to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "co-scientist"))

from agent.orchestrator import app, orchestrator


@pytest.fixture(autouse=True)
def setup_mock_orchestrator():
    """Ensure mock mode is active for offline testing."""
    orchestrator.mcp_client.use_mock = True
    orchestrator.memory_bank.use_mock = True


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Verify health probe returns status healthy."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "cancer-co-scientist-orchestrator"


@pytest.mark.asyncio
async def test_auth_login_and_me():
    """Verify user login returns JWT token and me endpoint returns profile."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login with default clinician
        login_res = await ac.post(
            "/api/auth/login",
            json={"email": "clinician@cancercenter.org", "password": "clinician123!"},
        )
        assert login_res.status_code == 200
        token_data = login_res.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        token = token_data["access_token"]

        # 2. Get profile with Bearer token
        headers = {"Authorization": f"Bearer {token}"}
        me_res = await ac.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        profile = me_res.json()
        assert profile["email"] == "clinician@cancercenter.org"
        assert "clinician" in profile["roles"]

        # 3. Unauthenticated request to /api/auth/me should fail with 401
        unauth_res = await ac.get("/api/auth/me")
        assert unauth_res.status_code == 401


@pytest.mark.asyncio
async def test_auth_register_flow():
    """Verify user registration and authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg_res = await ac.post(
            "/api/auth/register",
            json={
                "email": "sarah.walker@cancercenter.org",
                "password": "walkerPassword123!",
                "full_name": "Dr. Sarah Walker",
                "roles": ["researcher"],
            },
        )
        assert reg_res.status_code == 200
        data = reg_res.json()
        assert "access_token" in data
        assert data["user"]["email"] == "sarah.walker@cancercenter.org"
        assert "researcher" in data["user"]["roles"]


@pytest.mark.asyncio
async def test_sessions_lifecycle_endpoints():
    """Verify session creation, listing, message retrieval, and memory snapshot."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Login
        login_res = await ac.post(
            "/api/auth/login",
            json={"email": "clinician@cancercenter.org", "password": "clinician123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create session
        create_res = await ac.post(
            "/api/sessions",
            headers=headers,
            json={"title": "EGFR Clinical Evaluation", "metadata": {"stage": "IV"}},
        )
        assert create_res.status_code == 200
        session_data = create_res.json()
        sid = session_data["session_id"]
        assert session_data["title"] == "EGFR Clinical Evaluation"

        # List sessions
        list_res = await ac.get("/api/sessions", headers=headers)
        assert list_res.status_code == 200
        sessions = list_res.json()
        assert any(s["session_id"] == sid for s in sessions)

        # Get messages (initially empty)
        msgs_res = await ac.get(f"/api/sessions/{sid}/messages", headers=headers)
        assert msgs_res.status_code == 200
        assert isinstance(msgs_res.json(), list)

        # Get memory (initially empty)
        mem_res = await ac.get(f"/api/sessions/{sid}/memory", headers=headers)
        assert mem_res.status_code == 200
        mem = mem_res.json()
        assert mem["session_id"] == sid
        assert "entities" in mem
        assert "hypotheses" in mem


@pytest.mark.asyncio
async def test_chat_endpoint_full_cycle():
    """Verify chat endpoint requires auth, routes query, consolidates facts, and returns A2UI."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Unauthenticated request rejected
        unauth_chat = await ac.post(
            "/api/chat",
            json={"query": "What drugs target EGFR T790M in lung cancer?"},
        )
        assert unauth_chat.status_code == 401

        # 2. Login to get token
        login_res = await ac.post(
            "/api/auth/login",
            json={"email": "clinician@cancercenter.org", "password": "clinician123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create a session
        create_res = await ac.post(
            "/api/sessions",
            headers=headers,
            json={"title": "Turn 1 Clinical Inquiry"},
        )
        sid = create_res.json()["session_id"]

        # 4. Turn 1: Clinical Drug Repurposing Query
        chat_res = await ac.post(
            "/api/chat",
            headers=headers,
            json={
                "query": "What repurposed drugs or inhibitors target EGFR T790M resistance in lung cancer?",
                "session_id": sid,
            },
        )
        assert chat_res.status_code == 200
        payload = chat_res.json()
        assert payload["type"] == "A2UI_SURFACE"
        assert payload["intent"] == "DRUG_REPURPOSING"
        assert payload["recommended_algorithm"] == "Dijkstra"
        assert len(payload["components"]) >= 2
        comp_types = [c["component"] for c in payload["components"]]
        assert "InsightCard" in comp_types
        assert "DrugRepurposingTable" in comp_types
        assert "governance_metadata" in payload

        # 5. Check session messages updated
        msgs_res = await ac.get(f"/api/sessions/{sid}/messages", headers=headers)
        messages = msgs_res.json()
        assert len(messages) >= 2  # user + assistant

        # 6. Check Memory Bank consolidation
        mem_res = await ac.get(f"/api/sessions/{sid}/memory", headers=headers)
        memory = mem_res.json()
        assert memory["entity_count"] > 0
        entity_names = [e["entity_name"] for e in memory["entities"]]
        assert any("EGFR" in name for name in entity_names)

        # 7. Turn 2: Query benefiting from progressive semantic recall
        chat_res_2 = await ac.post(
            "/api/chat",
            headers=headers,
            json={
                "query": "What is the binding affinity and pathway mechanism for Osimertinib?",
                "session_id": sid,
            },
        )
        assert chat_res_2.status_code == 200
        payload2 = chat_res_2.json()
        recalled = payload2["governance_metadata"].get("recalled_memory_entities", [])
        assert any("Osimertinib" in name or "EGFR" in name for name in recalled)


@pytest.mark.asyncio
async def test_continuous_simulation_chat():
    """Verify continuous simulation queries route to OMPL RRT* and generate SimulationViewer."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post(
            "/api/auth/login",
            json={"email": "researcher@cancercenter.org", "password": "researcher123!"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        chat_res = await ac.post(
            "/api/chat",
            headers=headers,
            json={"query": "Generate AlphaFold ligand binding conformation docking trajectory with OMPL RRT* for EGFR"},
        )
        assert chat_res.status_code == 200
        payload = chat_res.json()
        assert payload["intent"] == "CONTINUOUS_SIMULATION"
        assert payload["recommended_algorithm"] == "Continuous_AlphaFold_OMPL_RRT"
        comp_types = [c["component"] for c in payload["components"]]
        assert "SimulationViewer" in comp_types


@pytest.mark.asyncio
async def test_telemetry_endpoint():
    """Verify telemetry returns live latency percentiles, token usage, and quality scores."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/stats/telemetry")
        assert res.status_code == 200
        stats = res.json()
        assert stats["status"] == "healthy"
        assert "p50" in stats["latency_ms"]
        assert "p95" in stats["latency_ms"]
        assert "p99" in stats["latency_ms"]
        assert stats["latency_ms"]["p50"] > 0
        assert stats["token_consumption"]["prompt_tokens"] > 0
        assert stats["token_consumption"]["cached_tokens"] > 0
        assert stats["token_consumption"]["cache_hit_rate"] > 0.40
        assert stats["quality_metrics"]["retrieval_map"] >= 0.82
