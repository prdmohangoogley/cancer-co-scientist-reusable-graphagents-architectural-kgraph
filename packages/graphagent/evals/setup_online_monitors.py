"""
Setup and management of continuous Online Evaluators (Monitors) in Vertex AI Agent Platform.
Governed by Enterprise Agents Guidelines DOC-01 and Spec 07.
"""
from __future__ import annotations
import os
import sys
from google.cloud import aiplatform_v1beta1
from google.cloud.aiplatform_v1beta1.types import online_evaluator, evaluation_service

PROJECT_ID = "fivedaysai-prd-sandbox-317383"
PROJECT_NUMBER = "301802433103"
LOCATION = "us-east1"

LEAD_ORCHESTRATOR_ID = os.getenv("GEA_LEAD_ORCHESTRATOR_ID", "6824256356745216000")
GRAPH_AGENT_ID = os.getenv("GEA_GRAPH_AGENT_ID", "4359942935643422720")

PREDEFINED_METRICS = [
    "tool_use_quality_v1",
    "final_response_quality_v1",
    "hallucination_v1",
    "safety_v1",
]


def get_online_evaluator_client() -> aiplatform_v1beta1.OnlineEvaluatorServiceClient:
    return aiplatform_v1beta1.OnlineEvaluatorServiceClient(
        client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
    )


def list_existing_evaluators(client: aiplatform_v1beta1.OnlineEvaluatorServiceClient) -> list:
    parent = f"projects/{PROJECT_NUMBER}/locations/{LOCATION}"
    return list(client.list_online_evaluators(parent=parent))


def create_or_get_monitor(
    client: aiplatform_v1beta1.OnlineEvaluatorServiceClient,
    display_name: str,
    reasoning_engine_id: str,
) -> online_evaluator.OnlineEvaluator:
    parent = f"projects/{PROJECT_NUMBER}/locations/{LOCATION}"
    agent_resource = f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/{reasoning_engine_id}"

    existing = list_existing_evaluators(client)
    for ev in existing:
        if ev.display_name == display_name or ev.agent_resource == agent_resource:
            print(f"Online evaluator already exists for {display_name}: {ev.name}")
            return ev

    print(f"Creating OnlineEvaluator for {display_name} targeting {agent_resource}...")
    eval_spec = online_evaluator.OnlineEvaluator(
        display_name=display_name,
        agent_resource=agent_resource,
        cloud_observability=online_evaluator.OnlineEvaluator.CloudObservability(
            trace_scope=online_evaluator.OnlineEvaluator.CloudObservability.TraceScope(),
            open_telemetry=online_evaluator.OnlineEvaluator.CloudObservability.OpenTelemetry(
                semconv_version="1.39.0"
            ),
        ),
        config=online_evaluator.OnlineEvaluator.Config(
            random_sampling=online_evaluator.OnlineEvaluator.Config.RandomSampling(
                percentage=100
            ),
        ),
        metric_sources=[
            evaluation_service.MetricSource(
                metric=evaluation_service.Metric(
                    predefined_metric_spec=evaluation_service.PredefinedMetricSpec(
                        metric_spec_name=metric_name
                    )
                )
            )
            for metric_name in PREDEFINED_METRICS
        ],
    )

    operation = client.create_online_evaluator(
        parent=parent, online_evaluator=eval_spec
    )
    print(f"Dispatched LRO: {operation.operation.name}. Waiting for completion...")
    res = operation.result(timeout=120)
    print(f"Successfully created OnlineEvaluator: {res.name}")
    return res


def main():
    client = get_online_evaluator_client()
    print("=" * 70)
    print("VERTEX AI AGENT PLATFORM - CONTINUOUS ONLINE MONITORS SETUP")
    print("=" * 70)

    # 1. Lead Orchestrator Monitor
    orch_eval = create_or_get_monitor(
        client=client,
        display_name="lead-orchestrator-continuous-monitor",
        reasoning_engine_id=LEAD_ORCHESTRATOR_ID,
    )

    # 2. Graph Agent Monitor
    graph_eval = create_or_get_monitor(
        client=client,
        display_name="graph-agent-continuous-monitor",
        reasoning_engine_id=GRAPH_AGENT_ID,
    )

    print("\nActive Online Evaluators:")
    evaluators = list_existing_evaluators(client)
    for e in evaluators:
        print(f"  • {e.display_name} -> {e.name}")
        print(f"    Target: {e.agent_resource}")
        metrics = [
            m.metric.predefined_metric_spec.metric_spec_name
            for m in e.metric_sources
            if m.metric and m.metric.predefined_metric_spec
        ]
        print(f"    Metrics: {metrics}")


if __name__ == "__main__":
    main()
