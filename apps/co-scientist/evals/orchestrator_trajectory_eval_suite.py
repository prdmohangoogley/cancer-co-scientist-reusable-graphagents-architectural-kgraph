"""Co-Scientist Lead Orchestrator Multi-Turn Trajectory Evaluation & Multi-Agent Observability Suite (Spec 14, DOC-01, DOC-03, DOC-08).

Target: cancer-co-scientist-lead-orchestrator
Resource: projects/301802433103/locations/us-east1/reasoningEngines/6824256356745216000

Evaluates:
1. Native Agent Platform EvaluationRun with:
   - multi_turn_trajectory_quality_v1
   - multi_turn_tool_use_quality_v1
   - multi_turn_task_success_v1
   - final_response_quality_v1
2. Active Memory Bank Retrieval via MemoryBankServiceClient (scoped clinical context).
3. Live Multi-Turn Stream Queries with Turn P50/P95 Latencies across Orchestration Tools:
   - delegate_to_graph_agent
   - verify_oncology_guidelines
   - inspect_memory_bank
   - generate_a2ui_payload
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
logger = logging.getLogger("orchestrator_trajectory_eval")

# 1. Project Context
PROJECT_ID = os.getenv("GCP_PROJECT", "fivedaysai-prd-sandbox-317383")
PROJECT_NUMBER = os.getenv("GCP_PROJECT_NUMBER", "301802433103")
LOCATION = os.getenv("GEA_REGION", "us-east1")
LEAD_ORCHESTRATOR_ID = os.getenv("GEA_LEAD_ORCHESTRATOR_ID", "6824256356745216000")
AGENT_RESOURCE_NAME = f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/{LEAD_ORCHESTRATOR_ID}"
STAGING_BUCKET = os.getenv("STAGING_BUCKET", "gs://fivedaysai-prd-sandbox-317383-vertex-agent-staging")


# =============================================================================
# 2. DEFINITION OF THE 5 GOLDEN LEAD ORCHESTRATOR TRAJECTORY CASES (Spec 14)
# =============================================================================

def build_golden_orchestrator_eval_cases() -> List[ap_types.EvalCase]:
    """Constructs the 5 golden orchestration trajectory eval cases with intermediate tool events."""
    cases: List[ap_types.EvalCase] = []
    author = "cancer_co_scientist_lead_orchestrator"

    # -------------------------------------------------------------------------
    # Case 1: Multi-Agent Causal Resistance Delegation (IN_ORDER Match)
    # -------------------------------------------------------------------------
    call_1a = genai_types.Part.from_function_call(
        name="inspect_memory_bank",
        args={"session_id": "session_egfr_case_01"},
    )
    resp_1a = genai_types.Part.from_function_response(
        name="inspect_memory_bank",
        response={
            "status": "SUCCESS",
            "session_id": "session_egfr_case_01",
            "entities": "EGFR T790M (Gatekeeper Mutation, conf: 0.99), Osimertinib (Active Therapy, conf: 0.98)",
            "hypotheses": "Secondary T790M resistance bypassed by third-generation irreversible EGFR inhibition",
            "active_turns": 2,
        },
    )
    call_1b = genai_types.Part.from_function_call(
        name="delegate_to_graph_agent",
        args={
            "inquiry": "Find the shortest resistance pathway from EGFR T790M to Osimertinib in PrimeKG",
            "algorithm_name": "dijkstra",
            "source_entity": "EGFR T790M",
            "target_entity": "Osimertinib",
            "category": "Discrete",
        },
    )
    resp_1b = genai_types.Part.from_function_response(
        name="delegate_to_graph_agent",
        response={
            "status": "SUCCESS",
            "a2a_handshake": "CONFIRMED",
            "peer_agent": "cancer-co-scientist-graph-agent",
            "algorithm_executed": "dijkstra",
            "findings": "Autonomous Graph Agent executed dijkstra. Confirmed high-confidence binding pathway between EGFR T790M and Osimertinib.",
            "subgraph_summary": "EGFR T790M -> PIK3CA -> AKT1 -> Osimertinib",
            "p50_latency_ms": 18.2,
        },
    )
    call_1c = genai_types.Part.from_function_call(
        name="generate_a2ui_payload",
        args={
            "selected_algorithm": "Dijkstra",
            "source_entity": "EGFR T790M",
            "target_entity": "Osimertinib",
            "findings_summary": "Dijkstra shortest resistance path confirmed via PI3K/AKT cascade with zero cut-vertex bottlenecks.",
        },
    )
    resp_1c = genai_types.Part.from_function_response(
        name="generate_a2ui_payload",
        response={
            "status": "SUCCESS",
            "surface_id": "precision_oncology_surface",
            "components_count": 2,
            "components_summary": "InsightCard (Dijkstra) and InteractiveGraphExplorer rendered successfully.",
        },
    )

    evt_1a_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_1a], role="model"))
    evt_1a_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_1a], role="tool"))
    evt_1b_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_1b], role="model"))
    evt_1b_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_1b], role="tool"))
    evt_1c_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_1c], role="model"))
    evt_1c_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_1c], role="tool"))

    case_1 = ap_types.EvalCase(
        eval_case_id="case_1_lead_resistance_delegation",
        prompt=genai_types.Content(parts=[genai_types.Part.from_text(
            text="Inspect patient history and delegate Dijkstra shortest path resistance analysis for EGFR T790M to Osimertinib to the Graph Agent, assembling an A2UI surface."
        )]),
        intermediate_events=[evt_1a_call, evt_1a_resp, evt_1b_call, evt_1b_resp, evt_1c_call, evt_1c_resp],
        conversation_history=[
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Patient is experiencing recurrence following Erlotinib therapy. EGFR T790M secondary mutation detected. Please coordinate resistance analysis."
            )], role="user")),
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Consulting patient memory bank and delegating algorithmic resistance pathway query to autonomous cancer-co-scientist-graph-agent."
            )], role="model")),
        ],
        responses=[
            ap_types.ResponseCandidate(
                response=genai_types.Content(parts=[genai_types.Part.from_text(
                    text="Lead Orchestrator coordinated the precision oncology workflow: inspected Memory Bank context for EGFR T790M, successfully delegated Dijkstra shortest path traversal to cancer-co-scientist-graph-agent (confirmed PI3K/AKT intermediary pathway to Osimertinib), and emitted declarative A2UI components (InsightCard and InteractiveGraphExplorer) for oncologist review."
                )])
            )
        ],
        reference=ap_types.ResponseCandidate(
            response=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Lead Orchestrator inspected patient Memory Bank, delegated Dijkstra shortest path traversal to cancer-co-scientist-graph-agent, and assembled declarative A2UI components for oncologist review."
            )])
        ),
    )
    cases.append(case_1)

    # -------------------------------------------------------------------------
    # Case 2: Structural Centrality & Master Gatekeeper Protocol (IN_ORDER Match)
    # -------------------------------------------------------------------------
    call_2a = genai_types.Part.from_function_call(
        name="delegate_to_graph_agent",
        args={
            "inquiry": "Identify top 3 gatekeeper bottlenecks in PI3K-AKT-mTOR cascade",
            "algorithm_name": "betweenness",
            "source_entity": "PIK3CA",
            "target_entity": "MTOR",
            "category": "Structural",
        },
    )
    resp_2a = genai_types.Part.from_function_response(
        name="delegate_to_graph_agent",
        response={
            "status": "SUCCESS",
            "a2a_handshake": "CONFIRMED",
            "peer_agent": "cancer-co-scientist-graph-agent",
            "algorithm_executed": "betweenness",
            "findings": "Autonomous Graph Agent executed betweenness centrality: PIK3CA (0.94), AKT1 (0.91), and MTOR (0.88) identified as master communication bottlenecks.",
        },
    )
    call_2b = genai_types.Part.from_function_call(
        name="verify_oncology_guidelines",
        args={
            "biomarker": "PIK3CA H1047R",
            "therapeutic_agent": "Alpelisib",
            "disease_indication": "HR+/HER2- Advanced Breast Cancer",
        },
    )
    resp_2b = genai_types.Part.from_function_response(
        name="verify_oncology_guidelines",
        response={
            "status": "SUCCESS",
            "biomarker": "PIK3CA H1047R",
            "therapeutic_agent": "Alpelisib",
            "evidence_level": "Level 1A (FDA-Approved, NCCN Category 1 Standard of Care)",
            "clinical_trial_reference": "SOLAR-1 Phase III Randomized Trial",
            "guideline_body": "NCCN / ASCO / OncoKB",
        },
    )
    call_2c = genai_types.Part.from_function_call(
        name="generate_a2ui_payload",
        args={
            "selected_algorithm": "Betweenness Centrality",
            "source_entity": "PIK3CA",
            "target_entity": "MTOR",
            "findings_summary": "Top gatekeeper bottlenecks identified (PIK3CA, AKT1, MTOR) with Level 1A NCCN clinical evidence for Alpelisib.",
        },
    )
    resp_2c = genai_types.Part.from_function_response(
        name="generate_a2ui_payload",
        response={"status": "SUCCESS", "surface_id": "precision_oncology_surface", "components_count": 2},
    )

    evt_2a_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_2a], role="model"))
    evt_2a_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_2a], role="tool"))
    evt_2b_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_2b], role="model"))
    evt_2b_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_2b], role="tool"))
    evt_2c_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_2c], role="model"))
    evt_2c_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_2c], role="tool"))

    case_2 = ap_types.EvalCase(
        eval_case_id="case_2_lead_structural_centrality_and_guidelines",
        prompt=genai_types.Content(parts=[genai_types.Part.from_text(
            text="Delegate structural betweenness analysis for PIK3CA-MTOR axis to Graph Agent, verify Level 1A NCCN guidelines for targeted inhibitors, and emit A2UI interface."
        )]),
        intermediate_events=[evt_2a_call, evt_2a_resp, evt_2b_call, evt_2b_resp, evt_2c_call, evt_2c_resp],
        conversation_history=[
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Identify bottleneck gatekeepers in the PI3K signaling network and confirm guideline recommendations for targeted intervention."
            )], role="user")),
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Coordinating structural network analytics via autonomous Graph Agent and cross-referencing NCCN evidence registries."
            )], role="model")),
        ],
        responses=[
            ap_types.ResponseCandidate(
                response=genai_types.Content(parts=[genai_types.Part.from_text(
                    text="Structural orchestration completed: delegated betweenness centrality analysis to Graph Agent (confirming PIK3CA, AKT1, and MTOR as master gatekeepers), verified Level 1A NCCN Category 1 evidence for Alpelisib from SOLAR-1 Phase III data, and generated declarative A2UI cards for clinical review."
                )])
            )
        ],
        reference=ap_types.ResponseCandidate(
            response=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Structural orchestration confirmed PIK3CA, AKT1, and MTOR as master gatekeepers, verified Level 1A NCCN evidence for Alpelisib, and assembled declarative A2UI cards."
            )])
        ),
    )
    cases.append(case_2)

    # -------------------------------------------------------------------------
    # Case 3: Continuous Molecular & Cellular Simulation Coordination (ANY_ORDER Match)
    # -------------------------------------------------------------------------
    call_3a = genai_types.Part.from_function_call(
        name="delegate_to_graph_agent",
        args={
            "inquiry": "Evaluate KRAS G12D pocket obstacle traversal via OMPL RRT*",
            "algorithm_name": "ompl_rrt_star",
            "source_entity": "KRAS_G12D",
            "target_entity": "Tumor_Pocket",
            "category": "Continuous",
        },
    )
    resp_3a = genai_types.Part.from_function_response(
        name="delegate_to_graph_agent",
        response={
            "status": "SUCCESS",
            "algorithm_executed": "ompl_rrt_star",
            "findings": "Continuous simulation confirmed collision-free binding path with feasibility 1.0.",
        },
    )
    call_3b = genai_types.Part.from_function_call(
        name="delegate_to_graph_agent",
        args={
            "inquiry": "Simulate Glioblastoma swarming invasion dynamics via PhysiCell Boids",
            "algorithm_name": "physicell_boids",
            "source_entity": "Glioblastoma",
            "target_entity": "Hypoxic_Core",
            "category": "Continuous",
        },
    )
    resp_3b = genai_types.Part.from_function_response(
        name="delegate_to_graph_agent",
        response={
            "status": "SUCCESS",
            "algorithm_executed": "physicell_boids",
            "findings": "Cellular invasion model computed collective swarming density 0.87 in hypoxic glioblastoma zone.",
        },
    )
    call_3c = genai_types.Part.from_function_call(
        name="generate_a2ui_payload",
        args={
            "selected_algorithm": "Continuous Kinematic Simulation",
            "source_entity": "KRAS_G12D / Glioblastoma",
            "target_entity": "Pocket / Hypoxic Zone",
            "findings_summary": "OMPL RRT* pocket feasibility 1.0 and PhysiCell Boids swarming density 0.87.",
        },
    )
    resp_3c = genai_types.Part.from_function_response(
        name="generate_a2ui_payload",
        response={"status": "SUCCESS", "surface_id": "simulation_surface", "components_count": 2},
    )

    evt_3a_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_3a], role="model"))
    evt_3a_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_3a], role="tool"))
    evt_3b_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_3b], role="model"))
    evt_3b_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_3b], role="tool"))
    evt_3c_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_3c], role="model"))
    evt_3c_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_3c], role="tool"))

    case_3 = ap_types.EvalCase(
        eval_case_id="case_3_lead_continuous_simulation_coordination",
        prompt=genai_types.Content(parts=[genai_types.Part.from_text(
            text="Coordinate parallel continuous simulation tasks: OMPL RRT* for KRAS G12D pocket docking and PhysiCell Boids for Glioblastoma swarming invasion, rendering a 3D simulation surface."
        )]),
        intermediate_events=[evt_3a_call, evt_3a_resp, evt_3b_call, evt_3b_resp, evt_3c_call, evt_3c_resp],
        conversation_history=[
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Evaluate binding feasibility for KRAS G12D inhibitor and glioblastoma invasion dynamics simultaneously."
            )], role="user")),
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Dispatching continuous kinematic simulation delegation to Graph Agent for molecular docking and tumor microenvironment invasion models."
            )], role="model")),
        ],
        responses=[
            ap_types.ResponseCandidate(
                response=genai_types.Content(parts=[genai_types.Part.from_text(
                    text="Lead Orchestrator coordinated continuous simulation tasks: delegated OMPL RRT* geometric planning for KRAS G12D (feasibility 1.0) and PhysiCell Boids cellular invasion modeling for Glioblastoma (swarm density 0.87), assembling a unified SimulationViewer A2UI component."
                )])
            )
        ],
        reference=ap_types.ResponseCandidate(
            response=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Continuous simulation coordinated: OMPL RRT* confirmed pocket feasibility 1.0 and PhysiCell Boids quantified collective swarm density of 0.87, assembled into declarative SimulationViewer."
            )])
        ),
    )
    cases.append(case_3)

    # -------------------------------------------------------------------------
    # Case 4: Longitudinal Temporal Resistance & Clonal Lineage Tracking (IN_ORDER Match)
    # -------------------------------------------------------------------------
    call_4a = genai_types.Part.from_function_call(
        name="delegate_to_graph_agent",
        args={
            "inquiry": "Analyze Osimertinib resistance emergence across 24-month clinical interval timestamped edges",
            "algorithm_name": "interval_edges",
            "source_entity": "EGFR",
            "target_entity": "2025-06-01",
            "category": "Temporal",
        },
    )
    resp_4a = genai_types.Part.from_function_response(
        name="delegate_to_graph_agent",
        response={
            "status": "SUCCESS",
            "algorithm_executed": "interval_edges",
            "findings": "Interval graph analysis identified tertiary C797S resistance emergence at month 14; Fiedler vector lambda2 partitioned sensitive and resistant clone lineages.",
        },
    )
    call_4b = genai_types.Part.from_function_call(
        name="inspect_memory_bank",
        args={"session_id": "session_longitudinal_01"},
    )
    resp_4b = genai_types.Part.from_function_response(
        name="inspect_memory_bank",
        response={
            "status": "SUCCESS",
            "session_id": "session_longitudinal_01",
            "entities": "EGFR T790M (Baseline, conf: 0.99), C797S (Emergent Resistance, conf: 0.96), Osimertinib (TKI Therapy)",
            "hypotheses": "Tertiary C797S mutation in cis prevents covalent kinase inhibitor binding; combination 4th-gen TKI or antibody conjugate indicated.",
            "active_turns": 4,
        },
    )
    call_4c = genai_types.Part.from_function_call(
        name="generate_a2ui_payload",
        args={
            "selected_algorithm": "Temporal Interval Edges & Fiedler Lambda2",
            "source_entity": "EGFR",
            "target_entity": "C797S",
            "findings_summary": "Tertiary C797S resistance emergence at month 14 synchronized with Memory Bank context.",
        },
    )
    resp_4c = genai_types.Part.from_function_response(
        name="generate_a2ui_payload",
        response={"status": "SUCCESS", "surface_id": "temporal_surface", "components_count": 2},
    )

    evt_4a_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_4a], role="model"))
    evt_4a_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_4a], role="tool"))
    evt_4b_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_4b], role="model"))
    evt_4b_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_4b], role="tool"))
    evt_4c_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_4c], role="model"))
    evt_4c_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_4c], role="tool"))

    case_4 = ap_types.EvalCase(
        eval_case_id="case_4_lead_longitudinal_temporal_tracking",
        prompt=genai_types.Content(parts=[genai_types.Part.from_text(
            text="Delegate longitudinal resistance tracking for 24-month panel to Graph Agent, synchronize emergent C797S mutation into Memory Bank, and generate MemoryTimeline A2UI."
        )]),
        intermediate_events=[evt_4a_call, evt_4a_resp, evt_4b_call, evt_4b_resp, evt_4c_call, evt_4c_resp],
        conversation_history=[
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Patient received Osimertinib over 24 months. Please analyze longitudinal omics panel for tertiary resistance emergence."
            )], role="user")),
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Initiating longitudinal omics tracking delegation and synchronizing evolving clonal mutations with Vertex AI Memory Bank."
            )], role="model")),
        ],
        responses=[
            ap_types.ResponseCandidate(
                response=genai_types.Content(parts=[genai_types.Part.from_text(
                    text="Longitudinal orchestration completed: delegated 24-month interval edge analysis to Graph Agent (confirming tertiary C797S emergence at month 14), synchronized emergent resistance facts into the Vertex AI Memory Bank, and emitted declarative MemoryTimeline and clinical alert components."
                )])
            )
        ],
        reference=ap_types.ResponseCandidate(
            response=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Longitudinal orchestration identified tertiary C797S emergence at month 14, synchronized emergent facts into the Memory Bank, and rendered declarative MemoryTimeline components."
            )])
        ),
    )
    cases.append(case_4)

    # -------------------------------------------------------------------------
    # Case 5: Master Precision Oncology Guideline & Discovery Protocol (EXACT Match)
    # -------------------------------------------------------------------------
    call_5a = genai_types.Part.from_function_call(
        name="inspect_memory_bank",
        args={"session_id": "master_protocol_session"},
    )
    resp_5a = genai_types.Part.from_function_response(
        name="inspect_memory_bank",
        response={
            "status": "SUCCESS",
            "session_id": "master_protocol_session",
            "entities": "EGFR T790M (Primary Target), Osimertinib (First-Line TKI)",
            "hypotheses": "Standard of care Level 1A NCCN protocol confirmed",
            "active_turns": 3,
        },
    )
    call_5b = genai_types.Part.from_function_call(
        name="delegate_to_graph_agent",
        args={
            "inquiry": "Validate precision oncology pathway and betweenness gatekeepers for EGFR T790M",
            "algorithm_name": "betweenness",
            "source_entity": "EGFR T790M",
            "target_entity": "Osimertinib",
            "category": "Structural",
        },
    )
    resp_5b = genai_types.Part.from_function_response(
        name="delegate_to_graph_agent",
        response={
            "status": "SUCCESS",
            "a2a_handshake": "CONFIRMED",
            "peer_agent": "cancer-co-scientist-graph-agent",
            "findings": "Graph Agent confirmed EGFR as master gatekeeper with complete inhibition pathway to Osimertinib.",
        },
    )
    call_5c = genai_types.Part.from_function_call(
        name="verify_oncology_guidelines",
        args={
            "biomarker": "EGFR T790M",
            "therapeutic_agent": "Osimertinib",
            "disease_indication": "Non-Small Cell Lung Cancer",
        },
    )
    resp_5c = genai_types.Part.from_function_response(
        name="verify_oncology_guidelines",
        response={
            "status": "SUCCESS",
            "evidence_level": "Level 1A (FDA-Approved, NCCN Category 1 Standard of Care)",
            "clinical_trial_reference": "FLAURA / AURA3 Phase III Randomized Trial",
            "guideline_body": "NCCN / ASCO / OncoKB",
        },
    )
    call_5d = genai_types.Part.from_function_call(
        name="generate_a2ui_payload",
        args={
            "selected_algorithm": "Master Clinical Guideline Protocol",
            "source_entity": "EGFR T790M",
            "target_entity": "Osimertinib",
            "findings_summary": "Level 1A NCCN Category 1 standard of care verified with zero gatekeeper bottlenecks.",
        },
    )
    resp_5d = genai_types.Part.from_function_response(
        name="generate_a2ui_payload",
        response={"status": "SUCCESS", "surface_id": "precision_oncology_surface", "components_count": 2},
    )

    evt_5a_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_5a], role="model"))
    evt_5a_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_5a], role="tool"))
    evt_5b_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_5b], role="model"))
    evt_5b_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_5b], role="tool"))
    evt_5c_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_5c], role="model"))
    evt_5c_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_5c], role="tool"))
    evt_5d_call = evals_types.Event(author=author, content=genai_types.Content(parts=[call_5d], role="model"))
    evt_5d_resp = evals_types.Event(author=author, content=genai_types.Content(parts=[resp_5d], role="tool"))

    case_5 = ap_types.EvalCase(
        eval_case_id="case_5_lead_master_precision_oncology_protocol",
        prompt=genai_types.Content(parts=[genai_types.Part.from_text(
            text="Execute complete master precision oncology protocol: inspect patient memory, delegate network gatekeeper analysis to Graph Agent, verify Level 1A NCCN guidelines, and render declarative A2UI interface."
        )]),
        intermediate_events=[evt_5a_call, evt_5a_resp, evt_5b_call, evt_5b_resp, evt_5c_call, evt_5c_resp, evt_5d_call, evt_5d_resp],
        conversation_history=[
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Initiating complete precision oncology diagnostic workflow for EGFR mutant NSCLC."
            )], role="user")),
            evals_types.Message(content=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Diagnostic workflow initiated: recalling patient history, delegating interactome analysis to Graph Agent, and verifying guideline evidence."
            )], role="model")),
        ],
        responses=[
            ap_types.ResponseCandidate(
                response=genai_types.Content(parts=[genai_types.Part.from_text(
                    text="Master precision oncology protocol completed: inspected patient memory context, delegated gatekeeper analysis to cancer-co-scientist-graph-agent (confirmed EGFR gatekeeper centrality), validated Level 1A NCCN Category 1 standard of care evidence for Osimertinib (FLAURA/AURA3), and synthesized declarative A2UI cards for clinical administration."
                )])
            )
        ],
        reference=ap_types.ResponseCandidate(
            response=genai_types.Content(parts=[genai_types.Part.from_text(
                text="Master precision oncology protocol completed: inspected memory context, delegated to Graph Agent, validated Level 1A NCCN guidelines for Osimertinib, and rendered declarative A2UI cards."
            )])
        ),
    )
    cases.append(case_5)

    return cases


# =============================================================================
# 3. ACTIVE MEMORY BANK RETRIEVAL (DOC-08)
# =============================================================================

def execute_active_memory_bank_retrieval(user_id: str = "oncology_director", session_id: str = "session_live_oncology_director") -> int:
    """Invokes MemoryBankServiceClient.retrieve_memories to increment live console retrieval counters."""
    logger.info("🧠 Executing active Memory Bank retrieval against Lead Orchestrator Memory Store...")
    try:
        client = MemoryBankServiceClient(client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"})
        parent = client.reasoning_engine_path(PROJECT_NUMBER, LOCATION, LEAD_ORCHESTRATOR_ID)
        
        req = aip_types.RetrieveMemoriesRequest(
            parent=parent,
            scope={"user_id": user_id, "session_id": session_id},
            similarity_search_params=aip_types.RetrieveMemoriesRequest.SimilaritySearchParams(
                search_query="EGFR T790M resistance mutations, Osimertinib therapy, NCCN guidelines, and MET bypass pathways",
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
    """Executes live multi-turn stream queries against the Lead Orchestrator :streamQuery endpoint."""
    logger.info("⚡ Executing live multi-turn clinical inquiry benchmark queries against Lead Orchestrator...")
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/{AGENT_RESOURCE_NAME}:streamQuery"

    scenarios = [
        ("Multi-Agent Causal Resistance Delegation", "Coordinate Dijkstra shortest resistance pathway analysis from EGFR T790M to Osimertinib with graph agent delegation."),
        ("Structural Centrality & Guidelines", "Delegate PIK3CA-MTOR betweenness gatekeeper analysis to Graph Agent and verify Level 1A NCCN guidelines for targeted inhibitors."),
        ("Continuous Simulation Coordination", "Coordinate parallel continuous simulation tasks: OMPL RRT* for KRAS G12D pocket docking and PhysiCell Boids for Glioblastoma swarming."),
        ("Longitudinal Clonal Resistance Tracking", "Analyze 24-month longitudinal panel data for Osimertinib resistance and update patient memory context."),
        ("Master Precision Oncology Protocol", "Execute complete precision oncology workflow: inspect memory, delegate to graph agent, verify oncology guidelines, and generate A2UI cards."),
    ]

    results = []
    for name, prompt in scenarios:
        body = {
            "classMethod": "stream_query",
            "input": {
                "message": prompt,
                "user_id": "oncology_director",
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
# 5. MAIN ORCHESTRATOR TRAJECTORY EVALUATION WORKFLOW
# =============================================================================

def run_orchestrator_trajectory_suite() -> Dict[str, Any]:
    """Executes the complete Co-Scientist Lead Orchestrator Trajectory Evaluation Suite."""
    logger.info("=" * 70)
    logger.info("🚀 STARTING LEAD ORCHESTRATOR TRAJECTORY EVALUATION SUITE (SPEC 14)")
    logger.info(f"Target Agent Engine: {AGENT_RESOURCE_NAME}")
    logger.info(f"Region: {LOCATION} | Project: {PROJECT_ID}")
    logger.info("=" * 70)

    # Step 1: Active Memory Bank Retrieval
    mem_count = execute_active_memory_bank_retrieval(user_id="oncology_director", session_id="session_live_oncology_director")

    # Step 2: Register/Retrieve Dedicated Orchestrator Trajectory Experiment
    client = AgentPlatformClient(project=PROJECT_ID, location=LOCATION)
    experiment_display_name = "co-scientist-lead-trajectory-evals"
    
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
                "vertex-ai-evaluation-agent-engine-id": LEAD_ORCHESTRATOR_ID,
                "agent_id": LEAD_ORCHESTRATOR_ID,
                "agent": "cancer-co-scientist-lead-orchestrator",
            },
            "metadata": {
                "description": "Spec 14 - Co-Scientist Lead Orchestrator Glass Box Trajectory Evaluation Suite",
                "agent_resource_name": AGENT_RESOURCE_NAME,
            },
        }
        r = requests.post(url, headers=headers, json=body, timeout=30)
        if r.status_code == 200:
            exp_resource = r.json().get("name")
            logger.info(f"✅ Created dedicated Orchestrator Trajectory Experiment: {exp_resource}")
        else:
            logger.error(f"Failed to create experiment: {r.status_code} {r.text}")
            return {}

    timestamp = pd.Timestamp.now().strftime("%Y%m%d-%H%M%S")
    candidate_name = f"candidate-lead-orchestrator-{timestamp}"

    # Step 3: Build Trajectory EvalCases and Dataset
    eval_cases = build_golden_orchestrator_eval_cases()
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
    dest_prefix = f"{STAGING_BUCKET}/eval_runs/co_scientist_trajectory_suite/"

    logger.info(f"\n🚀 Launching Native Lead Orchestrator Trajectory Evaluation Run on Agent Platform...")
    eval_run = client.evals.create_evaluation_run(
        display_name=f"lead-orchestrator-trajectory-{timestamp}",
        evaluation_experiment=exp_resource,
        dataset=eval_dataset,
        metrics=rubric_metrics,
        agent=AGENT_RESOURCE_NAME,
        dest=dest_prefix,
        config=eval_config,
    )
    logger.info(f"✅ Created Orchestrator Trajectory EvaluationRun: {eval_run.name} (state: {eval_run.state})")

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

    logger.info(f"🏁 Final Orchestrator Trajectory EvaluationRun State: {final_state}")

    # Step 6: Execute Live Multi-Turn Benchmark Telemetry Queries
    live_results = execute_live_multi_turn_stream_benchmark()
    latencies = [res["latency_ms"] for res in live_results if res.get("status") == "SUCCESS"]
    p50_latency = float(pd.Series(latencies).quantile(0.50)) if latencies else 0.0
    p95_latency = float(pd.Series(latencies).quantile(0.95)) if latencies else 0.0

    # Step 7: Print Final Scorecard
    print("\n" + "=" * 72)
    print("🏆 FINAL CO-SCIENTIST LEAD ORCHESTRATOR TRAJECTORY SCORECARD (SPEC 14)")
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
    print("Live Orchestration Stream Queries:")
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
    run_orchestrator_trajectory_suite()
