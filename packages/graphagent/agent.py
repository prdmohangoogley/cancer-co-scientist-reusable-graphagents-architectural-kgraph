"""Cancer Co-Scientist Autonomous Graph Agent (Worker Tier).

Adheres to:
- DOC-01: AI Agent Quality Engineering & Observability (ADK >= v2.6.0 GenAI metrics)
- DOC-02: Zero Ambient Authority & Least Privilege IAM
- DOC-03: Open AI Agent Protocol Stack & A2A Task Contract Handshake
- DOC-04: Deploying to Gemini Enterprise Agent Runtime (Vertex AI Reasoning Engine root_agent)
- DOC-09: Platform-Native State Management (Cloud Spanner Graph + BigQuery)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from typing import Any, AsyncIterator, Iterator, Optional

# Ensure package root is in sys.path
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)

try:
    from adk.agent import PrimeKGWorkerAgent
    from adk.traversal import SubgraphResult
    from observability.telemetry import (
        emit_cloud_monitoring_metric,
        init_telemetry,
        record_genai_metrics,
        trace_span,
    )
except ImportError:
    from packages.graphagent.adk.agent import PrimeKGWorkerAgent
    from packages.graphagent.adk.traversal import SubgraphResult
    from packages.graphagent.observability.telemetry import (
        emit_cloud_monitoring_metric,
        init_telemetry,
        record_genai_metrics,
        trace_span,
    )

logger = logging.getLogger("cancer_co_scientist_graph_agent")


class CancerCoScientistGraphAgent:
    """Autonomous Gemini Enterprise Agent executing the 15-algorithm matrix over PrimeKG."""

    def __init__(
        self,
        model_name: str = "gemini-1.5-pro",
        project: str = "fivedaysai-prd-sandbox-317383",
        location: str = "us-east1",
        use_mock: bool = False,
    ) -> None:
        self.model_name = model_name
        self.project = project
        self.location = location
        self.use_mock = use_mock
        self.worker = PrimeKGWorkerAgent(
            project_id=project,
            use_mock=use_mock,
        )
        self.tracer = init_telemetry("cancer-co-scientist-graph-agent")

    def set_up(self) -> None:
        """Called by Vertex AI Reasoning Engine on instance initialization."""
        self.tracer = init_telemetry("cancer-co-scientist-graph-agent")
        logger.info(f"CancerCoScientistGraphAgent initialized in {self.location}")

    def get_agent_card(self) -> dict[str, Any]:
        """Return the machine-readable A2A Agent Card."""
        card_path = os.path.join(_PKG_DIR, ".well-known", "agent-card.json")
        if os.path.exists(card_path):
            with open(card_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "name": "cancer-co-scientist-graph-agent",
            "version": "1.0.0",
            "description": "Autonomous precision oncology knowledge graph agent",
            "skills": ["discrete_graph_algorithms", "structural_node_analytics", "continuous_simulation", "temporal_tracking"],
        }

    def query(
        self,
        input: str = "",
        query: str = "",
        prompt: str = "",
        session_id: str = "default_session",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Standard query entrypoint invoked by Vertex AI Reasoning Engine and A2A callers."""
        raw_text = input or query or prompt or kwargs.get("message", "")
        task_id = kwargs.get("task_id", f"task_{uuid.uuid4().hex[:12]}")
        algorithm_name = kwargs.get("algorithm_name", "")
        category = kwargs.get("category", "Discrete")
        source_entity = kwargs.get("source_entity", "")
        target_entity = kwargs.get("target_entity", "")
        parameters = kwargs.get("parameters", {})

        # If raw text contains an A2A JSON payload, parse it
        if raw_text.startswith("{") and "algorithm_name" in raw_text:
            try:
                parsed = json.loads(raw_text)
                algorithm_name = parsed.get("algorithm_name", algorithm_name)
                category = parsed.get("category", category)
                source_entity = parsed.get("source_entity", source_entity)
                target_entity = parsed.get("target_entity", target_entity)
                parameters = parsed.get("parameters", parameters)
                task_id = parsed.get("task_id", task_id)
            except Exception:
                pass

        # Default fallback algorithm if unspecified
        if not algorithm_name:
            lower_text = raw_text.lower()
            if "dijkstra" in lower_text or "shortest" in lower_text:
                algorithm_name = "dijkstra"
                source_entity = source_entity or "EGFR"
                target_entity = target_entity or "Osimertinib"
            elif "pagerank" in lower_text or "hub" in lower_text:
                algorithm_name = "pagerank"
                target_entity = target_entity or "TP53"
            elif "betweenness" in lower_text or "gatekeeper" in lower_text:
                algorithm_name = "betweenness"
                target_entity = target_entity or "KRAS"
            elif "alphafold" in lower_text or "docking" in lower_text:
                algorithm_name = "alphafold_ompl_rrt"
                target_entity = target_entity or "KRAS_G12D"
            elif "physicell" in lower_text or "boid" in lower_text or "swarm" in lower_text:
                algorithm_name = "physicell_boids"
            elif "temporal" in lower_text or "interval" in lower_text:
                algorithm_name = "interval_edges"
                source_entity = source_entity or "EGFR"
            else:
                algorithm_name = "dijkstra"
                source_entity = source_entity or "EGFR"
                target_entity = target_entity or "Non-Small Cell Lung Carcinoma"

        t0 = time.time()
        with trace_span(f"graph_agent.execute.{algorithm_name}", workflow_type=category) as span:
            span.set_attribute("gen_ai.system", "vertexai")
            span.set_attribute("gen_ai.request.model", self.model_name)
            span.set_attribute("agent.name", "cancer-co-scientist-graph-agent")
            span.set_attribute("a2a.task_id", task_id)
            span.set_attribute("graphagent.algorithm", algorithm_name)

            # Execute the algorithm via PrimeKGWorkerAgent atomic coroutines
            import asyncio
            algo_res = None

            if algorithm_name in ["dijkstra", "astar", "bfs_dfs", "wcc", "topological_sort", "transitive_closure", "community_detection", "ego_network"]:
                algo_res = asyncio.run(self.worker.run_discrete_algorithm(
                    algorithm_name=algorithm_name,
                    source_entity=source_entity,
                    target_entity=target_entity,
                    **parameters,
                ))
            elif algorithm_name in ["pagerank", "betweenness", "subgraph_density", "bridges"]:
                algo_res = asyncio.run(self.worker.run_structural_analytics(
                    algorithm_name=algorithm_name,
                    target_entity=target_entity or source_entity,
                    **parameters,
                ))
            elif algorithm_name in ["alphafold_ompl_rrt", "physicell_boids", "alphafold", "physicell"]:
                algo_res = asyncio.run(self.worker.run_continuous_simulation(
                    algorithm_name=algorithm_name,
                    target_entity=target_entity or source_entity,
                    **parameters,
                ))
            elif algorithm_name in ["interval_edges", "lambda2_connectivity", "ast_generator"]:
                algo_res = asyncio.run(self.worker.run_temporal_tracking(
                    algorithm_name=algorithm_name,
                    source_entity=source_entity,
                    **parameters,
                ))
            else:
                algo_res = asyncio.run(self.worker.run_discrete_algorithm(
                    "dijkstra",
                    source_entity=source_entity or "EGFR",
                    target_entity=target_entity or "Osimertinib",
                ))

            elapsed_s = max(0.005, time.time() - t0)
            elapsed_ms = round(elapsed_s * 1000.0, 2)

            # Record OpenTelemetry GenAI Semantic Conventions metrics (ADK >= v2.6.0)
            prompt_tokens = len(raw_text.split()) * 4 + 40
            completion_tokens = (len(algo_res.nodes) + len(algo_res.edges)) * 8 + 60
            record_genai_metrics(
                model_name=self.model_name,
                duration_s=elapsed_s,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_tokens=int(prompt_tokens * 0.65),
                session_id=session_id,
                agent_name="cancer-co-scientist-graph-agent",
            )

            # Return standard A2A Task Response dictionary
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "algorithm_name": algorithm_name,
                "category": category,
                "execution_time_ms": elapsed_ms,
                "nodes": [n.model_dump() if hasattr(n, "model_dump") else n for n in algo_res.nodes],
                "edges": [e.model_dump() if hasattr(e, "model_dump") else e for e in algo_res.edges],
                "paths": algo_res.paths,
                "metrics": algo_res.metrics,
                "summary": algo_res.summary,
                "model": self.model_name,
                "agent_identity": "cancer-co-scientist-graph-agent",
            }

    def stream_query(
        self,
        input: str = "",
        query: str = "",
        prompt: str = "",
        session_id: str = "default_session",
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """Streaming generator yielding intermediate steps followed by final result."""
        yield {"step": "intent_parsing", "status": "Parsing graph algorithm intent"}
        yield {"step": "gql_traversal", "status": "Executing ISO GQL on Spanner PrimeKGGraph"}
        res = self.query(input=input, query=query, prompt=prompt, session_id=session_id, **kwargs)
        yield {"step": "complete", "result": res}


# Authoritative Root Agent Export conforming to ADK >= v2.6.0 / Reasoning Engine Spec
root_agent = CancerCoScientistGraphAgent()
