#!/usr/bin/env python3
"""CLI utility to query the Enterprise Agents Architectural Guidelines MCP Server."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

MCP_SERVER_DIR = Path("/Users/prdmohan/ge_spark_workspace/projects/architecture_best_practices_mcp")

RUNNER_SCRIPT = """
import asyncio
import json
import sys
from src.graph.client import GraphClient

async def run():
    client = GraphClient(use_mock=True)
    mode = sys.argv[1]

    if mode == "query":
        query = sys.argv[2]
        print(f"=== Searching Guidelines for: '{query}' ===")
        results = await client.search_guidelines(query=query)
        for g in results:
            print(f"\\n[{g.guideline_id}] {g.title} (#{g.category})")
            print(f"  Summary: {g.summary}")
            print(f"  Source:  {g.source_url}")

    elif mode == "id":
        gid = sys.argv[2]
        print(f"=== Details for: '{gid}' ===")
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
        print(f"=== Best Practice for Topic: '{topic}' ===")
        res = await client.get_best_practice(topic)
        print(json.dumps(res, indent=2))

    elif mode == "tradeoff":
        opt_a = sys.argv[2]
        opt_b = sys.argv[3]
        print(f"=== Tradeoff Evaluation: '{opt_a}' vs '{opt_b}' ===")
        try:
            res = await client.evaluate_tradeoffs(option_a=opt_a, option_b=opt_b)
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(f"Error evaluating tradeoffs: {e}")

asyncio.run(run())
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Enterprise Agents Guidelines")
    parser.add_argument("--query", "-q", help="Search keywords (e.g. 'a2ui', 'security')")
    parser.add_argument("--id", help="Guideline ID (e.g. 'DOC-03')")
    parser.add_argument("--best-practice", "-b", help="Best practice topic (e.g. 'ZAA')")
    parser.add_argument("--tradeoff-a", help="First architectural option")
    parser.add_argument("--tradeoff-b", help="Second architectural option")

    args = parser.parse_args()

    mode_args: list[str] = []
    if args.query:
        mode_args = ["query", args.query]
    elif args.id:
        mode_args = ["id", args.id]
    elif args.best_practice:
        mode_args = ["bp", args.best_practice]
    elif args.tradeoff_a and args.tradeoff_b:
        mode_args = ["tradeoff", args.tradeoff_a, args.tradeoff_b]
    else:
        parser.print_help()
        sys.exit(1)

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
    res = subprocess.run(cmd)
    sys.exit(res.returncode)


if __name__ == "__main__":
    main()
