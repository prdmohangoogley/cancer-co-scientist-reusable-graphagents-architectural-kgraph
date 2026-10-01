# AGY Goal: Phase 6.1 - Reusable Graph Agent Library (ADK Workers) & Algorithm Engine

## 📌 Context
Build the core `graphagent` Worker package using **Google ADK**. This package acts as the computational engine for the Cancer Co-Scientist. It exposes atomic tools optimized to execute complex graph algorithms across **Spanner Graph**, **BigQuery Graph**, and specialized compute pods.

---

## 📊 Algorithm Coverage Matrix & Optimization Strategy

### 🟢 1. Discrete Graph Algorithms (Native GQL in Spanner / BQ Graph)
These algorithms operate on the biological/knowledge graph topology (e.g., PrimeKG, Hetionet).

| Algorithm / Capability | Optimization & Implementation Path |
| :--- | :--- |
| **DFS / BFS** | Implemented using Native GQL Path Patterns (`MATCH p = (n)-[e*1..N]->(m)`). Optimized in Spanner by starting traversals from lower-cardinality nodes. |
| **Dijkstra / A*** | Point-to-point shortest path finding using Native GQL. Optimized with **Vector Search heuristics** embedded in node embeddings for A* targeting. |
| **D* Lite (Incremental)** | Real-time replanning by querying **Spanner Delta Tables**; only recomputes paths where edge weights (e.g., interaction confidence) have mutated. |
| **Connected Components (SCC/WCC)** | Executed via **Built-in Spanner Graph Algorithms** (e.g., `WeaklyConnectedComponents`) using Data Boost for zero impact on transactional traffic. |
| **Topological Sort** | Used for signaling cascades; executed via GQL traversal or DAG sequencing in ADK middlewares. |
| **Transitive Closure / Reachability** | Pre-calculated for critical metabolic paths or executed via BigQuery Graph `GRAPH_EXPAND` functions for large-scale analytical reachability. |
| **Community Detection** | Executed in BigQuery Graph or Spanner Graph catalog algorithms (e.g., Label Propagation) to identify disease modules. |
| **Ego-Network Inspection** | Extracted using depth-limited GQL queries (`k-hop`) tailored to a focal drug or patient node. |

---

### 🟡 2. Structural & Node-Level Analytics
Evaluating importance, vulnerability, and bottleneck density.

| Algorithm / Capability | Optimization & Implementation Path |
| :--- | :--- |
| **Node Statistics** (Degree, Betweenness) | **Spanner PageRank Algorithm** identifies "Hub" proteins. Betweenness identifies "Gatekeeper" adapter modules bridging disconnected signaling pathways. |
| **Subgraph Statistics** (Density, Bridges) | GQL aggregations identify overly tight circular packages (high density) or single points of failure (literal bridges/cut-vertices in the graph). |

---

### 🔵 3. Continuous Geometry & Multi-Agent Simulation (GKE Delegated)
*Note: Purely discrete codebases or graph DBs do not handle continuous 3D space. These are orchestrated by ADK Workers but computed on GKE.*

| Algorithm / Capability | Optimization & Implementation Path |
| :--- | :--- |
| **RRT* / PRM** | **Motion Planning Delegation Tool:** Workers invoke containerized **OMPL** on GKE to sample continuous high-dimensional space for **AlphaFold** protein docking/ligand binding paths. |
| **Reynolds' Boids** | **Simulation Injection Tool:** Workers generate parameter sets (Cohesion, Separation, Alignment) to run **PhysiCell** agent-based simulations of cellular swarming in tumor microenvironments. |

---

### 🟣 4. Temporal & Spatiotemporal Tracking
Capturing evolution over time (Git history, live telemetry, disease progression).

| Algorithm / Capability | Optimization & Implementation Path |
| :--- | :--- |
| **Temporal Graph Tracking** | Modeled using **Interval-Timestamped Edges** in Spanner Graph. GQL filtering applied: `valid_from <= t_x < valid_to`. |
| **Temporal Metric Profiling** | Rolling window metrics (e.g., Algebraic Connectivity $\lambda_2$) computed in BigQuery to flag collapsing organ-system coupling or swarm partitioning. |
| **Visualization Data Generators** | Tools emit structured **JSON ASTs** or **A2UI payloads** to stream 2D Hierarchical DAGs or 3D Geospatial HUDs to the client. |

---

## 🛠️ Tasks

1. **GQL Toolset:** Implement atomic Python tools in `packages/graphagent/tools/` for each GQL-based algorithm, maximizing pushdown to Spanner's Serverless Processing Units (SPUs).
2. **Container Connectors:** Implement wrappers for firing off RRT* (AlphaFold) and Boids (PhysiCell) compute jobs and extracting the resultant trajectory data.
3. **Data Type Handlers:** Ensure all outputs are strictly bound to Pydantic models to feed standard **A2UI (Agent-to-UI)** component catalogs.

## ✅ Acceptance Criteria
- Tools successfully abstract complex GQL/SQL/Container invocations into simple natural-language-callable functions.
- Latency for operational traversals (DFS/BFS) is within expectations.
- GKE hooks successfully dispatch compute-heavy continuous simulations.

# AGY Goal: Monorepo Phase 6.2 - Reusable Graph Agent Library & Telemetry

## 📌 Context
Consolidate the Graph capabilities into a reusable package. Every algorithmic worker must be fully instrumented with **OpenTelemetry (OTel)** to track tool latency, computational overhead, and execution bottlenecks.

---

## 🛠️ Tasks

### 1. Tools Exporter (`packages/graphagent/tools/`)
- Expose GQL/SQL querying wrappers as atomic, consumable tools.
- Implement explicit **Custom Spans** around heavy GQL algorithms and simulation dispatches using `opentelemetry.trace`.

### 2. OpenTelemetry Bindings (`packages/graphagent/observability/`)
- Enable standard GenAI semantic conventions for ADK:
  - Agent invocations (`invoke_agent`).
  - LLM call metrics (tokens, latency) via `call_llm`.
  - Tool call monitoring (`tool_call` / `tool_response`).
- Inject custom attributes into spans to distinguish workloads:
  - `gcp.vertex.agent.workflow_type` (e.g., `Discrete`, `Continuous`, `Temporal`).
  - `gcp.vertex.agent.db_target` (e.g., `Spanner`, `BigQuery`).

### 3. Performance & Retrieval Observability Metrics (DOC-01)
Configure the ADK environment to emit and monitor the following mandatory metrics:

| Metric Category | Metric Identifier | Target SLA | Telemetry Attribute | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Latency** | **p50 Latency** | `< 45 ms` | `telemetry.algorithm.latency.p50` | Median latency for native discrete GQL traversals (DFS/BFS, Dijkstra) |
| **Latency** | **p95 Latency** | `< 350 ms` | `telemetry.algorithm.latency.p95` | 95th percentile latency across community detection & PageRank |
| **Latency** | **p99 Latency** | `< 1200 ms` | `telemetry.algorithm.latency.p99` | 99th percentile tail latency for GKE simulation launch & temporal tracking |
| **Token Consumption** | **Prompt Tokens** | Tracked | `llm.tokens.prompt` | Input tokens consumed when passing algorithm parameters |
| **Token Consumption** | **Completion Tokens**| Tracked | `llm.tokens.completion` | Output tokens generated in algorithm synthesis |
| **Token Consumption** | **Cached Tokens** | `> 65%` | `llm.tokens.cached` | Context caching hit rate for static graph topology definitions |
| **Retrieval Quality** | **mAP** | `> 0.86` | `eval.retrieval.map` | Mean Average Precision of returned paths/subgraphs across 15 algorithms |
| **Retrieval Quality** | **Precision@k** | `> 0.89` ($k=10$) | `eval.retrieval.precision_at_k` | Precision of top-$k$ returned entities / pathway nodes |
| **Retrieval Quality** | **Recall@k** | `> 0.84` ($k=10$) | `eval.retrieval.recall_at_k` | Recall of ground-truth known interaction targets |
| **Agent Decision** | **Correct Algorithm Choice**| `> 0.95` | `agent.correct_algorithm_choice` | Evaluates whether Worker/Router chose optimal algorithm from the 15-algorithm matrix |

### 4. Security Hardening & Zero Ambient Authority (DOC-02)
- **Zero Ambient Authority (ZAA)**: Workers execute without ambient cloud credentials; IAM tokens are scoped exclusively to `roles/spanner.databaseReader` and `roles/bigquery.dataViewer`.
- **GKE Simulation Sandboxing**: Continuous simulation containers (OMPL RRT*, PhysiCell Boids) run as unprivileged users (`USER 10001:10001`) with seccomp profiles and network policies restricting egress to the local cluster.

### 5. Evaluation Harness & Quality Release Gate (`packages/graphagent/evals/`)
- Golden dataset evaluation test suite (`evals/test_algorithm_routing_eval.py`):
  - Injects synthetic clinical intent prompts across all 4 categories (Discrete, Structural, Continuous, Temporal).
  - Asserts that `agent.correct_algorithm_choice` achieves $\ge 95\%$ accuracy before any release is promoted.
  - Verifies OpenTelemetry trace generation and latency percentiles.

---

## ✅ Acceptance Criteria
- The package is installable locally (`pip install ./packages/graphagent`).
- Spans for all 15 algorithmic Workers successfully emit to Google Cloud Trace with fine-grained custom attributes (`gcp.vertex.agent.workflow_type`, `gcp.vertex.agent.db_target`).
- Latency meets budget (p50 < 45ms, p95 < 350ms, p99 < 1200ms).
- Retrieval metrics meet quality thresholds (mAP > 0.86, Precision@10 > 0.89, Recall@10 > 0.84).
- `agent.correct_algorithm_choice` score is validated at $\ge 95\%$ across the golden evaluation suite.
- GKE simulation connectors gracefully degrade with fallback heuristic graph statistics when continuous compute is unavailable.

