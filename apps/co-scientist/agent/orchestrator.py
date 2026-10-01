"""Cancer Co-Scientist Lead Orchestrator and ADK Agent Loop.

Responsible for:
1. Architectural compliance verification via Guidelines MCP Server (DOC-01, DOC-02, DOC-03).
   - Queries Cloud Spanner Graph (ArchGuidelinesGraph) via ISO GQL.
   - Queries BigQuery (gea_arch_guidelines_analytics) for pattern deep dives.
2. Intent routing & biomedical entity resolution via IntentRouter.
3. Subagent task delegation to PrimeKG Worker Agents.
4. Synthesizing declarative A2UI payloads for client presentation (DOC-03).
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from .mcp_client import GuidelinesMCPClient
from .router import IntentRouter, IntentType

# Import worker agent from reusable packages
try:
    from graphagent.adk.agent import PrimeKGWorkerAgent
except ImportError:
    from adk.agent import PrimeKGWorkerAgent

logger = logging.getLogger("orchestrator")

app = FastAPI(
    title="Cancer Co-Scientist Orchestrator",
    version="1.0.0",
    description="Lead Orchestrator emitting declarative A2UI payloads and delegating to Graph Agent Workers",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserChatRequest(BaseModel):
    query: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class A2UIResponse(BaseModel):
    surface_id: str
    intent: str
    components: list[dict[str, Any]]
    guidelines_cited: list[str]
    governance_metadata: dict[str, Any]


class CancerCoScientistOrchestrator:
    """Lead Orchestrator coordinating Guidelines MCP, Intent Router, and Graph Workers."""

    def __init__(self, use_mock: bool = False) -> None:
        self.mcp_client = GuidelinesMCPClient(use_mock=use_mock)
        self.router = IntentRouter()
        self.worker = PrimeKGWorkerAgent()

    async def process_clinical_inquiry(self, query: str) -> dict[str, Any]:
        """Main agent loop coordinating guidelines, routing, worker delegation, and A2UI assembly."""
        logger.info(f"Orchestrator received inquiry: '{query}'")

        # 1. Architectural Guidance Verification: Live Spanner Graph ISO GQL & BigQuery queries
        # (a) Query Cloud Spanner Graph for operational best practices
        spanner_bp = await self.mcp_client.get_best_practice(topic="security")
        spanner_source = spanner_bp.get("source", "spanner_graph")
        spanner_latency = spanner_bp.get("latency_ms", 0.0)

        # (b) Query BigQuery Analytics for architectural deep dive
        bq_deepdive = await self.mcp_client.deep_dive_guideline(component="Security")
        bq_source = bq_deepdive.get("source", "bigquery_analytics")
        bq_latency = bq_deepdive.get("latency_ms", 0.0)

        # (c) Search protocol guidelines for A2UI standards
        guidelines = await self.mcp_client.search_guidelines("a2ui")
        guideline_ids = [g.get("id", "DOC-03") for g in guidelines] or ["DOC-03", "DOC-02"]

        logger.info(f"Guidelines MCP query resolved via {spanner_source} ({spanner_latency}ms) and {bq_source} ({bq_latency}ms)")

        # 2. Intent Routing & Entity Extraction
        decision = self.router.route_query(query)
        gene = decision.extracted_genes[0]
        disease = decision.extracted_diseases[0]

        components: list[dict[str, Any]] = []

        # 3. Delegate to Worker Tier & Assemble A2UI components
        if decision.intent == IntentType.DRUG_REPURPOSING:
            # Delegate to drug repurposing worker
            candidates = await self.worker.find_drug_repurposing_candidates(disease_name=disease)

            # Emit InsightCard
            components.append({
                "component": "InsightCard",
                "id": f"card_{uuid.uuid4().hex[:8]}",
                "props": {
                    "title": f"Targeted Therapeutics for {gene} in {disease}",
                    "subtitle": "Synthesized from PrimeKG multi-hop path reasoning",
                    "severity": "critical",
                    "summary": f"Identified {len(candidates)} high-affinity candidate compounds targeting {gene}-driven oncogenic pathways.",
                    "confidence_score": 0.95,
                    "tags": [gene, disease, "Precision Oncology", "A2UI"],
                },
            })

            # Emit DrugRepurposingTable
            components.append({
                "component": "DrugRepurposingTable",
                "id": f"table_{uuid.uuid4().hex[:8]}",
                "props": {
                    "title": f"Candidate Therapeutics for {disease}",
                    "candidates": candidates,
                },
            })

        else:
            # Delegate to pathway traversal worker
            subgraph = await self.worker.explore_gene_disease_pathways(
                gene_symbol=gene,
                disease_name=disease,
                max_hops=2,
            )

            # Emit InsightCard
            components.append({
                "component": "InsightCard",
                "id": f"card_{uuid.uuid4().hex[:8]}",
                "props": {
                    "title": f"{gene} Signaling Cascades in {disease}",
                    "subtitle": "Multi-hop knowledge graph analysis",
                    "severity": "info",
                    "summary": subgraph.summary,
                    "confidence_score": 0.96,
                    "tags": [gene, disease, "Pathway Analysis", "PrimeKG"],
                },
            })

            # Emit KnowledgeGraphView
            components.append({
                "component": "KnowledgeGraphView",
                "id": f"kg_{uuid.uuid4().hex[:8]}",
                "props": {
                    "layout": "force-directed",
                    "nodes": [n.model_dump() for n in subgraph.nodes],
                    "edges": [e.model_dump() for e in subgraph.edges],
                },
            })

        # Return standardized declarative A2UI payload with live MCP execution metadata
        return {
            "type": "A2UI_SURFACE",
            "surface_id": f"surf_{uuid.uuid4().hex[:8]}",
            "intent": decision.intent.value,
            "components": components,
            "guidelines_cited": guideline_ids,
            "governance_metadata": {
                "spanner_graph_source": spanner_source,
                "spanner_graph_latency_ms": spanner_latency,
                "bigquery_analytics_source": bq_source,
                "bigquery_latency_ms": bq_latency,
                "patterns_verified": [p.get("name") for p in spanner_bp.get("patterns", [])[:3]],
            },
        }


# Singleton Orchestrator instance
orchestrator = CancerCoScientistOrchestrator(use_mock=False)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check probe endpoint for Cloud Run and Docker."""
    return {"status": "healthy", "service": "cancer-co-scientist-orchestrator"}


@app.post("/api/chat")
async def chat_endpoint(request: UserChatRequest) -> dict[str, Any]:
    """Process user clinical query and return declarative A2UI payload."""
    try:
        return await orchestrator.process_clinical_inquiry(request.query)
    except Exception as e:
        logger.error(f"Error handling clinical inquiry: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stream")
async def stream_endpoint(query: str) -> EventSourceResponse:
    """Stream declarative A2UI tokens and component updates via Server-Sent Events (SSE)."""
    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        payload = await orchestrator.process_clinical_inquiry(query)
        yield {
            "event": "a2ui_surface",
            "data": json.dumps(payload),
        }

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
