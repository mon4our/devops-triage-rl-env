"""Client for the DevOps Triage environment."""

from __future__ import annotations

from openenv.core.mcp_client import MCPToolClient


class DevOpsTriageEnv(MCPToolClient):
    """Client for interacting with the DevOps Triage environment.

    Inherits all functionality from MCPToolClient:
    - reset(**kwargs) — reset the environment (pass task="log_diagnosis"|"test_triage"|"outage_rca")
    - list_tools() — discover available tools
    - call_tool(name, **kwargs) — execute a tool
    - step(action) — low-level step

    Example:
        async with DevOpsTriageEnv(base_url="http://localhost:8000") as env:
            await env.reset(task="log_diagnosis")
            tools = await env.list_tools()
            result = await env.call_tool("get_services")
            result = await env.call_tool("get_logs", service="user-service", level="ERROR")
    """

    pass
