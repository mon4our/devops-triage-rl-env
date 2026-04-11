"""Reward computation for all 3 DevOps Triage tasks.

All graders are deterministic and structured-only. Free-text grading was
removed in favor of closed vocabularies because keyword-coverage scoring
is trivially gamed by stuffing every plausible term into a single blob.

Submissions are picks from closed enums and tag sets:
- INCIDENT_TYPES, SEVERITIES, ROOT_CAUSE_TAGS for Task 1
- CATEGORIES, RECOMMENDATIONS, EVIDENCE_TAGS for Task 2
- service names + per-scenario remediation step IDs for Task 3

Set components are F1-scored so over-submitting hurts as much as
under-submitting. Ordered components use precision-aware LCS
(lcs / max(len(sub), len(exp))) so padding the chain hurts.
"""

from __future__ import annotations

from typing import Iterable


# ── Shared helpers ──

def _normalize(s: str) -> str:
    return (s or "").lower().strip().replace("-", "_").replace(" ", "_")


def _normalize_set(items: Iterable[str] | str | None) -> set[str]:
    if not items:
        return set()
    if isinstance(items, str):
        items = [s for s in items.split(",") if s.strip()]
    out: set[str] = set()
    for it in items:
        n = _normalize(it)
        if n:
            out.add(n)
    return out


def _normalize_list(items: Iterable[str] | str | None) -> list[str]:
    if not items:
        return []
    if isinstance(items, str):
        items = [s for s in items.split(",") if s.strip()]
    out: list[str] = []
    for it in items:
        n = _normalize(it)
        if n:
            out.append(n)
    return out


def _f1(submitted: set[str], expected: set[str]) -> float:
    if not expected or not submitted:
        return 0.0
    tp = len(submitted & expected)
    if tp == 0:
        return 0.0
    precision = tp / len(submitted)
    recall = tp / len(expected)
    return 2 * precision * recall / (precision + recall)


def _ordered_lcs_score(sub: list[str], exp: list[str]) -> float:
    """Precision-aware LCS: lcs_len / max(len(sub), len(exp)).

    Dividing by max (not len(exp)) penalizes padding the submission with
    junk entries to game the LCS, while still rewarding correct ordering.
    """
    if not exp or not sub:
        return 0.0
    s = _normalize_list(sub)
    e = _normalize_list(exp)
    if not s or not e:
        return 0.0
    m, n = len(s), len(e)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s[i - 1] == e[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n] / max(m, n)


# ── Closed vocabularies ──

INCIDENT_TYPES: set[str] = {
    "database_connection_pool_exhaustion",
    "memory_leak",
    "tls_certificate_expiration",
    "rate_limiting",
    "disk_space_exhaustion",
    "dns_resolution_failure",
    "message_queue_consumer_lag",
    "network_timeout",
    "database_deadlock",
    "cache_poisoning",
}

INCIDENT_TYPE_ALIASES: dict[str, list[str]] = {
    "database_connection_pool_exhaustion": [
        "db_pool_exhaustion", "connection_pool_exhaustion", "database_pool",
        "pool_exhaustion", "db_connection_pool", "connection_pool",
    ],
    "memory_leak": ["oom", "out_of_memory", "heap_exhaustion", "memory_exhaustion"],
    "tls_certificate_expiration": [
        "cert_expiry", "certificate_expiration", "ssl_expiry", "tls_expiry",
        "certificate_expired", "ssl_certificate_expiration",
    ],
    "rate_limiting": ["rate_limit", "throttling", "too_many_requests", "429"],
    "disk_space_exhaustion": [
        "disk_full", "no_space_left", "enospc", "disk_exhaustion", "storage_full",
    ],
    "dns_resolution_failure": [
        "dns_failure", "dns_outage", "name_resolution_failure",
        "dns_resolver_failure", "dns_resolution",
    ],
    "message_queue_consumer_lag": [
        "kafka_consumer_lag", "consumer_lag", "queue_lag",
        "message_queue_lag", "kafka_lag", "consumer_group_lag",
    ],
    "network_timeout": [
        "upstream_timeout", "api_timeout", "connection_timeout",
        "firewall_issue", "network_issue", "packet_loss",
    ],
    "database_deadlock": [
        "deadlock", "lock_contention", "transaction_deadlock",
        "lock_timeout", "deadlock_detected",
    ],
    "cache_poisoning": [
        "stale_cache", "cache_corruption", "cache_invalidation_failure",
        "incorrect_cache", "bad_cache", "cache_inconsistency",
    ],
}

SEVERITIES: set[str] = {"p1", "p2", "p3", "p4"}

ROOT_CAUSE_TAGS: set[str] = {
    # connection / pool
    "connection_pool_exhausted", "max_connections_reached", "pool_timeout",
    # database
    "postgres", "deadlock", "lock_contention", "slow_query",
    # memory
    "memory_leak", "heap_exhausted", "oom", "gc_pressure",
    # certificates
    "certificate_expired", "tls_handshake_failed", "ca_chain_invalid",
    # rate limiting
    "rate_limit_exceeded", "throttling", "abusive_client",
    # disk
    "disk_full", "enospc", "log_rotation_failed", "retention_misconfigured",
    # dns
    "dns_resolution_failed", "servfail", "enotfound", "resolver_unreachable",
    # message queue
    "consumer_lag", "consumer_rebalance", "kafka_session_timeout", "partition_skew",
    # network
    "network_timeout", "firewall_block", "packet_loss", "etimedout", "upstream_unreachable",
    # cache
    "cache_stale", "cache_invalidation_failed", "cache_key_mismatch", "ttl_misconfigured",
}

CATEGORIES: set[str] = {"genuine_bug", "flaky_test", "environment_issue", "stale_test"}
RECOMMENDATIONS: set[str] = {"fix_code", "rerun", "update_test", "check_infra"}

EVIDENCE_TAGS: set[str] = {
    # bug indicators
    "recent_code_change", "regression", "calculation_error", "off_by_one",
    "null_dereference", "missing_validation", "wrong_constant", "incorrect_logic",
    "type_mismatch", "permission_logic_error",
    # flaky indicators
    "intermittent", "race_condition", "timing_dependent", "animation_dependent",
    "network_dependent", "passes_on_rerun", "history_inconsistent",
    # environment indicators
    "external_service_down", "staging_misconfigured", "credentials_expired",
    "infrastructure_failure", "network_unreachable", "third_party_outage",
    # stale indicators
    "outdated_assertion", "intentional_change", "format_change",
    "renamed_element", "deprecated_api", "design_update",
}


def _match_incident_type(submitted: str, expected: str) -> bool:
    norm = _normalize(submitted)
    if norm == _normalize(expected):
        return True
    aliases = INCIDENT_TYPE_ALIASES.get(_normalize(expected), [])
    return norm in {_normalize(a) for a in aliases}


# ── Task 1: Log Anomaly Diagnosis ──

def grade_log_diagnosis(submitted: dict, ground_truth: dict) -> float:
    score = 0.0

    # Incident type (0.35) — exact enum / alias match
    if _match_incident_type(submitted.get("incident_type", ""), ground_truth["incident_type"]):
        score += 0.35

    # Severity (0.20) — exact match
    if _normalize(submitted.get("severity", "")) == _normalize(ground_truth["severity"]):
        score += 0.20

    # Affected services (0.25) — F1
    sub_services = _normalize_set(submitted.get("affected_services"))
    exp_services = _normalize_set(ground_truth["affected_services"])
    score += 0.25 * _f1(sub_services, exp_services)

    # Root cause tags (0.20) — F1 over closed vocabulary
    sub_tags = _normalize_set(submitted.get("root_cause_tags"))
    exp_tags = _normalize_set(ground_truth["root_cause_tags"])
    score += 0.20 * _f1(sub_tags, exp_tags)

    return round(min(score, 1.0), 4)


# ── Task 2: CI/CD Test Failure Triage ──

def grade_test_classification(submitted: dict, ground_truth: dict) -> float:
    score = 0.0

    # Category (0.50)
    if _normalize(submitted.get("category", "")) == _normalize(ground_truth["category"]):
        score += 0.50

    # Evidence tags (0.30) — F1 over closed vocabulary
    sub_tags = _normalize_set(submitted.get("evidence_tags"))
    exp_tags = _normalize_set(ground_truth["evidence_tags"])
    score += 0.30 * _f1(sub_tags, exp_tags)

    # Recommendation (0.20)
    if _normalize(submitted.get("recommendation", "")) == _normalize(ground_truth["recommendation"]):
        score += 0.20

    return round(min(score, 1.0), 4)


def grade_test_triage(
    classifications: dict[str, dict],
    failed_tests: list[dict],
) -> float:
    if not failed_tests:
        return 0.0
    total = 0.0
    for test in failed_tests:
        test_id = test["test_id"]
        if test_id in classifications:
            total += grade_test_classification(classifications[test_id], test)
    return round(total / len(failed_tests), 4)


# ── Task 3: Multi-Service Outage RCA ──

def grade_outage_rca(submitted: dict, ground_truth: dict) -> float:
    score = 0.0

    # Root cause service (0.30) — exact match
    if _normalize(submitted.get("root_cause_service", "")) == _normalize(ground_truth["root_cause_service"]):
        score += 0.30

    # Failure chain (0.30) — precision-aware LCS
    sub_chain = submitted.get("failure_chain", [])
    if isinstance(sub_chain, str):
        sub_chain = [s.strip() for s in sub_chain.split(",") if s.strip()]
    score += 0.30 * _ordered_lcs_score(sub_chain, ground_truth["failure_chain"])

    # Remediation step IDs: set F1 (0.25) + ordering (0.15)
    sub_steps = submitted.get("remediation_step_ids", [])
    if isinstance(sub_steps, str):
        sub_steps = [s.strip() for s in sub_steps.split(",") if s.strip()]
    canonical = ground_truth.get("remediation_steps_canonical", [])
    exp_steps = [s["id"] for s in canonical]
    score += 0.25 * _f1(_normalize_set(sub_steps), _normalize_set(exp_steps))
    score += 0.15 * _ordered_lcs_score(sub_steps, exp_steps)

    return round(min(score, 1.0), 4)
