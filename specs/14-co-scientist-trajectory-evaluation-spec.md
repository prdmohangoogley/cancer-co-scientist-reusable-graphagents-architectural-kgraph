# Spec 14: Co-Scientist Lead Orchestrator Trajectory Evaluation & Multi-Agent Observability Specification

**Status**: Approved / In Implementation  
**Tier**: Orchestration Tier (`apps/co-scientist/`)  
**Target Agent Engine**: `projects/301802433103/locations/us-east1/reasoningEngines/6824256356745216000`  
**Governing Guidelines**: `DOC-01` (AI Agent Quality Engineering), `DOC-02` (ZAA & Agentic SecOps), `DOC-03` (Open AI Agent Protocol & A2UI), `DOC-08` (Context Engineering for Stateful Agents), `DOC-09` (Platform-Native State Management)

---

## 1. Executive Problem Statement & Motivation

While the Graph Agent worker tier executes isolated property graph queries and specialized algorithms over PrimeKG, clinical oncologists do not interact with raw graph workers. Instead, they interact with the **Co-Scientist Lead Orchestrator**.

Evaluating the Lead Orchestrator requires verifying:
1. **Multi-Agent Protocol Delegation (`A2A`)**: The Orchestrator must correctly formulate clinical intents and delegate them to the autonomous worker tier (`cancer-co-scientist-graph-agent`) without bypassing architectural layers or issuing raw SQL/GQL queries directly (`DOC-03 §2`).
2. **Clinical Evidence & Regulatory Grounding**: Validating oncology guideline bodies (NCCN Category 1, FDA approvals, ASCO, OncoKB Evidence Levels) for biomarker-drug pairings (`verify_oncology_guidelines`).
3. **Stateful Context & Memory Bank Recall**: Ensuring persistent entity state (e.g. secondary mutations, active lines of therapy) is actively retrieved from and synchronized with the Vertex AI Memory Bank (`inspect_memory_bank` and `retrieve_memories`) (`DOC-08`).
4. **Declarative User Experience (A2UI)**: Generating safe, non-executable JSON component specifications conforming to `catalog.json` (`generate_a2ui_payload`) with zero frontend script injection (`DOC-03 §1`).

---

## 2. Core Architectural Principles (DOC-01, DOC-03, DOC-08)

### 2.1 Multi-Agent Layer Separation (DOC-03 §2)
The Lead Orchestrator acts strictly as the router, clinical synthesizer, and A2UI assembler:
- **Zero Raw Database Queries**: The Lead Orchestrator never queries Spanner Graph or BigQuery directly; all biomedical data gathering is delegated to `cancer-co-scientist-graph-agent` via `delegate_to_graph_agent`.
- **A2UI Declarative Interface**: All visualization commands emit declarative JSON schemas (`catalog.json`) rendered safely by the web client without raw HTML/JS evaluation.

### 2.2 Glass Box Trajectory Assertion Modes (DOC-01 §3)
Every evaluation case defines expected orchestration tool calls evaluated under three match modes:
- **`EXACT` Match**: Strictly regulated clinical trial matching and guideline verification protocols. Tools must execute in the exact order: `inspect_memory_bank` $\to$ `delegate_to_graph_agent` $\to$ `verify_oncology_guidelines` $\to$ `generate_a2ui_payload`.
- **`IN_ORDER` Match**: Multi-step clinical inquiry workflows (e.g., patient history review $\to$ graph agent delegation $\to$ A2UI surface rendering).
- **`ANY_ORDER` Match**: Parallel sub-task delegation (e.g., simultaneous continuous pocket docking and cellular invasion simulation).

### 2.3 Active Memory Bank Contextualization (DOC-08)
Multi-turn sessions actively retrieve scoped clinical entities using `MemoryBankServiceClient.retrieve_memories` under `user_id='oncology_director'`, ensuring persistent memory counters and token consumption are tracked on the Agent Platform console.

---

## 3. The 5 Lead Orchestrator Trajectory Scenarios

### Scenario 1: Multi-Agent Causal Resistance Delegation (`IN_ORDER` Match)
- **Clinical Goal**: Ingest complex metastatic NSCLC case and coordinate autonomous worker traversal.
- **Turn 1**: Clinician presents NSCLC patient with disease progression on 1st-generation EGFR TKI.
- **Turn 2**: Orchestrator inspects patient memory context (`inspect_memory_bank`) and delegates to worker agent (`delegate_to_graph_agent(algorithm_name='dijkstra', source_entity='EGFR T790M', target_entity='Osimertinib')`), then emits declarative A2UI payload (`generate_a2ui_payload`).
- **Autorater Target**: `multi_turn_trajectory_quality_v1 >= 0.85`, `multi_turn_task_success_v1 = 1.0`.

### Scenario 2: Structural Centrality & Master Gatekeeper Protocol (`IN_ORDER` Match)
- **Clinical Goal**: Coordinate interactome bottleneck identification and therapeutic guideline verification.
- **Turn 1**: Clinician requests identification of critical communication hubs in the PI3K-AKT-mTOR cascade.
- **Turn 2**: Orchestrator delegates structural betweenness analysis to Graph Agent (`delegate_to_graph_agent`), queries clinical evidence for targeted inhibitors (`verify_oncology_guidelines`), and renders an `InsightCard` via `generate_a2ui_payload`.
- **Autorater Target**: `multi_turn_trajectory_quality_v1 >= 0.85`, `final_response_quality_v1 >= 0.80`.

### Scenario 3: Continuous Molecular & Cellular Simulation Coordination (`ANY_ORDER` Match)
- **Clinical Goal**: Evaluate steric drug-target feasibility and macro-scale tumor swarming invasion dynamics.
- **Turn 1**: Clinician requests physical feasibility analysis for KRAS G12D inhibitor and glioblastoma swarm invasion.
- **Turn 2**: Orchestrator delegates continuous geometric trajectory planning (`ompl_rrt_star`) and multi-cellular swarming simulation (`physicell_boids`) in parallel, assembling a combined `SimulationViewer` A2UI surface.
- **Autorater Target**: `multi_turn_task_success_v1 >= 0.80`.

### Scenario 4: Longitudinal Temporal Resistance & Clonal Lineage Tracking (`IN_ORDER` Match)
- **Clinical Goal**: Track longitudinal clonal evolution across 24 months of targeted therapy.
- **Turn 1**: Clinician submits 24-month serial biopsy timestamped panel data.
- **Turn 2**: Orchestrator delegates interval graph traversal and algebraic connectivity bisection (`interval_edges` / `fiedler_lambda2`) to Graph Agent, synchronizes newly detected tertiary C797S resistance into the Memory Bank (`inspect_memory_bank`), and renders `MemoryTimeline` via `generate_a2ui_payload`.
- **Autorater Target**: `multi_turn_trajectory_quality_v1 >= 0.85`.

### Scenario 5: Master Precision Oncology Guideline & Discovery Protocol (`EXACT` Match)
- **Clinical Goal**: End-to-end multi-agent clinical consultation protocol from patient history to guideline-backed prescription.
- **Turn 1**: Scoped patient memory inspection (`inspect_memory_bank`).
- **Turn 2**: Graph agent interactome delegation (`delegate_to_graph_agent`).
- **Turn 3**: NCCN / FDA evidence verification (`verify_oncology_guidelines`).
- **Turn 4**: Interactive declarative clinical card assembly (`generate_a2ui_payload`).
- **Autorater Target**: `multi_turn_trajectory_quality_v1 = 1.0`, `multi_turn_tool_use_quality_v1 = 1.0`, `multi_turn_task_success_v1 = 1.0`.

---

## 4. Evaluatable-by-Design Data Schema

Each orchestration case is structured into an `agentplatform.types.EvalCase`:
```python
EvalCase(
    prompt=Content(parts=[Part.from_text(text="...")]),
    conversation_history=[
        Message(content=Content(parts=[Part.from_text(text="...")], role="user")),
        Message(content=Content(parts=[Part.from_text(text="...")], role="model")),
    ],
    intermediate_events=[
        Event(
            author="cancer_co_scientist_lead_orchestrator",
            content=Content(parts=[Part.from_function_call(name="...", args={...})], role="model")
        ),
        Event(
            author="cancer_co_scientist_lead_orchestrator",
            content=Content(parts=[Part.from_function_response(name="...", response={...})], role="tool")
        ),
    ],
    responses=[
        ResponseCandidate(response=Content(parts=[Part.from_text(text="...")]))
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
| **Multi-Agent Protocol Invariant** | $100\%$ Delegation | Architectural | Zero Direct GQL / SQL |
| **A2UI Invariant** | $100\%$ Declarative | Security | Zero Raw JS / HTML Injection |
| **Turn P95 Latency** | $< 15\text{ s}$ (Stream) | Telemetry | Cloud Monitoring / Trace |
| **Memory Bank Active Recall Count** | $> 0$ | Telemetry | Memory Bank Metrics |
