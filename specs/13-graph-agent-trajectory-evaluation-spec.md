# Spec 13: Graph Agent Trajectory Evaluation & Memory Bank Activation Specification

**Status**: Approved / In Implementation  
**Tier**: Graph Agent Worker Tier (`packages/graphagent/`)  
**Target Agent Engine**: `projects/301802433103/locations/us-east1/reasoningEngines/4359942935643422720`  
**Governing Guidelines**: `DOC-01` (AI Agent Quality Engineering), `DOC-08` (Context Engineering for Stateful Agents), `DOC-09` (Platform-Native State Management)

---

## 1. Executive Problem Statement & Motivation

Point-in-time single-turn prompt evaluations fail to validate autonomous agents for two critical reasons:
1. **The "Lucky Guess" Hazard (DOC-01 §3)**: A model can produce a plausible clinical summary while skipping mandatory intermediate tools, calling wrong parameters, or hallucinating graph traversals.
2. **Missing Console Observability**: Single-turn evaluations do not populate multi-turn task completion rates, turn-by-turn latency distributions (P50/P95), or tool-use quality metrics on the Google Cloud Agent Platform console. Furthermore, absent active `retrieve_memories` invocations, the Memories dashboard reports `Retrieved memories count: 0`.

To satisfy `DOC-01` and `DOC-08`, this specification establishes a **Glass Box Trajectory Evaluation Suite** at the level of the Graph Agent (`cancer-co-scientist-graph-agent`).

---

## 2. Core Architectural Principles (DOC-01 & DOC-08)

### 2.1 Glass Box Trajectory Assertion Modes (DOC-01 §3)
Every evaluation case defines expected intermediate tool events (`FunctionCall` and `FunctionResponse`) evaluated under three match modes:
- **`EXACT` Match**: Strictly regulated clinical protocols. The exact sequence of tool names and serialized argument key-values must match without deviation.
- **`IN_ORDER` Match**: Multi-step causal workflows (e.g., entity grounding $\to$ subgraph extraction $\to$ algorithmic traversal). Harmless interleaved queries are permitted, but causal sequence order is strictly enforced.
- **`ANY_ORDER` Match**: Independent parallel data gathering (e.g., running molecular pocket simulation and cellular swarming simulation).

### 2.2 Active Memory Bank Retrieval (DOC-08 §3)
During multi-turn execution, the agent actively queries the Vertex AI Memory Bank via `MemoryBankServiceClient.retrieve_memories` with scoped patient context (`user_id`, `session_id`). This anchors the agent's reasoning in confirmed genomic facts and updates `Retrieved memories count` and memory token usage metrics on the Agent Platform dashboard.

---

## 3. The 5 Graph Agent Trajectory Scenarios

### Scenario 1: Discrete Resistance Traversal (`IN_ORDER` Match)
- **Clinical Goal**: Identify secondary resistance pathways bypassing EGFR inhibition in NSCLC.
- **Turn 1 (Grounding)**: Clinician submits `EGFR T790M` mutation profile.
  - *Expected Tool*: `query_primekg_graph(source_entity='EGFR T790M', depth=2)`
- **Turn 2 (Algorithmic Traversal)**: Clinician requests shortest biochemical pathway to `Osimertinib`.
  - *Expected Tool*: `execute_discrete_graph_algorithm(algorithm_name='dijkstra', source_entity='EGFR T790M', target_entity='Osimertinib')`
- **Autorater Target**: `multi_turn_trajectory_quality_v1 >= 0.85`, `multi_turn_task_success_v1 = 1.0`.

### Scenario 2: Structural Centrality & Bottleneck Discovery (`IN_ORDER` Match)
- **Clinical Goal**: Detect gatekeeper proteins in the PI3K-AKT-mTOR signaling cascade.
- **Turn 1 (Neighborhood Extraction)**: Clinician requests 2-hop interactome neighborhood of `PIK3CA`.
  - *Expected Tool*: `explore_target_subgraph_neighborhood(focal_entity='PIK3CA', depth=2)`
- **Turn 2 (Centrality Ranking)**: Clinician requests top gatekeeper vulnerabilities.
  - *Expected Tool*: `analyze_structural_centrality_gatekeepers(target_subnetwork='PIK3CA', algorithm='betweenness')`
- **Autorater Target**: `tool_use_quality_v1 >= 0.90`, `multi_turn_trajectory_quality_v1 >= 0.85`.

### Scenario 3: Continuous Simulation — Pocket to Invasion (`ANY_ORDER` Match)
- **Clinical Goal**: Assess KRAS G12D conformational pocket obstacle traversal and Glioblastoma hypoxic invasion.
- **Turn 1 (Conformational Docking)**: Assess steric binding feasibility for KRAS G12D small-molecule inhibitor.
  - *Expected Tool*: `run_continuous_simulation(algorithm_name='ompl_rrt_star', target_entity='KRAS_G12D')`
- **Turn 2 (Cellular Invasion)**: Evaluate collective swarming density under hypoxia.
  - *Expected Tool*: `run_continuous_simulation(algorithm_name='physicell_boids', target_entity='Glioblastoma')`
- **Autorater Target**: `multi_turn_task_success_v1 >= 0.80`.

### Scenario 4: Temporal Longitudinal Resistance Emergence (`IN_ORDER` Match)
- **Clinical Goal**: Track emergence of secondary resistance over a 24-month clinical interval.
- **Turn 1 (Temporal Graph)**: Clinician supplies 24-month longitudinal panel data under Osimertinib.
  - *Expected Tool*: `run_temporal_tracking(algorithm_name='interval_edges', source_entity='EGFR', target_timestamp='2025-06-01')`
- **Turn 2 (Spectral Partition)**: Clinician requests algebraic connectivity bisection for resistant subgraphs.
  - *Expected Tool*: `run_temporal_tracking(algorithm_name='fiedler_lambda2', source_entity='EGFR', target_timestamp='2025-06-01')`
- **Autorater Target**: `multi_turn_trajectory_quality_v1 >= 0.85`.

### Scenario 5: Master Precision Oncology Protocol (`EXACT` Match)
- **Clinical Goal**: End-to-end clinical discovery protocol from variant ingestion to combination therapy.
- **Turn 1**: Scoped Memory Bank recall (`retrieve_memories`).
- **Turn 2**: Knowledge graph neighborhood traversal (`query_primekg_graph`).
- **Turn 3**: Calculate betweenness gatekeepers (`analyze_structural_centrality_gatekeepers`).
- **Turn 4**: FDA / NCCN guideline evidence verification (`validate_precision_oncology_pathway`).
- **Autorater Target**: `multi_turn_trajectory_quality_v1 = 1.0`, `multi_turn_tool_use_quality_v1 = 1.0`.

---

## 4. Evaluatable-by-Design Data Schema

Each trajectory case is structured into an `agentplatform.types.EvalCase`:
```python
EvalCase(
    prompt=Content(parts=[Part.from_text(text="...")]),
    conversation_history=[
        Message(content=Content(parts=[Part.from_text(text="...")], role="user")),
        Message(content=Content(parts=[Part.from_text(text="...")], role="model")),
    ],
    intermediate_events=[
        Event(
            author="cancer_co_scientist_graph_agent",
            content=Content(parts=[Part.from_function_call(name="...", args={...})], role="model")
        ),
        Event(
            author="cancer_co_scientist_graph_agent",
            content=Content(parts=[Part.from_function_response(name="...", response={...})], role="tool")
        ),
    ],
    reference=ResponseCandidate(response=Content(parts=[Part.from_text(text="...")])),
)
```

---

## 5. Metrics & Verification Gates

| Metric | Target | Type | Evaluator |
| :--- | :---: | :---: | :--- |
| **`multi_turn_trajectory_quality_v1`** | $\ge 0.85$ | Rubric | Vertex AI Autorater |
| **`multi_turn_tool_use_quality_v1`** | $\ge 0.90$ | Rubric | Vertex AI Autorater |
| **`multi_turn_task_success_v1`** | $\ge 0.80$ | Rubric | Vertex AI Autorater |
| **`final_response_quality_v1`** | $\ge 0.80$ | Rubric | Vertex AI Autorater |
| **Deterministic Glass Box Adherence** | $100\%$ | Code | `GlassBoxTrajectoryEvaluator` |
| **Turn P95 Latency** | $< 350\text{ ms}$ (Tool) / $< 15\text{ s}$ (Stream) | Telemetry | Cloud Monitoring / Trace |
| **Memory Bank Recall Count** | $> 0$ | Telemetry | Memory Bank Metrics |
