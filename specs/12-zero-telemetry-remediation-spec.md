# Spec 12: Zero-Telemetry Remediation & Native Platform Operationalization

> **Author**: Antigravity  
> **Status**: Approved & Active  
> **Governing Standards**: DOC-01 (Observability & Evaluation), DOC-02 (ZAA), DOC-03 (Protocol Stack), DOC-08 (Memory Bank), DOC-09 (Native State)  
> **Target Environment**: `projects/fivedaysai-prd-sandbox-317383/locations/us-east1/reasoningEngines/4359942935643422720` (Graph Agent) & `6824256356745216000` (Lead Orchestrator)

---

## 1. Executive Summary & Root Cause Analysis

Initial observability inspections in the Google Cloud Vertex AI Agent Platform Console revealed zero metrics across telemetry graphs, model metrics, memories, and evaluation tabs. Deep-dive architectural analysis uncovered 5 root causes:

1. **Unbound Monitored Resource**: Custom metric emissions in `telemetry.py` used `resource.type = "global"` instead of the platform-mandated `aiplatform.googleapis.com/ReasoningEngine` with required labels (`resource_container`, `location`, `reasoning_engine_id`). As a result, Cloud Monitoring could not index the time series under the deployed Agent Engine instances.
2. **Missing OpenTelemetry Exporter Packaging**: The Reasoning Engine container image lacked `opentelemetry-exporter-gcp-trace` and `opentelemetry-exporter-gcp-monitoring` in `requirements.txt`, preventing in-process trace forwarding from tool spans.
3. **Decoupled Memory Bank**: `memory_bank.py` persisted clinical entities only to Cloud Spanner without synchronizing facts into the native Vertex AI Agent Engine Memory Bank service (`MemoryBankServiceClient`), leaving the console **Memories** tab unpopulated.
4. **Offline Evaluation Bench**: `run_vertex_eval_bench.py` evaluated models locally without recording experiments into the Vertex AI Evaluation API (`EvalTask` / `aiplatform.ExperimentRun`).
5. **Lack of Continuous Multi-Turn Live Traffic**: The Agent Engine observability dashboard relies on real-time invocation traces and function calls to populate its latency histograms, model token charts, and tool invocation counters.

---

## 2. Technical Remediation Plan

### Step 1: Telemetry Core Updates (`telemetry.py`)
- Bind Google Cloud Trace (`CloudTraceSpanExporter`) and Google Cloud Monitoring (`MetricServiceClient` / `CloudMonitoringMetricsExporter`) with exact GCP resource descriptor:
  - Resource Type: `aiplatform.googleapis.com/ReasoningEngine`
  - Labels:
    - `resource_container`: `projects/301802433103` (or `projects/fivedaysai-prd-sandbox-317383`)
    - `location`: `us-east1`
    - `reasoning_engine_id`: Deployed Agent Engine ID (`4359942935643422720` or `6824256356745216000`)
- Standardize all metric descriptors to OpenTelemetry GenAI v2.6.0 semantic conventions:
  - `gen_ai.client.token.usage` (Histogram, tokens: input, output, cached)
  - `gen_ai.client.operation.duration` (Histogram, seconds)
  - `gen_ai.server.request.duration` (Histogram, seconds)

### Step 2: Agent Tool Wrappers & Container Dependencies (`deploy_dual_gea_agents.py` & `agent.py`)
- Decorate all worker tools (`query_primekg_graph`, `execute_graph_algorithm`, `run_discrete_traversal`, `run_structural_analytics`, `run_continuous_simulation`, `run_temporal_tracking`) and orchestrator delegators with context-aware OpenTelemetry spans injecting trace parent headers.
- Update `COMMON_REQUIREMENTS` in `deploy_dual_gea_agents.py` to include:
  - `opentelemetry-exporter-gcp-trace>=1.7.0`
  - `opentelemetry-exporter-gcp-monitoring>=1.15.0a0`
  - `opentelemetry-instrumentation-google-genai<=1.1b0`
  - `google-cloud-aiplatform[evaluation]>=2.3.0`
  - `google-adk>=2.10.0`
- Re-deploy/update Reasoning Engine revisions with these dependencies.

### Step 3: Connect Native Memory Bank API (`memory_bank.py`)
- Implement `sync_to_vertex_memory_bank()` using `google.cloud.aiplatform_v1beta1.MemoryBankServiceClient`.
- When clinical mutations, biomarkers, and therapeutic hypotheses are consolidated, write each item as an `aiplatform_v1beta1.Memory` entity under the Reasoning Engine parent:
  `projects/301802433103/locations/us-east1/reasoningEngines/4359942935643422720`
- Ensure the console **Memories** tab reflects real patient cases (e.g. `EGFR T790M`, `Osimertinib`, `FLAURA Phase III`).

### Step 4: Connect Native Evaluation API (`run_vertex_eval_bench.py`)
- Initialize `aiplatform.init(experiment="cancer-co-scientist-eval-bench", project=PROJECT_ID, location=LOCATION)`.
- Use Vertex AI `EvalTask` with golden datasets to execute evaluation runs and log metrics:
  - `algorithm_choice_accuracy`
  - `mean_average_precision`
  - `precision_at_10`
  - `recall_at_10`
  - `latency_p50_ms`
  - `latency_p95_ms`
- Ensure experiments and evaluation scorecards are visible in the Vertex AI Experiments / Evaluation console.

### Step 5: Execute Live Benchmark Suite (`benchmark_live_suite.py`)
- Execute all 15 algorithms across the 4 families (Discrete, Structural, Continuous, Temporal) against live Reasoning Engine `4359942935643422720`.
- Verify non-zero metrics across all 7 console surfaces:
  1. **Dashboard / Overview**: Invocations > 0, Token throughput > 0, Active latency.
  2. **Traces**: Full trace trees displaying agent reasoning and tool executions.
  3. **Topology**: First-class A2A mesh with registered peer cards.
  4. **Models**: Per-model Gemini 2.5 Flash token counts and call latencies.
  5. **Memories**: Synchronized clinical memory facts.
  6. **Evaluation**: Native evaluation runs and metric scorecards.
  7. **Sessions**: Active multi-turn user conversation sessions.
