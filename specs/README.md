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
| **DOC-02** | Vibe Coding Agent Security & Evaluation | Sandboxing, Zero Ambient Authority (ZAA), SecOps | Cloud Run / GCE IAM token scoping, non-root containers |
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
