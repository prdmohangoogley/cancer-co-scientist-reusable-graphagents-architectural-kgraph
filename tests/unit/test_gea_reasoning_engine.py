"""Tests for Gemini Enterprise Agents (GEA) integration & Vertex AI Reasoning Engine.

Tests:
1. GET /api/gea/schema OpenAPI 3.0 specification endpoint.
2. POST /api/gea/invoke direct execution endpoint with trajectory.
3. CancerCoScientistReasoningEngine query and explore_primekg methods.
4. Non-regression of existing web app and A2UI endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from agent.orchestrator import app
from agent.reasoning_engine import CancerCoScientistReasoningEngine


@pytest.fixture
def client():
    return TestClient(app)


def test_gea_schema_endpoint(client):
    """Verify OpenAPI 3.0 schema generation for Vertex AI Agent Builder."""
    response = client.get("/api/gea/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["openapi"] == "3.0.0"
    assert "/api/gea/invoke" in data["paths"]
    assert "/api/primekg/explore" in data["paths"]
    
    invoke_op = data["paths"]["/api/gea/invoke"]["post"]
    assert invoke_op["operationId"] == "invokeClinicalAgent"
    assert "query" in invoke_op["requestBody"]["content"]["application/json"]["schema"]["properties"]


def test_gea_invoke_endpoint(client):
    """Verify direct GEA invocation without manual Bearer token handshake."""
    payload = {
        "query": "What are resistance mechanisms for EGFR T790M?",
        "session_id": "test_gea_session_01",
        "user_id": "dr_oncologist",
        "roles": ["clinician"],
        "include_trajectory": True,
    }
    response = client.post("/api/gea/invoke", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "narrative" in data
    assert "selected_algorithm" in data
    assert "a2ui_surface" in data
    assert data["a2ui_surface"]["type"] == "A2UI_SURFACE"
    
    # Verify reasoning trajectory
    assert "trajectory" in data
    assert len(data["trajectory"]) >= 4
    step_actions = [step["action"] for step in data["trajectory"]]
    assert any("Intent Classification" in a for a in step_actions)
    assert any("Graph Worker Traversal" in a for a in step_actions)
    assert any("A2UI" in a for a in step_actions)

    # Verify direct web app dashboard links for GEA
    assert "direct_links" in data
    assert "web_app_dashboard" in data["direct_links"]
    assert "primekg_explorer" in data["direct_links"]
    assert "observability_hud" in data["direct_links"]
    assert "Direct Web App & Dashboard Actions" in data["narrative"]


def test_reasoning_engine_adapter():
    """Verify CancerCoScientistReasoningEngine conforms to Vertex AI interface."""
    engine = CancerCoScientistReasoningEngine()
    engine.set_up()
    
    # Test query
    result = engine.query(
        query="Identify drug repurposing candidates for EGFR mutation in NSCLC",
        session_id="gea_unit_session",
    )
    assert result["type"] == "A2UI_SURFACE"
    assert "components" in result
    assert len(result["components"]) > 0

    # Test explore_primekg
    primekg_vis = engine.explore_primekg(focal_entity="EGFR", depth=2)
    assert primekg_vis["type"] == "A2UI_SURFACE"
    assert any(c["component"] == "InteractiveGraphExplorer" for c in primekg_vis["components"])

    # Test telemetry
    stats = engine.get_telemetry()
    assert "latency_ms" in stats
    assert "token_consumption" in stats


def test_existing_endpoints_unaffected(client):
    """Verify that adding GEA endpoints does not affect existing endpoints."""
    # Health / Telemetry
    resp_telemetry = client.get("/api/stats/telemetry")
    assert resp_telemetry.status_code == 200
    
    # PrimeKG explore
    resp_explore = client.get("/api/primekg/explore?focal_entity=EGFR&depth=2")
    assert resp_explore.status_code == 200
    assert resp_explore.json()["type"] == "A2UI_SURFACE"

    # Static UI root
    resp_ui = client.get("/")
    assert resp_ui.status_code == 200
    assert "text/html" in resp_ui.headers["content-type"]
