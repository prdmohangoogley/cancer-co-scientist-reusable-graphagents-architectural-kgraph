# Spec 02: Architecture Guidelines MCP Server Integration

**Status**: ACTIVE  
**Upstream Server**: [gea-agents-arch-guidelines-mcp-server](https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server)  
**Local Path**: `/Users/prdmohan/ge_spark_workspace/projects/architecture_best_practices_mcp`

---

## 1. Purpose & Scope
This specification defines how the `graphagents` monorepo interfaces with the Enterprise Agents Architectural Guidelines MCP Server. 

All specifications, architectural reviews, orchestration pipelines, and code generation steps must query the MCP server to ensure continuous conformance with Google Cloud AI agent architecture standards.

---

## 2. Integration Modes

The Guidelines MCP server supports two runtime integration modes:

### 2.1. Local Stdio Transport (Developer IDE & Antigravity CLI)
Antigravity and developer agents run the server as a local sub-process using `uv`:
```bash
uv --directory /Users/prdmohan/ge_spark_workspace/projects/architecture_best_practices_mcp run gea-mcp-server --transport stdio
```
Configuration is stored in `.agents/mcp_config.json`:
```json
{
  "mcpServers": {
    "gea-arch-guidelines": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/prdmohan/ge_spark_workspace/projects/architecture_best_practices_mcp",
        "run",
        "gea-mcp-server",
        "--transport",
        "stdio"
      ],
      "env": {
        "USE_MOCK_GRAPH": "true"
      }
    }
  }
}
```

### 2.2. Remote Server-Sent Events (SSE) Transport (Cloud Run / Orchestrator)
In production or remote staging environments, the server is hosted on Cloud Run:
```bash
uv run gea-mcp-server --transport sse --host 0.0.0.0 --port 8080
```
The Lead Orchestrator connects using `apps/co-scientist/agent/mcp_client.py` over HTTP/SSE.

---

## 3. Available Tools & Guidelines

| MCP Tool Name | Description | Example Arguments |
| :--- | :--- | :--- |
| `search_guidelines` | Keyword search across architectural knowledge base | `{"query": "a2ui", "limit": 5}` |
| `get_guideline_details` | Retrieve comprehensive markdown of a guideline | `{"guideline_id": "DOC-03"}` |
| `get_best_practice` | GQL query against Spanner Graph for topic patterns | `{"topic": "Zero Ambient Authority"}` |
| `evaluate_tradeoffs` | Comparative analysis between two architectural choices | `{"option_a": "Spanner Graph", "option_b": "Neo4j"}` |
| `deep_dive_guideline` | Analytical investigation of an architectural component | `{"component": "A2UI"}` |

---

## 4. Enforcement Protocol
1. **Spec Creation**: Whenever drafting a new spec under `specs/`, the author agent must invoke `search_guidelines` and cite the relevant guideline IDs (`DOC-xx`).
2. **Orchestrator Bootstrapping**: At startup, `apps/co-scientist/agent/orchestrator.py` verifies MCP connectivity via `apps/co-scientist/agent/mcp_client.py`.
3. **Developer Skill**: Developers can use `.agents/skills/guidelines_lookup/SKILL.md` to interactively query best practices during implementation.
