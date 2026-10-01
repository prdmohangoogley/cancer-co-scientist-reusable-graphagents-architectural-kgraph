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
- No ambient Google Cloud credentials passed to prompt context.
- Cloud Run orchestrator and GCE staging instances authenticate through granular Google IAM Service Accounts with workload identity federation.
- Containerized workloads run as non-root unprivileged users.

### 3.4. State Management (DOC-08, DOC-09)
- Stateless worker agents query Cloud Spanner Graph using deterministic ISO GQL.
- User session state and multi-turn clinical reasoning history reside in external memory/session stores.

---

## 4. Verification & Validation Gate
1. All directory nodes exist and match the canonical schema.
2. Root `pyproject.toml` binds the workspace packages (`packages/graphagent`, `apps/co-scientist`).
3. `AGENTS.md` and `guidelines_lookup` skill are registered under `.agents/`.
4. Guidelines MCP server is configured and executable over stdio/SSE.
5. A2UI catalog definitions and example JSON payloads parse successfully under JSON schema validators.
