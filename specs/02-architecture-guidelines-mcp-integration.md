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

### 2.2. Triplification & Knowledge Ingestion
```bash
uv run nl2kg-pipeline extract --source-dir docs/specs
uv run nl2kg-pipeline load --project-id your-gcp-project
```

### 2.3. Server Deployment
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
