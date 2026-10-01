---
name: guidelines_lookup
description: >-
  Query architectural guidelines, design patterns, security rules (Zero Ambient Authority, ZAA),
  and engineering tradeoffs from the Enterprise Agents Architectural Guidelines FastMCP server.
  Use when architecting agents, designing A2UI payloads, or implementing data/tool pipelines.
---

# Architecture Guidelines Lookup Skill

This skill empowers Antigravity and developers to interactively query Google Cloud enterprise agent design patterns and guidelines hosted by the `gea-agents-arch-guidelines-mcp-server`.

## 🛠️ Usage Procedures

### 1. Fast Guidelines Search
Search for specific architectural concepts (e.g., `A2UI`, `ZAA`, `Memory Bank`, `Spanner Graph`):
```bash
python .agents/skills/guidelines_lookup/scripts/lookup.py --query "a2ui"
```

### 2. Retrieve Specific Guideline Details
Fetch full summary and references by Guideline ID (`DOC-01`, `DOC-02`, `DOC-03`, `DOC-08`, `DOC-09`):
```bash
python .agents/skills/guidelines_lookup/scripts/lookup.py --id "DOC-03"
```

### 3. Evaluate Architecture Tradeoffs
Compare two implementation patterns (e.g., `Spanner Graph` vs `Neo4j`, or `A2UI` vs `Raw HTML`):
```bash
python .agents/skills/guidelines_lookup/scripts/lookup.py --tradeoff-a "Spanner Graph" --tradeoff-b "Neo4j"
```

### 4. Fetch Best Practice by Topic
Query ISO GQL best practice entities for a domain topic:
```bash
python .agents/skills/guidelines_lookup/scripts/lookup.py --best-practice "Zero Ambient Authority"
```

---

## 📚 References & Offline Fallbacks
For quick offline reference when network access to the MCP server is unavailable, refer to:
- [Guidelines Summary Reference](./references/guidelines_summary.md)
- [Monorepo Spec 02: MCP Integration](../../specs/02-architecture-guidelines-mcp-integration.md)
