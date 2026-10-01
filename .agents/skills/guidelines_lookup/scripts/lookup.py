#!/usr/bin/env python3
"""CLI utility to query the Enterprise Agents Architectural Guidelines MCP Server.

Executes live ISO GQL against Google Cloud Spanner Graph (ArchGuidelinesGraph)
and analytical queries against Google BigQuery (gea_arch_guidelines_analytics).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

MCP_SERVER_DIR = Path("/Users/prdmohan/ge_spark_workspace/projects/architecture_best_practices_mcp")

RUNNER_SCRIPT = """
import asyncio
import json
import sys
import os
from src.graph.client import GraphClient

async def run():
    mode = sys.argv[1]
    use_mock = os.getenv("USE_MOCK_GRAPH", "false").lower() == "true"
    
    # Initialize GraphClient with live Cloud Spanner Graph and BigQuery by default
    client = GraphClient(use_mock=use_mock)

    if mode == "query":
        query = sys.argv[2]
        print(f"=== [MCP Tool: search_guidelines] Searching: '{query}' ===")
        results = await client.search_guidelines(query=query)
        for g in results:
            print(f"\\n[{g.guideline_id}] {g.title} (#{g.category})")
            print(f"  Summary: {g.summary}")
            print(f"  Source:  {g.source_url}")

    elif mode == "id":
        gid = sys.argv[2]
        print(f"=== [MCP Tool: get_guideline_details] Guideline: '{gid}' ===")
        g = await client.get_guideline(gid)
        if g:
            print(f"ID:       {g.guideline_id}")
            print(f"Title:    {g.title}")
            print(f"Category: {g.category}")
            print(f"Summary:  {g.summary}")
            print(f"Source:   {g.source_url}")
        else:
            print(f"Guideline '{gid}' not found.")

    elif mode == "bp":
        topic = sys.argv[2]
        print(f"=== [MCP Tool: get_best_practice] ISO GQL Spanner Graph Query for: '{topic}' ===")
        res = await client.get_best_practice(topic)
        print(f"Status:       {res.get('status')}")
        print(f"Query Source: {res.get('source')} (Cloud Spanner Graph)")
        print(f"Latency:      {res.get('latency_ms')} ms")
        print(f"Total Matches:{res.get('total_matches')}")
        print(json.dumps(res, indent=2))

    elif mode == "deepdive":
        component = sys.argv[2]
        print(f"=== [MCP Tool: deep_dive_guideline] BigQuery Analytics Query for: '{component}' ===")
        res = await client.deep_dive_guideline(component)
        print(f"Status:       {res.get('status')}")
        print(f"Query Source: {res.get('source')} (Google BigQuery)")
        print(f"Latency:      {res.get('latency_ms')} ms")
        print(json.dumps(res, indent=2))

    elif mode == "tradeoff":
        opt_a = sys.argv[2]
        opt_b = sys.argv[3]
        print(f"=== [MCP Tool: evaluate_tradeoffs] Tradeoffs: '{opt_a}' vs '{opt_b}' ===")
        try:
            res = await client.evaluate_tradeoffs(option_a=opt_a, option_b=opt_b)
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"Error evaluating tradeoffs: {e}")

asyncio.run(run())
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Enterprise Agents Guidelines MCP Server (Live Spanner Graph & BigQuery)")
    parser.add_argument("--query", "-q", help="Search keywords (e.g. 'a2ui', 'security')")
    parser.add_argument("--id", help="Guideline ID (e.g. 'DOC-03')")
    parser.add_argument("--best-practice", "-b", help="Best practice topic queried via Spanner Graph GQL (e.g. 'security', 'protocol')")
    parser.add_argument("--deep-dive", "-d", help="Component deep dive queried via BigQuery analytics (e.g. 'Security', 'Quality')")
    parser.add_argument("--tradeoff-a", help="First architectural option")
    parser.add_argument("--tradeoff-b", help="Second architectural option")
    parser.add_argument("--mock", action="store_true", help="Force mock offline cache instead of live Spanner Graph / BigQuery")

    args = parser.parse_args()

    mode_args: list[str] = []
    if args.query:
        mode_args = ["query", args.query]
    elif args.id:
        mode_args = ["id", args.id]
    elif args.best_practice:
        mode_args = ["bp", args.best_practice]
    elif args.deep_dive:
        mode_args = ["deepdive", args.deep_dive]
    elif args.tradeoff_a and args.tradeoff_b:
        mode_args = ["tradeoff", args.tradeoff_a, args.tradeoff_b]
    else:
        parser.print_help()
        sys.exit(1)

    env = os.environ.copy()
    if args.mock:
        env["USE_MOCK_GRAPH"] = "true"
    else:
        env["USE_MOCK_GRAPH"] = "false"

    cmd = [
        "/Users/prdmohan/.local/bin/uv",
        "--directory",
        str(MCP_SERVER_DIR),
        "run",
        "python",
        "-c",
        RUNNER_SCRIPT,
        *mode_args,
    ]
    res = subprocess.run(cmd, env=env)
    sys.exit(res.returncode)


if __name__ == "__main__":
    main()
