# Spec 02: Architecture Guidelines MCP Server Integration

**Status**: ACTIVE  
**Upstream Server**: [gea-agents-arch-guidelines-mcp-server](https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server)  
**Local Path**: `/Users/prdmohan/ge_spark_workspace/projects/architecture_best_practices_mcp`  
**GCP Project**: `fivedaysai-prd-sandbox-317383`  
**Spanner Instance**: `gea-arch-guidelines-spanner` (`arch_guidelines_graph`)  
**BigQuery Dataset**: `gea_arch_guidelines_analytics`

---

## 1. Purpose & Scope
This specification defines how the `graphagents` monorepo interfaces with the Enterprise Agents Architectural Guidelines MCP Server. 

All specifications, architectural reviews, orchestration pipelines, and code generation steps must query the MCP server to ensure continuous conformance with Google Cloud AI agent architecture standards.

### 1.1. The MCP vs. A2A Boundary Rule (DOC-03)
Per **DOC-03 (Open AI Agent Protocol Stack)**:
- **MCP (Model Context Protocol)**: Connects an agent to a **tool or deterministic data store** (e.g., Cloud Spanner Graph ISO GQL queries, BigQuery analytics, Architecture Guidelines MCP Server). MCP tools are deterministic functions with defined input/output JSON schemas.
- **A2A (Agent-to-Agent Protocol)**: Connects an agent to an **autonomous peer agent** (e.g., Lead Orchestrator to `cancer-co-scientist-graph-agent`). A2A carries goal-level delegation, machine-readable Agent Cards (`.well-known/agent-card.json`), scoped task contracts, and versioned artifact exchanges across organizational and domain boundaries.
- **Anti-Pattern Prohibited**: Never use MCP as a substitute for A2A by reaching past an autonomous agent to query its database directly. The Lead Orchestrator must NEVER query `PrimeKGGraph` directly; it must delegate graph analysis to `cancer-co-scientist-graph-agent` via A2A!

---

## 2. Deploying the MCP Server in Your Own GCP Project

Teams deploying their own instance of the guidelines server should refer to the upstream repository:
👉 **[https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server](https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server)**

### 2.1. Infrastructure as Code (Terraform)
The upstream `iac/` folder provisions:
1. **Google Cloud Spanner**: `gea-arch-guidelines-spanner` with `arch_guidelines_graph` Property Graph DDL (`Nodes`, `Edges`, `ArchGuidelinesGraph`).
2. **Google BigQuery**: `gea_arch_guidelines_analytics` datasets (`guidelines`, `patterns`, `antipatterns`, `guideline_embeddings`).
3. **Google Cloud Storage**: Bucket for knowledge corpus and NL2KG pipelines.

```bash
cd iac
cp terraform.tfvars.example terraform.tfvars
# Update project_id = "your-gcp-project"
terraform init && terraform apply
```

### 2.2. Acquire OKF Architecture Data & Bootstrap Knowledge Base
The complete 20-document architectural knowledge bundle is hosted in Google Cloud Storage:
`gs://gea_agent_development_architectural_best_practices_1790796607/okf/`

To bootstrap your own project's knowledge base:
```bash
# 1. Create target GCS bucket in your project
gcloud storage buckets create gs://YOUR_TARGET_BUCKET_NAME \
  --project=your-gcp-project \
  --location=us-central1 \
  --uniform-bucket-level-access

# 2. Dump/sync the OKF bundle directly to your bucket
gcloud storage cp --recursive \
  gs://gea_agent_development_architectural_best_practices_1790796607/okf \
  gs://YOUR_TARGET_BUCKET_NAME/

# 3. (Optional) Download locally
mkdir -p data/okf
gcloud storage cp --recursive \
  gs://gea_agent_development_architectural_best_practices_1790796607/okf \
  ./data/
```

### 2.3. Triplification & Knowledge Ingestion (NL2KG)
```bash
# Extract entities and relationships from local concepts or synced bucket
uv run nl2kg-pipeline extract --source-dir ./data/okf/concepts/

# Validate ontology constraints
uv run nl2kg-pipeline validate --input-file build/graph/triples.json

# Commit to Cloud Spanner Graph & BigQuery
uv run nl2kg-pipeline load --project-id your-gcp-project
```

### 2.4. Server Deployment
- **Cloud Run (SSE mode)**:
  ```bash
  gcloud run deploy gea-arch-guidelines-mcp \
    --source . \
    --region us-central1 \
    --set-env-vars "GCP_PROJECT_ID=your-project,SPANNER_INSTANCE=gea-arch-guidelines-spanner,SPANNER_DATABASE=arch_guidelines_graph,BQ_DATASET=gea_arch_guidelines_analytics,USE_MOCK_GRAPH=false"
  ```
- **Local Stdio Mode (Antigravity CLI / Developer IDE)**:
  Configure `~/.gemini/config/mcp_config.json`:
  ```json
  {
    "mcpServers": {
      "gea-arch-guidelines": {
        "command": "uv",
        "args": [
          "--directory",
          "/path/to/gea-agents-arch-guidelines-mcp-server",
          "run",
          "gea-mcp-server",
          "--transport",
          "stdio"
        ],
        "env": {
          "GCP_PROJECT_ID": "fivedaysai-prd-sandbox-317383",
          "SPANNER_INSTANCE_ID": "gea-arch-guidelines-spanner",
          "SPANNER_DATABASE_ID": "arch_guidelines_graph",
          "BQ_DATASET_ID": "gea_arch_guidelines_analytics",
          "USE_MOCK_GRAPH": "false",
          "GOOGLE_APPLICATION_CREDENTIALS": "/Users/prdmohan/.config/gcloud/application_default_credentials.json"
        }
      }
    }
  }
  ```

---

## 3. Live Invocation Benchmarks & Query Stats

| Benchmark Target | Query Type | Backend Store | Live Latency | Status & Source |
| :--- | :--- | :--- | :--- | :--- |
| `get_best_practice("security")` | ISO GQL Traversal | Cloud Spanner Graph | **13.76 ms** | `success` (`spanner_graph`) |
| `deep_dive_guideline("Quality")` | Federated Multi-Table SQL | Google BigQuery | **2128.03 ms** | `success` (`bigquery_analytics`) |
| `process_clinical_inquiry(...)` | Orchestrator Agent Loop | ADK + MCP + A2UI | **1915.53 ms** | `success` (`A2UI_SURFACE`) |

### Verified Output: Cloud Spanner Graph
```text
=== [MCP Tool: get_best_practice] ISO GQL Spanner Graph Query for: 'security' ===
Status:       success
Query Source: spanner_graph (Cloud Spanner Graph)
Latency:      13.76 ms
Total Matches:10
Patterns:
  - JIT Downscoped Credentials (DOC-02)
  - Multimodal Rendered Artifact Evaluation
  - Defense-in-Depth Security Architecture
  - Stateful Circuit Breaker with Git Checkpointing
  - Vibe Diff with Hardware MFA
```

### Verified Output: BigQuery Analytics
```text
=== [MCP Tool: deep_dive_guideline] BigQuery Analytics Query for: 'Quality' ===
Status:       success
Query Source: bigquery_analytics (Google BigQuery)
Latency:      2128.03 ms
Patterns:
  - Quality Scorecard as Executable Release Gate (DOC-01)
  - Glass Box Trajectory Assertion
  - Black Box Golden Dataset Regression
  - Calibrated LLM Judge
```

---

## 4. Security Hardening & Zero Ambient Authority (DOC-02)

To satisfy `PAT-ZAA` during MCP communication:
1. **Workload Identity Federation**: The Lead Orchestrator connects to the guidelines MCP server using short-lived Google OpenID Connect (OIDC) identity tokens minted on-demand via the metadata server or direct stdio process execution, scoped exclusively to authorized service identities.
2. **Zero Ambient Credentials**: Neither the local developer environment nor the Agent Engine execution environments hold permanent service account keys in environment variables or code repositories.
3. **Runtime Sandbox**: The guidelines MCP server executes inside unprivileged environments (`USER 10001:10001`) with read-only root filesystems and restricted network egress. Zero Cloud Run services are deployed in the Cancer Co-Scientist system.

---

## 5. Telemetry, Observability Management & Error Handling (DOC-01)

### 5.1. OpenTelemetry Custom Spans & Attributes
The MCP client (`apps/co-scientist/agent/mcp_client.py`) is instrumented with custom spans around all remote tool executions:
- `mcp.tool_call`: Span enclosing tool request dispatch and response deserialization.
- Attributes:
  - `mcp.server_name`: `gea-arch-guidelines`
  - `mcp.tool_name`: `get_best_practice`, `deep_dive_guideline`, `search_guidelines`, `evaluate_design_tradeoffs`
  - `mcp.query_category`: `#quality`, `#security`, `#runtime`, `#context`, `#protocols`
  - `mcp.execution_latency_ms`: Execution time in milliseconds
  - `mcp.backend_source`: `spanner_graph`, `bigquery_analytics`, `embedded_cache`

### 5.2. Circuit Breaking & Graceful Fallback
- **Timeout Threshold**: Calls to `get_best_practice` timeout at 500ms; `deep_dive_guideline` timeouts at 4000ms.
- **Circuit Breaker**: After 3 consecutive network failures or 504 timeouts, the client trips into OPEN state for 30 seconds, automatically routing queries to the local embedded guideline cache (`data/okf/`) without blocking the Orchestrator loop.
- **Structured Error Taxonomy**: Emits standardized JSON errors with correlation IDs (`correlation_id`, `mcp_error_code`, `fallback_used`).

---

## 6. Retrieval & Agent Observability Metrics (DOC-01)

To ensure the highest standard of architectural knowledge retrieval and agent reasoning quality:

| Metric Dimension | Metric Identifier | Target / SLA | Telemetry Attribute | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Latency** | **p50 Latency** | `< 25 ms` | `telemetry.mcp.latency.p50` | Median latency for Spanner Graph ISO GQL pattern retrieval |
| **Latency** | **p95 Latency** | `< 300 ms` | `telemetry.mcp.latency.p95` | 95th percentile latency across Spanner and cache hits |
| **Latency** | **p99 Latency** | `< 2500 ms` | `telemetry.mcp.latency.p99` | 99th percentile tail latency for BigQuery analytical joins |
| **Token Consumption** | **Prompt Tokens** | Tracked | `llm.tokens.prompt` | Input tokens consumed when guidelines are injected into prompt context |
| **Token Consumption** | **Completion Tokens**| Tracked | `llm.tokens.completion` | Tokens generated by Orchestrator synthesizing architectural guidance |
| **Token Consumption** | **Cached Tokens** | `> 65%` | `llm.tokens.cached` | Token caching hit rate for static guideline catalogs via Vertex AI |
| **Retrieval Quality** | **mAP** | `> 0.88` | `eval.retrieval.map` | Mean Average Precision of retrieved guidelines against architectural rubrics |
| **Retrieval Quality** | **Precision@k** | `> 0.90` ($k=5$) | `eval.retrieval.precision_at_k` | Precision of top-$k$ retrieved patterns for design query |
| **Retrieval Quality** | **Recall@k** | `> 0.85` ($k=5$) | `eval.retrieval.recall_at_k` | Fraction of relevant architectural patterns captured |
| **Agent Decision** | **Correct Algorithm Choice**| `> 0.95` | `agent.correct_algorithm_choice` | Accuracy of agent selecting appropriate MCP tool (e.g. topological lookup vs BQ deep-dive vs tradeoff matrix) |

