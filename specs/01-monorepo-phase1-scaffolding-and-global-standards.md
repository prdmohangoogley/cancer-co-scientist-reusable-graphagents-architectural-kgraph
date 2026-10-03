# Spec 01: Monorepo Phase 1 - Scaffolding & Global Standards

**Milestone**: Phase 1 Scaffolding & Global Standards  
**Status**: APPROVED & IMPLEMENTED  
**Governing Architecture MCP**: [gea-agents-arch-guidelines-mcp-server](https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server)  
**Guidelines Cited**: `DOC-01`, `DOC-02`, `DOC-03`, `DOC-08`, `DOC-09`

---

## 1. Executive Summary & Context
The `graphagents` monorepo establishes an enterprise-grade platform uniting reusable biomedical graph intelligence libraries (**Workers**) with full-stack agentic applications (**Orchestrators**).

The flagship application is the **Cancer Co-Scientist**, an autonomous oncological reasoning system designed for clinicians and researchers. Its core architecture decouples cognitive tasks across four decoupled tiers following **DOC-03** and **A2A (Agent-to-Agent)** protocol federation:
1. **Lead Orchestrator Agent (`cancer-co-scientist-lead-orchestrator`)**: Autonomous Gemini Enterprise Agent built on Google ADK (>= v2.6.0) exporting `agent.py:root_agent`. Interprets unstructured clinical inquiries, manages user sessions and Memory Bank, delegates graph computational tasks to the Graph Agent via **A2A Task Delegation Contracts**, and emits declarative **A2UI (Agent-to-UI)** JSON schemas for safe client presentation.
2. **Autonomous Graph Agent (`cancer-co-scientist-graph-agent`)**: Independent Gemini Enterprise Agent built on Google ADK (>= v2.6.0) exporting `agent.py:root_agent` and publishing its Agent Card at `/.well-known/agent-card.json`. Executes ISO GQL graph traversals over **Cloud Spanner Graph** (housing PrimeKG) and analytics over **BigQuery**, exposing the 15-algorithm matrix to the Lead Orchestrator over A2A.
3. **Architectural Guidelines Engine**: A remote Model Context Protocol (MCP) server providing real-time best practice validation, pattern retrieval, and tradeoff evaluation to ensure adherence to Google Cloud enterprise agent standards.
4. **Platform-Native State & Observability Tier**: Spanner Sessions, BigQuery Analytics, Vertex AI Memory Bank, and Google Cloud Monitoring/Trace capturing OpenTelemetry GenAI semantic metrics (`gen_ai.client.token.usage`, `gen_ai.client.operation.duration`).

---

## 2. Directory Hierarchy Specification

```markdown
graphagents/
├── .agents/                    # 🚀 Antigravity Central Command
│   ├── rules/                 # Always-active guidelines (AGENTS.md)
│   └── skills/                # Reusable developer skills (guidelines_lookup)
├── specs/                     # 📋 Tracked Technical Specifications
│   ├── 01-monorepo-phase1-scaffolding-and-global-standards.md
│   ├── 02-architecture-guidelines-mcp-integration.md
│   ├── 03-primekg-dataloader-spec.md
│   ├── 04-worker-tier-primekg-ingestion-spec.md
│   ├── 05-worker-tier-graph-traversal-tools-spec.md
│   ├── 06-graphagents-adkworkers-spec.md
│   ├── 07-co-scientist-spec-web-app.md
│   ├── 08-graph-visualization-agent-spec.md
│   ├── 09-gemini-enterprise-agents-deployment-spec.md
│   ├── 10-gea-console-observability-evals-memorybank-spec.md
│   └── 11-a2a-protocol-mesh-agent-card-federation-spec.md
├── docs/                       # 📖 Global Specs & OKF Guidelines
│   ├── architecture.md        # Comprehensive multi-agent architecture
│   └── okf_guidelines.md      # Ontology Knowledge Framework standards
├── infra/                      # 🏗️ Global Infrastructure (Terraform)
│   ├── datalake/              # Core GCS (OKF Data Lake)
│   └── primekg_staging/       # 🗄️ PrimeKG Staging & GCE Curl Pipelines
├── packages/                   # 🧩 REUSABLE PACKAGES & LIBRARIES
│   └── graphagent/            # Autonomous Graph Agent (Worker Tier)
│       ├── agent.py           # Standard ADK root_agent export (ADK >= v2.6.0)
│       ├── .well-known/       # A2A Agent Card definition
│       │   └── agent-card.json
│       ├── adk/               # ADK definitions & A2A Task Handlers
│       ├── tools/             # 15-Algorithm GQL/SQL Traversal & Querying tools
│       ├── observability/     # GenAI OTel metric instruments & Cloud Trace
│       ├── evals/             # Golden routing & retrieval evaluation suite
│       └── iac/               # Package-specific IaC (Spanner Graph + BQ)
└── apps/                       # 🌐 FULL-STACK APPLICATIONS
    └── co-scientist/          # 🩺 Cancer Co-Scientist (Lead Orchestrator Tier)
        ├── agent.py           # Standard ADK root_agent export (ADK >= v2.6.0)
        ├── a2ui/              # 🎨 A2UI Artifacts (Catalog, Examples)
        │   ├── catalog.json   # Component definitions (Cards, Charts, etc.)
        │   └── examples/      # Few-shot prompts for UI generation
        ├── agent/             # 🧠 Lead Orchestrator, A2A Client, Router Logic
        │   ├── orchestrator.py# Main ADK Agent Loop & API Endpoints
        │   ├── a2a_client.py  # A2A Client consuming Graph Agent Card
        │   ├── memory_bank.py # Platform-Native Sessions & Memory Bank
        │   ├── auth.py        # ZAA JWT Token Verification
        │   └── router.py      # Intent Classification & A2A Delegation
        ├── ui/                # 💻 A2UI Renderer Client (TypeScript/Lit)
        │   ├── src/
        │   ├── package.json
        │   └── Dockerfile
        └── iac/               # ☁️ Application Deployment IaC (Vertex Agent Engine)
```

---

## 3. Protocol Architecture & Invariants

### 3.1. Layer Separation & A2A Federation (DOC-03)
Strict boundary enforcement:
- **Presentation Layer**: `A2UI` (Declarative JSON UI schemas, zero executable code).
- **Agent Orchestration Layer**: Lead Orchestrator (`cancer-co-scientist-lead-orchestrator`), exposed via `agent.py:root_agent`. Handles intent routing, session lifecycle, and Memory Bank.
- **Worker Federation Layer**: Autonomous Graph Agent (`cancer-co-scientist-graph-agent`), exposed via `agent.py:root_agent` and `.well-known/agent-card.json`. The Orchestrator delegates graph tasks via **A2A Task Delegation Contracts** (never in-process monolithic coupling).
- **Data & Tools Layer**: `FastMCP` and ISO GQL over Cloud Spanner Graph and BigQuery. MCP connects agents to tools; A2A connects agents to autonomous peers.

Under no circumstances may an agent inject raw HTML, JavaScript, CSS strings, or executable scripts into responses.

### 3.2. A2UI Contract (DOC-03)
The Lead Orchestrator constructs an adjacency tree of visual components validated against `apps/co-scientist/a2ui/catalog.json`:
- `InsightCard`: Clinical findings, evidence levels, and therapeutic summaries.
- `KnowledgeGraphView`: Interactive subgraph nodes and edges (Gene, Disease, Drug, Pathway).
- `PathwayChart`: Visual biochemical cascades and signaling pathways.
- `DrugRepurposingTable`: Ranked candidate therapeutics with mechanism-of-action and confidence.
- `EvidenceDrawer`: Curated literature citations, PubMed IDs, and clinical trial links.
- `MemoryTimeline`: Consolidated clinical entities and therapeutic hypotheses across turns.
- `SimulationViewer`: 3D continuous trajectory viewer for AlphaFold docking and cellular swarms.

### 3.3. Security & Zero Ambient Authority (DOC-02)
- **Zero Ambient Authority (ZAA)**: No ambient Google Cloud credentials or raw tokens passed to prompt contexts. Workload identity tokens are minted just-in-time and scoped strictly to minimal necessity (`PAT-ZAA`).
- **User Registration & Authentication**: Clinicians and researchers authenticate via Google Cloud Identity Platform / OIDC (OAuth2 + PKCE). Endpoints require short-lived (15 min) cryptographically signed JWT session tokens with claims (`sub`, `roles`, `tenant_id`, `exp`).
- **Container Sandboxing & Hardening**: All runtimes (e.g. Agent Engine managed sandboxes) enforce non-root execution (`USER 10001:10001`) with read-only root filesystems and tmpfs scratch space.
- **Least Privilege IAM**: The Lead Orchestrator Agent only requires read permissions on BigQuery and Spanner, and invoker access to Worker tier agents. Zero Cloud Run services are deployed.

### 3.4. Telemetry, Observability & Error Handling (DOC-01)
- **ADK >= v2.6.0 OpenTelemetry Instrumentation**: Distributed tracing and metric instruments conforming to GenAI Semantic Conventions:
  - Metric `gen_ai.client.token.usage` with `gen_ai.token.type` (`input` / `output`) and `gen_ai.request.model`.
  - Metric `gen_ai.client.operation.duration` (Histogram of model inference duration).
  - Spans: `agent.run` (with `session.id`, `user.id`), `llm.generate` (`gen_ai.system`, request model, token counts), `tool.execute`, and `agent.transfer` (A2A handshakes).
- **Structured Error Taxonomy**: Standardized JSON error schema with correlation IDs (`trace_id`, `span_id`, `user_id`, `session_id`), standardized HTTP error mapping, and defined fallback strategies for degraded backends.
- **Graceful Degradation**: Fallback to heuristic subgraphs or cached knowledge when remote compute pods (OMPL / PhysiCell) or live databases experience timeouts.

### 3.5. Mandatory Retrieval & Agent Observability Metrics (DOC-01)
All data retrieval pipelines and agentic reasoning workflows must record and report:
1. **Latency Breakdowns**:
   - `telemetry.latency.p50` (< 120 ms)
   - `telemetry.latency.p95` (< 500 ms)
   - `telemetry.latency.p99` (< 1500 ms)
   - Granular breakdown across local memory traversal, Cloud Spanner SPU queries, BigQuery analytical scans, and GKE continuous simulation compute.
2. **Token Consumption Telemetry**:
   - `llm.tokens.prompt`: Input context token volume.
   - `llm.tokens.completion`: Generated response token volume.
   - `llm.tokens.cached`: Tokens served via Vertex AI context caching (DOC-08 target > 60%).
3. **Information Retrieval (IR) Quality Metrics**:
   - **mAP (Mean Average Precision)**: Ranking accuracy of multi-hop biomedical paths (> 0.82).
   - **Precision@k**: Proportion of retrieved nodes/edges that are medically relevant (> 0.88 at $k=10$).
   - **Recall@k**: Proportion of known biological interactions successfully retrieved (> 0.80 at $k=10$).
4. **Agent Decision Quality Metric**:
   - **`agent.correct_algorithm_choice`**: Golden evaluation and runtime assertion tracking whether the Lead Orchestrator and Router selected the optimal graph algorithm (Dijkstra, A*, BFS/DFS, PageRank, WCC, Transitive Closure, RRT*, Boids) matching the clinician's query (> 0.95 accuracy).

### 3.6. Stateful Context & Memory Bank Standards (DOC-08, DOC-09)
- **Session Persistence**: Multi-turn chat history (user prompts, agent reasoning, declarative A2UI ASTs) is persisted in Cloud Spanner (`chat_sessions`, `chat_messages`) and mirrored in native Vertex AI Agent Engine Sessions.
- **Enterprise Memory Bank (`PAT-MEM-BANK`)**: Decouples working conversation memory from persistent factual state:
  - Asynchronous entity & hypothesis extraction at the end of each turn.
  - Progressive disclosure and semantic recall using BigQuery vector embeddings, mitigating catastrophic forgetting, session drift, and context window bloat.

---

## 4. Verification & Validation Gate
1. All directory nodes exist and match the canonical schema.
2. Root `pyproject.toml` binds the workspace packages (`packages/graphagent`, `apps/co-scientist`).
3. `AGENTS.md` and `guidelines_lookup` skill are registered under `.agents/`.
4. Guidelines MCP server is configured and executable over stdio/SSE.
5. A2UI catalog definitions and example JSON payloads parse successfully under JSON schema validators.
6. OpenTelemetry exporters successfully emit trace spans with latency p50/p95/p99, token counts, and retrieval metrics.
7. Golden evaluation suites assert `agent.correct_algorithm_choice` meets the >95% threshold.

