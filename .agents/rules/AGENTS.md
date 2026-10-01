# Antigravity Central Command: Workspace Architectural Rules

> **Applicability**: Monorepo root and all child packages/apps (`cancer-co-scientist-reusable-graphagents-architectural-kgraph`).  
> **Authority**: Governed by Enterprise Agents Guidelines MCP Server (`https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server`).

---

## 1. Architectural Guidance & MCP Server Governance
- **Mandatory MCP Alignment**: Before designing new components, agents, or data pipelines, developers and AI agents must consult the guidelines MCP server using the `.agents/skills/guidelines_lookup` skill or `specs/02-architecture-guidelines-mcp-integration.md`.
- **Referenced Guidelines**:
  - `DOC-01`: AI Agent Quality Engineering & Observability
  - `DOC-02`: Zero Ambient Authority (ZAA) & Agentic SecOps
  - `DOC-03`: Open AI Agent Protocol Stack & A2UI Declarative Interfaces
  - `DOC-08`: Context Engineering for Stateful Multi-Agent Meshes
  - `DOC-09`: Platform-Native State Management (Spanner Graph + BigQuery)

---

## 2. Multi-Agent Layer Separation Standards (DOC-03)
Strict boundary enforcement must be maintained between the four layers of the agent stack:
1. **User Experience Layer (A2UI)**: 
   - Agents emit **only** declarative, non-executable JSON schemas defined in `apps/co-scientist/a2ui/catalog.json`.
   - **Zero Executable Code Injection**: Never emit raw HTML, CSS, JavaScript, or executable code for frontend evaluation (prevents XSS and sandbox bypasses).
   - Component state bindings must use standard JSON pointer data binding.
2. **Orchestration Layer (Router & Lead Orchestrator)**:
   - Resides in `apps/co-scientist/agent/orchestrator.py` and `router.py`.
   - Responsible for intent classification, sub-task delegation, and A2UI assembly.
   - Does **not** perform raw database SQL or GQL queries directly.
3. **Worker Tier (Graph Agents)**:
   - Resides in `packages/graphagent/`.
   - Headless, reusable specialist agents that execute targeted queries over biomedical subgraphs.
   - Emits typed Pydantic payloads back to the Orchestrator.
4. **Tool & Knowledge Layer (Spanner Graph & BigQuery)**:
   - Property graph queries against `PrimeKGGraph` must use ISO GQL with parameterization.
   - Heavy aggregations and gene embeddings query BigQuery.

---

## 3. Security & Zero Ambient Authority (ZAA) (DOC-02)
- **Token Scoping**: Workloads must authenticate using fine-grained Google Cloud Workload Identity Federation or dedicated Service Accounts. Do not pass ambient environment credentials to agent contexts.
- **Least Privilege**: The Cloud Run Orchestrator service only requires read permissions on BigQuery and Spanner, and invoker access to the Worker tier.
- **Container Sandboxing**: All Dockerfiles (`apps/co-scientist/ui/Dockerfile`, Cloud Run containers) must execute as non-root users (`USER 10001:10001`).

---

## 4. Code & Quality Standards (DOC-01)
- **Language Requirements**: Python 3.11+ managed by `uv`. Strict type hints (`from __future__ import annotations`, Pydantic v2).
- **Observability**: OpenTelemetry tracing must be integrated across agent reasoning loops and database tools.
- **Testing**: Maintain unit tests in `tests/` alongside evaluation benchmarks for graph retrieval accuracy.
