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

### 3. Performance & Latency Metrics
Configure the ADK environment to emit the following derived metrics:
- **Tool Latency Breakdowns:** Distinguish between local traversal time, GKE container spin-up, and external API latency.
- **Continuous Compute Latencies:** Track total runtime of RRT* (AlphaFold) and Boids (PhysiCell) simulation packages.
- **Success/Error Paths:** Emit custom metrics for GQL pipeline crashes or validation failures.

### 4. Evaluation Harness (`packages/graphagent/evals/`)
- Create benchmark scripts to inject artificial bottlenecks and verify that the OpenTelemetry pipeline captures latency spikes appropriately.

---

## ✅ Acceptance Criteria
- The package is installable locally (`pip install ./packages/graphagent`).
- Spans for algorithmic Workers successfully emit to Google Cloud Trace with fine-grained custom attributes.
- Average invocation latency for standard `PrimeKGSight` local traversals meets budget (<100ms) with visible latency breakdowns in telemetry.
