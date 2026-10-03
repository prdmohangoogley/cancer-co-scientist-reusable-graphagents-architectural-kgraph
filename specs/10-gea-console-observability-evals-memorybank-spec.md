# Spec 10: Gemini Enterprise Agents (GEA) Console Dashboard Operationalization, Interactive Playground, Vertex AI Evaluation Bench, Memory Bank & Continuous Multi-Agent Monitors

**Milestone**: Phase 10 — GCP GEA Platform Console Operationalization & Multi-Agent Continuous Governance  
**Status**: APPROVED & ARCHITECTED  
**Governing Architecture MCP**: [gea-agents-arch-guidelines-mcp-server](https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server)  
**Target GCP Project**: `fivedaysai-prd-sandbox-317383` (Region: `us-east1`)  
**Deployed Agent Engine Resource**: `projects/301802433103/locations/us-east1/agentEngines/4359942935643422720` (`cancer-co-scientist-graph-agent`)  
**Deployed Lead Orchestrator Resource**: `projects/301802433103/locations/us-east1/reasoningEngines/7288443777713176576` (`cancer-co-scientist-lead-orchestrator`)  
**Guidelines Cited**: 
- `DOC-01`: AI Agent Quality Engineering, Observability & Evaluation Benchmarks
- `DOC-02`: Zero Ambient Authority (ZAA) & Agentic SecOps
- `DOC-03`: Open AI Agent Protocol Stack, A2UI Declarative Interfaces & Safe Schemas
- `DOC-08`: Context Engineering for Stateful AI Agents, Memory Banks & Prompt Caching
- `DOC-09`: Platform-Native State Management (Gemini Enterprise Agent Runtime & Memory Bank)

---

## 1. Executive Summary & Purpose

While previous specs established the multi-agent architecture (Specs 01–06), the Co-Scientist web application (Spec 07), the Graph Visualization Specialist Agent (Spec 08), and the high-level cloud deployment (Spec 09), this specification addresses the operationalization of the **native Google Cloud Platform Gemini Enterprise Agent (GEA) / Vertex AI Agent Engine Console Dashboard**.

The objective is to ensure that the GCP Console for `cancer-co-scientist-lead-orchestrator` is operational and populated across all native tabs:
1. **Overview Tab**: Displays live agent health, endpoints, deployment metadata, and operational summaries.
2. **Playground Tab**: Enables interactive chat testing directly inside the GCP Console by implementing the Google ADK/Reasoning Engine query interface (`input`, `query`, `prompt`, `session_id`, `stream_query`).
3. **Evaluation Tab (Eval Bench)**: Populates evaluation runs, experiments, and quality scorecards using the Vertex AI Rapid Evaluation API (`EvalTask`) across golden clinical inquiries, measuring groundedness, question-answering accuracy, latency SLAs, and `agent.correct_algorithm_choice`.
4. **Metrics Tab & Telemetry Charts**: Displays latency distributions (LRO latency, p50, p95, p99), invocation counts, error rates, and token consumption charts in Cloud Monitoring and GEA console.
5. **Traces Tab & Tools Tab**: Surfaces distributed OpenTelemetry spans exported to Google Cloud Trace tagged with `aiplatform.googleapis.com/ReasoningEngine` so tool executions (`query_primekg_graph`, `execute_graph_algorithm`, `consult_architecture_guidelines`, `inspect_memory_bank`) and their parameters are visible in the waterfall breakdown.
6. **Usage & Logs Tab**: Streams structured JSON logs to Cloud Logging under the Reasoning Engine resource hierarchy.
7. **Memories Tab (Memory Bank)**: Populates sessions, clinical entities (e.g., `EGFR T790M`, `Osimertinib`), and therapeutic hypotheses directly in the native GEA Memory Bank.
8. **Continuous Multi-Agent Monitors & Experiments**: Deploys continuous automated health monitors for:
   - **Graph Agents (Worker Tier)**: Verifying the 15-algorithm matrix SLA and error rates.
   - **Agent2UI (A2UI)**: Verifying non-executable JSON AST generation and catalog conformance (`DOC-03`).
   - **Graph Visualization Agent**: Verifying deterministic 2D/3D layouts and node collision metrics.

---

## 2. GCP GEA Console Dashboard Architecture

```mermaid
graph TB
    subgraph GCP_GEA_Console["Google Cloud Platform — Vertex AI Agent Engine Console"]
        OverviewTab["1. Overview Tab (Status & Metadata)"]
        PlaygroundTab["2. Playground Tab (Interactive Test Chat)"]
        EvalsTab["3. Evaluation Tab (Eval Runs & Scorecards)"]
        MetricsTab["4. Metrics Tab (Latency p50/p95, Tokens, Errors)"]
        TracesTab["5. Traces & Tools Tab (OTel Spans & Tool Activity)"]
        LogsTab["6. Usage & Logs Tab (Structured Cloud Logging)"]
        MemoriesTab["7. Memories Tab (Vertex AI Memory Bank)"]
    end

    subgraph Deployed_Agent_Runtime["Vertex AI Agent Engine (us-east1 / 7288443777713176576)"]
        ReasoningEngine["CancerCoScientistLeadOrchestrator"]
        QuerySignature["query(input, query, prompt, session_id) & stream_query"]
        ToolsRegistry["Registered Tools: PrimeKG, Algorithms, Guidelines, Memory"]
        LocalState["Session & Memory State Handler"]
    end

    subgraph Evaluation_Engine["Evaluation & Quality Framework (DOC-01)"]
        VertexEvalBench["Vertex AI Rapid Evaluation Bench (run_vertex_eval_bench.py)"]
        GoldenDataset["Golden Precision Oncology Dataset (15 Benchmark Inquiries)"]
        LLMJudge["Calibrated Gemini 1.5 Pro Judge (Groundedness & Accuracy)"]
    end

    subgraph Observability_Pipeline["Observability & Telemetry Pipeline (DOC-01)"]
        OTelExporter["OpenTelemetry Cloud Trace Exporter (opentelemetry-exporter-gcp-trace)"]
        CloudMonMetrics["Google Cloud Monitoring Client (custom.googleapis.com)"]
        CloudLogger["Google Cloud Logging (aiplatform.googleapis.com/ReasoningEngine)"]
    end

    subgraph Continuous_Monitors["Continuous Multi-Agent Monitors"]
        GraphAgentMonitor["Worker Tier Monitor (15 Algorithms)"]
        A2UIMonitor["Agent2UI Catalog Conformance Monitor"]
        GraphVisMonitor["Graph Visualization Layout Monitor"]
    end

    PlaygroundTab -->|Invokes query(input=...)| QuerySignature
    QuerySignature --> ReasoningEngine
    ReasoningEngine --> ToolsRegistry
    ToolsRegistry --> TracesTab
    
    ReasoningEngine --> OTelExporter
    OTelExporter --> TracesTab
    ReasoningEngine --> CloudMonMetrics
    CloudMonMetrics --> MetricsTab
    ReasoningEngine --> CloudLogger
    CloudLogger --> LogsTab
    ReasoningEngine --> LocalState
    LocalState --> MemoriesTab

    VertexEvalBench --> GoldenDataset
    VertexEvalBench --> LLMJudge
    VertexEvalBench --> EvalsTab

    Continuous_Monitors --> GraphAgentMonitor
    Continuous_Monitors --> A2UIMonitor
    Continuous_Monitors --> GraphVisMonitor
    GraphAgentMonitor --> CloudMonMetrics
    A2UIMonitor --> CloudMonMetrics
    GraphVisMonitor --> CloudMonMetrics
```

---

## 3. Vertex AI Reasoning Engine Interface Contract & AdkApp Architecture (Playground Tab)

To ensure full compatibility with the **Vertex AI Agent Builder / Reasoning Engine Playground tab**, **Agent Platform Registry**, and **Observability Dashboards**, the root agent is built using **Google ADK (`google-adk>=2.10.0`)** and deployed via **`vertexai.agent_engines.templates.adk.AdkApp`**:

```python
from google.adk.agents import Agent
from vertexai.agent_engines.templates.adk import AdkApp

# 1. Orchestrator ADK Agent Definition
lead_orchestrator = Agent(
    name="cancer-co-scientist-lead-orchestrator",
    description="Gemini Enterprise Lead Orchestrator for Precision Oncology Multi-Hop Graph Traversal",
    model="gemini-2.5-flash",
    instruction="""You are the Cancer Co-Scientist Lead Orchestrator. 
Analyze clinical oncology inquiries, coordinate multi-hop traversals over PrimeKG, 
delegate graph algorithmic tasks to the deployed cancer-co-scientist-graph-agent peer agent,
and emit strictly declarative A2UI JSON components.""",
    tools=[
        delegate_to_graph_agent,
        consult_architecture_guidelines,
        inspect_memory_bank,
        generate_a2ui_payload,
    ],
)

# 2. Wrapped in AdkApp with Tracing Enabled
app = AdkApp(agent=lead_orchestrator, enable_tracing=True)
```

### 3.1 Why AdkApp is Architecturally Required for GCP Console Dashboards
Deploying a raw custom Python class causes all GCP Console dashboards to show zeroes because Vertex AI Agent Engine cannot bind its native services. Wrapping with `AdkApp` guarantees:
1. **`agentFramework: "google-adk"`**: The GCP Console recognizes the workload as an official ADK Agent.
2. **`VertexAiSessionService` Auto-Binding**: When running inside Vertex AI Agent Engine, `AdkApp` automatically attaches to `VertexAiSessionService`, recording sessions and turns to populate the **Overview Tab (Sessions, Avg turns, Invocations)**.
3. **`VertexAiMemoryBankService` Auto-Binding**: Seamlessly connects to the **Memories Tab**, persisting extracted genomic entities and therapeutic hypotheses.
4. **GenAI Semantic Metrics (`opentelemetry-instrumentation-google-genai`)**: Automatically instruments all Gemini model calls, emitting `gen_ai.client.token.usage` and `gen_ai.client.operation.duration` to populate the **Models Tab (Model calls, P95 duration)** and **Usage Tab (Token timeseries)**.
5. **Console Playground Streaming**: Implements standard ADK `stream_query` and session management, allowing clinicians to test the agent directly in the GCP Console Playground chat bubble.

### 3.2 Registered Tool Methods (Populating the "Tools" Tab)
The Agent exposes atomic callable tools surfaced directly in the GCP Console Tools tab:
1. `delegate_to_graph_agent(inquiry: str, source_entity: str, target_entity: str, algorithm_name: str) -> dict`: Dispatches A2A contract to `cancer-co-scientist-graph-agent`.
2. `query_primekg_graph(source_entity: str, target_entity: str = None, relation_type: str = None, depth: int = 2) -> dict`: Cloud Spanner Graph ISO GQL query tool.
3. `execute_graph_algorithm(algorithm_name: str, source_entity: str = None, target_entity: str = None, parameters: dict = None) -> dict`: 15-algorithm matrix execution tool.
4. `consult_architecture_guidelines(topic: str = "Quality") -> dict`: FastMCP architecture guidelines integration.
5. `inspect_memory_bank(session_id: str) -> dict`: Vertex AI Memory Bank progressive recall.

---

## 4. Cloud Trace & Cloud Monitoring Telemetry (Metrics & Traces Tabs)

### 4.1 Cloud Trace Exporter Configuration & GenAI Span Hierarchy
Spans are emitted using `opentelemetry-exporter-gcp-trace` with explicit monitored resource attributes linking them directly to the Vertex AI Agent Engine / Reasoning Engine instance in GCP:
- `gcp.resource_type`: `"aiplatform.googleapis.com/ReasoningEngine"`
- `aiplatform.googleapis.com/reasoning_engine_id`: `"4359942935643422720"` (Agent Engine Worker) and `"7288443777713176576"` (Lead Orchestrator)
- `service.name`: `"cancer-co-scientist-graph-agent"` (Worker) and `"cancer-co-scientist-lead-orchestrator"` (Orchestrator)
- `cloud.region`: `"us-east1"`
- `gcp.project_id`: `"fivedaysai-prd-sandbox-317383"`

Span hierarchy follows **DOC-01** & OpenTelemetry GenAI Semantic Conventions:
1. `agent.run`: Captures end-to-end turn with attributes `agent.name`, `agent.version`, `session.id`, `user.id`.
2. `llm.generate` / `gen_ai.client.operation`: Captures model calls with attributes `gen_ai.system="vertexai"`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.prompt_tokens`, `gen_ai.usage.completion_tokens`.
3. `tool.execute` / `gen_ai.tool.name`: Captures tool dispatches with attributes `gen_ai.tool.name` (`execute_discrete_graph_algorithm`, `explore_target_subgraph_neighborhood`, etc.), parameters, status, and duration.
4. `agent.transfer`: Captures A2A task delegation from Lead Orchestrator to Graph Agent with W3C `traceparent` context propagation.

### 4.2 ADK >= v2.6.0 OpenTelemetry GenAI Semantic Metrics (Console Charts)
The GCP Agent Platform / Agent Engine Observability dashboard charts are populated directly from OpenTelemetry metrics emitted by ADK >= v2.6.0 conforming to standard GenAI Semantic Conventions:

| Console Chart / Card | OTel Metric Instrument | Metric Kind & Unit | Attributes / Dimensions |
| :--- | :--- | :--- | :--- |
| **Model Calls** | `gen_ai.client.operation.duration` | Histogram (seconds) | `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.system="vertexai"` |
| **P95 Duration by Model** | `gen_ai.client.operation.duration` | Histogram (seconds) | `gen_ai.request.model` (`gemini-2.5-flash`, `gemini-1.5-pro`) |
| **Token Usage (Prompt/Output)** | `gen_ai.client.token.usage` | Histogram / Counter (tokens) | `gen_ai.token.type` (`input`, `output`), `gen_ai.request.model` |
| **Invocations** | `gen_ai.server.request.duration` / `agent.invocations` | Cumulative Counter | `agent.name`, `status` (`success`, `error`), `http.response.status_code` |
| **Sessions & Avg Turns** | `agent.sessions` & `agent.turns` | Counter / Gauge | `session.id`, `user.id`, `agent.turn_count` |
| **Tool Execution Activity (Tools Tab)** | `gen_ai.tool.duration` & `gen_ai.tool.call_count` | Counter & Histogram | `gen_ai.tool.name` (`execute_discrete_graph_algorithm`, `explore_target_subgraph_neighborhood`, `analyze_structural_centrality_gatekeepers`, `validate_precision_oncology_pathway`) |

### 4.3 Custom Cloud Monitoring Metrics
Custom metrics provisioned under `custom.googleapis.com/agent/`:

| Metric Type | Metric Name | Metric Kind | Value Type | Description |
| :--- | :--- | :--- | :--- | :--- |
| `agent/orchestrator/latency` | End-to-End Inquiry Latency | `GAUGE` / `DISTRIBUTION` | `DOUBLE` | Latency in ms for agent reasoning loops (p50, p95, p99) |
| `agent/orchestrator/invocations` | Total Invocations | `CUMULATIVE` | `INT64` | Counter of queries executed through Playground or REST |
| `agent/orchestrator/error_count` | Total Errors | `CUMULATIVE` | `INT64` | Counter of failed queries or unhandled exceptions |
| `agent/orchestrator/tokens_consumed` | Total Token Usage | `CUMULATIVE` | `INT64` | Prompt, completion, and cached tokens consumed |
| `agent/graph_algorithm/latency` | Graph Algorithm Latency | `GAUGE` / `DISTRIBUTION` | `DOUBLE` | Execution latency for the 15 graph algorithms |
| `agent/quality/algorithm_choice_accuracy` | Algorithm Selection Accuracy | `GAUGE` | `DOUBLE` | Score (0.0 to 1.0) evaluating intent router decisions |
| `agent/visualization/layout_latency` | Visualization Layout Latency | `GAUGE` | `DOUBLE` | Time in ms to generate declarative A2UI SVG ASTs |

---

## 5. Vertex AI Rapid Evaluation Bench (Evaluation Tab)

Adhering to `DOC-01` (`AI Agent Quality Engineering`) and expanded in **Spec 12**:
- **Script**: `packages/graphagent/evals/run_vertex_eval_bench.py` and `packages/graphagent/evals/register_gea_experiments.py`
- **Categorized Experiment Structure in GEA Dashboard**:
  Experiments are partitioned and formally registered into the Vertex AI Experiments API under four distinct categories:
  1. `graph-agent-discrete-algorithms`: Dijkstra, A*, D* Lite, BFS/DFS, WCC/SCC, Topological Sort, Transitive Closure, Community Detection, Ego-Network.
  2. `graph-agent-structural-centrality`: PageRank Hubs, Betweenness Gatekeepers, Density, Bridges.
  3. `graph-agent-continuous-simulation`: OMPL RRT* AlphaFold docking, PhysiCell microenvironment simulation.
  4. `graph-agent-temporal-omics`: Interval-Timestamped Edges, Algebraic Connectivity $\lambda_2$, Precision Oncology Pathway Validation.
- **Evaluated Metrics**:
  - `groundedness`: Verification that facts in response exist in Spanner PrimeKGGraph.
  - `question_answering_quality`: Evaluated by calibrated LLM judge (`gemini-2.5-flash` / `gemini-1.5-pro`).
  - `agent.correct_algorithm_choice`: Proportion of inquiries correctly routed to the optimal algorithm ($\ge 95\%$).
  - `latency_sla_compliance`: Verification that p50 < 45ms and p95 < 350ms.
- **Reporting & Registration Contract**:
  Runs are registered via `google.cloud.aiplatform.init(experiment=...)` and logged using `aiplatform.start_run()`, directly populating the **Evaluation Tab -> Experiments** list in the GEA console.

---

## 6. Native GEA Memory Bank Integration (Memories Tab)

Adhering to `DOC-08` and `DOC-09`:
- The Agent integrates directly with the **Vertex AI Agent Engine Memory Bank REST API**:
  - Endpoint: `https://us-east1-aiplatform.googleapis.com/v1beta1/projects/301802433103/locations/us-east1/agentEngines/4359942935643422720/memories`
  - Operations:
    1. **Create Memory**: Writes extracted clinical entities and hypotheses directly to the Agent Engine runtime.
    2. **Generate Memories (LRO)**: Dispatches `memories:generate` post-session consolidation, populating the *Generate memories token count* and *Memory LRO latency* charts.
    3. **Retrieve Memories**: Invocations during clinical query turns call `memories:retrieve`, populating the *Retrieved memories count* and *Memory mutation count* metrics.
- Persisted clinical data:
  1. **Entities**: Genomic alterations (e.g. `EGFR T790M`, `BRAF V600E`, `KRAS G12D`), drugs (e.g. `Osimertinib`, `Dabrafenib`), and cancer phenotypes (e.g. `Non-Small Cell Lung Carcinoma`, `Cutaneous Melanoma`).
  2. **Hypotheses**: Actionable therapeutic assertions (e.g. *"Osimertinib overcomes T790M-mediated gatekeeper resistance by covalently binding to Cys797"*).
- Entities and hypotheses are tagged with `session_id`, `user_id`, `entity_type`, and timestamp, populating both the active facts list and time-series telemetry charts in the GEA Memories tab.

---

## 7. Continuous Multi-Agent Monitors & Experiments

To guarantee production quality and reliability, three continuous synthetic monitors run in the background:
1. **Graph Agents Worker Monitor (`packages/graphagent/evals/monitor_graph_agents.py`)**:
   - Executes periodic test probes against all 4 algorithmic families every 5 minutes.
   - Measures p50 and p95 latencies and updates `custom.googleapis.com/agent/graph_algorithm/latency`.
   - Emits alerts if error rate exceeds 0.5% or p95 exceeds 500ms.
2. **Agent2UI Declarative Interface Monitor (`packages/graphagent/evals/monitor_a2ui.py`)**:
   - Validates generated JSON ASTs against `apps/co-scientist/a2ui/catalog.json`.
   - Asserts zero executable script tags or HTML attributes (`DOC-03`).
3. **Graph Visualization Agent Monitor (`packages/graphagent/evals/monitor_visualization.py`)**:
   - Computes layout coordinates for benchmark subgraphs.
   - Evaluates node collision rates, boundary containment, and layout calculation time.

---

## 8. Verification & Acceptance Criteria

- [ ] **GCP Playground Chat Interactive**: Typing a prompt in the GCP Vertex AI Agent Engine Playground tab returns a formatted clinical response with step-by-step reasoning trajectories.
- [ ] **Tools Tab Shows Registered Tools**: Tools tab displays `query_primekg_graph`, `execute_graph_algorithm`, `consult_architecture_guidelines`, and `inspect_memory_bank`.
- [ ] **Cloud Trace Waterfall Populated**: Distributed traces for multi-hop graph queries appear in Google Cloud Trace with parent-child span breakdowns.
- [ ] **Cloud Monitoring Metrics Live**: Time-series charts for latency, invocations, error counts, and token usage display non-zero live metrics.
- [ ] **Memories Tab Populated**: Extracted entities and clinical hypotheses are visible in the GCP GEA Console Memories tab.
- [ ] **Evaluation Bench Executed**: `run_vertex_eval_bench.py` executes successfully and reports scorecards to the Evaluation tab with >95% algorithm accuracy.
- [ ] **Continuous Monitors Active**: Synthetic monitors for Graph Agents, A2UI, and Graph Visualization execute and record health status to Cloud Monitoring.
