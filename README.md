---
title: DevOps Triage
emoji: 🔧
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 8000
---

# DevOps Triage — OpenEnv Environment

An OpenEnv-compliant reinforcement learning environment that simulates real-world DevOps tasks. Agents diagnose production incidents by analyzing logs, triaging test failures, and performing root cause analysis on multi-service outages.

## Motivation

DevOps tasks like incident response, test triage, and outage investigation are performed daily by SREs and developers. These tasks require pattern recognition, structured reasoning, and domain knowledge — making them ideal benchmarks for evaluating AI agents. Unlike toy problems, the scenarios use realistic log formats, error messages, and service architectures.

## Tasks

| Task | Difficulty | Description | Max Steps |
|------|-----------|-------------|-----------|
| `log_diagnosis` | Easy | Diagnose a production incident from service logs | 25 |
| `test_triage` | Medium | Classify CI/CD test failures (bug, flaky, env issue, stale) | 35 |
| `outage_rca` | Hard | Root cause analysis across a microservice architecture | 40 |

### Task 1: Log Anomaly Diagnosis (Easy)

The agent queries production logs from a web service cluster to identify what incident is occurring.

**Scenarios:** Database connection pool exhaustion, memory leak, TLS certificate expiration, rate limiting, disk space exhaustion, DNS resolution failure, message queue consumer lag, network timeout, database deadlock, cache poisoning.

**Actions:**
- `get_services()` — list available services
- `get_logs(service, level, limit)` — retrieve log entries
- `search_logs(keyword)` — search across all logs
- `get_runbook()` — generic incident response runbook (does NOT enumerate the incident-type vocabulary)
- `submit_diagnosis(incident_type, severity, affected_services, root_cause_tags)` — structured submission

**Observations:** Log entries with timestamp, level, service, and message fields.

**Grading:** `incident_type` enum (35%), `severity` enum (20%), `affected_services` F1 (25%), `root_cause_tags` F1 over the closed `ROOT_CAUSE_TAGS` vocabulary (20%). Kitchen-sinking the sets tanks the score because F1 is precision-aware.

### Task 2: CI/CD Test Failure Triage (Medium)

The agent analyzes a completed E2E test suite run and classifies each of 5 failed tests.

**Categories:** `genuine_bug`, `flaky_test`, `environment_issue`, `stale_test`

**Actions:**
- `get_test_summary()` — pass/fail counts and failed test IDs
- `get_test_details(test_id)` — error output, stack traces, console logs, DOM snapshots
- `get_test_history(test_id, num_runs)` — pass/fail history across CI runs
- `get_source_code(file_path)` — view app or test source code
- `get_recent_changes()` — recent git commits and diffs
- `get_ci_config()` — CI/CD pipeline configuration (runner, timeouts, environment)
- `submit_classification(test_id, category, recommendation, evidence_tags)` — structured classification per failed test (submissions for unknown `test_id` are rejected)

**Observations:** Test results, error messages, historical pass/fail data, source code, and git diffs.

**Grading:** Per-test average of `category` enum (50%), `evidence_tags` F1 over the closed `EVIDENCE_TAGS` vocabulary (30%), `recommendation` enum (20%).

### Task 3: Multi-Service Outage RCA (Hard)

The agent investigates a cascading outage across a microservice architecture (14 services) to find the root cause and propose remediation.

**Actions:**
- `get_service_status()` — health of all services
- `get_service_metrics(service, metric)` — CPU, memory, latency, error_rate, throughput, connections
- `get_service_logs(service, level, limit)` — service logs
- `get_service_config(service)` — configuration and versions
- `get_dependency_graph()` — service dependency map
- `trace_request(trace_id)` — distributed traces (trace IDs are embedded in alert messages; there is no dump tool)
- `get_alert_history()` — recent alerts with trace IDs embedded in the message field
- `get_deployment_history(service)` — recent deployments, optionally filtered by service
- `get_remediation_steps()` — canonical remediation step bank (list of `{id, label}`) for this scenario
- `submit_report(root_cause_service, failure_chain, remediation_step_ids)` — structured report; agents pick step IDs from the canonical bank instead of writing prose

**Observations:** Service statuses, metrics, logs, configs, dependency graph, distributed traces, and alerts.

**Grading:** `root_cause_service` exact (30%), `failure_chain` precision-aware LCS (30%), `remediation_step_ids` F1 (25%) + ordering LCS (15%). LCS divides by `max(len(sub), len(exp))` so padding the chain hurts.

## Reward Function

Each task provides **incremental rewards** during investigation, plus a final grading score on submission.

- Positive shaping for useful first-time actions (querying relevant services, checking test history, tracing known request IDs).
- Shaping is **capped at `MAX_SHAPING_REWARD = 0.15` per episode**. Once the shaping budget is exhausted, further exploration earns zero shaping. The cap is kept below the smallest non-zero submission component (severity = 0.20) so a pure-exploration agent can never beat even a minimal successful submission.
- Repeat-action penalty: `-0.05` per repeated action. The action key is hashed over semantically meaningful args only (e.g. `service` for `get_logs`), so bumping `limit=1 → limit=2` does not evade the penalty.
- Step penalty after a per-task threshold: `-0.03` per step. Over the horizon this strictly dominates the shaping cap, so "wander forever" is worse than "submit something".
- The final grading score (0.0–1.0) is added on submission via one of `submit_diagnosis`, `submit_classification`, or `submit_report`. Termination via max-step cutoff does not count as a submission; `inference.py` credits `score = 0` for episodes that never submit.

## Grading & determinism

All grading is **deterministic and structured-only**. Free-text fields were removed in favor of closed vocabularies because keyword-coverage scoring was trivially gamed by stuffing every plausible term into a blob.

Closed vocabularies live in `server/rewards.py`:
- `INCIDENT_TYPES` (10) + `INCIDENT_TYPE_ALIASES` for Task 1
- `SEVERITIES` (P1–P4) for Task 1
- `ROOT_CAUSE_TAGS` (~37 tags across 10 incident families) for Task 1
- `CATEGORIES` (`genuine_bug`, `flaky_test`, `environment_issue`, `stale_test`) for Task 2
- `RECOMMENDATIONS` (`fix_code`, `rerun`, `update_test`, `check_infra`) for Task 2
- `EVIDENCE_TAGS` (~28 tags) for Task 2
- A per-scenario remediation step bank (`remediation_steps_canonical`) for Task 3 — submissions pick step IDs from this list

Set components are F1-scored so over-submitting hurts as much as under-submitting. Ordered components use precision-aware LCS (`lcs / max(len(sub), len(exp))`) so padding the chain hurts.

### Train/test split

Each scenario is tagged with `split: "train" | "test"`. `reset(seed=..., split="test")` filters to the held-out pool and picks a scenario from a local `random.Random(seed)` — it never touches the global RNG, so fixed-seed runs are byte-reproducible. The default split is `"train"`.

Split sizes (7 train / 3 test per task, 21 train / 9 test total):
- Task 1 test pool: `upstream_api_timeout`, `database_deadlock`, `cache_poisoning`
- Task 2 test pool: `project_tracker`, `search_engine`, `authentication_flow`
- Task 3 test pool: `cache_thundering_herd`, `dns_outage`, `queue_backlog`

### Reproducing a baseline

```bash
uv run uvicorn server.app:app --port 8000 &
ENV_BASE_URL=http://localhost:8000 HF_TOKEN=$HF_TOKEN uv run python inference.py
```

`inference.py` runs all three tasks against the test split (via `reset(split="test")` in a future change, or by omitting split for now). Scores are reproducible across runs at a fixed model + seed. Run twice and diff the `[END]` lines — they should match exactly.

## Anti-gaming

The env was hardened across **two audit passes** — the initial pre-submission audit and a Phase 3 oracle-hunt pass that killed two closed-form solutions on Task 3. Every fix is pinned by an adversarial test in [`tests/test_exploits.py`](tests/test_exploits.py) so a regression re-opens a known hole *loudly* in CI. Run the suite with `uv run python -m pytest tests/ -q` (takes ~2 seconds).

- **Keyword stuffing** — F1 scoring + closed vocabularies. Pinned by `test_keyword_stuffing_*` and `test_kitchen_sink_services_component_capped`.
- **Answer-key oracles** — `get_runbook` no longer enumerates incident types; `search_logs("")` is rejected; `get_service_metrics` no longer falls back to healthy metrics for unknown services; `get_alert_history` no longer dumps trace IDs; `get_logs(limit=…)` is clamped to 50. Pinned by `test_get_runbook_does_not_leak_vocab`, `test_search_logs_rejects_empty_keyword`, `test_get_logs_clamps_limit`, `test_get_service_metrics_no_healthy_fallback`.
- **Scenario-ID leakage** — `reset()` no longer echoes `scenario_id` in observation metadata. Pinned by `test_scenario_id_not_in_reset_metadata`.
- **Args-noise repeat-penalty evasion** — the repeat key hashes only semantically meaningful args. Pinned by `test_args_noise_does_not_farm_shaping`.
- **Shaping-reward farming** — per-episode cap enforced in `_credit_shaping`. Pinned by `test_shaping_cap_enforced` and `test_shaping_cap_below_minimum_submission`.
- **"Never submit" loophole** — `inference.py` credits `score = 0` when no `submit_*` tool was called, and terminal max-step cutoffs are not miscounted as submissions. Pinned by `test_step_penalty_dwarfs_shaping_cap`.
- **Seed-dependent scenario selection** — local `Random(seed)`, never the global module RNG. Pinned by `test_seed_determinism_same_scenario`, `test_different_seeds_can_differ`, `test_train_test_split_disjoint`.
- **Cross-task submission leakage** — `submit_*` tools refuse to score when the active task is different. Pinned by `test_submit_tool_rejects_wrong_task`.
- **Remediation-bank oracle** — `get_remediation_steps()` now returns the canonical steps *plus plausible distractors*, shuffled deterministically per scenario. Blind-copying the bank drops the remediation component of the Task 3 score materially because F1 is precision-aware and the ordering LCS divides by max length. Pinned by `test_remediation_bank_superset_of_canonical` and `test_blind_bank_copy_is_bounded`.
- **Dependency-walk service-status oracle** — `service_statuses` now always contains red-herring non-healthy services that are *not* part of the real failure chain, so "walk the dep graph from the upstream-most unhealthy service" is no longer a closed-form solution. A real investigative policy can still rule out the red herrings via metrics/logs/traces. Pinned by `test_service_status_has_red_herring` and `test_naive_dep_walk_oracle_is_bounded`.

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Locally

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t devops-triage .
docker run -p 8000:8000 devops-triage
```

### Run Inference

```bash
export HF_TOKEN=your_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py
```

## Baseline Performance

| Task | Baseline Score |
|------|---------------|
| `log_diagnosis` | ~0.55–0.75 |
| `test_triage` | ~0.40–0.60 |
| `outage_rca` | ~0.30–0.50 |

Scores vary by model. Larger models with strong reasoning capabilities perform better on the harder tasks. These baselines were measured against the structured-submission grader described in the **Grading & determinism** section, not the earlier keyword-coverage grader.

## Future work

These are intentional non-goals for the hackathon submission and are documented for posterity:

- **Parametric scenario generator.** A seeded generator for Task 1/2 would make the train split essentially unbounded, which matters more for RL fine-tuning than for hackathon eval.
- **LLM-judge grading for prose remediation.** Dropped because keyword coverage was gameable and structured IDs are verifiable. Could be re-added if the vocabulary feels too restrictive.
- **Three-way train/val/test split.** Currently two-way; adding a val split matters for hyperparameter tuning loops.
- **Hermetic eval-mode flag** that disables shaping entirely so pure-eval scores equal pure submission reward.

## Output Format

The inference script emits structured logs:

```
[START] task=log_diagnosis env=devops_triage model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=get_services({}) reward=0.00 done=false error=null
[STEP] step=2 action=get_logs({"service":"user-service","level":"ERROR"}) reward=0.02 done=false error=null
...
[END] success=true steps=8 score=0.75 rewards=0.00,0.02,0.01,...
```
