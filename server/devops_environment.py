"""DevOps Triage Environment — MCPEnvironment subclass with all 3 tasks.

Hardening notes (what makes this env hard to game):
- Submissions are structured (closed-vocab enums + lists), not prose. See
  `server.rewards` for the closed vocabularies. Free-text grading is gone.
- Shaping rewards are capped at MAX_SHAPING_REWARD per episode so they
  cannot beat or replace the submission reward. The "wander forever"
  attractor is killed by a step penalty that exceeds the cap over the
  episode horizon.
- Repeat-action detection hashes a *semantic* key (tool name + relevant
  args only) so adding noise to the args (e.g. bumping `limit`) does not
  evade the repeat penalty.
- Tools that previously leaked the answer key (`get_runbook`, empty
  `search_logs`, `get_alert_history`'s trace dump, `get_service_metrics`'s
  healthy fallback, `reset`'s scenario_id echo) have been neutered.
- `reset(seed=...)` is honored. A `split="train"|"test"` arg picks from
  disjoint scenario pools so eval scores are reproducible at fixed seed.
"""

from __future__ import annotations

import json
import random
from typing import Any, Iterable, Optional
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
from .rewards import (
    CATEGORIES,
    EVIDENCE_TAGS,
    INCIDENT_TYPES,
    RECOMMENDATIONS,
    ROOT_CAUSE_TAGS,
    SEVERITIES,
    grade_log_diagnosis,
    grade_outage_rca,
    grade_test_triage,
)


def _sorted_list(items) -> list[str]:
    return sorted(items)


_INCIDENT_TYPES_STR = ", ".join(_sorted_list(INCIDENT_TYPES))
_ROOT_CAUSE_TAGS_STR = ", ".join(_sorted_list(ROOT_CAUSE_TAGS))
_CATEGORIES_STR = ", ".join(_sorted_list(CATEGORIES))
_RECOMMENDATIONS_STR = ", ".join(_sorted_list(RECOMMENDATIONS))
_EVIDENCE_TAGS_STR = ", ".join(_sorted_list(EVIDENCE_TAGS))
_SEVERITIES_STR = ", ".join(s.upper() for s in _sorted_list(SEVERITIES))


TASK_NAMES = {"log_diagnosis", "test_triage", "outage_rca"}
TASK_MAX_STEPS = {"log_diagnosis": 25, "test_triage": 35, "outage_rca": 40}
SUBMIT_TOOLS = {"submit_diagnosis", "submit_classification", "submit_report"}

# Shaping reward cap per episode. Kept strictly below the smallest
# non-zero submission component (severity = 0.20) so wandering forever
# cannot beat even a minimal successful submission. Combined with
# STEP_PENALTY this makes "never submit" strictly worse than "submit".
MAX_SHAPING_REWARD = 0.15
STEP_PENALTY_AFTER_THRESHOLD = -0.03
REPEAT_PENALTY = -0.05
LOG_LIMIT_MAX = 50

# Semantic args that the repeat-penalty key cares about. Args not listed
# here (e.g. limit, level) cannot be used to evade the repeat penalty.
SEMANTIC_ARG_KEYS: dict[str, tuple[str, ...]] = {
    "get_logs": ("service",),
    "search_logs": ("keyword",),
    "get_runbook": ("incident_type",),
    "get_test_details": ("test_id",),
    "get_test_history": ("test_id",),
    "get_source_code": ("file_path",),
    "get_service_metrics": ("service", "metric"),
    "get_service_logs": ("service",),
    "get_service_config": ("service",),
    "trace_request": ("trace_id",),
    "get_deployment_history": ("service",),
}


def _split_scenarios(scenarios: list[dict], split: str) -> list[dict]:
    filtered = [s for s in scenarios if s.get("split", "train") == split]
    return filtered or scenarios  # never return empty


def _coerce_str_list(value: Any) -> list[str]:
    """Accept list[str] | str | None and return a clean list[str].
    Strings are split on commas/newlines so legacy callers still work."""
    if value is None:
        return []
    if isinstance(value, str):
        parts: list[str] = []
        for chunk in value.replace("\n", ",").split(","):
            chunk = chunk.strip()
            if chunk:
                parts.append(chunk)
        return parts
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value)]


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
        self._shaping_budget_used = 0.0

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
        self._action_history: set[str] = set()

        # Task 2 accumulates classifications
        self._test_classifications: dict[str, dict] = {}
        self._final_score: float = 0.0

        # Per-step reward breakdown (consumed by _process_step_result)
        self._last_breakdown: dict[str, float] = {}

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
            """Get log entries from a service. Filter by level (ERROR/WARN/INFO/ALL). Returns up to `limit` entries (capped at 50)."""
            services = env._scenario.get("services", {})
            if service not in services:
                return [{"error": f"Service '{service}' not found."}]
            logs = services[service]
            if level != "ALL":
                logs = [e for e in logs if e["level"] == level.upper()]
            try:
                limit_int = max(1, min(int(limit), LOG_LIMIT_MAX))
            except (TypeError, ValueError):
                limit_int = 20
            return logs[:limit_int]

        @mcp.tool
        def search_logs(keyword: str) -> list[dict]:
            """Search across all service logs for entries containing the keyword. Empty keywords are rejected. Returns up to 30 matches."""
            if not keyword or not keyword.strip():
                return [{"error": "keyword required"}]
            kw = keyword.lower()
            results = []
            for service_name, logs in env._scenario.get("services", {}).items():
                for entry in logs:
                    if kw in entry["message"].lower():
                        results.append({**entry, "service": service_name})
            return results[:30]

        @mcp.tool
        def get_runbook(incident_type: str = "") -> dict:
            """Generic incident response runbook. The runbook does not enumerate incident types — agents must determine the incident type from the logs."""
            return {
                "title": "Generic incident response",
                "diagnostic_steps": [
                    "Identify which services are degraded using get_services() and get_logs(service, level='ERROR')",
                    "Search for error patterns across the cluster with search_logs(keyword)",
                    "Correlate timestamps to find the originating service",
                    "Read the relevant ERROR/WARN log lines to determine the failure mode",
                ],
                "remediation": [
                    "Confirm the incident type from log evidence",
                    "Apply the standard remediation for that class of incident",
                    "Verify recovery and document the root cause",
                ],
            }

        @mcp.tool
        def submit_diagnosis(
            incident_type: str,
            severity: str,
            affected_services: list[str] | str,
            root_cause_tags: list[str] | str,
        ) -> dict:
            f"""Submit your incident diagnosis (structured, closed-vocabulary).

            Arguments:
            - incident_type: EXACTLY ONE of: {_INCIDENT_TYPES_STR}
            - severity: ONE of: {_SEVERITIES_STR}
            - affected_services: list of service names from the cluster (or comma-separated string). F1-scored, so submitting every service hurts.
            - root_cause_tags: list of 2-5 tags from: {_ROOT_CAUSE_TAGS_STR}. F1-scored — over-submitting tanks the score as much as under-submitting.

            Grading: incident_type (0.35) + severity (0.20) + affected_services F1 (0.25) + root_cause_tags F1 (0.20).
            """
            if env._current_task != "log_diagnosis":
                return {"error": "submit_diagnosis is only available for the log_diagnosis task"}
            submitted = {
                "incident_type": incident_type,
                "severity": severity,
                "affected_services": _coerce_str_list(affected_services),
                "root_cause_tags": _coerce_str_list(root_cause_tags),
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
            return {"error": f"test_id '{test_id}' not found"}

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
            return {"error": f"test_id '{test_id}' not found"}

        @mcp.tool
        def get_source_code(file_path: str) -> str:
            """View application or test source code by file path."""
            files = env._scenario.get("source_files", {})
            if file_path in files:
                return files[file_path]
            return f"File '{file_path}' not found"

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
        def submit_classification(
            test_id: str,
            category: str,
            recommendation: str,
            evidence_tags: list[str] | str,
        ) -> dict:
            f"""Classify a failed test (structured, closed-vocabulary). Call once per failed test.

            Arguments:
            - test_id: must match an id from get_test_summary().failed_test_ids
            - category: EXACTLY ONE of: {_CATEGORIES_STR}
            - recommendation: EXACTLY ONE of: {_RECOMMENDATIONS_STR}
            - evidence_tags: list of 1-4 tags from: {_EVIDENCE_TAGS_STR}. F1-scored — do not kitchen-sink.

            Grading (per test, averaged): category (0.50) + evidence_tags F1 (0.30) + recommendation (0.20).
            """
            if env._current_task != "test_triage":
                return {"error": "submit_classification is only available for the test_triage task"}

            failed_ids = {t["test_id"] for t in env._scenario.get("failed_tests", [])}
            if test_id not in failed_ids:
                return {"error": f"test_id '{test_id}' is not a known failed test"}

            env._test_classifications[test_id] = {
                "category": category,
                "recommendation": recommendation,
                "evidence_tags": _coerce_str_list(evidence_tags),
            }

            failed_tests = env._scenario.get("failed_tests", [])
            classified_ids = set(env._test_classifications.keys())
            remaining = failed_ids - classified_ids

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
            if service not in metrics:
                return {"error": f"service '{service}' has no metrics recorded"}
            if metric not in metrics[service]:
                return {"error": f"metric '{metric}' not recorded for service '{service}'"}
            return {"service": service, "metric": metric, "value": metrics[service][metric]}

        @mcp.tool
        def get_service_logs(service: str, level: str = "ALL", limit: int = 20) -> list[dict]:
            """Get log entries from a specific service in the microservice cluster (capped at 50)."""
            logs_data = env._scenario.get("service_logs", {})
            if service not in logs_data:
                return [{"info": f"No logs available for '{service}'"}]
            logs = logs_data[service]
            if level != "ALL":
                logs = [e for e in logs if e["level"] == level.upper()]
            try:
                limit_int = max(1, min(int(limit), LOG_LIMIT_MAX))
            except (TypeError, ValueError):
                limit_int = 20
            return logs[:limit_int]

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
            """Get a distributed trace showing request flow through services. Trace IDs are referenced in alert messages."""
            for t in env._scenario.get("traces", []):
                if t["trace_id"] == trace_id:
                    return t
            return {"error": f"trace '{trace_id}' not found"}

        @mcp.tool
        def get_alert_history() -> list[dict]:
            """Get recent alerts with timestamps, services, severities, and messages. Trace IDs (when present) are embedded in alert messages."""
            return env._scenario.get("alerts", [])

        @mcp.tool
        def get_deployment_history(service: str = "") -> list[dict]:
            """Get recent deployment history. Optionally filter by service name."""
            deployments = env._scenario.get("deployment_history", [])
            if service:
                deployments = [d for d in deployments if d.get("service") == service]
            if not deployments:
                return [{"info": "No recent deployments found"}]
            return deployments

        @mcp.tool
        def get_remediation_steps() -> list[dict]:
            """List the candidate remediation step bank for this scenario.

            The bank contains BOTH applicable steps AND plausible distractors —
            you must decide which IDs apply to the current incident. Submitting
            the entire bank hurts your score: F1 is precision-aware and
            ordering LCS divides by max length, so extras drag both components
            down.

            Each entry has an `id` and a human-readable `label`. Submit only
            the applicable IDs, in operational order, via
            submit_report(remediation_step_ids=...).
            """
            bank = env._scenario.get("remediation_steps_bank")
            if bank:
                return bank
            return env._scenario.get("remediation_steps_canonical", [])

        @mcp.tool
        def submit_report(
            root_cause_service: str,
            failure_chain: list[str] | str,
            remediation_step_ids: list[str] | str,
        ) -> dict:
            """Submit incident report (structured).

            Arguments:
            - root_cause_service: the service where the root cause originated (must match exactly, see get_service_status() for valid names)
            - failure_chain: ordered list of services in causal order. Scored by precision-aware LCS (lcs / max(len(sub), len(exp))), so padding the chain hurts.
            - remediation_step_ids: ordered list of step IDs picked from get_remediation_steps(). Do NOT invent IDs. F1 + ordering LCS, so extra IDs hurt.

            Grading: root_cause_service (0.30) + failure_chain LCS (0.30) + step F1 (0.25) + step ordering LCS (0.15).
            """
            if env._current_task != "outage_rca":
                return {"error": "submit_report is only available for the outage_rca task"}
            submitted = {
                "root_cause_service": root_cause_service,
                "failure_chain": _coerce_str_list(failure_chain),
                "remediation_step_ids": _coerce_str_list(remediation_step_ids),
            }
            score = grade_outage_rca(submitted, env._scenario)
            env._final_score = score
            env._done = True
            return {"submitted": True, "score": score, "done": True}

    # ── Incremental Reward Logic ──

    def _semantic_action_key(self, tool_name: str, tool_args: dict) -> str:
        """Hash the action by semantically meaningful args only.

        This prevents agents from evading the repeat penalty by varying
        irrelevant args (e.g. `limit=20` vs `limit=21` for `get_logs`).
        """
        keys = SEMANTIC_ARG_KEYS.get(tool_name)
        if keys is None:
            payload = json.dumps(tool_args, sort_keys=True, default=str)
            return f"{tool_name}:{payload}"
        relevant = {k: tool_args.get(k) for k in keys}
        return f"{tool_name}:{json.dumps(relevant, sort_keys=True, default=str)}"

    def _credit_shaping(self, amount: float) -> float:
        """Pay out shaping reward subject to the per-episode budget cap."""
        if amount <= 0:
            return 0.0
        remaining = MAX_SHAPING_REWARD - self._shaping_budget_used
        if remaining <= 0:
            return 0.0
        granted = min(amount, remaining)
        self._shaping_budget_used += granted
        return granted

    def _compute_step_reward(self, tool_name: str, tool_args: dict) -> float:
        """Compute incremental reward for a single step based on which tool was called."""
        breakdown = {"shaping": 0.0, "step_penalty": 0.0, "repeat_penalty": 0.0}
        action_key = self._semantic_action_key(tool_name, tool_args)

        # Repeat penalty (semantic)
        if action_key in self._action_history:
            breakdown["repeat_penalty"] = REPEAT_PENALTY
        self._action_history.add(action_key)

        candidate_shaping = 0.0

        if self._current_task == "log_diagnosis":
            step_threshold = 15
            if tool_name == "get_logs":
                svc = tool_args.get("service", "")
                if svc and svc not in self._queried_services:
                    self._queried_services.add(svc)
                    if svc in self._scenario.get("relevant_services", []):
                        candidate_shaping += 0.02
            elif tool_name == "search_logs":
                kw = (tool_args.get("keyword") or "").lower().strip()
                if kw and kw not in self._search_terms_used:
                    self._search_terms_used.add(kw)
                    for term in self._scenario.get("relevant_search_terms", []):
                        if term.lower() in kw or kw in term.lower():
                            candidate_shaping += 0.01
                            break

        elif self._current_task == "test_triage":
            step_threshold = 20
            if tool_name == "get_test_details":
                tid = tool_args.get("test_id", "")
                if tid and tid not in self._tests_inspected:
                    self._tests_inspected.add(tid)
                    failed_ids = {t["test_id"] for t in self._scenario.get("failed_tests", [])}
                    if tid in failed_ids:
                        candidate_shaping += 0.03
            elif tool_name == "get_test_history":
                tid = tool_args.get("test_id", "")
                if tid and tid not in self._tests_history_checked:
                    self._tests_history_checked.add(tid)
                    failed_ids = {t["test_id"] for t in self._scenario.get("failed_tests", [])}
                    if tid in failed_ids:
                        candidate_shaping += 0.03
            elif tool_name == "get_source_code":
                fp = tool_args.get("file_path", "")
                if fp and fp not in self._source_files_viewed:
                    self._source_files_viewed.add(fp)
                    if fp in self._scenario.get("source_files", {}):
                        candidate_shaping += 0.02
            elif tool_name == "get_recent_changes":
                if "__recent_changes_viewed__" not in self._source_files_viewed:
                    self._source_files_viewed.add("__recent_changes_viewed__")
                    candidate_shaping += 0.03

        elif self._current_task == "outage_rca":
            step_threshold = 25
            statuses = self._scenario.get("service_statuses", {})
            if tool_name == "get_service_status":
                if "__status_checked__" not in self._rca_services_checked:
                    self._rca_services_checked.add("__status_checked__")
                    candidate_shaping += 0.03
            elif tool_name == "get_service_metrics":
                svc = tool_args.get("service", "")
                key = f"{svc}:{tool_args.get('metric', '')}"
                if key not in self._rca_metrics_checked:
                    self._rca_metrics_checked.add(key)
                    if svc in self._scenario.get("service_metrics", {}):
                        candidate_shaping += 0.02
            elif tool_name == "trace_request":
                tid = tool_args.get("trace_id", "")
                known_traces = {t["trace_id"] for t in self._scenario.get("traces", [])}
                if tid and tid in known_traces and tid not in self._rca_traces_viewed:
                    self._rca_traces_viewed.add(tid)
                    candidate_shaping += 0.04
            elif tool_name == "get_service_logs":
                svc = tool_args.get("service", "")
                if svc and svc not in self._rca_logs_viewed:
                    self._rca_logs_viewed.add(svc)
                    root = self._scenario.get("root_cause_service", "")
                    if svc == root:
                        candidate_shaping += 0.04
                    elif statuses.get(svc) and statuses[svc] != "healthy":
                        candidate_shaping += 0.01
            elif tool_name == "get_dependency_graph":
                if "__dep_graph_viewed__" not in self._rca_services_checked:
                    self._rca_services_checked.add("__dep_graph_viewed__")
                    candidate_shaping += 0.03
        else:
            step_threshold = 20

        breakdown["shaping"] = self._credit_shaping(candidate_shaping)

        # Step penalty after threshold (sized to dwarf the shaping cap over
        # the episode horizon, so wandering forever loses).
        if self._state.step_count > step_threshold:
            breakdown["step_penalty"] = STEP_PENALTY_AFTER_THRESHOLD

        self._last_breakdown = breakdown
        return sum(breakdown.values())

    # ── Core Environment Methods ──

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task: str = "log_diagnosis",
        scenario_id: Optional[str] = None,
        split: str = "train",
        **kwargs: Any,
    ) -> Observation:
        if task not in TASK_NAMES:
            return Observation(
                done=True,
                reward=0.0,
                metadata={"error": f"Unknown task '{task}'. Valid: {sorted(TASK_NAMES)}"},
            )
        if split not in {"train", "test"}:
            split = "train"

        self._current_task = task

        # Select scenario pool by split
        if task == "log_diagnosis":
            scenarios = TASK1_SCENARIOS
        elif task == "test_triage":
            scenarios = TASK2_SCENARIOS
        else:
            scenarios = TASK3_SCENARIOS

        pool = _split_scenarios(scenarios, split)

        # Honor seed via a local RNG instance — don't touch the global module RNG.
        rng = random.Random(seed)

        if scenario_id and seed is not None:
            # Replay path: explicit scenario_id is only honored when the
            # caller also provides a seed (signaling intent to reproduce).
            matching = [s for s in pool if s["id"] == scenario_id]
            self._scenario = matching[0] if matching else rng.choice(pool)
        else:
            self._scenario = rng.choice(pool)

        # Reset state
        eid = episode_id or str(uuid4())
        self._state = DevOpsState(
            episode_id=eid,
            step_count=0,
            task=task,
            scenario_id=self._scenario["id"],  # kept in state for debugging only
            split=split,
        )
        self._done = False
        self._accumulated_reward = 0.0
        self._final_score = 0.0
        self._shaping_budget_used = 0.0
        self._action_history = set()
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
        self._last_breakdown = {}

        # Build initial observation message. Use the public description so
        # the agent cannot fingerprint scenarios from the initial obs.
        description = self._scenario.get("description", "Investigate the incident.")
        vocab_hint = ""
        if task == "log_diagnosis":
            tools_hint = (
                "Tools: get_services(), get_logs(service, level, limit), search_logs(keyword), "
                "get_runbook(), submit_diagnosis(incident_type, severity, affected_services, root_cause_tags)"
            )
            vocab_hint = (
                f"Closed vocabularies (submissions are F1-scored — pick precisely, do NOT kitchen-sink):\n"
                f"  incident_type ∈ {{{_INCIDENT_TYPES_STR}}}\n"
                f"  severity ∈ {{{_SEVERITIES_STR}}}\n"
                f"  root_cause_tags ⊂ {{{_ROOT_CAUSE_TAGS_STR}}}"
            )
        elif task == "test_triage":
            tools_hint = (
                "Tools: get_test_summary(), get_test_details(test_id), get_test_history(test_id, num_runs), "
                "get_source_code(file_path), get_recent_changes(), get_ci_config(), "
                "submit_classification(test_id, category, recommendation, evidence_tags)"
            )
            description = self._scenario.get("app_description", description)
            vocab_hint = (
                f"Closed vocabularies (F1-scored — pick precisely):\n"
                f"  category ∈ {{{_CATEGORIES_STR}}}\n"
                f"  recommendation ∈ {{{_RECOMMENDATIONS_STR}}}\n"
                f"  evidence_tags ⊂ {{{_EVIDENCE_TAGS_STR}}}\n"
                f"You must call submit_classification once per failed test id."
            )
        else:
            tools_hint = (
                "Tools: get_service_status(), get_service_metrics(service, metric), "
                "get_service_logs(service, level, limit), get_service_config(service), "
                "get_dependency_graph(), trace_request(trace_id), get_alert_history(), "
                "get_deployment_history(service), get_remediation_steps(), "
                "submit_report(root_cause_service, failure_chain, remediation_step_ids)"
            )
            vocab_hint = (
                "Submission: root_cause_service must be a service name from get_service_status(); "
                "remediation_step_ids MUST come from get_remediation_steps() — do not invent IDs. "
                "Padding failure_chain or step list with extras lowers the score (precision-aware)."
            )

        return Observation(
            done=False,
            reward=0.0,
            metadata={
                "task": task,
                "description": description,
                "tools": tools_hint,
                "vocabulary": vocab_hint,
                "max_steps": TASK_MAX_STEPS.get(task, 30),
                "shaping_budget": MAX_SHAPING_REWARD,
                # NOTE: scenario_id is intentionally NOT echoed to the agent.
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
        breakdown = dict(self._last_breakdown)
        breakdown["final"] = 0.0

        if self._done and tool_name in SUBMIT_TOOLS:
            step_reward += self._final_score
            breakdown["final"] = self._final_score

        # Max-step enforcement
        max_steps = TASK_MAX_STEPS.get(self._current_task, 30)
        if not self._done and self._state.step_count >= max_steps:
            self._done = True

        self._accumulated_reward += step_reward
        self._state.accumulated_reward = round(self._accumulated_reward, 4)

        # Mutate the observation in-place so serialization preserves its
        # subclass fields (e.g. CallToolObservation.result, .tool_name).
        obs.done = self._done
        obs.reward = round(step_reward, 4)
        if obs.metadata is None:
            obs.metadata = {}
        obs.metadata.setdefault("step_count", self._state.step_count)
        obs.metadata.setdefault("max_steps", max_steps)
        obs.metadata.setdefault("shaping_budget_remaining", round(MAX_SHAPING_REWARD - self._shaping_budget_used, 4))
        obs.metadata.setdefault("reward_breakdown", {k: round(v, 4) for k, v in breakdown.items()})
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
