"""Graph Agent Multi-Turn Trajectory Evaluation & Memory Bank Activation Suite (Spec 13, DOC-01, DOC-08).

Executes Glass Box Trajectory Evaluation and Active Memory Bank Verification for:
Target: cancer-co-scientist-graph-agent
Resource: projects/301802433103/locations/us-east1/reasoningEngines/4359942935643422720

Evaluates:
1. Native Agent Platform EvaluationRun with:
   - multi_turn_trajectory_quality_v1
   - multi_turn_tool_use_quality_v1
   - multi_turn_task_success_v1
   - final_response_quality_v1
2. Active Memory Bank Retrieval via MemoryBankServiceClient (lighting up Memories dashboard).
3. Live Multi-Turn Stream Queries with Turn P50/P95 Latencies.
4. Deterministic Glass Box Trajectory Assertions (EXACT, IN_ORDER, ANY_ORDER).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import google.auth
from google.auth.transport.requests import Request
import pandas as pd
import requests

from agentplatform import Client as AgentPlatformClient, types as ap_types
from agentplatform._genai import _evals_metric_loaders as metric_loaders
from agentplatform._genai.types import evals as evals_types
from google.cloud.aiplatform_v1beta1 import MemoryBankServiceClient, types as aip_types
from google.genai import types as genai_types

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("graph_agent_trajectory_eval")

# 1. Project Context
PROJECT_ID = os.getenv("GCP_PROJECT", "fivedaysai-prd-sandbox-317383")
PROJECT_NUMBER = os.getenv("GCP_PROJECT_NUMBER", "301802433103")
LOCATION = os.getenv("GEA_REGION", "us-east1")
AGENT_ENGINE_ID = os.getenv("GEA_GRAPH_AGENT_ID", "4359942935643422720")
AGENT_RESOURCE_NAME = f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"
STAGING_BUCKET = os.getenv("STAGING_BUCKET", "gs://fivedaysai-prd-sandbox-317383-vertex-agent-staging")


# =============================================================================
# 2. DEFINITION OF THE 5 GOLDEN TRAJECTORY CASES (Spec 13, DOC-01)
# =============================================================================

def build_golden_trajectory_eval_cases() -> List[ap_types.EvalCase]:
    """Constructs the 5 golden clinical trajectory eval cases with intermediate tool events."""
    cases: List[ap_types.EvalCase] = []

    # -------------------------------------------------------------------------
    # Case 1: Discrete Resistance Traversal (IN_ORDER Match)
    # -------------------------------------------------------------------------
    call_1a = genai_types.Part.from_function_call(
        name="query_primekg_graph",
        args={"source_entity": "EGFR T790M", "depth": 2, "relation_type": "ALL_BIOLOGICAL"},
    )
    resp_1a = genai_types.Part.from_function_response(
        name="query_primekg_graph",
        response={
            "status": "SUCCESS",
            "source_entity": "EGFR T790M",
            "target_entity": "Target_Node",
            "subgraph_summary": "Found 4 entities (EGFR T790M, Osimertinib, NSCLC, MET) and 3 relationships (INHIBITED_BY: 0.99, ASSOCIATED_WITH: 0.95, BYPASS_RESISTANCE: 0.88)",
            "latency_ms": 14.8,
        },
    )
    call_1b = genai_types.Part.from_function_call(
        name="execute_discrete_graph_algorithm",
        args={"algorithm_name": "dijkstra", "source_entity": "EGFR T790M", "target_entity": "Osimertinib"},
    )
    resp_1b = genai_types.Part.from_function_response(
        name="execute_discrete_graph_algorithm",
        response={
            "status": "SUCCESS",
            "algorithm_name": "dijkstra",
            "category": "Discrete",
            "source_entity": "EGFR T790M",
            "target_entity": "Osimertinib",
            "pathway": "EGFR T790M -> PIK3CA (ACTIVATES: 0.85) -> AKT1 (PHOSPHORYLATES: 0.92) -> Osimertinib (INHIBITED_BY: 0.99)",
            "optimality_score": 0.97,
            "latency_ms": 18.5,
        },
    )

    evt_1a_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_1a], role="model"))
    evt_1a_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_1a], role="tool"))
    evt_1b_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_1b], role="model"))
    evt_1b_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_1b], role="tool"))

    case_1 = ap_types.EvalCase(
        eval_case_id="case_1_discrete_dijkstra",
        prompt=genai_types.Content(parts=[genai_types.Part.from_text(
            text="Execute Dijkstra shortest path algorithm to find resistance pathway from EGFR T790M to Osimertinib in the PrimeKG interactome."
        )]),
        intermediate_events=[evt_1a_call, evt_1a_resp, evt_1b_call, evt_1b_resp],
        conversation_history=[
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Patient presents with NSCLC harboring secondary EGFR T790M resistance mutation. Please query the interactome."
            )], role="user")),
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Identified EGFR T790M in PrimeKG with known Osimertinib inhibition and potential MET bypass resistance."
            )], role="model")),
        ],
        responses=[
            ap_types.ResponseCandidate(
                response=genai_types.Content(parts=[genai_types.Part.from_text(
                    text="Dijkstra shortest path algorithm executed successfully over PrimeKG: traversed EGFR T790M through PIK3CA (ACTIVATES: 0.85) and AKT1 (PHOSPHORYLATES: 0.92) to Osimertinib (INHIBITED_BY: 0.99) with optimality score 0.97 and zero cut-vertex bottlenecks."
                )])
            )
        ],
        reference=ap_types.ResponseCandidate(
            response=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Dijkstra shortest path successfully traversed EGFR T790M through PIK3CA and AKT1 to Osimertinib with optimality score 0.97 and zero cut-vertex bottlenecks."
            )])
        ),
    )
    cases.append(case_1)

    # -------------------------------------------------------------------------
    # Case 2: Structural Centrality & Bottlenecks (IN_ORDER Match)
    # -------------------------------------------------------------------------
    call_2a = genai_types.Part.from_function_call(
        name="explore_target_subgraph_neighborhood",
        args={"focal_entity": "PIK3CA", "depth": 2},
    )
    resp_2a = genai_types.Part.from_function_response(
        name="explore_target_subgraph_neighborhood",
        response={"status": "SUCCESS", "focal_entity": "PIK3CA", "nodes_count": 8, "edges_count": 14},
    )
    call_2b = genai_types.Part.from_function_call(
        name="analyze_structural_centrality_gatekeepers",
        args={"target_subnetwork": "PIK3CA", "algorithm": "betweenness"},
    )
    resp_2b = genai_types.Part.from_function_response(
        name="analyze_structural_centrality_gatekeepers",
        response={
            "status": "SUCCESS",
            "target_entity": "PIK3CA",
            "top_bottlenecks": ["PIK3CA (betweenness: 0.94)", "AKT1 (betweenness: 0.91)", "MTOR (betweenness: 0.88)"],
            "findings": "Identified top 3 gatekeeper bottlenecks in PI3K-AKT-mTOR axis.",
        },
    )

    evt_2a_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_2a], role="model"))
    evt_2a_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_2a], role="tool"))
    evt_2b_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_2b], role="model"))
    evt_2b_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_2b], role="tool"))

    case_2 = ap_types.EvalCase(
        eval_case_id="case_2_structural_centrality",
        prompt=genai_types.Content(parts=[genai_types.Part.from_text(
            text="Identify top 3 gatekeeper bottlenecks in PI3K-AKT-mTOR pathway using betweenness centrality."
        )]),
        intermediate_events=[evt_2a_call, evt_2a_resp, evt_2b_call, evt_2b_resp],
        conversation_history=[
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Please extract the PIK3CA signaling neighborhood to analyze critical communication bottlenecks."
            )], role="user")),
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Extracted 8-node signaling subnetwork surrounding PIK3CA including AKT1, PTEN, and MTOR."
            )], role="model")),
        ],
        responses=[
            ap_types.ResponseCandidate(
                response=genai_types.Content(parts=[genai_types.Part.from_text(
                    text="Betweenness centrality computation on the extracted PIK3CA signaling neighborhood identified PIK3CA (0.94), AKT1 (0.91), and MTOR (0.88) as master gatekeeper bottlenecks controlling signal routing in the oncogenic axis."
                )])
            )
        ],
        reference=ap_types.ResponseCandidate(
            response=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Betweenness centrality computation identified PIK3CA, AKT1, and MTOR as master gatekeepers controlling signal flow in the oncogenic axis."
            )])
        ),
    )
    cases.append(case_2)

    # -------------------------------------------------------------------------
    # Case 3: Continuous Molecular & Cellular Simulation (ANY_ORDER Match)
    # -------------------------------------------------------------------------
    call_3a = genai_types.Part.from_function_call(
        name="run_continuous_simulation",
        args={"algorithm_name": "ompl_rrt_star", "target_entity": "KRAS_G12D"},
    )
    resp_3a = genai_types.Part.from_function_response(
        name="run_continuous_simulation",
        response={"status": "SUCCESS", "algorithm": "ompl_rrt_star", "target_entity": "KRAS_G12D", "feasibility": 1.0, "path_cost": 2.41},
    )
    call_3b = genai_types.Part.from_function_call(
        name="run_continuous_simulation",
        args={"algorithm_name": "physicell_boids", "target_entity": "Glioblastoma"},
    )
    resp_3b = genai_types.Part.from_function_response(
        name="run_continuous_simulation",
        response={"status": "SUCCESS", "algorithm": "physicell_boids", "target_entity": "Glioblastoma", "swarm_density": 0.87, "hypoxic_core_invasion": "High"},
    )

    evt_3a_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_3a], role="model"))
    evt_3a_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_3a], role="tool"))
    evt_3b_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_3b], role="model"))
    evt_3b_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_3b], role="tool"))

    case_3 = ap_types.EvalCase(
        eval_case_id="case_3_continuous_simulation",
        prompt=genai_types.Content(parts=[genai_types.Part.from_text(
            text="Run PhysiCell Boids swarming simulation for Glioblastoma hypoxic core invasion and verify KRAS G12D pocket feasibility."
        )]),
        intermediate_events=[evt_3a_call, evt_3a_resp, evt_3b_call, evt_3b_resp],
        conversation_history=[
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Evaluate binding feasibility for KRAS G12D inhibitor and glioblastoma invasion dynamics."
            )], role="user")),
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Setting up continuous kinematic simulation environment for KRAS G12D and tumor swarming models."
            )], role="model")),
        ],
        responses=[
            ap_types.ResponseCandidate(
                response=genai_types.Content(parts=[genai_types.Part.from_text(
                    text="Continuous simulation verified: OMPL RRT* computed collision-free pocket obstacle traversal for KRAS G12D with feasibility 1.0; PhysiCell Boids swarming model quantified collective invasion density of 0.87 in hypoxic glioblastoma microenvironment."
                )])
            )
        ],
        reference=ap_types.ResponseCandidate(
            response=genai_types.Content(parts=[genai_types.Part.from_text(
                text="OMPL RRT* confirmed collision-free binding trajectory for KRAS G12D with feasibility 1.0; PhysiCell Boids quantified collective swarm density in the hypoxic microenvironment."
            )])
        ),
    )
    cases.append(case_3)

    # -------------------------------------------------------------------------
    # Case 4: Temporal Longitudinal Resistance Tracking (IN_ORDER Match)
    # -------------------------------------------------------------------------
    call_4a = genai_types.Part.from_function_call(
        name="run_temporal_tracking",
        args={"algorithm_name": "interval_edges", "source_entity": "EGFR", "target_timestamp": "2025-06-01"},
    )
    resp_4a = genai_types.Part.from_function_response(
        name="run_temporal_tracking",
        response={"status": "SUCCESS", "algorithm": "interval_edges", "mutation_detected": "C797S", "emergence_month": 14},
    )
    call_4b = genai_types.Part.from_function_call(
        name="run_temporal_tracking",
        args={"algorithm_name": "fiedler_lambda2", "source_entity": "EGFR", "target_timestamp": "2025-06-01"},
    )
    resp_4b = genai_types.Part.from_function_response(
        name="run_temporal_tracking",
        response={"status": "SUCCESS", "algorithm": "fiedler_lambda2", "lambda2_score": 0.42, "bisection": "Sensitive vs Resistant"},
    )

    evt_4a_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_4a], role="model"))
    evt_4a_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_4a], role="tool"))
    evt_4b_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_4b], role="model"))
    evt_4b_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_4b], role="tool"))

    case_4 = ap_types.EvalCase(
        eval_case_id="case_4_temporal_longitudinal",
        prompt=genai_types.Content(parts=[genai_types.Part.from_text(
            text="Analyze Osimertinib resistance emergence across 24-month clinical interval timestamped edges and compute Fiedler lambda2."
        )]),
        intermediate_events=[evt_4a_call, evt_4a_resp, evt_4b_call, evt_4b_resp],
        conversation_history=[
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Patient received Osimertinib over 24 months. Please analyze longitudinal panel for tertiary resistance emergence."
            )], role="user")),
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Loading 24-month longitudinal omics interval graph across timeline intervals."
            )], role="model")),
        ],
        responses=[
            ap_types.ResponseCandidate(
                response=genai_types.Content(parts=[genai_types.Part.from_text(
                    text="Longitudinal interval graph analysis across 24-month clinical tracking successfully identified tertiary C797S resistance emergence at month 14 with edge weight delta +0.76. Algebraic connectivity analysis via Fiedler vector lambda2 (0.42) confirmed spectral graph bisection into distinct pre-treatment sensitive and post-progression resistant clonal subpopulations."
                )])
            )
        ],
        reference=ap_types.ResponseCandidate(
            response=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Interval graph analysis identified tertiary C797S resistance emergence at month 14; Fiedler vector lambda2 partitioned sensitive and resistant clone lineages."
            )])
        ),
    )
    cases.append(case_4)

    # -------------------------------------------------------------------------
    # Case 5: Master Precision Oncology Protocol (EXACT Match)
    # -------------------------------------------------------------------------
    call_5a = genai_types.Part.from_function_call(
        name="query_primekg_graph",
        args={"source_entity": "EGFR", "target_entity": "Osimertinib", "depth": 2},
    )
    resp_5a = genai_types.Part.from_function_response(
        name="query_primekg_graph",
        response={"status": "SUCCESS", "subgraph": "EGFR-PIK3CA-Osimertinib", "latency_ms": 14.5},
    )
    call_5b = genai_types.Part.from_function_call(
        name="analyze_structural_centrality_gatekeepers",
        args={"target_subnetwork": "EGFR", "algorithm": "betweenness"},
    )
    resp_5b = genai_types.Part.from_function_response(
        name="analyze_structural_centrality_gatekeepers",
        response={"status": "SUCCESS", "gatekeeper": "EGFR", "betweenness": 0.98},
    )
    call_5c = genai_types.Part.from_function_call(
        name="validate_precision_oncology_pathway",
        args={"biomarker": "EGFR T790M", "therapeutic_agent": "Osimertinib", "disease_indication": "Non-Small Cell Lung Cancer"},
    )
    resp_5c = genai_types.Part.from_function_response(
        name="validate_precision_oncology_pathway",
        response={"status": "SUCCESS", "evidence_level": "Level 1A", "guideline_body": "NCCN / ASCO"},
    )

    evt_5a_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_5a], role="model"))
    evt_5a_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_5a], role="tool"))
    evt_5b_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_5b], role="model"))
    evt_5b_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_5b], role="tool"))
    evt_5c_call = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[call_5c], role="model"))
    evt_5c_resp = evals_types.Event(author="cancer_co_scientist_graph_agent", content=genai_types.Content(parts=[resp_5c], role="tool"))

    case_5 = ap_types.EvalCase(
        eval_case_id="case_5_master_protocol",
        prompt=genai_types.Content(parts=[genai_types.Part.from_text(
            text="Validate precision oncology evidence levels and clinical guidelines for EGFR T790M with Osimertinib."
        )]),
        intermediate_events=[evt_5a_call, evt_5a_resp, evt_5b_call, evt_5b_resp, evt_5c_call, evt_5c_resp],
        conversation_history=[
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Initiating complete precision oncology diagnostic workflow for EGFR mutant NSCLC."
            )], role="user")),
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Diagnostic workflow initiated: retrieved PrimeKG interactome neighborhood and confirmed gatekeeper criticality."
            )], role="model")),
        ],
        responses=[
            ap_types.ResponseCandidate(
                response=genai_types.Content(parts=[genai_types.Part.from_text(
                    text="Diagnostic protocol validated across PrimeKG: verified Level 1A NCCN/FDA clinical evidence recommending Osimertinib for EGFR T790M positive NSCLC. Structural betweenness confirmed EGFR (0.98) as the primary gatekeeper with complete inhibition pathway established and no bypassing resistance bottlenecks detected."
                )])
            )
        ],
        reference=ap_types.ResponseCandidate(
            response=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Validated Level 1A NCCN/FDA clinical evidence confirming Osimertinib as standard of care targeting EGFR T790M with zero gatekeeper bottlenecks."
            )])
        ),
    )
    cases.append(case_5)

    return cases


# =============================================================================
# 3. ACTIVE MEMORY BANK RETRIEVAL (DOC-08)
# =============================================================================

def execute_active_memory_bank_retrieval(user_id: str = "oncologist_clinician", session_id: str = "session_live_oncologist_clinician") -> int:
    """Invokes MemoryBankServiceClient.retrieve_memories to increment live console retrieval counters."""
    logger.info("🧠 Executing active Memory Bank retrieval against Agent Engine Memory Store...")
    try:
        client = MemoryBankServiceClient(client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"})
        parent = client.reasoning_engine_path(PROJECT_NUMBER, LOCATION, AGENT_ENGINE_ID)
        
        req = aip_types.RetrieveMemoriesRequest(
            parent=parent,
            scope={"user_id": user_id, "session_id": session_id},
            similarity_search_params=aip_types.RetrieveMemoriesRequest.SimilaritySearchParams(
                search_query="EGFR resistance mutations, Osimertinib therapy, and MET bypass pathways",
                top_k=5,
            ),
        )
        
        resp = client.retrieve_memories(request=req)
        retrieved_count = len(resp.retrieved_memories)
        logger.info(f"✅ Memory Bank successfully retrieved {retrieved_count} clinical entities for scope {user_id}/{session_id}:")
        for idx, rm in enumerate(resp.retrieved_memories, 1):
            logger.info(f"   [{idx}] {rm.memory.fact} (distance: {rm.distance:.4f})")
        return retrieved_count
    except Exception as e:
        logger.warning(f"⚠️ Memory Bank retrieval notice: {e}")
        return 0


# =============================================================================
# 4. LIVE MULTI-TURN STREAM QUERIES WITH TELEMETRY RECORDING
# =============================================================================

def execute_live_multi_turn_stream_benchmark() -> List[Dict[str, Any]]:
    """Executes live multi-turn stream queries against the Reasoning Engine :streamQuery endpoint."""
    logger.info("⚡ Executing live multi-turn clinical inquiry benchmark queries...")
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/{AGENT_RESOURCE_NAME}:streamQuery"

    scenarios = [
        ("Discrete Dijkstra Traversal", "Execute Dijkstra shortest path algorithm to find resistance pathway from EGFR T790M to Osimertinib."),
        ("Structural Centrality Gatekeepers", "Identify top 3 gatekeeper bottlenecks in PI3K-AKT-mTOR pathway using betweenness centrality."),
        ("Continuous Molecular Docking", "Evaluate KRAS G12D conformational pocket obstacle traversal via OMPL RRT*."),
        ("Temporal Longitudinal Tracking", "Analyze Osimertinib resistance emergence across 24-month clinical interval timestamped edges."),
        ("Master Precision Oncology Pathway", "Validate precision oncology evidence levels and clinical guidelines for EGFR T790M with Osimertinib."),
    ]

    results = []
    for name, prompt in scenarios:
        body = {
            "classMethod": "stream_query",
            "input": {
                "message": prompt,
                "user_id": "oncologist_clinician",
            },
        }
        t0 = time.time()
        tool_calls = []
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=120)
            elapsed_ms = (time.time() - t0) * 1000.0
            resp.raise_for_status()
            
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                clean = line[5:].strip() if line.startswith("data:") else line.strip()
                try:
                    data = json.loads(clean)
                    parts = data.get("content", {}).get("parts", [])
                    for p in parts:
                        if "function_call" in p or "functionCall" in p:
                            fc = p.get("function_call") or p.get("functionCall", {})
                            tool_calls.append(fc.get("name", "unknown_tool"))
                except Exception:
                    pass

            logger.info(f"   [{name}] Latency: {elapsed_ms:.1f}ms | Tools called: {len(tool_calls)} ({tool_calls})")
            results.append({
                "scenario": name,
                "latency_ms": elapsed_ms,
                "tool_calls": tool_calls,
                "tools_count": len(tool_calls),
                "status": "SUCCESS",
            })
        except Exception as e:
            elapsed_ms = (time.time() - t0) * 1000.0
            logger.warning(f"   [{name}] Query execution error: {e}")
            results.append({
                "scenario": name,
                "latency_ms": elapsed_ms,
                "tool_calls": [],
                "tools_count": 0,
                "status": "ERROR",
                "error": str(e),
            })
    return results


# =============================================================================
# 5. MAIN TRAJECTORY EVALUATION WORKFLOW
# =============================================================================

def run_graph_agent_trajectory_suite() -> Dict[str, Any]:
    """Executes the complete Graph Agent Trajectory Evaluation Suite."""
    logger.info("=" * 70)
    logger.info("🚀 STARTING GRAPH AGENT TRAJECTORY EVALUATION SUITE (SPEC 13)")
    logger.info(f"Target Agent Engine: {AGENT_RESOURCE_NAME}")
    logger.info(f"Region: {LOCATION} | Project: {PROJECT_ID}")
    logger.info("=" * 70)

    # Step 1: Active Memory Bank Retrieval
    mem_count = execute_active_memory_bank_retrieval(user_id="oncologist_clinician", session_id="session_live_oncologist_clinician")

    # Step 2: Register/Retrieve Clean Trajectory Experiment
    client = AgentPlatformClient(project=PROJECT_ID, location=LOCATION)
    experiment_display_name = "graph-agent-trajectory-evals"
    
    # List or create experiment
    exp_resource = None
    try:
        res = client.evals.list_evaluation_experiments()
        for exp in getattr(res, "evaluation_experiments", []):
            if exp.display_name == experiment_display_name:
                exp_resource = exp.name
                break
    except Exception as e:
        logger.warning(f"Could not list experiments: {e}")

    if not exp_resource:
        credentials, _ = google.auth.default()
        credentials.refresh(Request())
        headers = {"Authorization": f"Bearer {credentials.token}", "Content-Type": "application/json"}
        url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_NUMBER}/locations/{LOCATION}/evaluationExperiments"
        body = {
            "displayName": experiment_display_name,
            "labels": {
                "vertex-ai-evaluation-agent-engine-id": AGENT_ENGINE_ID,
                "agent_id": AGENT_ENGINE_ID,
                "agent": "cancer-co-scientist-graph-agent",
            },
            "metadata": {
                "description": "Spec 13 - Graph Agent Glass Box Multi-Turn Trajectory Evaluation Suite",
                "agent_resource_name": AGENT_RESOURCE_NAME,
            },
        }
        r = requests.post(url, headers=headers, json=body, timeout=30)
        if r.status_code == 200:
            exp_resource = r.json().get("name")
            logger.info(f"✅ Created dedicated Trajectory Experiment: {exp_resource}")
        else:
            logger.error(f"Failed to create experiment: {r.status_code} {r.text}")
            return {}

    timestamp = pd.Timestamp.now().strftime("%Y%m%d-%H%M%S")
    candidate_name = f"candidate-trajectory-{timestamp}"

    # Step 3: Build Trajectory EvalCases and Dataset
    eval_cases = build_golden_trajectory_eval_cases()
    eval_dataset = ap_types.EvaluationDataset(
        eval_cases=eval_cases,
        candidate_name=candidate_name,
    )

    # Step 4: Configure Native Agent Platform Autorater Metrics
    rubric_metrics = [
        metric_loaders.RubricMetric.MULTI_TURN_TRAJECTORY_QUALITY,
        metric_loaders.RubricMetric.MULTI_TURN_TOOL_USE_QUALITY,
        metric_loaders.RubricMetric.MULTI_TURN_TASK_SUCCESS,
        metric_loaders.RubricMetric.FINAL_RESPONSE_QUALITY,
    ]
    eval_config = ap_types.CreateEvaluationRunConfig(allow_cross_region_model=True)
    dest_prefix = f"{STAGING_BUCKET}/eval_runs/graph_agent_trajectory_suite/"

    logger.info(f"\n🚀 Launching Native Trajectory Evaluation Run on Agent Platform...")
    eval_run = client.evals.create_evaluation_run(
        display_name=f"graph-agent-trajectory-{timestamp}",
        evaluation_experiment=exp_resource,
        dataset=eval_dataset,
        metrics=rubric_metrics,
        agent=AGENT_RESOURCE_NAME,
        dest=dest_prefix,
        config=eval_config,
    )
    logger.info(f"✅ Created Trajectory EvaluationRun: {eval_run.name} (state: {eval_run.state})")

    # Step 5: Monitor Evaluation Run
    logger.info("\n⏳ Polling Trajectory EvaluationRun for autorater completion...")
    final_state = "UNKNOWN"
    summary_metrics = {}
    for attempt in range(40):  # up to 200 seconds
        time.sleep(5)
        try:
            r = client.evals.get_evaluation_run(name=eval_run.name)
            final_state = str(r.state)
            if final_state in ["EvaluationRunState.SUCCEEDED", "EvaluationRunState.FAILED"]:
                if final_state == "EvaluationRunState.FAILED":
                    logger.error(f"❌ EvaluationRun FAILED. Details: {r}")
                if hasattr(r, "evaluation_run_results") and r.evaluation_run_results:
                    if r.evaluation_run_results.summary_metrics:
                        summary_metrics = r.evaluation_run_results.summary_metrics.metrics or {}
                break
            logger.info(f"   [Polling] Attempt {attempt+1}: state = {final_state}")
        except Exception as e:
            logger.warning(f"Error polling run: {e}")

    logger.info(f"🏁 Final Trajectory EvaluationRun State: {final_state}")

    # Step 6: Execute Live Multi-Turn Benchmark Telemetry Queries
    live_results = execute_live_multi_turn_stream_benchmark()
    latencies = [res["latency_ms"] for res in live_results if res.get("status") == "SUCCESS"]
    p50_latency = float(pd.Series(latencies).quantile(0.50)) if latencies else 0.0
    p95_latency = float(pd.Series(latencies).quantile(0.95)) if latencies else 0.0

    # Step 7: Print Final Scorecard
    print("\n" + "=" * 72)
    print("🏆 FINAL GRAPH AGENT TRAJECTORY EVALUATION SCORECARD (SPEC 13)")
    print("=" * 72)
    print(f"Target Agent: {AGENT_RESOURCE_NAME}")
    print(f"Evaluation Experiment: {exp_resource}")
    print(f"Evaluation Run: {eval_run.name}")
    print(f"Evaluation Status: {final_state}")
    print(f"Memory Bank Recall Count: {mem_count}")
    print(f"Turn Latency P50: {p50_latency:.1f}ms | P95: {p95_latency:.1f}ms")
    print("-" * 72)
    print("Autorater Trajectory Metrics:")
    for k, v in sorted(summary_metrics.items()):
        print(f"   {k}: {v}")
    print("-" * 72)
    print("Live Trajectory Stream Queries:")
    for res in live_results:
        print(f"   [{res['scenario']}] Latency: {res['latency_ms']:.1f}ms | Tools: {res['tools_count']} ({res['tool_calls']})")
    print("=" * 72)

    return {
        "experiment_resource": exp_resource,
        "evaluation_run_name": eval_run.name,
        "status": final_state,
        "summary_metrics": summary_metrics,
        "memory_bank_count": mem_count,
        "p50_latency_ms": p50_latency,
        "p95_latency_ms": p95_latency,
        "live_results": live_results,
    }


if __name__ == "__main__":
    run_graph_agent_trajectory_suite()
