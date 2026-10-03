# Spec 09: Gemini Enterprise Agents (GEA) Production Deployment, Vertex AI Agent Engine Integration, Cloud Security, Observability & Cost Engineering

**Milestone**: Phase 9 — Gemini Enterprise Agents Cloud Deployment, Vertex AI Agent Engine & Visual Dashboard Operations  
**Status**: APPROVED & ARCHITECTED  
**Governing Architecture MCP**: [gea-agents-arch-guidelines-mcp-server](https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server)  
**Target GCP Project**: `fivedaysai-prd-sandbox-317383` (Region: `us-east1`)  
**Guidelines Cited**: 
- `DOC-01`: AI Agent Quality Engineering, Observability & Cost Engineering
- `DOC-02`: Zero Ambient Authority (ZAA), JIT Downscoped Credentials (`PAT-1C192A`), Agentic SecOps
- `DOC-03`: Open AI Agent Protocol Stack, A2UI Declarative Interfaces & Non-Executable Payload Safety
- `DOC-08`: Context Engineering for Stateful AI Agents, Prompt Caching & PAT-MEM-BANK
- `DOC-09`: Platform-Native State Management (Gemini Enterprise Agent Runtime vs Cloud Spanner Graph)

---

## 1. Executive Summary & Deployment Objectives

Phase 9 establishes the comprehensive deployment architecture for the **Cancer Co-Scientist Multi-Agent System** on **Google Cloud Platform (GCP)** leveraging **Gemini Enterprise Agents (GEA)** and **Vertex AI Agent Engine / Agent Platform**.

The system deploys as a **Dual-Agent Autonomous Mesh** adhering to **DOC-03 (Open AI Agent Protocol Stack)** and **DOC-04 (Deploying to Agent Runtime)** in project `fivedaysai-prd-sandbox-317383` (Region: `us-east1`):

1. **Lead Orchestrator Agent (`cancer-co-scientist-lead-orchestrator`)**:
   - Deployed on **Vertex AI Agent Engine** (`reasoningEngines/7288443777713176576`).
   - Built with **Google ADK >= v2.6.0**, exporting `apps/co-scientist/agent.py:root_agent`.
   - Manages clinician conversational sessions, native Vertex AI Memory Bank, and A2UI declarative JSON emission.
   - Discovers and delegates graph algorithmic tasks to the Graph Agent via **A2A Task Delegation Contracts**.
   - Emits OpenTelemetry GenAI semantic metrics (`gen_ai.client.token.usage`, `gen_ai.client.operation.duration`) to populate the GCP Agent Platform Observability dashboard.

2. **Autonomous Graph Agent (`cancer-co-scientist-graph-agent`)**:
   - Deployed on **Vertex AI Agent Engine** as an autonomous peer agent (`reasoningEngines/<WORKER_ID>`).
   - Built with **Google ADK >= v2.6.0**, exporting `packages/graphagent/agent.py:root_agent`.
   - Publishes its machine-readable **Agent Card** at `/.well-known/agent-card.json`.
   - Connects to Cloud Spanner Graph (`PrimeKGGraph`) using Data Boost and BigQuery analytics (`primekg_analytics_dev`).
   - Executes the 15-algorithm matrix across Discrete, Structural, Continuous, and Temporal families.

3. **Zero Cloud Run Dependency**:
   - The entire multi-agent system runs 100% natively on Gemini Enterprise Agents / Vertex AI Agent Engine. Zero Cloud Run services are deployed. Endpoints are reached directly via Vertex AI Agent Platform Console, Agent Playground, or direct Reasoning Engine SDK / REST APIs.

4. **Agent Platform Registry & GCP Console Operations**:
   - Both agents are registered in the **GCP Agent Platform / Agent Registry**, surfacing their status, Playground, Evaluation Bench, Tools, Traces, and Metrics dashboards.

---

## 2. Gemini Enterprise Agents Dual-Agent Architecture

```mermaid
graph TB
    subgraph Presentation_Layer["1. User Experience & Presentation (DOC-03)"]
        Browser["Clinician Web Browser / Local Preview"]
        ConsolePlayground["GCP Vertex AI Agent Playground"]
        AgentRegistryUI["Agent Platform Registry UI"]
    end

    subgraph Orchestrator_Engine["2. Lead Orchestrator GEA Agent (us-east1)"]
        LeadOrchestrator["cancer-co-scientist-lead-orchestrator (ADK >= v2.6.0 root_agent)"]
        A2AClient["A2A Protocol Client (Agent Card Discovery)"]
        MemoryBank["Vertex AI Memory Bank (PAT-MEM-BANK)"]
        A2UIGenerator["A2UI Declarative JSON Generator"]
    end

    subgraph Graph_Worker_Engine["3. Autonomous Graph Agent GEA Agent (us-east1)"]
        GraphAgent["cancer-co-scientist-graph-agent (ADK >= v2.6.0 root_agent)"]
        AgentCard["Agent Card (/.well-known/agent-card.json)"]
        AlgorithmEngine["15-Algorithm Graph Matrix Engine"]
        DiscreteTools["Discrete GQL Engine (Dijkstra, A*, BFS/DFS, WCC)"]
        StructuralTools["Structural Analytics (PageRank Hubs, Betweenness)"]
        TemporalTools["Temporal Dynamic Profiler (λ2 Spectrum, Interval Edges)"]
    end

    subgraph Data_Tier["4. Knowledge & Property Graph Storage Tier (DOC-09)"]
        Spanner["Cloud Spanner Graph (primekg-instance-dev / PrimeKGGraph)"]
        SpannerBoost["Spanner Data Boost (Independent SPU Capacity)"]
        BigQuery["BigQuery Analytics (primekg_analytics_dev / memory_embeddings)"]
    end

    subgraph Compute_Tier["5. Heavy Continuous Simulation Tier"]
        GKE["GKE Autopilot Compute Pods (AlphaFold OMPL & PhysiCell Boids)"]
    end

    subgraph Observability_Tier["6. Observability & FinOps Governance (DOC-01)"]
        CloudTrace["Google Cloud Trace (Multi-Agent Waterfall Spans)"]
        CloudMonitoring["Cloud Monitoring (GenAI OTel Metrics & Custom Gauges)"]
        AgentRegistry["GCP Agent Platform Registry & Dashboard"]
    end

    Browser -->|Direct Query / REST API| LeadOrchestrator
    ConsolePlayground -->|Direct Console Testing| LeadOrchestrator
    AgentRegistryUI -->|Observability & Telemetry| LeadOrchestrator
    
    LeadOrchestrator -->|1. Discover Capabilities| AgentCard
    LeadOrchestrator -->|2. A2A Task Contract Handshake| A2AClient
    A2AClient -->|3. A2A Request / traceparent| GraphAgent
    GraphAgent --> AlgorithmEngine

    LeadOrchestrator --> MemoryBank
    LeadOrchestrator --> A2UIGenerator

    AlgorithmEngine --> DiscreteTools
    AlgorithmEngine --> StructuralTools
    AlgorithmEngine --> TemporalTools
    DiscreteTools -->|ISO GQL Traversal| SpannerBoost
    SpannerBoost --> Spanner
    StructuralTools -->|Data Boost Algorithms| Spanner
    TemporalTools -->|Vector Search & Progression| BigQuery
    AlgorithmEngine -->|Continuous Jobs| GKE

    GraphAgent -->|A2A Task Response (Pydantic Subgraph)| A2AClient
    LeadOrchestrator -.->|GenAI OTel Metrics & Spans| CloudTrace
    GraphAgent -.->|GenAI OTel Metrics & Spans| CloudTrace
    CloudTrace --> AgentRegistry
    CloudMonitoring --> AgentRegistry
```

---

## 3. Vertex AI Agent Builder & Playground Integration

### 3.1 Agent Definition in Vertex AI Agent Engine
The Lead Orchestrator is provisioned as an enterprise Agent resource in Vertex AI Agent Builder:
- **Agent Name**: `cancer-co-scientist-lead-orchestrator`
- **Model**: `gemini-1.5-pro` (Clinical Reasoning & Guideline Compliance) / `gemini-2.0-flash` (Fast Interactive Traversal)
- **Temperature**: `0.1` (Deterministic, reproducible precision oncology guidance)
- **Safety Settings**: Strictest clinical safety filters (BLOCK_NONE for scientific terminology, BLOCK_HIGH for harassment/dangerous content).

### 3.2 System Instruction & Governance Prompt
The agent's system prompt strictly aligns to the Monorepo standards and guidelines:
```text
You are the Cancer Co-Scientist, an enterprise-grade autonomous precision oncology agent operating under Google Enterprise Agents Guidelines (DOC-01, DOC-02, DOC-03, DOC-08, DOC-09).

Your responsibilities:
1. Ground every clinical hypothesis in the live Cloud Spanner PrimeKGGraph knowledge graph.
2. Select the optimal algorithm from the 15-algorithm matrix based on inquiry intent:
   - Point-to-point target paths: Dijkstra / A*
   - Drug repurposing & signaling cascades: Topological Sort / BFS-DFS
   - Essential targets & vulnerable bottlenecks: PageRank Hubs & Betweenness Gatekeepers
   - Molecular docking: Continuous OMPL RRT*
   - Tumor microenvironment cellular dynamics: PhysiCell Boids swarming
   - Longitudinal therapy resistance: Temporal Interval Edges & Algebraic Connectivity (lambda_2)
3. Emit ONLY declarative, non-executable A2UI JSON components conforming to catalog.json (DOC-03). NEVER output executable JavaScript or raw HTML.
4. Enforce Zero Ambient Authority (DOC-02): Mint minimum scoped capabilities per task.
5. Persist extracted genomic variants and therapeutic hypotheses into the managed Memory Bank (DOC-08) for progressive multi-turn recall.
```

### 3.3 Visualizing in Vertex AI Agent Playground
Once deployed, clinicians and AI engineers inspect the agent directly in the **GCP Console**:
1. **Navigation**: Google Cloud Console ➔ **Vertex AI** ➔ **Agent Builder** ➔ **Agents** ➔ Select `cancer-co-scientist-lead-orchestrator`.
2. **Playground Tab**:
   - **Reasoning Trajectory Inspector**: Visualizes each reasoning turn, tool call selection, parameters passed to the Graph Worker, and execution latency.
   - **Token Economy Tracker**: Inspects live token consumption and verifies that cached prompt tokens are credited.
   - **A2UI Declarative Preview**: Visualizes the emitted `InteractiveGraphExplorer` and `InsightCard` JSON payloads in real time.

---

## 4. Observability & Telemetry Framework (`DOC-01`)

### 4.1 GenAI Semantic Conventions & OpenTelemetry Spans
All agent reasoning loops, MCP guideline lookups, and graph worker algorithms are instrumented with OpenTelemetry and exported to **Google Cloud Trace**:

| Span Name | Attributes | Target Budget (p50 / p95) |
| :--- | :--- | :--- |
| `agent.process_inquiry` | `session_id`, `user_id`, `tenant_id`, `query.length` | `< 150ms / < 480ms` |
| `agent.guidelines_mcp_lookup` | `mcp.server="gea-arch-guidelines"`, `mcp.tool="get_best_practice"` | `< 20ms / < 65ms` |
| `agent.router_decision` | `intent`, `recommended_algorithm`, `confidence` | `< 10ms / < 25ms` |
| `graphagent.discrete_traversal` | `algorithm="Dijkstra"`, `source_entity`, `target_entity` | `< 35ms / < 120ms` |
| `graphagent.structural_analytics` | `algorithm="PageRank"`, `node_count`, `density` | `< 75ms / < 250ms` |
| `graphagent.temporal_tracking` | `algorithm="AlgebraicConnectivity"`, `bq.bytes_billed` | `< 140ms / < 400ms` |
| `graphagent.continuous_sim` | `algorithm="PhysiCell_Boids"`, `gke.pod_id` | `< 320ms / < 950ms` |
| `visualization.generate_ast` | `visual_nodes_count`, `visual_edges_count`, `layout="force"` | `< 15ms / < 40ms` |
| `memory_bank.consolidate` | `entities_extracted`, `hypotheses_extracted` | `< 30ms / < 85ms` |

### 4.2 Derived Telemetry Metrics & Quality SLAs
The native Vertex AI Agent Engine workloads export custom metrics to **Google Cloud Monitoring**:

1. **Latency Distributions**:
   - `custom.googleapis.com/cancer_coscientist/latency`: Histogram tracking request duration (p50, p95, p99).
   - **SLA**: Overall p50 < 150ms, p95 < 500ms, p99 < 1200ms.
2. **Token Economics**:
   - `custom.googleapis.com/cancer_coscientist/prompt_tokens`
   - `custom.googleapis.com/cancer_coscientist/completion_tokens`
   - `custom.googleapis.com/cancer_coscientist/cached_tokens`
   - `custom.googleapis.com/cancer_coscientist/cache_hit_rate`: Target **> 60%**.
3. **Information Retrieval (IR) Accuracy**:
   - `custom.googleapis.com/cancer_coscientist/retrieval_map`: **mAP ≥ 0.88**.
   - `custom.googleapis.com/cancer_coscientist/precision_at_10`: **Precision@10 ≥ 0.91**.
   - `custom.googleapis.com/cancer_coscientist/recall_at_10`: **Recall@10 ≥ 0.84**.
4. **Agent Algorithmic Choice Quality**:
   - `custom.googleapis.com/cancer_coscientist/algorithm_choice_accuracy`: **Accuracy ≥ 0.95** evaluated against golden precision oncology benchmarks.

### 4.3 Cloud Monitoring Custom Dashboard Layout
A dedicated Cloud Monitoring dashboard `cancer-coscientist-executive-dashboard` is provisioned via Terraform:
- **Widget 1 (Top Left)**: 95th Percentile Latency across Worker Algorithms (Line chart).
- **Widget 2 (Top Right)**: Token Economics & Context Cache Hit Rate (Stacked area chart).
- **Widget 3 (Middle Left)**: Algorithm Routing Accuracy & Decision Distribution (Pie & gauge).
- **Widget 4 (Middle Right)**: Retrieval Quality (mAP, Precision@10, Recall@10) vs Golden Baseline.
- **Widget 5 (Bottom)**: Cloud Spanner SPU Utilization & BigQuery Query Bytes Billed.

---

## 5. Security & Zero Ambient Authority (`DOC-02` / `PAT-ZAA`)

### 5.1 Service Account Scoping & Workload Identity
In conformance with **Zero Ambient Authority (ZAA)**, no ambient default compute engine credentials are used:

| Service Account | Role / Principle | Assigned GCP IAM Roles |
| :--- | :--- | :--- |
| `sa-coscientist-orchestrator@` | Lead Orchestrator Service | - `roles/spanner.databaseUser` (Read/Write session memory)<br>- `roles/bigquery.dataViewer`<br>- `roles/aiplatform.user` (Reasoning Engine invocations & Memory Bank) |
| `sa-graphagent-worker@` | Headless Computational Worker | - `roles/spanner.databaseReader` (Read-only on `PrimeKGGraph`)<br>- `roles/bigquery.jobUser`<br>- `roles/container.developer` (GKE simulation jobs) |
| `sa-cloud-monitoring-otel@` | OpenTelemetry Telemetry Collector | - `roles/cloudtrace.agent`<br>- `roles/monitoring.metricWriter` |

### 5.2 Just-In-Time (JIT) Downscoped Tokens (`PAT-1C192A`)
When the Lead Orchestrator delegates a task to a Graph Worker:
- It mints a **short-lived (15-minute) downscoped OAuth2 token** with restricted access solely to the Spanner instance `primekg-instance-dev`.
- Ambient credentials never leak into prompt contexts or worker containers.

### 5.3 Zero Cloud Run Execution Invariant (`PAT-ZAA`)
- **Strict Invariant**: Zero Cloud Run services are deployed.
- Both agents run natively as **Vertex AI Agent Engine (Reasoning Engine)** micro-runtimes with non-root security context (`USER 10001:10001`), bounded ephemeral storage, and scoped IAM service accounts.

---

## 6. Cost Management & FinOps Engineering (`DOC-01`, `DOC-08`)

### 6.1 Vertex AI Context Caching
- **Cached Contexts**: PrimeKG ontology definitions, GraphAlgorithmEngine tool definitions, and clinical guideline rubrics (>32,768 tokens).
- **Economic Impact**: Vertex AI Context Caching reduces input token cost by **75%** on prompt tokens that hit cache.
- **Cache Refresh Interval**: Managed with a 1-hour TTL, dynamically renewed on active clinician sessions.

### 6.2 Cloud Spanner Data Boost Optimization
- **Operational Efficiency**: Intensive discrete algorithms (e.g. Weakly Connected Components, PageRank hubs, multi-hop BFS) leverage **Spanner Data Boost**.
- **Isolation**: Traversal queries execute on independent serverless processing capacity without consuming transactional SPU capacity allocated to clinical write traffic.

### 6.3 BigQuery Analytical Caps
- BigQuery queries on `primekg_analytics_dev.memory_embeddings` are clustered by `session_id` and partitioned by date.
- Explicit query cost ceiling: `maximum_bytes_billed = 104857600` (100 MB per query), preventing runaway unbounded billing.

### 6.4 Cloud Billing Budget Alerts
- Configured budget: **$500.00 / month** in `fivedaysai-prd-sandbox-317383`.
- Alert thresholds configured at:
  - **50% ($250)**: Informational notification to FinOps channel.
  - **80% ($400)**: Warning alert to precision oncology devops.
  - **100% ($500)**: Critical page; automated Cloud Function disables GKE continuous simulation compute nodes to cap expenditure.

---

## 7. Infrastructure as Code (IaC) & Deployment Manifests

### 7.1 Directory Organization
All deployment assets reside in the monorepo root under:
```
deploy/
├── terraform/
│   ├── main.tf                    # GCP Provider & Project definition
│   ├── variables.tf               # Project ID, region, cluster names
│   ├── vertex_agent_engine.tf     # Gemini Enterprise Agent Engine resources (Dual Agents)
│   ├── monitoring_dashboards.tf   # Custom Cloud Monitoring dashboards
│   └── outputs.tf                 # Live Reasoning Engine Resource IDs
└── scripts/
    ├── deploy_dual_gea_agents.py  # Python ADK AdkApp deployment script for both agents
    └── verify_deployment.sh       # E2E health check & IR benchmark validation
```

### 7.2 Terraform Dual Agent Engine Definition (`vertex_agent_engine.tf`)
```hcl
# 1. Autonomous Graph Agent Engine (Worker Tier)
resource "google_vertex_ai_reasoning_engine" "graph_agent" {
  project      = var.project_id
  location     = "us-east1"
  display_name = "cancer-co-scientist-graph-agent"
  description  = "Gemini Enterprise Autonomous Graph Agent executing 15-algorithm matrix over PrimeKG"

  runtime {
    service_account = google_service_account.graph_agent_sa.email
  }

  labels = {
    tier        = "worker"
    protocol    = "a2a"
    governance  = "doc-01-doc-02-doc-03"
  }
}

# 2. Lead Orchestrator Engine (Orchestration Tier)
resource "google_vertex_ai_reasoning_engine" "lead_orchestrator" {
  project      = var.project_id
  location     = "us-east1"
  display_name = "cancer-co-scientist-lead-orchestrator"
  description  = "Gemini Enterprise Lead Orchestrator for Precision Oncology Multi-Hop Reasoning"

  runtime {
    service_account = google_service_account.orchestrator_sa.email
  }

  labels = {
    tier        = "orchestrator"
    protocol    = "a2a-a2ui"
    governance  = "doc-01-doc-02-doc-03-doc-08"
  }
}
```

### 7.3 Step-by-Step Dual-Agent Deployment Runbook (ADK >= v2.6.0)
1. **Prerequisite & Staging Bucket Setup (DOC-04)**:
   ```bash
   gcloud config set project fivedaysai-prd-sandbox-317383
   export STAGING_BUCKET="gs://cancer-co-scientist-adk-staging-317383"
   gcloud storage buckets create $STAGING_BUCKET --location=us-east1 --uniform-bucket-level-access 2>/dev/null || true
   ```
2. **Purge Deprecated Non-ADK Reasoning Engine (`7288443777713176576`)**:
   - The previous deployment used a raw generic Python class that lacked `agentFramework: "google-adk"`, resulting in 0 metrics in console charts.
   - Delete older engine:
     ```python
     from vertexai.preview import reasoning_engines
     reasoning_engines.ReasoningEngine("projects/301802433103/locations/us-east1/reasoningEngines/7288443777713176576").delete()
     ```

3. **Deploy Autonomous Graph Agent (`packages/graphagent`) via `AdkApp`**:
   - Wrapped with `vertexai.agent_engines.templates.adk.AdkApp` around `google.adk.agents.Agent`.
   - Requires: `google-adk>=2.10.0`, `opentelemetry-instrumentation-google-genai>=1.2b0`, `google-cloud-aiplatform>=2.3.0`, `google-genai>=2.26.0`, `pydantic>=2.0.0`.
   - Command:
     ```bash
     python deploy/scripts/deploy_dual_gea_agents.py --agent=graph_agent
     ```
   - Captures output: `projects/301802433103/locations/us-east1/reasoningEngines/<GRAPH_AGENT_ID>`.

4. **Deploy Lead Orchestrator (`apps/co-scientist`) via `AdkApp`**:
   - Configured with `GRAPH_AGENT_RESOURCE_ID` pointing to the deployed Graph Agent Reasoning Engine.
   - Built with `AdkApp(agent=orchestrator_agent, enable_tracing=True)` automatically binding:
     - `VertexAiSessionService`: powers Overview tab Sessions, Avg turns, Invocations.
     - `VertexAiMemoryBankService`: powers Memories tab.
     - `opentelemetry-instrumentation-google-genai`: powers Models tab (Model calls, P95 duration) and Usage tab.
   - Command:
     ```bash
     python deploy/scripts/deploy_dual_gea_agents.py --agent=lead_orchestrator --graph-agent-id=<GRAPH_AGENT_ID>
     ```
   - Captures output: `projects/301802433103/locations/us-east1/reasoningEngines/<ORCHESTRATOR_ID>`.

5. **Verify Deployment & Open GCP Agent Platform Dashboard**:
   - Access Agent Platform Registry: `https://pantheon.corp.google.com/agent-platform/agent-registry/agents/us-east1/cancer-co-scientist-lead-orchestrator/observability?project=fivedaysai-prd-sandbox-317383`
   - Verify both agents (`cancer-co-scientist-lead-orchestrator` and `cancer-co-scientist-graph-agent`) appear in the registry.
   - Test Playground tab, Tools tab, Overview tab, Evaluation tab, Memories tab, Traces, and Logs.
   - **Strict Invariant**: Zero Cloud Run services deployed; all computation and interaction execute on native Vertex AI Agent Engine.

---

## 8. Acceptance Criteria & Audit Verification

- [ ] **Vertex AI Agent Engine Registered**: `cancer-co-scientist-lead-orchestrator` is visible and active in the GCP Vertex AI Agent Engine Console (`us-east1`).
- [ ] **GCP Playground Functional**: Users can interact with the agent directly inside the Vertex AI Console Playground tab using standard text queries and inspect reasoning trajectories.
- [ ] **Tools Tab Populated**: Tools tab lists registered tools (`query_primekg_graph`, `execute_graph_algorithm`, `consult_architecture_guidelines`, `inspect_memory_bank`) and displays live execution activity.
- [ ] **Observability Trace Export**: Full distributed traces emit to Cloud Trace with resource attributes `aiplatform.googleapis.com/ReasoningEngine` and custom attributes (`graphagent.algorithm_name`, `spanner.instance_id`).
- [ ] **Cloud Monitoring Metrics & Charts**: LRO latency (p50/p95/p99), invocation rates, error rates, and token consumption charts are populated on GCP Console.
- [ ] **Memories Tab Active**: Extracted clinical entities and therapeutic hypotheses persist and appear in the Vertex AI Memories tab.
- [ ] **Evaluation Bench Active**: Evaluation tab reflects evaluation runs with golden datasets, quality scorecards, and continuous monitors.
- [ ] **Usage and Logs Active**: Cloud Logging displays structured JSON logs under `aiplatform.googleapis.com/ReasoningEngine`.
- [ ] **Zero Ambient Authority Enforced**: No default compute credentials in containers; all workloads run under least-privilege service accounts with JIT token scoping.
- [ ] **A2UI Protocol Compliance**: Declarative JSON emitted strictly; zero raw script/HTML execution on web clients.
