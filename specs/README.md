# Architecture & Engineering Specifications (`specs/`)

This directory maintains the authoritative, version-controlled technical specifications, milestone definitions, and architectural decisions for the `graphagents` monorepo.

## 📌 Architectural Governance
Per project requirements, **every specification in this directory must align with and cite architectural standards from the official guidelines MCP server**:
- **MCP Server Repository**: [gea-agents-arch-guidelines-mcp-server](https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server)
- **Local Workspace**: `/Users/prdmohan/ge_spark_workspace/projects/architecture_best_practices_mcp`

### Core Guidelines Referenced
| ID | Title | Core Focus | Application in Monorepo |
| :--- | :--- | :--- | :--- |
| **DOC-01** | AI Agent Quality Engineering | Systematic evaluation, observability, cost & security | Worker eval harness, OpenTelemetry tracing across agents |
| **DOC-02** | Vibe Coding Agent Security & Evaluation | Sandboxing, Zero Ambient Authority (ZAA), SecOps | Agent Engine IAM token scoping, non-root sandboxes |
| **DOC-03** | Open AI Agent Protocol Stack | MCP, A2A, UCP, AP2/x402, and A2UI layering | A2UI non-executable UI generation, MCP tool integration |
| **DOC-08** | Context Engineering for Stateful AI Agents | Sessions, Memory Banks, RAG architectures | State tracking between router and worker graph agents |
| **DOC-09** | Platform-Native State Management | Cloud Spanner Graph + BigQuery runtime persistence | Spanner Graph ISO GQL traversal of PrimeKG |

---

## 📑 Specification Index

| Milestone / File | Status | Description |
| :--- | :--- | :--- |
| [01-monorepo-phase1-scaffolding-and-global-standards.md](./01-monorepo-phase1-scaffolding-and-global-standards.md) | **Active** | Phase 1 Scaffolding, directory hierarchy, A2UI catalog, and Central Command setup |
| [02-architecture-guidelines-mcp-integration.md](./02-architecture-guidelines-mcp-integration.md) | **Active** | Guidelines FastMCP bridge, stdio/SSE client integration, and validation rules |
| [03-primekg-dataloader-spec.md](./03-primekg-dataloader-spec.md) | **Active** | Phase 2 PrimeKG data acquisition, GCE fast runner, and GCS landing zone staging |
| [04-worker-tier-primekg-ingestion-spec.md](./04-worker-tier-primekg-ingestion-spec.md) | **Active** | Phase 3 Worker Tier ingestion into Cloud Spanner Graph (ISO GQL) & BigQuery |
| [05-worker-tier-graph-traversal-tools-spec.md](./05-worker-tier-graph-traversal-tools-spec.md) | **Active** | Phase 4 Worker Tier Graph Traversal, Query Tools (ISO GQL / BigQuery) & ADK |
| [06-graphagents-adkworkers-spec.md](./06-graphagents-adkworkers-spec.md) | **Active** | Phase 6 Reusable Graph Agent Library (ADK Workers), 15-Algorithm Engine & Telemetry |
| [07-co-scientist-spec-web-app.md](./07-co-scientist-spec-web-app.md) | **Active** | Phase 7 Lead Orchestrator, A2UI Web App, Security Hardening, Chat History & Memory Bank |
| [08-graph-visualization-agent-spec.md](./08-graph-visualization-agent-spec.md) | **Active** | Phase 8 Graph Visualization Specialist Agent & Interactive A2UI Graph Visualizer |
| [09-gemini-enterprise-agents-deployment-spec.md](./09-gemini-enterprise-agents-deployment-spec.md) | **Active** | Phase 9 Gemini Enterprise Agents Production Deployment, Vertex AI Agent Engine & Cloud Observability |
| [10-gea-console-observability-evals-memorybank-spec.md](./10-gea-console-observability-evals-memorybank-spec.md) | **Active** | Phase 10 GEA Console Dashboard Operationalization, Interactive Playground, Vertex AI Evaluation Bench, Memory Bank & Continuous Multi-Agent Monitors |
| [11-a2a-protocol-mesh-agent-card-federation-spec.md](./11-a2a-protocol-mesh-agent-card-federation-spec.md) | **Active** | Phase 11 A2A Protocol Mesh, Agent Card Federation & Dual GEA Runtime Integration |
| [12-gea-categorized-experiments-and-live-bench-spec.md](./12-gea-categorized-experiments-and-live-bench-spec.md) | **Active** | Phase 12 GEA Console Categorized Evaluation Experiments, Live Multi-Turn Benchmark Suite, Distributed Tracing & Memory Bank Telemetry |

---

## 🎯 Global Mandatory Observability & Quality Standards (Audited Across All Specs)

Every retrieval pipeline, agent reasoning loop, and algorithmic worker in this monorepo must adhere to:

1. **Retrieval Latency Budget**:
   - **p50**: `< 25-120 ms` (native GQL / 1-hop lookups)
   - **p95**: `< 200-500 ms` (2-hop traversals & community detection)
   - **p99**: `< 850-1500 ms` (heavy BigQuery joins & continuous simulations)
2. **Token Consumption Telemetry**:
   - Continuous instrumentation of `llm.tokens.prompt`, `llm.tokens.completion`, and `llm.tokens.cached` (>60% cache hit SLA via Vertex AI context caching).
3. **Information Retrieval (IR) Evaluation Metrics**:
   - **mAP (Mean Average Precision)**: `> 0.82 - 0.88` across multi-hop biomedical subgraph retrieval.
   - **Precision@k**: `> 0.88 - 0.90` ($k=10$).
   - **Recall@k**: `> 0.80 - 0.85` ($k=10$).
4. **Agent Decision Quality Metric**:
   - **`agent.correct_algorithm_choice`**: `> 0.95` accuracy on golden evaluation benchmarks assessing whether Orchestrators/Routers/Workers select the optimal graph traversal algorithm for clinical intent.
5. **Security Hardening (DOC-02)**:
   - Zero Ambient Authority (ZAA): Tokens minted just-in-time and scoped strictly.
   - OAuth2 / OIDC authentication with short-lived JWT session tokens for Web App users.
   - Containers run non-root (`USER 10001:10001`) with read-only root filesystems.
6. **State & Memory Bank (DOC-08, DOC-09)**:
   - Spanner-backed ACID session persistence (`chat_sessions`, `chat_messages`).
   - Managed Memory Bank (`PAT-MEM-BANK`) with automated entity/hypothesis consolidation and progressive semantic recall.



