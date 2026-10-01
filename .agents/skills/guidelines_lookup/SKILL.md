---
name: guidelines_lookup
description: >-
  Query architectural guidelines, design patterns, security rules (Zero Ambient Authority, ZAA),
  and engineering tradeoffs from the Enterprise Agents Architectural Guidelines FastMCP server.
  Queries live Cloud Spanner Graph (ArchGuidelinesGraph) via ISO GQL and BigQuery analytics.
---

# Architecture Guidelines Lookup Skill

This skill empowers Antigravity and developers to interactively query Google Cloud enterprise agent design patterns and guidelines hosted by the `gea-agents-arch-guidelines-mcp-server`.

Live queries connect directly to:
- **Cloud Spanner Graph**: `ArchGuidelinesGraph` in instance `gea-arch-guidelines-spanner` (ISO GQL)
- **BigQuery Analytics**: `gea_arch_guidelines_analytics` in project `fivedaysai-prd-sandbox-317383`

---

## 🛠️ Usage Procedures

### 1. Live ISO GQL Query against Cloud Spanner Graph
Query operational best practice and architectural pattern entities via Cloud Spanner Graph:
```bash
python .agents/skills/guidelines_lookup/scripts/lookup.py --best-practice "security"
```
*Executes ISO GQL `QUERY_BEST_PRACTICES_BY_TOPIC` on `ArchGuidelinesGraph` and returns live execution latency (`latency_ms: ~13ms`).*

### 2. Live Analytical Deep Dive against Google BigQuery
Perform deep-dive analytical investigation of component patterns, antipattern hazards, and remedies:
```bash
python .agents/skills/guidelines_lookup/scripts/lookup.py --deep-dive "Security"
```
*Queries federated tables `guidelines`, `patterns`, `antipatterns` in BigQuery dataset `gea_arch_guidelines_analytics`.*

### 3. Fast Guidelines Search
Search for specific architectural concepts (e.g., `A2UI`, `ZAA`, `Memory Bank`, `Spanner Graph`):
```bash
python .agents/skills/guidelines_lookup/scripts/lookup.py --query "protocol"
```

### 4. Retrieve Specific Guideline Details
Fetch full summary and references by Guideline ID (`DOC-01`, `DOC-02`, `DOC-03`, `DOC-08`, `DOC-09`):
```bash
python .agents/skills/guidelines_lookup/scripts/lookup.py --id "DOC-03"
```

### 5. Evaluate Architecture Tradeoffs
Compare two implementation patterns (e.g., `Spanner Graph` vs `Neo4j`, or `A2UI` vs `Raw HTML`):
```bash
python .agents/skills/guidelines_lookup/scripts/lookup.py --tradeoff-a "Spanner Graph" --tradeoff-b "Neo4j"
```

---

## 📚 References & Offline Fallbacks
For quick offline reference when network access is unavailable, pass `--mock` or refer to:
- [Guidelines Summary Reference](./references/guidelines_summary.md)
- [Monorepo Spec 02: MCP Integration](../../specs/02-architecture-guidelines-mcp-integration.md)
