"""Unit tests for the structured graders in server/rewards.py.

Each grader gets three fixtures:
- A "perfect" submission that scores >= 0.95
- A "half-right" submission that scores in (0.4, 0.7)
- A "wrong" submission that scores <= 0.2

These pin the grader's behavior so future edits to weights or vocab can't
silently shift baseline scores.
"""

from __future__ import annotations

from server.rewards import (
    _f1,
    _normalize,
    _normalize_set,
    _ordered_lcs_score,
    grade_log_diagnosis,
    grade_outage_rca,
    grade_test_classification,
    grade_test_triage,
)


# ── Helper primitives ──

def test_normalize_strips_case_and_separators():
    assert _normalize("  Database-Connection_Pool ") == "database_connection_pool"
    assert _normalize("") == ""
    assert _normalize(None) == ""  # type: ignore[arg-type]


def test_normalize_set_handles_str_and_list():
    assert _normalize_set("a, b ,c") == {"a", "b", "c"}
    assert _normalize_set(["A", "b", "B"]) == {"a", "b"}
    assert _normalize_set(None) == set()
    assert _normalize_set([]) == set()


def test_f1_perfect_and_zero():
    assert _f1({"a", "b"}, {"a", "b"}) == 1.0
    assert _f1(set(), {"a"}) == 0.0
    assert _f1({"a"}, set()) == 0.0
    assert _f1({"x"}, {"a"}) == 0.0


def test_f1_penalizes_over_submission():
    # Recall=1.0 but precision=0.5 -> F1 = 0.667
    score = _f1({"a", "b", "c", "d"}, {"a", "b"})
    assert 0.66 < score < 0.67


def test_ordered_lcs_penalizes_padding():
    # Perfect order -> 1.0
    assert _ordered_lcs_score(["a", "b", "c"], ["a", "b", "c"]) == 1.0
    # Padding cuts the score
    score = _ordered_lcs_score(["a", "b", "c", "x", "y", "z"], ["a", "b", "c"])
    assert score == 0.5  # lcs=3, max(6,3)=6
    # Reversed -> low
    assert _ordered_lcs_score(["c", "b", "a"], ["a", "b", "c"]) < 0.5


# ── Task 1: log_diagnosis ──

LOG_GROUND_TRUTH = {
    "incident_type": "database_connection_pool_exhaustion",
    "severity": "P2",
    "affected_services": ["user-service", "auth-service", "api-gateway"],
    "root_cause_tags": ["connection_pool_exhausted", "max_connections_reached", "postgres"],
}


def test_log_diagnosis_perfect():
    submission = {
        "incident_type": "database_connection_pool_exhaustion",
        "severity": "P2",
        "affected_services": ["user-service", "auth-service", "api-gateway"],
        "root_cause_tags": ["connection_pool_exhausted", "max_connections_reached", "postgres"],
    }
    assert grade_log_diagnosis(submission, LOG_GROUND_TRUTH) >= 0.95


def test_log_diagnosis_alias_match_still_credits_incident():
    submission = {
        "incident_type": "db_pool_exhaustion",  # alias
        "severity": "P2",
        "affected_services": ["user-service", "auth-service", "api-gateway"],
        "root_cause_tags": ["connection_pool_exhausted", "max_connections_reached", "postgres"],
    }
    assert grade_log_diagnosis(submission, LOG_GROUND_TRUTH) >= 0.95


def test_log_diagnosis_half_right():
    submission = {
        "incident_type": "database_connection_pool_exhaustion",  # 0.35
        "severity": "P3",                                          # 0
        "affected_services": ["user-service"],                     # F1 -> 0.5, weighted 0.125
        "root_cause_tags": ["postgres"],                           # F1 -> 0.5, weighted 0.10
    }
    score = grade_log_diagnosis(submission, LOG_GROUND_TRUTH)
    assert 0.4 < score < 0.7


def test_log_diagnosis_wrong():
    submission = {
        "incident_type": "memory_leak",
        "severity": "P4",
        "affected_services": ["payment-service"],
        "root_cause_tags": ["dns_resolution_failed"],
    }
    assert grade_log_diagnosis(submission, LOG_GROUND_TRUTH) <= 0.2


def test_log_diagnosis_kitchen_sink_services_loses_precision():
    """Submitting every service in the cluster should NOT max out the
    affected_services component because F1 punishes low precision."""
    submission = {
        "incident_type": "database_connection_pool_exhaustion",
        "severity": "P2",
        "affected_services": [
            "user-service", "auth-service", "api-gateway", "payment-service",
            "product-service", "logging-service", "monitoring-service",
            "notification-service", "queue", "worker", "cache", "user-db",
        ],
        "root_cause_tags": ["connection_pool_exhausted", "max_connections_reached", "postgres"],
    }
    score = grade_log_diagnosis(submission, LOG_GROUND_TRUTH)
    # Without F1 this would be 1.0. With F1, services component is ~0.4 of its 0.25 weight.
    assert score < 0.90


# ── Task 2: test_triage ──

TEST_GROUND_TRUTH = {
    "test_id": "checkout_001",
    "category": "genuine_bug",
    "recommendation": "fix_code",
    "evidence_tags": ["recent_code_change", "regression", "calculation_error"],
}


def test_classification_perfect():
    submission = {
        "category": "genuine_bug",
        "recommendation": "fix_code",
        "evidence_tags": ["recent_code_change", "regression", "calculation_error"],
    }
    assert grade_test_classification(submission, TEST_GROUND_TRUTH) >= 0.95


def test_classification_half_right():
    submission = {
        "category": "genuine_bug",        # 0.50
        "recommendation": "rerun",        # 0
        "evidence_tags": ["regression"],  # F1 -> 0.5, weighted 0.15
    }
    score = grade_test_classification(submission, TEST_GROUND_TRUTH)
    assert 0.4 < score < 0.7


def test_classification_wrong():
    submission = {
        "category": "stale_test",
        "recommendation": "update_test",
        "evidence_tags": ["intermittent"],
    }
    assert grade_test_classification(submission, TEST_GROUND_TRUTH) <= 0.2


def test_test_triage_averages_per_test():
    failed_tests = [
        {**TEST_GROUND_TRUTH, "test_id": "t1"},
        {**TEST_GROUND_TRUTH, "test_id": "t2"},
    ]
    classifications = {
        "t1": {"category": "genuine_bug", "recommendation": "fix_code",
               "evidence_tags": ["recent_code_change", "regression", "calculation_error"]},
        # t2 not classified -> 0
    }
    # t1 = 1.0, t2 = 0.0 -> average 0.5
    assert grade_test_triage(classifications, failed_tests) == 0.5


# ── Task 3: outage_rca ──

RCA_GROUND_TRUTH = {
    "root_cause_service": "user-db",
    "failure_chain": ["user-db", "user-service", "auth-service", "api-gateway"],
    "remediation_steps_canonical": [
        {"id": "increase_max_connections_user_db", "label": "Increase max_connections"},
        {"id": "restart_user_service", "label": "Restart user-service"},
        {"id": "monitor_auth_service_recovery", "label": "Monitor auth-service"},
        {"id": "add_pgbouncer", "label": "Add PgBouncer"},
    ],
}


def test_rca_perfect():
    submission = {
        "root_cause_service": "user-db",
        "failure_chain": ["user-db", "user-service", "auth-service", "api-gateway"],
        "remediation_step_ids": [
            "increase_max_connections_user_db",
            "restart_user_service",
            "monitor_auth_service_recovery",
            "add_pgbouncer",
        ],
    }
    assert grade_outage_rca(submission, RCA_GROUND_TRUTH) >= 0.95


def test_rca_half_right():
    submission = {
        "root_cause_service": "user-db",                                # 0.30
        "failure_chain": ["user-db", "auth-service"],                   # LCS=2, max(2,4)=4 -> 0.5 * 0.30 = 0.15
        "remediation_step_ids": [
            "increase_max_connections_user_db",
            "restart_user_service",
        ],  # F1 = 2*1.0*0.5/(1.5)=0.667 * 0.25 = 0.167, LCS=2/max(2,4)=0.5 * 0.15 = 0.075
    }
    score = grade_outage_rca(submission, RCA_GROUND_TRUTH)
    # ~0.30 + 0.15 + 0.167 + 0.075 = ~0.69
    assert 0.55 < score < 0.75


def test_rca_wrong():
    submission = {
        "root_cause_service": "payment-service",
        "failure_chain": ["payment-service", "queue"],
        "remediation_step_ids": ["rollback_payment_service"],
    }
    assert grade_outage_rca(submission, RCA_GROUND_TRUTH) <= 0.2


def test_rca_padding_chain_does_not_max_score():
    submission = {
        "root_cause_service": "user-db",
        "failure_chain": [
            "user-db", "user-service", "auth-service", "api-gateway",
            "cache", "queue", "worker", "payment-service", "product-service", "search-service",
        ],
        "remediation_step_ids": [
            "increase_max_connections_user_db",
            "restart_user_service",
            "monitor_auth_service_recovery",
            "add_pgbouncer",
        ],
    }
    score = grade_outage_rca(submission, RCA_GROUND_TRUTH)
    # Without precision-aware LCS this would be 1.0; with it, chain component shrinks.
    assert score < 0.95
