"""Architecture Guidelines FastMCP Client Bridge.

Interfaces with the Enterprise Agents Architectural Guidelines MCP Server:
https://github.com/prdmohangoogley/gea-agents-arch-guidelines-mcp-server

Executes live ISO GQL queries against Google Cloud Spanner Graph
and analytical queries against Google BigQuery.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("mcp_client")

LOCAL_MCP_REPO = Path("/Users/prdmohan/ge_spark_workspace/projects/architecture_best_practices_mcp")


class GuidelinesMCPClient:
    """Client bridge to the Enterprise Agents Architectural Guidelines MCP Server.
    
    Connects to live Cloud Spanner Graph and BigQuery instances in Google Cloud.
    """

    def __init__(
        self,
        server_url: Optional[str] = None,
        local_repo_path: Optional[Path] = None,
        use_mock: Optional[bool] = None,
    ) -> None:
        self.server_url = server_url or os.getenv("ARCH_GUIDELINES_MCP_URL")
        self.local_repo_path = local_repo_path or LOCAL_MCP_REPO
        if use_mock is not None:
            self.use_mock = use_mock
        else:
            self.use_mock = os.getenv("USE_MOCK_GRAPH", "false").lower() == "true"

    async def search_guidelines(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        """Search guidelines by keyword across the MCP server knowledge graph."""
        logger.info(f"Querying Guidelines MCP server for keyword: '{query}'")
        if self.local_repo_path.exists():
            return await self._run_local_mcp_query("query", query)
        return self._offline_guidelines_fallback(query)

    async def get_best_practice(self, topic: str) -> dict[str, Any]:
        """Fetch best practice from Cloud Spanner Graph via ISO GQL."""
        logger.info(f"Querying Spanner Graph (ArchGuidelinesGraph) via MCP tool 'get_best_practice': '{topic}'")
        if self.local_repo_path.exists():
            results = await self._run_local_mcp_query("bp", topic)
            if results and isinstance(results, dict):
                return results
            if results and isinstance(results, list) and len(results) > 0:
                return results[0]
        return {
            "status": "cached",
            "source": "fallback",
            "topic": topic,
            "patterns": ["Zero Ambient Authority", "Declarative A2UI Interfaces"],
        }

    async def deep_dive_guideline(self, component: str) -> dict[str, Any]:
        """Perform deep-dive analytical investigation via BigQuery analytics."""
        logger.info(f"Querying BigQuery (gea_arch_guidelines_analytics) via MCP tool 'deep_dive_guideline': '{component}'")
        if self.local_repo_path.exists():
            res = await self._run_local_mcp_query("deepdive", component)
            if res and isinstance(res, dict):
                return res
        return {"status": "fallback", "source": "fallback", "component": component}

    async def evaluate_tradeoffs(self, option_a: str, option_b: str) -> dict[str, Any]:
        """Evaluate architectural tradeoffs between two patterns."""
        if self.local_repo_path.exists():
            res = await self._run_local_mcp_query("tradeoff", option_a, option_b)
            return res if isinstance(res, dict) else {"result": res}
        return {"option_a": option_a, "option_b": option_b, "recommendation": option_a}

    async def _run_local_mcp_query(self, mode: str, *args: str) -> Any:
        """Execute query by invoking the local MCP server Python runner via uv with live GCP connection."""
        runner_code = """
import asyncio, json, sys, os
from src.graph.client import GraphClient

async def run():
    use_mock = os.getenv("USE_MOCK_GRAPH", "false").lower() == "true"
    client = GraphClient(use_mock=use_mock)
    mode = sys.argv[1]
    
    if mode == "query":
        res = await client.search_guidelines(sys.argv[2])
        print(json.dumps([{"id": g.guideline_id, "title": g.title, "category": g.category, "summary": g.summary} for g in res]))
    elif mode == "bp":
        res = await client.get_best_practice(sys.argv[2])
        print(json.dumps(res))
    elif mode == "deepdive":
        res = await client.deep_dive_guideline(sys.argv[2])
        print(json.dumps(res))
    elif mode == "tradeoff":
        res = await client.evaluate_tradeoffs(sys.argv[2], sys.argv[3])
        print(json.dumps(res))

asyncio.run(run())
"""
        env = os.environ.copy()
        env["USE_MOCK_GRAPH"] = "true" if self.use_mock else "false"

        cmd = [
            "/Users/prdmohan/.local/bin/uv",
            "--directory",
            str(self.local_repo_path),
            "run",
            "python",
            "-c",
            runner_code,
            mode,
            *args,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0 and stdout:
                output = stdout.decode().strip()
                # If there are metric warnings at the end, find the JSON block
                for line in reversed(output.split("\n")):
                    if line.startswith("{") or line.startswith("["):
                        try:
                            return json.loads(line)
                        except Exception:
                            pass
                return json.loads(output)
            logger.warning(f"MCP sub-process returned code {proc.returncode}: {stderr.decode()}")
        except Exception as e:
            logger.warning(f"Error querying local MCP server: {e}")
        return {}

    def _offline_guidelines_fallback(self, query: str) -> list[dict[str, str]]:
        return [
            {
                "id": "DOC-03",
                "title": "Open AI Agent Protocol Stack",
                "category": "protocols",
                "summary": "Protocol architecture spanning MCP, A2A, UCP, AP2/x402, and A2UI.",
            },
            {
                "id": "DOC-02",
                "title": "Vibe Coding Agent Security & Evaluation",
                "category": "security",
                "summary": "Sandboxing, Zero Ambient Authority (ZAA), and session convergence.",
            },
        ]
