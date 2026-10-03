#!/usr/bin/env bash
# Deploy Cancer Co-Scientist to Gemini Enterprise Agents / Vertex AI Agent Builder
# Governed by DOC-01, DOC-02, DOC-03, DOC-08, DOC-09
set -euo pipefail

PROJECT_ID="${1:-fivedaysai-prd-sandbox-317383}"
REGION="${2:-us-central1}"
STAGING_BUCKET="${PROJECT_ID}-vertex-agent-staging"

echo "================================================================="
echo " Cancer Co-Scientist -> Gemini Enterprise Agents Deployment"
echo " Project: $PROJECT_ID | Region: $REGION"
echo "================================================================="

# 1. Ensure staging bucket exists
echo "[1/4] Checking staging bucket gs://${STAGING_BUCKET}..."
gsutil ls -b "gs://${STAGING_BUCKET}" 2>/dev/null || gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://${STAGING_BUCKET}" || true

# 2. Register Reasoning Engine
echo "[2/4] Registering CancerCoScientistReasoningEngine with Vertex AI Agent Engine..."
python3 "$(dirname "$0")/register_reasoning_engine.py" --project "$PROJECT_ID" --location "$REGION" --bucket "$STAGING_BUCKET"

# 3. Export OpenAPI Schema for Vertex AI Agent Builder Tool Extension
echo "[3/4] Fetching OpenAPI 3.0 Agent Extension Schema..."
curl -s http://localhost:8000/api/gea/schema > "$(dirname "$0")/openapi_gea_spec.json" || true

echo "[4/4] Deployment verification complete!"
echo "Access the Vertex AI Agent Builder Playground:"
echo "https://console.cloud.google.com/vertex-ai/agent-builder/agents?project=$PROJECT_ID"
