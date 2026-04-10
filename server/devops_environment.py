"""DevOps Triage Environment — MCPEnvironment subclass with all 3 tasks."""

from __future__ import annotations

import json
import random
from typing import Any, Optional
from uuid import uuid4

try:
    from openenv.core.env_server.mcp_environment import MCPEnvironment
    from openenv.core.env_server.types import Action, Observation, State
except ImportError:
    from openenv.core.env_server.mcp_environment import MCPEnvironment
    from openenv.core.env_server.interfaces import Action, Observation, State

from fastmcp import FastMCP

from models import DevOpsState
from .data.task1_log_diagnosis import SCENARIOS as TASK1_SCENARIOS
from .data.task2_test_triage import SCENARIOS as TASK2_SCENARIOS
from .data.task3_outage_rca import SCENARIOS as TASK3_SCENARIOS, SERVICE_TOPOLOGY
from .rewards import grade_log_diagnosis, grade_test_triage, grade_outage_rca


TASK_NAMES = {"log_diagnosis", "test_triage", "outage_rca"}
TASK_MAX_STEPS = {"log_diagnosis": 25, "test_triage": 35, "outage_rca": 40}


class DevOpsEnvironment(MCPEnvironment):
    """DevOps Triage environment with 3 tasks of increasing difficulty."""

    def __init__(self) -> None:
        mcp = FastMCP("devops_triage")
        self._register_tools(mcp)
        super().__init__(mcp)

        self._state = DevOpsState(episode_id=str(uuid4()), step_count=0)
        self._current_task: str = ""
        self._scenario: dict = {}
        self._done = False
        self._accumulated_reward = 0.0

        # Tracking for incremental rewards
        self._queried_services: set[str] = set()
        self._search_terms_used: set[str] = set()
        self._tests_inspected: set[str] = set()
        self._tests_history_checked: set[str] = set()
        self._source_files_viewed: set[str] = set()
        self._rca_services_checked: set[str] = set()
        self._rca_metrics_checked: set[str] = set()
        self._rca_traces_viewed: set[str] = set()
        self._rca_logs_viewed: set[str] = set()
        self._action_history: list[str] = []

        # Task 2 accumulates classifications
        self._test_classifications: dict[str, dict] = {}
        self._final_score: float = 0.0

    # ── Tool Registration ──

    def _register_tools(self, mcp: FastMCP) -> None:
        env = self

        # ── Task 1 Tools ──
        @mcp.tool
        def get_services() -> list[str]:
            """List all available services in the cluster."""
            return list(env._scenario.get("services", {}).keys())

        @mcp.tool
        def get_logs(service: str, level: str = "ALL", limit: int = 20) -> list[dict]:
            """Get log entries from a service. Filter by level (ERROR/WARN/INFO/ALL). Returns up to `limit` entries."""
            services = env._scenario.get("services", {})
            if service not in services:
                return [{"error": f"Service '{service}' not found. Use get_services() to list available services."}]
            logs = services[service]
            if level != "ALL":
                logs = [e for e in logs if e["level"] == level.upper()]
            return logs[:limit]

        @mcp.tool
        def search_logs(keyword: str) -> list[dict]:
            """Search across all service logs for entries containing the keyword. Returns up to 30 matches."""
            results = []
            for service_name, logs in env._scenario.get("services", {}).items():
                for entry in logs:
                    if keyword.lower() in entry["message"].lower():
                        results.append({**entry, "service": service_name})
            return results[:30]

        @mcp.tool
        def get_runbook(incident_type: str) -> dict:
            """Look up the operations runbook for a given incident type. Returns diagnostic steps and remediation procedures."""
            runbooks = {
                "memory_leak": {
                    "title": "Memory Leak Runbook",
                    "diagnostic_steps": [
                        "Check heap usage trends with get_logs(service, level='WARN')",
                        "Look for OOM or OutOfMemoryError in logs",
                        "Identify which service has growing memory over time",
                        "Check for large cache sizes or unclosed resources",
                    ],
                    "remediation": ["Restart affected service", "Increase memory limits", "Deploy fix for leak source"],
                },
                "database_connection_pool": {
                    "title": "DB Connection Pool Exhaustion Runbook",
                    "diagnostic_steps": [
                        "Check connection pool stats in service logs",
                        "Identify services sharing the database",
                        "Look for slow queries holding connections open",
                    ],
                    "remediation": ["Increase pool size", "Fix slow queries", "Add connection pooler (PgBouncer)"],
                },
                "certificate_expiration": {
                    "title": "TLS Certificate Expiration Runbook",
                    "diagnostic_steps": [
                        "Check certificate expiry dates in logs",
                        "Identify affected endpoints and services",
                        "Verify auto-renewal configuration",
                    ],
                    "remediation": ["Renew certificate immediately", "Fix auto-renewal process", "Restart affected services"],
                },
                "rate_limiting": {
                    "title": "Rate Limiting Runbook",
                    "diagnostic_steps": [
                        "Check for 429 Too Many Requests in gateway logs",
                        "Identify source of excessive traffic",
                        "Review rate limit configuration",
                    ],
                    "remediation": ["Block abusive IPs/clients", "Adjust rate limits if legitimate", "Add caching layer"],
                },
                "disk_space": {
                    "title": "Disk Space Exhaustion Runbook",
                    "diagnostic_steps": [
                        "Check for ENOSPC errors in logs",
                        "Identify which service or volume is full",
                        "Check log retention and rotation policies",
                    ],
                    "remediation": ["Clear old logs or temp files", "Increase volume size", "Fix log rotation"],
                },
                "dns": {
                    "title": "DNS Resolution Failure Runbook",
                    "diagnostic_steps": [
                        "Check for ENOTFOUND or SERVFAIL errors in logs",
                        "Test DNS resolution from affected service",
                        "Check DNS resolver health",
                    ],
                    "remediation": ["Restart DNS resolver", "Flush DNS cache", "Switch to backup DNS"],
                },
                "deadlock": {
                    "title": "Database Deadlock Runbook",
                    "diagnostic_steps": [
                        "Check for deadlock detection messages in database logs",
                        "Identify conflicting transactions and tables",
                        "Review query patterns and lock ordering",
                    ],
                    "remediation": ["Kill blocking transactions", "Fix lock ordering in application code", "Add retry logic for deadlocks"],
                },
                "cache_poisoning": {
                    "title": "Cache Poisoning Runbook",
                    "diagnostic_steps": [
                        "Compare cached values against source of truth",
                        "Check cache invalidation events and TTLs",
                        "Identify when stale data was written",
                    ],
                    "remediation": ["Flush affected cache keys", "Fix cache invalidation logic", "Add cache validation checks"],
                },
            }
            key = incident_type.lower().replace(" ", "_").replace("-", "_")
            for rk, rv in runbooks.items():
                if key in rk or rk in key:
                    return rv
            return {"info": f"No runbook found for '{incident_type}'. Available types: {list(runbooks.keys())}"}

        @mcp.tool
        def submit_diagnosis(incident_type: str, severity: str, affected_services: str, root_cause: str) -> dict:
            """Submit your incident diagnosis.
            - incident_type: the type of incident (e.g. 'memory_leak', 'database_connection_pool_exhaustion')
            - severity: P1/P2/P3/P4
            - affected_services: comma-separated service names
            - root_cause: free-text description of the root cause
            """
            if env._current_task != "log_diagnosis":
                return {"error": "submit_diagnosis is only available for the log_diagnosis task"}
            submitted = {
                "incident_type": incident_type,
                "severity": severity,
                "affected_services": affected_services,
                "root_cause": root_cause,
            }
            score = grade_log_diagnosis(submitted, env._scenario["ground_truth"])
            env._final_score = score
            env._done = True
            return {"submitted": True, "score": score, "done": True}

        # ── Task 2 Tools ──
        @mcp.tool
        def get_test_summary() -> dict:
            """Get overview of the test suite results: total, passed, failed, skipped counts and list of failed test IDs."""
            summary = env._scenario.get("test_summary", {})
            failed_ids = [t["test_id"] for t in env._scenario.get("failed_tests", [])]
            return {**summary, "failed_test_ids": failed_ids}

        @mcp.tool
        def get_test_details(test_id: str) -> dict:
            """Get detailed output for a specific test: error message, stack trace, console logs, DOM snapshot."""
            for t in env._scenario.get("failed_tests", []):
                if t["test_id"] == test_id:
                    return {
                        "test_id": t["test_id"],
                        "name": t["name"],
                        "error_output": t["error_output"],
                        "stack_trace": t["stack_trace"],
                        "console_logs": t["console_logs"],
                        "dom_snapshot": t["dom_snapshot"],
                    }
            return {"error": f"Test '{test_id}' not found. Use get_test_summary() to list failed tests."}

        @mcp.tool
        def get_test_history(test_id: str, num_runs: int = 10) -> dict:
            """Get pass/fail history for a test across recent CI runs. True=pass, False=fail."""
            for t in env._scenario.get("failed_tests", []):
                if t["test_id"] == test_id:
                    history = t["history"][:num_runs]
                    pass_rate = sum(history) / len(history) if history else 0
                    return {
                        "test_id": test_id,
                        "history": history,
                        "pass_rate": round(pass_rate, 2),
                        "total_runs": len(history),
                    }
            return {"error": f"Test '{test_id}' not found."}

        @mcp.tool
        def get_source_code(file_path: str) -> str:
            """View application or test source code by file path."""
            files = env._scenario.get("source_files", {})
            if file_path in files:
                return files[file_path]
            available = list(files.keys())
            return f"File '{file_path}' not found. Available files: {available}"

        @mcp.tool
        def get_recent_changes() -> list[dict]:
            """Get recent git commits with diffs that may have caused test failures."""
            return env._scenario.get("recent_changes", [])

        @mcp.tool
        def get_ci_config() -> dict:
            """Get the CI/CD pipeline configuration: test runner, environment, timeout settings, retry policy."""
            return env._scenario.get("ci_config", {
                "runner": "GitHub Actions",
                "test_framework": "Playwright",
                "timeout_ms": 30000,
                "retries": 0,
                "parallel": True,
                "environment": "staging",
                "node_version": "18.x",
                "browser": "chromium",
            })

        @mcp.tool
        def submit_classification(test_id: str, category: str, evidence: str, recommendation: str) -> dict:
            """Classify a failed test.
            - test_id: the test identifier
            - category: genuine_bug | flaky_test | environment_issue | stale_test
            - evidence: describe what evidence led to your classification
            - recommendation: fix_code | rerun | update_test | check_infra
            """
            if env._current_task != "test_triage":
                return {"error": "submit_classification is only available for the test_triage task"}

            env._test_classifications[test_id] = {
                "category": category,
                "evidence": evidence,
                "recommendation": recommendation,
            }

            failed_tests = env._scenario.get("failed_tests", [])
            classified_ids = set(env._test_classifications.keys())
            all_ids = {t["test_id"] for t in failed_tests}
            remaining = all_ids - classified_ids

            if not remaining:
                score = grade_test_triage(env._test_classifications, failed_tests)
                env._final_score = score
                env._done = True
                return {"submitted": True, "test_id": test_id, "remaining": 0, "score": score, "done": True}

            return {"submitted": True, "test_id": test_id, "remaining": len(remaining), "remaining_ids": list(remaining), "done": False}

        # ── Task 3 Tools ──
        @mcp.tool
        def get_service_status() -> dict:
            """Get health status of all services: healthy, degraded, or unhealthy."""
            return env._scenario.get("service_statuses", {})

        @mcp.tool
        def get_service_metrics(service: str, metric: str) -> dict:
            """Get a specific metric for a service. metric: cpu | memory | latency_ms | error_rate | throughput | connections."""
            metrics = env._scenario.get("service_metrics", {})
            if service in metrics and metric in metrics[service]:
                return {"service": service, "metric": metric, "value": metrics[service][metric]}
            if service not in metrics:
                from .data.task3_outage_rca import _HEALTHY_METRICS
                if metric in _HEALTHY_METRICS:
                    return {"service": service, "metric": metric, "value": _HEALTHY_METRICS[metric]}
                return {"error": f"Unknown metric '{metric}'. Valid: cpu, memory, latency_ms, error_rate, throughput, connections"}
            return {"error": f"Unknown metric '{metric}'."}

        @mcp.tool
        def get_service_logs(service: str, level: str = "ALL", limit: int = 20) -> list[dict]:
            """Get log entries from a specific service in the microservice cluster."""
            logs_data = env._scenario.get("service_logs", {})
            if service not in logs_data:
                return [{"info": f"No logs available for '{service}'. This service may be operating normally."}]
            logs = logs_data[service]
            if level != "ALL":
                logs = [e for e in logs if e["level"] == level.upper()]
            return logs[:limit]

        @mcp.tool
        def get_service_config(service: str) -> dict:
            """Get configuration for a service (version, replicas, limits, etc.)."""
            configs = env._scenario.get("service_configs", {})
            if service in configs:
                return {"service": service, **configs[service]}
            from .data.task3_outage_rca import _BASE_CONFIG
            return {"service": service, **_BASE_CONFIG}

        @mcp.tool
        def get_dependency_graph() -> dict:
            """Get the service dependency map showing which services depend on which."""
            return SERVICE_TOPOLOGY

        @mcp.tool
        def trace_request(trace_id: str) -> dict:
            """Get a distributed trace showing request flow through services. Use get_alert_history() to find trace IDs."""
            for t in env._scenario.get("traces", []):
                if t["trace_id"] == trace_id:
                    return t
            available = [t["trace_id"] for t in env._scenario.get("traces", [])]
            return {"error": f"Trace '{trace_id}' not found. Available traces: {available}"}

        @mcp.tool
        def get_alert_history() -> list[dict]:
            """Get recent alerts with timestamps, services, severities, and messages."""
            alerts = env._scenario.get("alerts", [])
            trace_ids = [t["trace_id"] for t in env._scenario.get("traces", [])]
            return {"alerts": alerts, "available_trace_ids": trace_ids}

        @mcp.tool
        def get_deployment_history(service: str = "") -> list[dict]:
            """Get recent deployment history. Optionally filter by service name."""
            deployments = env._scenario.get("deployment_history", [])
            if service:
                deployments = [d for d in deployments if d.get("service") == service]
            if not deployments:
                return [{"info": "No recent deployments found" + (f" for '{service}'" if service else "")}]
            return deployments

        @mcp.tool
        def submit_report(root_cause_service: str, root_cause_description: str, failure_chain: str, remediation_steps: str) -> dict:
            """Submit incident report.
            - root_cause_service: the service where the root cause originated
            - root_cause_description: describe the root cause
            - failure_chain: comma-separated service names in causal order (e.g. 'user-db,user-service,auth-service,api-gateway')
            - remediation_steps: newline-separated remediation steps in priority order
            """
            if env._current_task != "outage_rca":
                return {"error": "submit_report is only available for the outage_rca task"}
            submitted = {
                "root_cause_service": root_cause_service,
                "root_cause_description": root_cause_description,
                "failure_chain": failure_chain,
                "remediation_steps": remediation_steps,
            }
            score = grade_outage_rca(submitted, env._scenario)
            env._final_score = score
            env._done = True
            return {"submitted": True, "score": score, "done": True}

    # ── Incremental Reward Logic ──

    def _compute_step_reward(self, tool_name: str, tool_args: dict) -> float:
        """Compute incremental reward for a single step based on which tool was called."""
        reward = 0.0
        action_key = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"

        # Repeat penalty
        if action_key in self._action_history:
            reward -= 0.02

        self._action_history.append(action_key)

        if self._current_task == "log_diagnosis":
            step_threshold = 15
            if tool_name == "get_logs":
                svc = tool_args.get("service", "")
                if svc and svc not in self._queried_services:
                    self._queried_services.add(svc)
                    if svc in self._scenario.get("relevant_services", []):
                        reward += 0.02
            elif tool_name == "search_logs":
                kw = tool_args.get("keyword", "").lower()
                if kw and kw not in self._search_terms_used:
                    self._search_terms_used.add(kw)
                    for term in self._scenario.get("relevant_search_terms", []):
                        if term.lower() in kw or kw in term.lower():
                            reward += 0.01
                            break

        elif self._current_task == "test_triage":
            step_threshold = 20
            if tool_name == "get_test_details":
                tid = tool_args.get("test_id", "")
                if tid and tid not in self._tests_inspected:
                    self._tests_inspected.add(tid)
                    failed_ids = {t["test_id"] for t in self._scenario.get("failed_tests", [])}
                    if tid in failed_ids:
                        reward += 0.03
            elif tool_name == "get_test_history":
                tid = tool_args.get("test_id", "")
                if tid and tid not in self._tests_history_checked:
                    self._tests_history_checked.add(tid)
                    reward += 0.05
            elif tool_name == "get_source_code":
                fp = tool_args.get("file_path", "")
                if fp and fp not in self._source_files_viewed:
                    self._source_files_viewed.add(fp)
                    if fp in self._scenario.get("source_files", {}):
                        reward += 0.02
            elif tool_name == "get_recent_changes":
                if "__recent_changes_viewed__" not in self._source_files_viewed:
                    self._source_files_viewed.add("__recent_changes_viewed__")
                    reward += 0.03

        elif self._current_task == "outage_rca":
            step_threshold = 25
            statuses = self._scenario.get("service_statuses", {})
            if tool_name == "get_service_status":
                if "__status_checked__" not in self._rca_services_checked:
                    self._rca_services_checked.add("__status_checked__")
                    reward += 0.03
            elif tool_name == "get_service_metrics":
                svc = tool_args.get("service", "")
                key = f"{svc}:{tool_args.get('metric', '')}"
                if key not in self._rca_metrics_checked:
                    self._rca_metrics_checked.add(key)
                    if svc in self._scenario.get("service_metrics", {}):
                        reward += 0.03
            elif tool_name == "trace_request":
                tid = tool_args.get("trace_id", "")
                if tid and tid not in self._rca_traces_viewed:
                    self._rca_traces_viewed.add(tid)
                    reward += 0.05
            elif tool_name == "get_service_logs":
                svc = tool_args.get("service", "")
                if svc and svc not in self._rca_logs_viewed:
                    self._rca_logs_viewed.add(svc)
                    root = self._scenario.get("root_cause_service", "")
                    if svc == root:
                        reward += 0.04
                    elif statuses.get(svc) != "healthy":
                        reward += 0.01
            elif tool_name == "get_dependency_graph":
                if "__dep_graph_viewed__" not in self._rca_services_checked:
                    self._rca_services_checked.add("__dep_graph_viewed__")
                    reward += 0.03
        else:
            step_threshold = 20

        # Step penalty after threshold
        if self._state.step_count > step_threshold:
            reward -= 0.01

        return reward

    # ── Core Environment Methods ──

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task: str = "log_diagnosis",
        scenario_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Observation:
        if task not in TASK_NAMES:
            return Observation(
                done=True,
                reward=0.0,
                metadata={"error": f"Unknown task '{task}'. Valid: {sorted(TASK_NAMES)}"},
            )

        self._current_task = task

        # Select scenario
        if task == "log_diagnosis":
            scenarios = TASK1_SCENARIOS
        elif task == "test_triage":
            scenarios = TASK2_SCENARIOS
        else:
            scenarios = TASK3_SCENARIOS

        if scenario_id:
            matching = [s for s in scenarios if s["id"] == scenario_id]
            self._scenario = matching[0] if matching else random.choice(scenarios)
        else:
            self._scenario = random.choice(scenarios)

        # Reset state
        eid = episode_id or str(uuid4())
        self._state = DevOpsState(
            episode_id=eid,
            step_count=0,
            task=task,
            scenario_id=self._scenario["id"],
        )
        self._done = False
        self._accumulated_reward = 0.0
        self._final_score = 0.0
        self._action_history = []
        self._queried_services = set()
        self._search_terms_used = set()
        self._tests_inspected = set()
        self._tests_history_checked = set()
        self._source_files_viewed = set()
        self._rca_services_checked = set()
        self._rca_metrics_checked = set()
        self._rca_traces_viewed = set()
        self._rca_logs_viewed = set()
        self._test_classifications = {}

        # Build initial observation message
        description = self._scenario.get("description", "Investigate the incident.")
        if task == "log_diagnosis":
            tools_hint = "Tools: get_services(), get_logs(service, level, limit), search_logs(keyword), get_runbook(incident_type), submit_diagnosis(incident_type, severity, affected_services, root_cause)"
        elif task == "test_triage":
            tools_hint = "Tools: get_test_summary(), get_test_details(test_id), get_test_history(test_id, num_runs), get_source_code(file_path), get_recent_changes(), get_ci_config(), submit_classification(test_id, category, evidence, recommendation)"
            description = self._scenario.get("app_description", description)
        else:
            tools_hint = "Tools: get_service_status(), get_service_metrics(service, metric), get_service_logs(service, level, limit), get_service_config(service), get_dependency_graph(), trace_request(trace_id), get_alert_history(), get_deployment_history(service), submit_report(root_cause_service, root_cause_description, failure_chain, remediation_steps)"

        return Observation(
            done=False,
            reward=0.0,
            metadata={
                "task": task,
                "scenario_id": self._scenario["id"],
                "description": description,
                "tools": tools_hint,
            },
        )

    def _step_impl(
        self,
        action: Action,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> Observation:
        return Observation(
            done=False,
            reward=0.0,
            metadata={
                "error": f"Unknown action type: {type(action).__name__}. Use ListToolsAction or CallToolAction."
            },
        )

    # ── Shared step helpers ──

    def _extract_tool_info(self, action: Action) -> tuple[str, dict]:
        """Extract tool name and arguments from an action."""
        tool_name = ""
        tool_args: dict = {}
        if hasattr(action, "tool_name") and action.tool_name:
            tool_name = action.tool_name
        if hasattr(action, "arguments") and action.arguments:
            tool_args = action.arguments if isinstance(action.arguments, dict) else {}
        return tool_name, tool_args

    def _process_step_result(
        self, tool_name: str, tool_args: dict, obs: Observation,
    ) -> Observation:
        """Apply reward logic, max-step enforcement, and done state."""
        step_reward = self._compute_step_reward(tool_name, tool_args)

        if self._done:
            step_reward += self._final_score

        # Max-step enforcement
        max_steps = TASK_MAX_STEPS.get(self._current_task, 30)
        if not self._done and self._state.step_count >= max_steps:
            self._done = True

        self._accumulated_reward += step_reward
        self._state.accumulated_reward = round(self._accumulated_reward, 4)

        # Mutate the observation in-place so serialization preserves its
        # subclass fields (e.g. CallToolObservation.result, .tool_name)
        obs.done = self._done
        obs.reward = round(step_reward, 4)
        return obs

    def step(
        self,
        action: Action,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> Observation:
        self._state.step_count += 1
        tool_name, tool_args = self._extract_tool_info(action)
        obs = super().step(action, timeout_s=timeout_s, **kwargs)
        return self._process_step_result(tool_name, tool_args, obs)

    async def step_async(
        self,
        action: Action,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> Observation:
        self._state.step_count += 1
        tool_name, tool_args = self._extract_tool_info(action)
        obs = await super().step_async(action, timeout_s=timeout_s, **kwargs)
        return self._process_step_result(tool_name, tool_args, obs)

    @property
    def state(self) -> DevOpsState:
        return self._state
