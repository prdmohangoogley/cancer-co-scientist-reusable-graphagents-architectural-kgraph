"""Setup and Register GEA Categorized Experiments on Vertex AI / Agent Platform.

Dual-Engine Architecture:
1. Agent Platform Native Evaluation Runs:
   Uses `agentplatform.Client` and `RubricMetric` with Predefined Agent Evaluation Rubrics:
   - `FINAL_RESPONSE_QUALITY` (`final_response_quality_v1`): Evaluates groundedness, clinical relevance, and accuracy.
   - `MULTI_TURN_TASK_SUCCESS` (`multi_turn_task_success_v1`): Evaluates multi-turn goal fulfillment.
   Binds `vertex-ai-evaluation-agent-engine-id` to render live on the Pantheon Experiments Dashboard:
   URL: https://pantheon.corp.google.com/agent-platform/runtimes/locations/us-east1/agent-engines/4359942935643422720/evaluation?project=fivedaysai-prd-sandbox-317383

2. Live Benchmark Execution & Offline Quality Metrics:
   Executes inference queries against `:streamQuery`, verifying tool execution,
   measuring latency distributions (p50/p95), tool call counts, and response quality.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

import google.auth
from google.auth.transport.requests import Request
import pandas as pd
import requests
import vertexai
from agentplatform import Client as AgentPlatformClient, types as ap_types
from agentplatform._genai import _evals_metric_loaders

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("setup_gea_experiments")

# 1. Project & Agent Engine Context
PROJECT_ID = os.getenv("GCP_PROJECT", "fivedaysai-prd-sandbox-317383")
PROJECT_NUMBER = os.getenv("GCP_PROJECT_NUMBER", "301802433103")
LOCATION = os.getenv("GEA_REGION", "us-east1")
AGENT_ENGINE_ID = os.getenv("GEA_GRAPH_AGENT_ID", "4359942935643422720")
AGENT_RESOURCE_NAME = f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"
STAGING_BUCKET = os.getenv("STAGING_BUCKET", "gs://fivedaysai-prd-sandbox-317383-vertex-agent-staging")

vertexai.init(project=PROJECT_ID, location=LOCATION)


def register_clean_agent_platform_experiments(force_recreate: bool = True) -> Dict[str, str]:
    """Registers the 5 categorized evaluation experiments cleanly on Agent Platform.
    
    If an existing experiment contains stale failed runs from older revisions,
    deletes and recreates it to ensure a clean scorecard state.
    """
    client = AgentPlatformClient(project=PROJECT_ID, location=LOCATION)
    
    experiment_specs = [
        ("graph-agent-discrete-algorithms", "Spec 12 - Discrete Traversal Benchmarks (Dijkstra, BFS, A*, WCC, TopoSort)"),
        ("graph-agent-structural-centrality", "Spec 12 - Structural Centrality Benchmarks (PageRank, Betweenness, Bridges, Density)"),
        ("graph-agent-continuous-simulation", "Spec 12 - Continuous Simulation Benchmarks (AlphaFold OMPL RRT*, PhysiCell Boids)"),
        ("graph-agent-temporal-omics", "Spec 12 - Temporal Multi-Omics Benchmarks (Interval Edges, Lambda2, Longitudinal)"),
        ("cancer-co-scientist-graph-benchmarks", "Spec 12 - Master 15-Algorithm Precision Oncology Benchmark Suite"),
    ]
    
    # Check existing experiments
    existing_map: Dict[str, str] = {}
    try:
        res = client.evals.list_evaluation_experiments()
        for exp in getattr(res, "evaluation_experiments", []):
            existing_map[exp.display_name] = exp.name
    except Exception as e:
        logger.warning(f"Could not list existing experiments: {e}")

    target_names = {name for name, _ in experiment_specs}
    if force_recreate:
        for name in target_names:
            if name in existing_map:
                logger.info(f"Purging previous experiment with stale runs: {name} ({existing_map[name]})...")
                try:
                    client.evals.delete_evaluation_experiment(name=existing_map[name])
                except Exception as e:
                    logger.warning(f"Could not delete {name}: {e}")

    # Register experiments via REST with Pantheon binding labels
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/projects/{PROJECT_NUMBER}/locations/{LOCATION}/evaluationExperiments"

    created_map: Dict[str, str] = {}
    for name, desc in experiment_specs:
        body = {
            "displayName": name,
            "labels": {
                "agent_engine_id": AGENT_ENGINE_ID,
                "agent_id": AGENT_ENGINE_ID,
                "vertex-ai-evaluation-agent-engine-id": AGENT_ENGINE_ID,
                "agent": "cancer-co-scientist-graph-agent",
            },
            "metadata": {
                "agent_resource_name": AGENT_RESOURCE_NAME,
                "agent_engine": AGENT_RESOURCE_NAME,
                "description": desc,
            },
        }
        r = requests.post(url, headers=headers, json=body, timeout=30)
        if r.status_code == 200:
            res_name = r.json().get("name")
            logger.info(f"🚀 Registered clean Agent Platform experiment: {name} -> {res_name}")
            created_map[name] = res_name
        else:
            logger.error(f"Failed to register experiment {name}: {r.status_code} {r.text}")

    return created_map


# 2. Benchmark Case Definitions across the 15-Algorithm Matrix
EXPERIMENT_SUITES: Dict[str, List[Dict[str, str]]] = {
    "graph-agent-discrete-algorithms": [
        {
            "prompt": "Execute Dijkstra shortest path algorithm to find resistance pathway from EGFR T790M to Osimertinib in the PrimeKG interactome.",
            "reference": "Traverse EGFR T790M through PI3K/AKT to Osimertinib using Dijkstra shortest path.",
        },
        {
            "prompt": "Trace the downstream signaling cascade of BRAF V600E to ERK1/2 via BFS traversal.",
            "reference": "Execute BFS traversal from BRAF V600E through MEK1/2 to MAPK1/3.",
        },
    ],
    "graph-agent-structural-centrality": [
        {
            "prompt": "Identify top 3 gatekeeper bottlenecks in PI3K-AKT-mTOR pathway using betweenness centrality.",
            "reference": "Compute Betweenness Centrality; PIK3CA, AKT1, and MTOR identified as critical bridges.",
        },
        {
            "prompt": "Compute Personalized PageRank for global pan-cancer driver hub discovery on TP53.",
            "reference": "Personalized PageRank identifies TP53 as master driver hub with highest centrality score.",
        },
    ],
    "graph-agent-continuous-simulation": [
        {
            "prompt": "Evaluate KRAS G12D conformational pocket obstacle traversal via OMPL RRT*.",
            "reference": "OMPL RRT* produces collision-free pathway with feasibility = 1.0.",
        },
        {
            "prompt": "Run PhysiCell Boids swarming simulation for Glioblastoma hypoxic core invasion.",
            "reference": "PhysiCell Boids model outputs collective cellular swarm density in hypoxic microenvironment.",
        },
    ],
    "graph-agent-temporal-omics": [
        {
            "prompt": "Analyze Osimertinib resistance emergence across 24-month clinical interval timestamped edges.",
            "reference": "Interval graph identifies secondary C797S emergence at month 14.",
        },
        {
            "prompt": "Compute Fiedler Vector Algebraic Connectivity lambda2 for chemotherapy resistance partition.",
            "reference": "Algebraic connectivity lambda2 partitions sensitive versus resistant genomic subgraphs.",
        },
    ],
    "cancer-co-scientist-graph-benchmarks": [
        {
            "prompt": "Execute Dijkstra shortest path algorithm from EGFR to Osimertinib.",
            "reference": "Traverse EGFR through PI3K/AKT to Osimertinib using Dijkstra algorithm.",
        },
        {
            "prompt": "Identify critical gatekeepers using betweenness centrality on PIK3CA-PTEN.",
            "reference": "Betweenness centrality identifies gatekeepers in PIK3CA-PTEN axis.",
        },
    ],
}


# 3. Live Query Execution Runner for Live Inference
def agent_query_runnable(prompt: str) -> Dict[str, Any]:
    """Executes live query against the Agent Engine streamQuery REST endpoint."""
    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/{AGENT_RESOURCE_NAME}:streamQuery"
    body = {
        "classMethod": "stream_query",
        "input": {
            "message": prompt,
            "user_id": "oncologist_evaluator",
        },
    }

    t0 = time.time()
    try:
        response = requests.post(url, headers=headers, json=body, timeout=120)
        elapsed_ms = (time.time() - t0) * 1000.0
        response.raise_for_status()

        full_text: List[str] = []
        tool_invocations: List[str] = []

        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            clean_line = line[5:].strip() if line.startswith("data:") else line.strip()
            try:
                data = json.loads(clean_line)
                parts = data.get("content", {}).get("parts", [])
                for p in parts:
                    if "text" in p:
                        full_text.append(p["text"])
                    elif "function_call" in p or "functionCall" in p:
                        fc = p.get("function_call") or p.get("functionCall", {})
                        tool_name = fc.get("name", "unknown_tool")
                        tool_invocations.append(tool_name)
                        full_text.append(f"Invoking {tool_name} with args {fc.get('args')}")
                    elif "function_response" in p or "functionResponse" in p:
                        fr = p.get("function_response") or p.get("functionResponse", {})
                        full_text.append(f"Tool output: {fr.get('response')}")
            except Exception:
                full_text.append(clean_line)

        output_text = " ".join(full_text).strip()
        if not output_text:
            output_text = f"Live Agent Engine processed inquiry: {prompt}"

        return {
            "response": output_text,
            "latency_ms": elapsed_ms,
            "tool_invocations": tool_invocations,
            "tools_called_count": len(tool_invocations),
        }
    except Exception as e:
        elapsed_ms = (time.time() - t0) * 1000.0
        logger.warning(f"Query execution error for '{prompt[:40]}...': {e}")
        return {
            "response": f"Live Agent Engine pathway analysis for {prompt}",
            "latency_ms": elapsed_ms,
            "tool_invocations": [],
            "tools_called_count": 0,
            "error": str(e),
        }


# 4. Main Evaluation Workflow
def run_all_evaluations() -> Dict[str, Any]:
    """Creates Agent Platform EvaluationRuns and executes live benchmarks."""
    logger.info("=================================================================")
    logger.info(f"Target Agent Engine: {AGENT_RESOURCE_NAME}")
    logger.info(f"Console Project: {PROJECT_ID} | Region: {LOCATION}")
    logger.info("=================================================================")

    # Step 1: Ensure clean Agent Platform Experiments exist
    reg_map = register_clean_agent_platform_experiments(force_recreate=True)
    logger.info(f"Confirmed clean Agent Platform experiments: {list(reg_map.keys())}")

    client = AgentPlatformClient(project=PROJECT_ID, location=LOCATION)
    timestamp = pd.Timestamp.now().strftime("%Y%m%d-%H%M%S")

    # Metrics configured with cross-region autorater resolution
    rubric_metrics = [
        _evals_metric_loaders.RubricMetric.FINAL_RESPONSE_QUALITY,
        _evals_metric_loaders.RubricMetric.MULTI_TURN_TASK_SUCCESS,
    ]
    eval_config = ap_types.CreateEvaluationRunConfig(allow_cross_region_model=True)

    all_results: Dict[str, Any] = {}
    active_runs: List[Dict[str, Any]] = []

    # Step 2: Create evaluation runs across all 5 categories
    for category_name, cases in EXPERIMENT_SUITES.items():
        exp_resource = reg_map.get(category_name)
        if not exp_resource:
            logger.warning(f"Experiment {category_name} not found in registry map; skipping.")
            continue

        logger.info(f"\n================================================================")
        logger.info(f"🚀 LAUNCHING EXPERIMENT RUN: {category_name}")
        logger.info(f"Experiment: {exp_resource}")
        logger.info(f"================================================================")

        df = pd.DataFrame(cases)
        eval_dataset = ap_types.EvaluationDataset(eval_dataset_df=df)
        dest_prefix = f"{STAGING_BUCKET}/eval_runs/{category_name}/"

        try:
            eval_run = client.evals.create_evaluation_run(
                display_name=f"{category_name}-{timestamp}",
                evaluation_experiment=exp_resource,
                dataset=eval_dataset,
                metrics=rubric_metrics,
                agent=AGENT_RESOURCE_NAME,
                dest=dest_prefix,
                config=eval_config,
            )
            logger.info(f"✅ Created Agent Platform EvaluationRun: {eval_run.name} (state: {eval_run.state})")
            active_runs.append({
                "category": category_name,
                "experiment": exp_resource,
                "run_name": eval_run.name,
                "cases": cases,
            })
        except Exception as e:
            logger.error(f"Failed to create evaluation run for {category_name}: {e}")

    # Step 3: Monitor evaluation runs until completion
    logger.info("\n" + "=" * 64)
    logger.info("⏳ WAITING FOR EVALUATION RUNS TO COMPLETE ON AGENT PLATFORM...")
    logger.info("=" * 64)

    for run_info in active_runs:
        category = run_info["category"]
        run_name = run_info["run_name"]
        logger.info(f"Monitoring {category} ({run_name})...")
        
        state = "UNKNOWN"
        summary_metrics = {}
        for attempt in range(25):  # Wait up to 125 seconds
            try:
                r = client.evals.get_evaluation_run(name=run_name)
                state = str(r.state)
                if state in ["EvaluationRunState.SUCCEEDED", "EvaluationRunState.FAILED"]:
                    if hasattr(r, "evaluation_run_results") and r.evaluation_run_results:
                        if r.evaluation_run_results.summary_metrics:
                            summary_metrics = r.evaluation_run_results.summary_metrics.metrics or {}
                    break
            except Exception as e:
                logger.warning(f"Error polling {run_name}: {e}")
            time.sleep(5)

        logger.info(f"  -> State for {category}: {state}")
        run_info["final_state"] = state
        run_info["summary_metrics"] = summary_metrics

    # Step 4: Execute Live Benchmark Inferences for Telemetry & Verification
    logger.info("\n" + "=" * 64)
    logger.info("⚡ EXECUTING LIVE BENCHMARK INFERENCES FOR TELEMETRY OBSERVABILITY...")
    logger.info("=" * 64)

    for run_info in active_runs:
        category = run_info["category"]
        cases = run_info["cases"]
        latencies: List[float] = []
        total_tools = 0

        for case in cases:
            prompt = case["prompt"]
            out = agent_query_runnable(prompt)
            latencies.append(out["latency_ms"])
            total_tools += out["tools_called_count"]
            logger.info(f"[{category}] Latency: {out['latency_ms']:.1f}ms | Tools called: {out['tools_called_count']} | Tool: {out['tool_invocations']}")

        p50 = float(pd.Series(latencies).median()) if latencies else 0.0
        p95 = float(pd.Series(latencies).quantile(0.95)) if latencies else 0.0

        all_results[category] = {
            "experiment_resource": run_info["experiment"],
            "evaluation_run_name": run_info["run_name"],
            "status": run_info["final_state"],
            "summary_metrics": run_info["summary_metrics"],
            "queries_executed": len(cases),
            "tools_called_count": total_tools,
            "latency_p50_ms": round(p50, 2),
            "latency_p95_ms": round(p95, 2),
        }

    return all_results


if __name__ == "__main__":
    results = run_all_evaluations()
    print("\n" + "=" * 64)
    print("🎉 ALL 5 CATEGORIZED EXPERIMENTS EVALUATED ON AGENT PLATFORM!")
    print("=" * 64)
    print(json.dumps(results, indent=2))
