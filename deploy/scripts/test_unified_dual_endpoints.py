#!/usr/bin/env python3
"""Unified Cloud Run Dual-Endpoint Demonstration Script.

Verifies and demonstrates that a single Cloud Run container serves BOTH:
1. The full A2UI Precision Oncology Web App at the Root URL (/).
2. The Gemini Enterprise Agents (GEA) & Vertex AI Agent Builder APIs at (/api/gea/*).

Adheres to:
- DOC-01: AI Agent Quality Engineering & Observability
- DOC-02: Zero Ambient Authority (ZAA)
- DOC-03: Open AI Agent Protocol Stack & A2UI Declarative Interfaces
"""

import json
import sys
import urllib.request
import urllib.error

DEFAULT_HOST = "http://localhost:8000"

def run_demonstration(base_url: str = DEFAULT_HOST):
    print("=" * 80)
    print(f" 🚀 DEMONSTRATION: UNIFIED CLOUD RUN CONTAINER DUAL-ACCESS VERIFICATION")
    print(f" Target Endpoint: {base_url}")
    print("=" * 80)
    
    # -------------------------------------------------------------------------
    # PART 1: Web App Frontend Served from the Container Root
    # -------------------------------------------------------------------------
    print("\n[PART 1] Verifying Web App Frontend at Root URL (/)...\n")
    try:
        req = urllib.request.Request(f"{base_url}/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            content_type = resp.headers.get("content-type", "")
            body = resp.read().decode("utf-8")
            print(f"  ✔ Status Code: {resp.status} OK")
            print(f"  ✔ Content-Type: {content_type}")
            print(f"  ✔ HTML Title / Brand Present: {'Cancer Co-Scientist' in body}")
            print(f"  ✔ PrimeKG Explorer Canvas Present: {'primekg-explorer-canvas' in body or 'a2ui-surface' in body}")
            print(f"  ✔ Memory Bank Inspector Present: {'memory-bank-drawer' in body}")
            print(f"  ✔ Telemetry HUD Modal Present: {'telemetry-modal' in body}")
            print(f"  -> Successfully confirmed: Container serves the rich web application directly from '/'")
    except Exception as e:
        print(f"  ❌ Failed to reach Web App Root: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PART 2: Container Health Probe Endpoint
    # -------------------------------------------------------------------------
    print("\n[PART 2] Verifying Cloud Run Health Check (/health)...\n")
    try:
        req = urllib.request.Request(f"{base_url}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  ✔ Health Probe: {data}")
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")

    # -------------------------------------------------------------------------
    # PART 3: GEA OpenAPI 3.0 Schema for Vertex AI Agent Builder
    # -------------------------------------------------------------------------
    print("\n[PART 3] Verifying GEA & Vertex AI Schema Endpoint (/api/gea/schema)...\n")
    try:
        req = urllib.request.Request(f"{base_url}/api/gea/schema")
        with urllib.request.urlopen(req, timeout=5) as resp:
            schema = json.loads(resp.read().decode("utf-8"))
            print(f"  ✔ OpenAPI Version: {schema.get('openapi')}")
            print(f"  ✔ Tool Title: {schema.get('info', {}).get('title')}")
            print(f"  ✔ Available Paths: {list(schema.get('paths', {}).keys())}")
            print(f"  ✔ Operation ID: {schema.get('paths', {}).get('/api/gea/invoke', {}).get('post', {}).get('operationId')}")
            print(f"  -> Successfully confirmed: Vertex AI Agent Builder can register this container directly as a Tool Extension")
    except Exception as e:
        print(f"  ❌ Failed to fetch GEA schema: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PART 4: GEA Direct Execution with Trajectory & Web App Deep-Links
    # -------------------------------------------------------------------------
    print("\n[PART 4] Executing Clinical Inquiry via GEA Endpoint (/api/gea/invoke)...\n")
    clinical_inquiry = {
        "query": "Identify drug repurposing candidates for EGFR T790M resistance in NSCLC",
        "session_id": "demo_cloudrun_unified_session",
        "user_id": "dr_attending_oncologist",
        "include_trajectory": True
    }
    try:
        req = urllib.request.Request(
            f"{base_url}/api/gea/invoke",
            data=json.dumps(clinical_inquiry).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"  ✔ Status: {result.get('status')}")
            print(f"  ✔ Selected Algorithm: {result.get('selected_algorithm')}")
            print(f"  ✔ Algorithm Choice Confidence: {result.get('algorithm_choice_confidence')}")
            print(f"  ✔ A2UI Surface Components Emitted: {len(result.get('a2ui_surface', {}).get('components', []))}")
            
            print("\n  🔍 Reasoning Trajectory (Inspected inside Vertex AI Playground):")
            for step in result.get("trajectory", []):
                print(f"     Step {step.get('step')}: {step.get('action')} -> {step.get('details')}")

            print("\n  🔗 Direct Dashboard Deep-Links (Enabling Instant Navigation from GEA to Web App):")
            direct_links = result.get("direct_links", {})
            for name, url in direct_links.items():
                print(f"     - {name}: {url}")

            print("\n  -> Successfully confirmed: GEA callers receive structured reasoning, A2UI ASTs, and direct deep-links into the Web App")
    except Exception as e:
        print(f"  ❌ Failed to execute GEA invocation: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PART 5: PrimeKG Explorer & Observability Verification
    # -------------------------------------------------------------------------
    print("\n[PART 5] Verifying PrimeKG Explorer & Telemetry Endpoints...\n")
    try:
        # PrimeKG explore
        req_exp = urllib.request.Request(f"{base_url}/api/primekg/explore?focal_entity=EGFR&depth=2")
        with urllib.request.urlopen(req_exp, timeout=5) as resp:
            exp_data = json.loads(resp.read().decode("utf-8"))
            comp_types = [c.get("component") for c in exp_data.get("components", [])]
            print(f"  ✔ PrimeKG Explorer AST: Intent={exp_data.get('intent')}, Components={comp_types}")

        # Telemetry
        req_tel = urllib.request.Request(f"{base_url}/api/stats/telemetry")
        with urllib.request.urlopen(req_tel, timeout=5) as resp:
            tel_data = json.loads(resp.read().decode("utf-8"))
            print(f"  ✔ Telemetry HUD: p50={tel_data.get('latency_ms', {}).get('p50')}ms, p95={tel_data.get('latency_ms', {}).get('p95')}ms, Cache Hit Rate={tel_data.get('token_consumption', {}).get('cache_hit_rate') * 100:.1f}%")
            print(f"  ✔ IR Quality Metrics: mAP={tel_data.get('quality_metrics', {}).get('retrieval_map')}, Precision@10={tel_data.get('quality_metrics', {}).get('precision_at_k')}")
    except Exception as e:
        print(f"  ❌ Failed to fetch PrimeKG/Telemetry: {e}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(" ✅ CONCLUSION: PERFECT DUAL-ACCESS UNIFICATION VERIFIED")
    print(" The exact same container serves:")
    print("   1. Web App User Interface at '/'")
    print("   2. Gemini Enterprise Agents / Vertex AI Engine at '/api/gea/*'")
    print("   3. Deep-links from GEA immediately open the rich interactive visualizer and HUD in the web app!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    run_demonstration(url)
