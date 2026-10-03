# Spec 12: Vertex AI Agent Engine Live Observability, Native Memory Bank, Distributed Tracing & Evaluation Bench

## 1. Objective
Achieve 100% telemetry, trace, session, memory, and evaluation population in the Google Cloud Agent Platform Console for `cancer-co-scientist-graph-agent` (Engine ID: `4359942935643422720`, Location: `us-east1`, Project: `fivedaysai-prd-sandbox-317383`).

## 2. Architectural Remediation Modules

### Module 1: OpenTelemetry Standard GenAI Semantic Conventions (`packages/graphagent/observability/telemetry.py`)
- Upgrade OpenTelemetry instrumentation to conform strictly to ADK >= v2.6.0 GenAI conventions.
- Configure `CloudTraceSpanExporter` with mandatory resource attributes:
  - `gcp.resource_type`: `"aiplatform.googleapis.com/ReasoningEngine"`
  - `aiplatform.googleapis.com/reasoning_engine_id`: `"4359942935643422720"`
  - `service.name`: `"cancer-co-scientist-graph-agent"`
  - `cloud.region`: `"us-east1"`
  - `gcp.project_id`: `"fivedaysai-prd-sandbox-317383"`
- Replace custom metric names with canonical OTel GenAI metrics:
  - `gen_ai.client.token.usage` (attributes: `gen_ai.token.type`, `gen_ai.response.model`)
  - `gen_ai.client.operation.duration` (attributes: `gen_ai.operation.name`, `gen_ai.request.model`)
  - `gen_ai.server.request.duration` (attributes: `http.response.status_code`)
- Ensure every tool method in `packages/graphagent/tools/algorithms.py` and `deploy/scripts/deploy_dual_gea_agents.py` is wrapped with `@trace_tool` to emit child spans (`gen_ai.tool.name`) linked to the active trace context.

### Module 2: Native Vertex AI Agent Engine Memory Bank Bridge (`apps/co-scientist/agent/memory_bank.py`)
- Implement dual-write architecture:
  1. Internal Cloud Spanner tables for relational graph persistence.
  2. Native GCP Agent Engine Memory Bank REST/gRPC API:
     - Endpoint: `https://us-east1-aiplatform.googleapis.com/v1beta1/projects/301802433103/locations/us-east1/agentEngines/4359942935643422720/memories`
     - Methods: `create_memory`, `list_memories`, `generate_memories`.
- When consolidating clinical entities (e.g. EGFR T790M, Osimertinib, PI3K-AKT-mTOR), automatically invoke `create_memory(fact=..., scope=...)` so records appear in the Memories tab.

### Module 3: Distributed Trace Context Propagation (`apps/co-scientist/agent/a2a_client.py`)
- Inject W3C `traceparent` and `tracestate` headers into all A2A inter-agent delegations and Reasoning Engine REST calls.
- This creates the linked span DAG required by the **Topology** tab to draw edges connecting `cancer-co-scientist-lead-orchestrator` -> `cancer-co-scientist-graph-agent` -> `SpannerGraph` -> `BigQuery`.

### Module 4: Live Vertex AI Evaluation Bench (`packages/graphagent/evals/run_vertex_eval_bench.py`)
- Replace the local-only evaluation reporter with native Vertex AI `EvaluationRun` / `EvalTask`:
  - Utilize `google.cloud.aiplatform.v1beta1.EvaluationServiceClient`.
  - Create registered experiments under `cancer-co-scientist-graph-agent-evals`.
  - Log standard evaluation metrics: `algorithm_choice_accuracy`, `retrieval_map`, `groundedness`, `latency_p95`.
- This ensures the **Evaluation** tab (Screenshot 8) displays live experiment rows, status, and comparative benchmarks.

### Module 5: End-to-End Live Multi-Turn Benchmark Suite (`packages/graphagent/evals/benchmark_live_suite.py`)
- Create a new production benchmark runner:
  - Iterates through the 15-case precision oncology golden dataset.
  - Reuses existing active sessions (`8521266242554691584`, `7845726298449117184`, etc.) and creates structured multi-turn sessions (turns >= 3).
  - Invokes the live Vertex AI Agent Engine via authenticated REST/gRPC using Google Cloud ADC.
  - Validates non-zero telemetry emission across all 7 GCP Console tabs.