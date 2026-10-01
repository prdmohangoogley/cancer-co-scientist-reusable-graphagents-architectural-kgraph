# Spec 01: Monorepo Phase 1 - Scaffolding & Global Standards

**Milestone**: Phase 1 Scaffolding & Global Standards  
**Status**: APPROVED & IMPLEMENTED  
**Governing Architecture MCP**: [gea-agents-arch-guidelines-mcp-server](https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server)  
**Guidelines Cited**: `DOC-01`, `DOC-02`, `DOC-03`, `DOC-08`, `DOC-09`

---

## 1. Executive Summary & Context
The `graphagents` monorepo establishes an enterprise-grade platform uniting reusable biomedical graph intelligence libraries (**Workers**) with full-stack agentic applications (**Orchestrators**).

The flagship application is the **Cancer Co-Scientist**, an autonomous oncological reasoning system designed for clinicians and researchers. Its core architecture decouples cognitive tasks across three decoupled tiers:
1. **Lead Orchestrator (Router)**: Interprets unstructured clinical/biomedical inquiries, plans graph exploration steps, delegates sub-queries to domain-specific worker agents, and emits declarative **A2UI (Agent-to-UI)** payloads for safe client-side presentation.
2. **Graph Agent Workers**: Headless domain specialist agents built on Google ADK, executing ISO GQL graph traversals over **Cloud Spanner Graph** (housing the PrimeKG precision medicine knowledge graph) and analytical queries over **BigQuery**.
3. **Architectural Guidelines Engine**: A remote Model Context Protocol (MCP) server providing real-time best practice validation, pattern retrieval, and tradeoff evaluation to ensure adherence to Google Cloud enterprise agent standards.

---

## 2. Directory Hierarchy Specification

```markdown
graphagents/
├── .agents/                    # 🚀 Antigravity Central Command
│   ├── rules/                 # Always-active guidelines (AGENTS.md)
│   └── skills/                # Reusable developer skills (guidelines_lookup)
├── specs/                     # 📋 Tracked Technical Specifications
│   ├── 01-monorepo-phase1-scaffolding-and-global-standards.md
│   └── 02-architecture-guidelines-mcp-integration.md
├── docs/                       # 📖 Global Specs & OKF Guidelines
│   ├── architecture.md        # Comprehensive multi-agent architecture
│   └── okf_guidelines.md      # Ontology Knowledge Framework standards
├── infra/                      # 🏗️ Global Infrastructure (Terraform)
│   ├── datalake/              # Core GCS (OKF Data Lake)
│   └── primekg_staging/       # 🗄️ PrimeKG Staging & GCE Curl Pipelines
├── packages/                   # 🧩 REUSABLE PACKAGES & LIBRARIES
│   └── graphagent/            # Core Reusable Graph Agent Library (Worker Tier)
│       ├── adk/               # ADK definitions for PrimeKG traversal
│       ├── tools/             # GQL/SQL Traversal & Querying tools
│       ├── data_loaders/       # 🚚 PrimeKG Ingestion Pipelines
│       └── iac/               # Package-specific IaC (Spanner + BQ)
└── apps/                       # 🌐 FULL-STACK APPLICATIONS
    └── co-scientist/          # 🩺 Cancer Co-Scientist Application (Orchestrator Tier)
        ├── a2ui/              # 🎨 A2UI Artifacts (Catalog, Examples)
        │   ├── catalog.json   # Component definitions (Cards, Charts, etc.)
        │   └── examples/      # Few-shot prompts for UI generation
        ├── agent/             # 🧠 Lead Orchestrator, Router Logic
        │   ├── orchestrator.py# Main ADK Agent Loop
        │   ├── mcp_client.py   # Architecture Guidelines MCP Bridge
        │   └── router.py      # Intent Classification & Delegation
        ├── ui/                # 💻 A2UI Renderer Client (TypeScript/Lit)
        │   ├── src/
        │   ├── package.json
        │   └── Dockerfile
        └── iac/               # ☁️ Application Deployment IaC (Cloud Run)
```

---

## 3. Protocol Architecture & Invariants

### 3.1. Layer Separation (DOC-03)
Strict boundary enforcement:
- **Presentation**: `A2UI` (Declarative JSON UI schemas).
- **Agent Orchestration**: Router / ADK Host Agent.
- **Worker Federation**: Subagent task delegation.
- **Data & Tools**: `FastMCP` and ISO GQL over Cloud Spanner Graph.

Under no circumstances may an agent inject raw HTML, JavaScript, CSS strings, or executable scripts into responses.

### 3.2. A2UI Contract (DOC-03)
The Lead Orchestrator constructs an adjacency tree of visual components validated against `apps/co-scientist/a2ui/catalog.json`:
- `InsightCard`: Clinical findings, evidence levels, and therapeutic summaries.
- `KnowledgeGraphView`: Interactive subgraph nodes and edges (Gene, Disease, Drug, Pathway).
- `PathwayChart`: Visual biochemical cascades and signaling pathways.
- `DrugRepurposingTable`: Ranked candidate therapeutics with mechanism-of-action and confidence.
- `EvidenceDrawer`: Curated literature citations, PubMed IDs, and clinical trial links.

### 3.3. Security & Zero Ambient Authority (DOC-02)
- **Zero Ambient Authority (ZAA)**: No ambient Google Cloud credentials or raw tokens passed to prompt contexts. Workload identity tokens are minted just-in-time and scoped strictly to minimal necessity (`PAT-ZAA`).
- **User Registration & Authentication**: Clinicians and researchers authenticate via Google Cloud Identity Platform / OIDC (OAuth2 + PKCE). Endpoints require short-lived (15 min) cryptographically signed JWT session tokens with claims (`sub`, `roles`, `tenant_id`, `exp`).
- **Container Sandboxing & Hardening**: All Dockerfiles (e.g. `apps/co-scientist/ui/Dockerfile`, Cloud Run services) enforce non-root execution (`USER 10001:10001`) with read-only root filesystems and tmpfs scratch space.
- **Least Privilege IAM**: The Cloud Run Lead Orchestrator service only requires read permissions on BigQuery and Spanner, and internal invoker access to Worker tier containers.

### 3.4. Telemetry, Observability & Error Handling (DOC-01)
- **OpenTelemetry Instrumentation**: Distributed tracing across all agent reasoning loops (`invoke_agent`, `call_llm`), tool dispatches (`tool_call`), and database RPCs (`spanner.execute_query`, `bigquery.query`).
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
- **Session Persistence**: Multi-turn chat history (user prompts, agent reasoning, declarative A2UI ASTs) is persisted in Cloud Spanner (`chat_sessions`, `chat_messages`).
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

