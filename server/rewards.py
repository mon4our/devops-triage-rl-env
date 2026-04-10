"""Reward computation for all 3 DevOps Triage tasks."""

from __future__ import annotations

import re


def _normalize(s: str) -> str:
    return s.lower().strip().replace("-", "_").replace(" ", "_")


def _keyword_coverage(text: str, keywords: list[str]) -> float:
    """Score how many keywords appear in text using word-boundary matching."""
    if not keywords:
        return 0.0
    text_lower = text.lower()
    hits = 0
    for kw in keywords:
        kw_lower = kw.lower()
        # Use leading \b to prevent matching inside other words
        # (e.g. "pool" won't match "carpool") while still allowing
        # prefix keywords like "throttl" to match "throttling".
        pattern = r'\b' + re.escape(kw_lower)
        if re.search(pattern, text_lower):
            hits += 1
    return min(hits / len(keywords), 1.0)


# ── Task 1: Log Anomaly Diagnosis ──

INCIDENT_TYPE_ALIASES = {
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


def _match_incident_type(submitted: str, expected: str) -> bool:
    norm = _normalize(submitted)
    if norm == _normalize(expected):
        return True
    aliases = INCIDENT_TYPE_ALIASES.get(_normalize(expected), [])
    return norm in [_normalize(a) for a in aliases]


def grade_log_diagnosis(
    submitted: dict,
    ground_truth: dict,
) -> float:
    score = 0.0

    # Incident type (0.35)
    if _match_incident_type(submitted.get("incident_type", ""), ground_truth["incident_type"]):
        score += 0.35

    # Severity (0.20)
    if _normalize(submitted.get("severity", "")) == _normalize(ground_truth["severity"]):
        score += 0.20

    # Affected services (0.25 — partial credit)
    submitted_services = {
        _normalize(s.strip())
        for s in submitted.get("affected_services", "").split(",")
        if s.strip()
    }
    expected_services = {_normalize(s) for s in ground_truth["affected_services"]}
    if expected_services:
        overlap = len(submitted_services & expected_services)
        score += 0.25 * overlap / len(expected_services)

    # Root cause keywords (0.20)
    score += 0.20 * _keyword_coverage(
        submitted.get("root_cause", ""),
        ground_truth["root_cause_keywords"],
    )

    return round(min(score, 1.0), 4)


# ── Task 2: CI/CD Test Failure Triage ──

VALID_CATEGORIES = {"genuine_bug", "flaky_test", "environment_issue", "stale_test"}
VALID_RECOMMENDATIONS = {"fix_code", "rerun", "update_test", "check_infra"}


def grade_test_classification(
    submitted: dict,
    ground_truth: dict,
) -> float:
    score = 0.0

    # Category (0.50)
    if _normalize(submitted.get("category", "")) == _normalize(ground_truth["category"]):
        score += 0.50

    # Evidence keywords (0.30)
    score += 0.30 * _keyword_coverage(
        submitted.get("evidence", ""),
        ground_truth["evidence_keywords"],
    )

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
        # Missing classifications score 0

    return round(total / len(failed_tests), 4)


# ── Task 3: Multi-Service Outage RCA ──

def _chain_score(submitted_chain: list[str], expected_chain: list[str]) -> float:
    """Score for failure chain: reward matching elements in correct order."""
    if not expected_chain:
        return 0.0

    sub = [_normalize(s) for s in submitted_chain]
    exp = [_normalize(s) for s in expected_chain]

    # Longest common subsequence
    m, n = len(sub), len(exp)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if sub[i - 1] == exp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs_len = dp[m][n]
    return lcs_len / len(exp)


def _remediation_score(submitted_steps: list[str], remediation_keywords: list[list[str]]) -> float:
    """Score remediation: each step gets partial credit for keyword matches."""
    if not remediation_keywords:
        return 0.0

    step_scores = []
    for expected_kws in remediation_keywords:
        best = 0.0
        for step in submitted_steps:
            coverage = _keyword_coverage(step, expected_kws)
            best = max(best, coverage)
        step_scores.append(best)

    return sum(step_scores) / len(step_scores) if step_scores else 0.0


def _remediation_order_score(submitted_steps: list[str], remediation_keywords: list[list[str]]) -> float:
    """Score for ordering: are remediation steps in the correct sequence?"""
    if len(remediation_keywords) < 2 or len(submitted_steps) < 2:
        return 0.0

    # Map each submitted step to its best-matching expected step index
    matched_indices = []
    for step in submitted_steps:
        best_idx = -1
        best_score = 0.0
        for idx, expected_kws in enumerate(remediation_keywords):
            coverage = _keyword_coverage(step, expected_kws)
            if coverage > best_score:
                best_score = coverage
                best_idx = idx
        if best_idx >= 0 and best_score > 0.3:
            matched_indices.append(best_idx)

    if len(matched_indices) < 2:
        return 0.0

    # Count concordant pairs
    concordant = 0
    total_pairs = 0
    for i in range(len(matched_indices)):
        for j in range(i + 1, len(matched_indices)):
            total_pairs += 1
            if matched_indices[i] < matched_indices[j]:
                concordant += 1

    return concordant / total_pairs if total_pairs > 0 else 0.0


def grade_outage_rca(
    submitted: dict,
    ground_truth: dict,
) -> float:
    score = 0.0

    # Root cause service (0.25)
    if _normalize(submitted.get("root_cause_service", "")) == _normalize(ground_truth["root_cause_service"]):
        score += 0.25

    # Root cause description (0.20)
    score += 0.20 * _keyword_coverage(
        submitted.get("root_cause_description", ""),
        ground_truth["root_cause_description_keywords"],
    )

    # Failure chain (0.25)
    submitted_chain = [
        s.strip()
        for s in submitted.get("failure_chain", "").split(",")
        if s.strip()
    ]
    score += 0.25 * _chain_score(submitted_chain, ground_truth["failure_chain"])

    # Remediation completeness (0.20)
    submitted_steps = [
        s.strip()
        for s in submitted.get("remediation_steps", "").split("\n")
        if s.strip()
    ]
    score += 0.20 * _remediation_score(submitted_steps, ground_truth["remediation_keywords"])

    # Remediation ordering (0.10)
    score += 0.10 * _remediation_order_score(submitted_steps, ground_truth["remediation_keywords"])

    return round(min(score, 1.0), 4)
