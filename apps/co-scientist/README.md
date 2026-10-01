# Cancer Co-Scientist (Orchestrator Tier)

The **Cancer Co-Scientist** is an autonomous multi-agent clinical discovery application. It serves as the Lead Orchestrator tier, coordinating intent routing, guidelines verification, worker delegation, and declarative **A2UI (Agent-to-UI)** generation.

---

## 🏗️ Directory Layout

```markdown
apps/co-scientist/
├── a2ui/              # 🎨 A2UI Artifacts (Catalog, Examples)
│   ├── catalog.json   # Declarative component schemas (Cards, Tables, Graphs)
│   └── examples/      # Few-shot prompts and example payloads
├── agent/             # 🧠 Lead Orchestrator, Router Logic
│   ├── orchestrator.py# Main ADK Agent Loop & A2UI generator
│   ├── mcp_client.py   # Architecture Guidelines FastMCP Bridge
│   └── router.py      # Intent Classification & Delegation
├── ui/                # 💻 A2UI Renderer Client (TypeScript/Lit)
│   ├── src/
│   ├── package.json
│   └── Dockerfile
└── iac/               # ☁️ Application Deployment IaC (Cloud Run)
    ├── main.tf
    ├── cloud_run.tf
    └── variables.tf
```

---

## ⚡ Running Locally

### 1. Launch the Orchestrator Service
```bash
uv run uvicorn apps.co_scientist.agent.orchestrator:app --reload --port 8000
```

### 2. Launch the A2UI Frontend Client
```bash
cd apps/co-scientist/ui
npm install
npm run dev
```
Navigate to `http://localhost:5173` to interact with the Co-Scientist clinical portal.
