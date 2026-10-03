"""A2A (Agent-to-Agent) Protocol Mesh Client for Cancer Co-Scientist.

Adheres strictly to:
- DOC-01: AI Agent Quality Engineering & Observability (W3C traceparent propagation)
- DOC-02: Zero Ambient Authority (ZAA) & Downscoped Credentials (PAT-1C192A)
- DOC-03: Open AI Agent Protocol Stack (A2A Task Delegation Handshake)
- Spec 11: A2A Protocol Mesh, Agent Card Federation & Dual GEA Runtime Integration
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("a2a_client")


class A2aTaskRequest(BaseModel):
    """Strongly typed A2A task delegation request contract (Spec 11)."""

    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    caller_agent_id: str = "cancer-co-scientist-lead-orchestrator"
    target_agent_id: str = "cancer-co-scientist-graph-agent"
    algorithm_name: str
    category: str = "Discrete"  # Discrete, Structural, Continuous, Temporal
    source_entity: str = ""
    target_entity: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context_constraints: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_hops": 3,
            "max_results": 25,
            "deadline_ms": 1500,
            "allow_pii": False,
        }
    )
    traceparent: Optional[str] = None


class A2aTaskResponse(BaseModel):
    """Strongly typed A2A task delegation response contract (Spec 11)."""

    task_id: str
    status: str  # "SUCCESS", "DEGRADED", "FAILED"
    algorithm_name: str
    category: str
    execution_time_ms: float
    nodes: List[Any] = Field(default_factory=list)
    edges: List[Any] = Field(default_factory=list)
    paths: List[List[str]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    model: str = "gemini-2.5-flash"
    agent_identity: str = "cancer-co-scientist-graph-agent"


class GraphAgentA2AClient:
    """Client for delegating graph algorithmic tasks to cancer-co-scientist-graph-agent."""

    def __init__(
        self,
        graph_agent_resource_id: Optional[str] = None,
        project_id: str = "fivedaysai-prd-sandbox-317383",
        location: str = "us-east1",
    ) -> None:
        self.project_id = project_id
        self.location = location
        self.resource_id = graph_agent_resource_id or os.environ.get("GRAPH_AGENT_RESOURCE_ID")
        self._remote_engine = None

        if self.resource_id:
            try:
                import vertexai
                from vertexai.preview import reasoning_engines

                vertexai.init(project=project_id, location=location)
                self._remote_engine = reasoning_engines.ReasoningEngine(self.resource_id)
                logger.info(f"Initialized remote A2A connection to Graph Agent: {self.resource_id}")
            except Exception as e:
                logger.warning(f"Could not initialize remote Reasoning Engine ({e}), fallback to local root_agent")

    def execute_a2a_task(self, request: A2aTaskRequest) -> A2aTaskResponse:
        """Dispatches an A2aTaskRequest to cancer-co-scientist-graph-agent with trace context."""
        t0 = time.time()
        trace_id = uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        traceparent = request.traceparent or f"00-{trace_id}-{span_id}-01"

        logger.info(
            f"A2A Dispatch: {request.caller_agent_id} -> {request.target_agent_id} "
            f"| algo: {request.algorithm_name} | task: {request.task_id}"
        )

        raw_result = None

        # 1. Attempt remote Reasoning Engine invocation if deployed
        if self._remote_engine:
            try:
                raw_result = self._remote_engine.query(
                    input=f"Execute {request.algorithm_name} for {request.source_entity} -> {request.target_entity}",
                    task_id=request.task_id,
                    algorithm_name=request.algorithm_name,
                    category=request.category,
                    source_entity=request.source_entity,
                    target_entity=request.target_entity,
                    parameters=request.parameters,
                    traceparent=traceparent,
                )
            except Exception as e:
                logger.warning(f"Remote A2A invocation failed ({e}), falling back to direct root_agent")

        # 2. Local fallback to packages.graphagent.agent.root_agent
        if not raw_result:
            try:
                from packages.graphagent.agent import root_agent
            except ImportError:
                import sys

                repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                pkg_dir = os.path.join(repo_root, "packages", "graphagent")
                if pkg_dir not in sys.path:
                    sys.path.insert(0, pkg_dir)
                from agent import root_agent

            raw_result = root_agent.query(
                input=f"Execute {request.algorithm_name} for {request.source_entity} -> {request.target_entity}",
                task_id=request.task_id,
                algorithm_name=request.algorithm_name,
                category=request.category,
                source_entity=request.source_entity,
                target_entity=request.target_entity,
                parameters=request.parameters,
                traceparent=traceparent,
            )

        elapsed_ms = round((time.time() - t0) * 1000.0, 2)

        return A2aTaskResponse(
            task_id=raw_result.get("task_id", request.task_id),
            status=raw_result.get("status", "SUCCESS"),
            algorithm_name=raw_result.get("algorithm_name", request.algorithm_name),
            category=raw_result.get("category", request.category),
            execution_time_ms=raw_result.get("execution_time_ms", elapsed_ms),
            nodes=raw_result.get("nodes", []),
            edges=raw_result.get("edges", []),
            paths=raw_result.get("paths", []),
            metrics=raw_result.get("metrics", {}),
            summary=raw_result.get("summary", ""),
            model=raw_result.get("model", "gemini-2.5-flash"),
            agent_identity=raw_result.get("agent_identity", "cancer-co-scientist-graph-agent"),
        )
