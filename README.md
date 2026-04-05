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

**Scenarios:** Database connection pool exhaustion, memory leak, TLS certificate expiration, rate limiting, disk space exhaustion.

**Actions:**
- `get_services()` — list available services
- `get_logs(service, level, limit)` — retrieve log entries
- `search_logs(keyword)` — search across all logs
- `submit_diagnosis(incident_type, severity, affected_services, root_cause)` — submit answer

**Observations:** Log entries with timestamp, level, service, and message fields.

**Grading:** incident_type (35%), severity (20%), affected_services (25%), root_cause keywords (20%).

### Task 2: CI/CD Test Failure Triage (Medium)

The agent analyzes a completed E2E test suite run and classifies each of 5 failed tests.

**Categories:** `genuine_bug`, `flaky_test`, `environment_issue`, `stale_test`

**Actions:**
- `get_test_summary()` — pass/fail counts and failed test IDs
- `get_test_details(test_id)` — error output, stack traces, console logs, DOM snapshots
- `get_test_history(test_id, num_runs)` — pass/fail history across CI runs
- `get_source_code(file_path)` — view app or test source code
- `get_recent_changes()` — recent git commits and diffs
- `submit_classification(test_id, category, evidence, recommendation)` — classify a test

**Observations:** Test results, error messages, historical pass/fail data, source code, and git diffs.

**Grading:** Per-test average of category (50%), evidence quality (30%), recommendation (20%).

### Task 3: Multi-Service Outage RCA (Hard)

The agent investigates a cascading outage across a microservice architecture (14 services) to find the root cause and propose remediation.

**Actions:**
- `get_service_status()` — health of all services
- `get_service_metrics(service, metric)` — CPU, memory, latency, error_rate, throughput, connections
- `get_service_logs(service, level, limit)` — service logs
- `get_service_config(service)` — configuration and versions
- `get_dependency_graph()` — service dependency map
- `trace_request(trace_id)` — distributed traces
- `get_alert_history()` — alerts and available trace IDs
- `submit_report(root_cause_service, root_cause_description, failure_chain, remediation_steps)` — submit report

**Observations:** Service statuses, metrics, logs, configs, dependency graph, distributed traces, and alerts.

**Grading:** root_cause_service (25%), description (20%), failure_chain ordering (25%), remediation (20%), remediation ordering (10%).

## Reward Function

Each task provides **incremental rewards** during investigation:
- Positive rewards for useful actions (querying relevant services, checking test history, tracing failures)
- Penalties for repeated identical tool calls (-0.02) and excessive steps (-0.01/step past threshold)
- Final grading score (0.0–1.0) added on submission

This provides meaningful feedback throughout the trajectory, not just at the end.

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

Scores vary by model. Larger models with strong reasoning capabilities perform better on the harder tasks.

## Output Format

The inference script emits structured logs:

```
[START] task=log_diagnosis env=devops_triage model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=get_services({}) reward=0.00 done=false error=null
[STEP] step=2 action=get_logs({"service":"user-service","level":"ERROR"}) reward=0.02 done=false error=null
...
[END] success=true steps=8 score=0.75 rewards=0.00,0.02,0.01,...
```
