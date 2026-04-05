# DevOps Triage — OpenEnv Environment: Technical Document

---

## 1. Project Overview

**DevOps Triage** is a reinforcement learning environment built on the [OpenEnv](https://github.com/meta-pytorch/OpenEnv) framework for the Meta PyTorch OpenEnv Hackathon. It simulates three real-world DevOps tasks that Site Reliability Engineers (SREs), QA engineers, and developers perform daily:

1. **Log Anomaly Diagnosis** (Easy) — Diagnose a production incident from service logs
2. **CI/CD Test Failure Triage** (Medium) — Classify failed E2E tests as bugs, flaky tests, environment issues, or stale tests
3. **Multi-Service Outage Root Cause Analysis** (Hard) — Investigate a cascading failure across a microservice architecture

### Why DevOps?

- **Real-world tasks, not toy problems.** These are genuine daily activities, not games or synthetic puzzles.
- **Deterministic grading.** Each task has an objectively correct answer: the root cause IS X, the test IS flaky, the failure chain IS A→B→C. This enables reproducible, deterministic scoring.
- **Natural difficulty ladder.** Reading logs (easy) → triaging tests with multiple evidence types (medium) → multi-service RCA with dependency graphs and distributed traces (hard).
- **Underrepresented in AI benchmarks.** Existing OpenEnv environments cover coding, finance, calendar, and games. DevOps intelligence is a novel and valuable domain.

---

## 2. Architecture

### 2.1 OpenEnv Interface

The environment implements the standard OpenEnv contract:

```
reset(task, scenario_id) → Observation
step(action)             → Observation (with reward, done)
state                    → DevOpsState
```

All agent interactions happen through **MCP (Model Context Protocol) tools** — the agent discovers tools via `ListToolsAction`, then calls them via `CallToolAction`. This mirrors how real LLM agents interact with tool-use APIs.

### 2.2 Client-Server Model

```
┌─────────────────┐         WebSocket / HTTP         ┌─────────────────────┐
│   inference.py   │  ◄──────────────────────────►   │  FastAPI Server      │
│   (LLM Agent)    │                                  │  (DevOpsEnvironment) │
│                  │    reset(task="log_diagnosis")    │                     │
│  OpenAI Client   │    step(CallToolAction(...))      │  18 MCP Tools       │
│  DevOpsTriageEnv │    state()                        │  Reward Computation  │
└─────────────────┘                                   │  Scenario Data       │
                                                      └─────────────────────┘
```

- **Server** (`server/app.py`): FastAPI application created via `openenv.core.env_server.http_server.create_app()`. Exposes `/reset`, `/step`, `/state`, `/health`, `/ws`, and `/mcp` endpoints.
- **Client** (`client.py`): `DevOpsTriageEnv` subclasses `MCPToolClient` from `openenv-core`. Provides `reset()`, `step()`, `list_tools()`, and `call_tool()` methods over WebSocket.
- **Inference** (`inference.py`): Standalone script that uses the OpenAI client to get LLM decisions, parses them into tool calls, and executes them against the environment.

### 2.3 Technology Stack

| Component | Technology |
|-----------|-----------|
| Framework | OpenEnv (`openenv-core` v0.2.3) |
| Server | FastAPI + Uvicorn |
| MCP Tools | FastMCP |
| Models | Pydantic v2 |
| LLM Client | OpenAI Python SDK |
| Container | Docker (Python 3.11-slim) |
| Deployment | HuggingFace Spaces |

---

## 3. Project Structure

```
openenv/
├── openenv.yaml                     # OpenEnv metadata (name, runtime, port)
├── pyproject.toml                   # Python project config with server entry point
├── requirements.txt                 # pip dependencies
├── uv.lock                         # Dependency lock file
├── Dockerfile                      # Container definition
├── inference.py                    # Baseline LLM inference script (root, mandatory)
├── README.md                       # User-facing documentation
├── DOCUMENT.md                     # This document
├── models.py                       # Pydantic DevOpsState model
├── client.py                       # MCPToolClient subclass
├── __init__.py                     # Package init
└── server/
    ├── __init__.py
    ├── app.py                      # FastAPI app creation via create_app()
    ├── devops_environment.py       # MCPEnvironment subclass — core logic (530 lines)
    ├── rewards.py                  # Grading functions for all 3 tasks (234 lines)
    └── data/
        ├── __init__.py
        ├── task1_log_diagnosis.py  # 5 synthetic log incident scenarios
        ├── task2_test_triage.py    # 3 synthetic test failure scenarios
        └── task3_outage_rca.py     # 3 synthetic outage scenarios
```

### File-by-File Walkthrough

#### `openenv.yaml`
OpenEnv metadata. Declares the environment name (`devops_triage`), runtime (`fastapi`), app entry point (`server.app:app`), and port (`8000`).

#### `models.py`
Defines `DevOpsState`, a Pydantic model extending `openenv.core.env_server.types.State`. Adds `task`, `scenario_id`, and `accumulated_reward` fields beyond the inherited `episode_id` and `step_count`.

#### `client.py`
`DevOpsTriageEnv` subclasses `MCPToolClient` with a pass-through body. The parent class provides all WebSocket communication, tool discovery, and tool calling. Usage:
```python
async with DevOpsTriageEnv(base_url="http://localhost:8000") as env:
    await env.reset(task="log_diagnosis")
    result = await env.call_tool("get_services")
```

#### `server/app.py`
Creates the FastAPI application via `create_app()` from `openenv-core`. Includes `DevOpsCallToolAction`, a subclass of `CallToolAction` with a Pydantic validator that auto-parses JSON string arguments from the web UI.

#### `server/devops_environment.py`
The core of the project. `DevOpsEnvironment` subclasses `MCPEnvironment` and:
1. Registers **18 MCP tools** via `FastMCP` in `_register_tools()`
2. Implements `reset()` to select task + scenario and return initial observation
3. Implements `step()` / `step_async()` to execute tools, compute incremental rewards, detect submission, and compute final grading
4. Tracks investigation state (queried services, viewed files, action history) for reward shaping

#### `server/rewards.py`
Pure functions for grading. No side effects. Three main entry points:
- `grade_log_diagnosis(submitted, ground_truth) → float`
- `grade_test_triage(classifications, failed_tests) → float`
- `grade_outage_rca(submitted, ground_truth) → float`

Also includes utilities: `_normalize()`, `_keyword_coverage()`, `_chain_score()` (LCS-based), `_remediation_score()`, `_remediation_order_score()` (concordant pairs).

#### `server/data/task1_log_diagnosis.py`
5 scenarios as Python dicts. Each contains services with realistic log entries, ground truth diagnosis, and lists of relevant services/search terms for incremental rewards.

#### `server/data/task2_test_triage.py`
3 scenarios. Each contains a test suite summary, 5 failed tests with full artifacts (error output, stack traces, console logs, DOM snapshots, pass/fail history), recent git commits with diffs, and source code files.

#### `server/data/task3_outage_rca.py`
3 scenarios plus a shared 14-service topology. Each scenario contains service statuses, metrics, logs, configs, distributed traces, and alerts.

#### `inference.py`
Runs all 3 tasks sequentially against the environment using the OpenAI client. For each task, it loops: observation → LLM prompt → parse tool call → execute → log. Emits `[START]`/`[STEP]`/`[END]` lines to stdout per the hackathon spec.

#### `Dockerfile`
Based on `python:3.11-slim`. Installs `curl` for health checks, `pip install` dependencies, copies code, sets `PYTHONPATH=/app`, and runs Uvicorn on port 8000. Includes a `HEALTHCHECK` directive.

---

## 4. Task Details

### 4.1 Task 1: Log Anomaly Diagnosis (Easy)

**Objective:** The agent receives access to production logs from a web service cluster (4-5 services). One predefined incident is occurring. The agent must query logs, identify the anomaly, and submit a structured diagnosis.

#### Scenarios (5 total)

| ID | Incident | Severity | Affected Services |
|----|----------|----------|-------------------|
| `db_pool_exhaustion` | Database connection pool exhausted (50/50 connections) | P2 | user-service, auth-service, api-gateway |
| `memory_leak` | Java heap OOM in worker-service (ReportCache leak) | P2 | worker-service, api-gateway |
| `cert_expiry` | TLS certificate expired on auth-service | P1 | auth-service, api-gateway, user-service |
| `rate_limiting` | Bot client consuming 60% of request capacity | P3 | api-gateway, product-service |
| `disk_full` | Disk at 100% on logging-service, dropping events | P2 | logging-service, monitoring-service, api-gateway |

#### Available Tools (4)

| Tool | Arguments | Returns |
|------|-----------|---------|
| `get_services()` | none | `list[str]` — service names |
| `get_logs(service, level, limit)` | `service: str`, `level: str = "ALL"`, `limit: int = 20` | `list[dict]` — log entries with timestamp, level, message |
| `search_logs(keyword)` | `keyword: str` | `list[dict]` — matching entries across all services (max 30) |
| `submit_diagnosis(incident_type, severity, affected_services, root_cause)` | `incident_type: str`, `severity: str` (P1-P4), `affected_services: str` (comma-sep), `root_cause: str` | `dict` with score and done=True |

#### Log Entry Format
```json
{
  "timestamp": "2026-04-04T14:02:00Z",
  "level": "ERROR",
  "service": "user-service",
  "message": "Failed to acquire database connection from pool: pool exhausted (active=50, max=50)"
}
```

Each scenario contains 5-10 log entries per service. Affected services have a mix of normal INFO logs and anomalous ERROR/WARN logs. Unaffected services have only routine INFO logs, creating realistic noise.

#### Data Design Rationale
Logs are crafted to have a clear gradient of specificity:
- **api-gateway**: Sees symptoms (upstream 503s, latency spikes) but not the root cause
- **Affected services**: Show specific error messages pointing to the root cause
- **Unaffected services**: Normal operations, serving as distractors

This means a lazy agent that only checks one service will get partial credit, while a thorough agent that traces errors upstream will score higher.

---

### 4.2 Task 2: CI/CD Test Failure Triage (Medium)

**Objective:** A CI pipeline has run an E2E test suite. Several tests failed. The agent must analyze each failure using test output, history, source code, and recent changes, then classify it into one of four categories.

#### Classification Categories

| Category | Description | Signal | Recommendation |
|----------|-------------|--------|----------------|
| `genuine_bug` | Application code is actually broken | Was passing, now consistently fails; recent commit introduced bug | `fix_code` |
| `flaky_test` | Intermittent failure, non-deterministic | Pass/fail history is inconsistent (e.g., TFTFTF); timing-related errors | `rerun` |
| `environment_issue` | External dependency unavailable | ECONNREFUSED to staging service; infrastructure maintenance | `check_infra` |
| `stale_test` | Test assertion outdated, doesn't match current requirements | Recent product decision changed behavior; test broke at that commit | `update_test` |

#### Scenarios (3 total)

| ID | App | Failed Tests |
|----|-----|-------------|
| `ecommerce_checkout` | E-commerce checkout flow (Playwright) | Discount calculation bug, payment redirect flaky, inventory API down, shipping address format stale, pagination bug |
| `user_dashboard` | SaaS dashboard (Cypress) | SSO provider down, chart render flaky, RBAC permission bug, CSV export format stale, notification context bug |
| `social_feed` | Social media app (Selenium) | Image upload preview bug, infinite scroll flaky, WebSocket chat down, bio limit stale, hashtag parser bug |

Each scenario has exactly **5 failed tests** — typically 2 genuine bugs, 1 flaky, 1 environment issue, and 1 stale test.

#### Available Tools (6)

| Tool | Arguments | Returns |
|------|-----------|---------|
| `get_test_summary()` | none | `dict` with total/passed/failed/skipped counts + failed_test_ids |
| `get_test_details(test_id)` | `test_id: str` | `dict` with error_output, stack_trace, console_logs, dom_snapshot |
| `get_test_history(test_id, num_runs)` | `test_id: str`, `num_runs: int = 10` | `dict` with history (bool list), pass_rate, total_runs |
| `get_source_code(file_path)` | `file_path: str` | `str` — file contents (or error with available files) |
| `get_recent_changes()` | none | `list[dict]` — commits with author, message, files_changed, diff |
| `submit_classification(test_id, category, evidence, recommendation)` | `test_id: str`, `category: str`, `evidence: str`, `recommendation: str` | `dict` with remaining count; done=True when all 5 classified |

#### Evidence Artifacts
Each failed test includes realistic artifacts:
- **Error output**: Actual assertion failures (`Expected $45.00, got $50.00`)
- **Stack traces**: Realistic call stacks with file paths and line numbers
- **Console logs**: Application logs captured during test execution
- **DOM snapshots**: HTML state at the time of failure
- **History**: Boolean array of pass/fail over last 10 CI runs (key signal for flakiness)
- **Source code**: Both application code and test code with comments showing bugs
- **Git diffs**: Realistic commit diffs that introduced the issues

#### Data Design Rationale
The scenarios are designed so that:
- **Genuine bugs** have a clear regression point: history was all-pass then suddenly fails, and a recent commit diff shows the bug
- **Flaky tests** have inconsistent history (TFTFTF pattern) and timing-related errors
- **Environment issues** show ECONNREFUSED to external services with maintenance notes in console logs
- **Stale tests** have a clear transition point in history and reference a JIRA ticket explaining the intentional change

The agent must cross-reference multiple evidence types (history pattern + error message + recent changes) to classify correctly. Just reading the error is insufficient.

---

### 4.3 Task 3: Multi-Service Outage Root Cause Analysis (Hard)

**Objective:** A cascading production outage is affecting users. The agent must investigate health, metrics, logs, configs, dependency graphs, and distributed traces across a 14-service microservice architecture to identify the root cause, trace the failure cascade, and propose an ordered remediation plan.

#### Service Topology (14 services)

```
api-gateway ──► auth-service ──► user-db
            │               └──► cache
            ├──► user-service ──► user-db
            └──► product-service ──► product-db
                                └──► search-service ──► product-db

payment-service ──► payment-gateway
                └──► queue ◄── worker ──► notification-service ──► email-provider
```

#### Scenarios (3 total)

| ID | Root Cause | Failure Chain | Key Signal |
|----|-----------|---------------|------------|
| `db_connection_limit` | user-db max_connections=100 reached | user-db → user-service → auth-service → api-gateway | Config shows max_connections=100; metrics show connections=100/100 |
| `bad_deploy` | payment-service v2.4.0 broke JSON serialization | payment-service → api-gateway, worker | Config shows version=2.4.0, deployed 15min ago; logs show TypeError on amount field |
| `cert_expiry_cascade` | Redis (cache) TLS certificate expired | cache → auth-service → api-gateway | Config shows tls_cert_expiry in the past; logs show SSL_ERROR_EXPIRED_CERT |

#### Available Tools (8)

| Tool | Arguments | Returns |
|------|-----------|---------|
| `get_service_status()` | none | `dict` — all 14 services mapped to healthy/degraded/unhealthy |
| `get_service_metrics(service, metric)` | `service: str`, `metric: str` | `dict` with service, metric, value |
| `get_service_logs(service, level, limit)` | `service: str`, `level: str = "ALL"`, `limit: int = 20` | `list[dict]` — log entries |
| `get_service_config(service)` | `service: str` | `dict` — version, replicas, limits, TLS settings, etc. |
| `get_dependency_graph()` | none | `dict` — full SERVICE_TOPOLOGY adjacency list |
| `trace_request(trace_id)` | `trace_id: str` | `dict` with trace_id and spans (service, operation, duration, status, error) |
| `get_alert_history()` | none | `dict` with alerts list and available_trace_ids |
| `submit_report(root_cause_service, root_cause_description, failure_chain, remediation_steps)` | all `str`; failure_chain comma-sep, remediation newline-sep | `dict` with score and done=True |

#### Distributed Traces
Each scenario includes 2-3 traces:
- **Failure trace**: Shows a request flowing through the failing chain with errors propagating from root cause
- **Success trace**: Shows a request taking a path that avoids the failing services (proves the issue is isolated)
- **Additional failure trace**: Confirms the pattern

Example trace span:
```json
{
  "service": "user-db",
  "operation": "query",
  "duration_ms": 0,
  "status": "error",
  "error": "FATAL: too many connections (100/100)",
  "timestamp": "2026-04-04T14:02:31Z"
}
```

#### Data Design Rationale
The difficulty comes from:
1. **Scale**: 14 services, only 3-4 are affected. The agent must efficiently narrow down.
2. **Cascading failures**: Symptoms appear at the edge (api-gateway) but the root cause is deeper (user-db, cache). The agent must trace upstream.
3. **Multiple evidence types**: Status gives a quick overview, metrics quantify severity, logs explain what happened, configs reveal misconfigurations, traces show the actual failure path.
4. **Remediation ordering**: Steps must be in the right sequence (fix root cause first, then restart dependents, then monitor, then long-term fix).

---

## 5. Reward System

The environment provides two types of rewards:

### 5.1 Incremental Rewards (per step, during investigation)

These reward useful investigative actions and penalize waste. All are **first-time-only** — repeating the same query yields no bonus.

#### Task 1: Log Diagnosis

| Action | Reward | Condition |
|--------|--------|-----------|
| `get_logs` for a relevant service | +0.02 | Service is in scenario's `relevant_services` list |
| `search_logs` with a relevant keyword | +0.01 | Keyword matches any term in `relevant_search_terms` |
| Any step after step 15 | -0.01 | Discourages aimless exploration |
| Exact duplicate tool call | -0.02 | Same tool + same arguments as a previous step |

#### Task 2: Test Triage

| Action | Reward | Condition |
|--------|--------|-----------|
| `get_test_details` for a failed test | +0.03 | test_id is in the failed test list |
| `get_test_history` for any test | +0.05 | First time checking that test's history |
| `get_source_code` for a relevant file | +0.02 | File exists in scenario's `source_files` |
| Any step after step 20 | -0.01 | |
| Exact duplicate tool call | -0.02 | |

#### Task 3: Outage RCA

| Action | Reward | Condition |
|--------|--------|-----------|
| `get_service_status` (reveals degraded services) | +0.02 each | Per degraded/unhealthy service discovered |
| `get_service_metrics` for an affected service | +0.03 | Service has anomalous metrics in scenario |
| `trace_request` | +0.05 | First time viewing each trace |
| `get_service_logs` for root cause service | +0.04 | Service is the scenario's `root_cause_service` |
| `get_service_logs` for other affected service | +0.01 | Service status is not "healthy" |
| Any step after step 25 | -0.01 | |
| Exact duplicate tool call | -0.02 | |

### 5.2 Final Grading (on submission, 0.0–1.0)

#### Task 1: `grade_log_diagnosis`

| Component | Weight | Scoring |
|-----------|--------|---------|
| Incident type | 0.35 | Exact match (with aliases, e.g., "db_pool_exhaustion" = "connection_pool_exhaustion") |
| Severity | 0.20 | Exact match (P1/P2/P3/P4) |
| Affected services | 0.25 | Partial credit: `|submitted ∩ expected| / |expected|` |
| Root cause description | 0.20 | Keyword coverage: `min(hits / total_keywords, 1.0)` |

**Incident type aliases** are defined in `INCIDENT_TYPE_ALIASES` to accept reasonable variations (e.g., "memory_leak", "oom", "out_of_memory", "heap_exhaustion" all match).

#### Task 2: `grade_test_triage`

Per-test score (averaged across all 5 failed tests):

| Component | Weight | Scoring |
|-----------|--------|---------|
| Category | 0.50 | Exact match (genuine_bug / flaky_test / environment_issue / stale_test) |
| Evidence quality | 0.30 | Keyword coverage against `evidence_keywords` list |
| Recommendation | 0.20 | Exact match (fix_code / rerun / update_test / check_infra) |

`final_score = mean(per_test_scores)`. Missing classifications score 0.

#### Task 3: `grade_outage_rca`

| Component | Weight | Scoring |
|-----------|--------|---------|
| Root cause service | 0.25 | Exact match |
| Root cause description | 0.20 | Keyword coverage against `root_cause_description_keywords` |
| Failure chain | 0.25 | Longest Common Subsequence ratio: `LCS(submitted, expected) / len(expected)` |
| Remediation completeness | 0.20 | Each expected step matched to best submitted step by keyword coverage, averaged |
| Remediation ordering | 0.10 | Concordant pairs ratio (Kendall tau-like) over matched step indices |

**Failure chain scoring** uses LCS to give partial credit for correct ordering even if some services are missing or extra ones are included. For example, submitting `[user-db, auth-service, api-gateway]` when the expected chain is `[user-db, user-service, auth-service, api-gateway]` scores 3/4 = 0.75.

### 5.3 Reward Flow in a Step

```
step(action) is called
  │
  ├── MCPEnvironment executes the tool → returns observation
  │
  ├── _compute_step_reward() calculates incremental reward
  │     ├── Check if action is a duplicate → -0.02
  │     ├── Check if tool reveals useful info → +bonus
  │     └── Check if step count > threshold → -0.01
  │
  ├── If submission tool was called:
  │     └── Add final grading score to step reward
  │
  ├── accumulated_reward += step_reward
  │
  └── Return Observation(done, reward=step_reward, metadata)
```

---

## 6. State Management

### DevOpsState (Pydantic model)

```python
class DevOpsState(State):
    task: str = ""                    # "log_diagnosis" | "test_triage" | "outage_rca"
    scenario_id: str = ""            # e.g., "db_pool_exhaustion"
    accumulated_reward: float = 0.0  # Running total
    # Inherited: episode_id, step_count
```

### Internal Tracking (not exposed in state, reset on `reset()`)

| Field | Purpose |
|-------|---------|
| `_queried_services: set` | Which services have been queried with `get_logs` (Task 1) |
| `_search_terms_used: set` | Which keywords have been searched (Task 1) |
| `_tests_inspected: set` | Which test details have been viewed (Task 2) |
| `_tests_history_checked: set` | Which test histories have been viewed (Task 2) |
| `_source_files_viewed: set` | Which source files have been viewed (Task 2) |
| `_rca_services_checked: set` | Which degraded services were discovered (Task 3) |
| `_rca_metrics_checked: set` | Which service+metric combos were queried (Task 3) |
| `_rca_traces_viewed: set` | Which trace IDs have been viewed (Task 3) |
| `_rca_logs_viewed: set` | Which service logs have been viewed (Task 3) |
| `_action_history: list` | All previous `tool:args` keys for duplicate detection |
| `_test_classifications: dict` | Accumulated test classifications (Task 2 only) |
| `_final_score: float` | Grading result from submission |
| `_done: bool` | Episode completion flag |

---

## 7. Inference Script

### Environment Variables

| Variable | Default | Required | Purpose |
|----------|---------|----------|---------|
| `API_BASE_URL` | `https://router.huggingface.co/v1` | No | LLM API endpoint |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` | No | Model identifier |
| `HF_TOKEN` | (none) | **Yes** | HuggingFace / API key |
| `IMAGE_NAME` | (none) | No | Docker image for `from_docker_image()` |
| `ENV_BASE_URL` | `http://localhost:8000` | No | Fallback if no IMAGE_NAME |

### Execution Flow

```
main()
  ├── Initialize OpenAI client with API_BASE_URL and HF_TOKEN
  ├── Connect to environment (Docker image or base URL)
  ├── For each task in [log_diagnosis, test_triage, outage_rca]:
  │     ├── Print [START] line
  │     ├── env.reset(task=task_name)
  │     ├── Loop up to max_steps:
  │     │     ├── Format observation as prompt
  │     │     ├── Call LLM (OpenAI chat completion, temp=0.2, max_tokens=500)
  │     │     ├── Parse JSON tool call from response: {"tool": "...", "args": {...}}
  │     │     ├── Execute via env.call_tool(tool, **args)
  │     │     ├── Print [STEP] line
  │     │     └── Break if done
  │     ├── Compute final score
  │     └── Print [END] line
  └── Print [SUMMARY] with average score
```

### LLM Prompting Strategy

Each task has a dedicated system prompt that:
1. Assigns a persona (SRE, QA Engineer)
2. Lists all available tools with argument signatures
3. Provides a step-by-step strategy
4. Instructs the LLM to respond with `{"tool": "<name>", "args": {<arguments>}}`

The conversation history is maintained (last 10 exchanges) so the LLM can build on previous observations.

### Output Format

Per the hackathon spec:

```
[START] task=log_diagnosis env=devops_triage model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=get_services({}) reward=0.00 done=false error=null
[STEP] step=2 action=get_logs({"service":"user-service","level":"ERROR"}) reward=0.02 done=false error=null
[STEP] step=3 action=search_logs({"keyword":"pool exhausted"}) reward=0.01 done=false error=null
[STEP] step=4 action=submit_diagnosis({...}) reward=0.92 done=true error=null
[END] success=true steps=4 score=0.92 rewards=0.00,0.02,0.01,0.92
```

---

## 8. Deployment

### Local Development

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t devops-triage .
docker run -p 8000:8000 devops-triage
```

The Dockerfile:
- Base image: `python:3.11-slim` (small footprint for 2 vCPU / 8 GB RAM limit)
- Installs `curl` for health checks
- Copies code and dependencies
- Runs Uvicorn on port 8000
- Health check: `curl -f http://localhost:8000/health` every 30s

### HuggingFace Spaces

1. Create a new Space (SDK: Docker, tagged `openenv`)
2. Push this repo to the Space
3. Wait for build to complete and status to show "Running"
4. Verify: `curl -X POST https://your-space.hf.space/reset -H "Content-Type: application/json" -d '{}'`

### Resource Constraints

The environment is designed to fit within:
- **2 vCPU**: No CPU-intensive operations. All data is in-memory Python dicts.
- **8 GB RAM**: Scenario data totals ~500KB. FastAPI + Uvicorn use ~50MB. Well within limits.
- **20 min inference runtime**: Each task uses 25-40 LLM calls max. At ~1s per call, total is ~3-4 minutes for all 3 tasks.

---

## 9. OpenEnv Compliance Checklist

| Requirement | Status | Implementation |
|-------------|--------|---------------|
| Typed Observation, Action, Reward models (Pydantic) | Done | `DevOpsState` extends `State`; uses `CallToolAction`, `CallToolObservation` from openenv-core |
| `step(action) → (observation, reward, done, info)` | Done | `DevOpsEnvironment.step()` returns `Observation` with reward and done |
| `reset() → initial observation` | Done | `DevOpsEnvironment.reset(task=..., scenario_id=...)` |
| `state() → current state` | Done | `DevOpsEnvironment.state` property returns `DevOpsState` |
| `openenv.yaml` with metadata | Done | `spec_version: 1`, `name: devops_triage`, `type: space`, `runtime: fastapi` |
| Passes `openenv validate` | Done | Validated successfully |
| Minimum 3 tasks with agent graders | Done | `log_diagnosis`, `test_triage`, `outage_rca` with programmatic graders in `rewards.py` |
| Easy → medium → hard difficulty | Done | 4 tools / 5 scenarios → 6 tools / 15 tests → 8 tools / 14 services |
| Scores between 0.0 and 1.0 | Done | All grading functions return `round(min(score, 1.0), 4)` |
| Deterministic, reproducible grading | Done | Pure function grading, keyword matching, LCS for chains |
| Meaningful reward function (not just terminal) | Done | Incremental rewards at every step + final grading |
| Penalizes undesirable behaviors | Done | -0.02 for repeated calls, -0.01/step after threshold |
| Baseline inference script | Done | `inference.py` using OpenAI client |
| Reads `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` from env | Done | With defaults for API_BASE_URL and MODEL_NAME |
| `[START]`/`[STEP]`/`[END]` output format | Done | `log_start()`, `log_step()`, `log_end()` helpers |
| Working Dockerfile | Done | Builds and runs successfully |
| Deployable on HuggingFace Spaces | Done | Container-based, port 8000, health check included |

---

## 10. Verification Results

### Unit Tests (Grading Functions)

```
Task 1 perfect answer:                0.92  (4/5 keywords matched)
Task 1 wrong type, partial services:  0.28  (only severity + 1/3 services)
Task 2 good classification:           0.85  (correct category + recommendation, 3/6 evidence keywords)
Task 3 good RCA:                      0.93  (all components scored well)
```

### Integration Tests (Full Step Cycles)

```
Task 1 (log_diagnosis):
  Step 1 (list tools):              reward=0.00, done=false
  Step 2 (get_services):            reward=0.00, done=false
  Step 3 (get_logs user-service):   reward=0.02, done=false  ← relevant service bonus
  Step 4 (search_logs "pool"):      reward=0.01, done=false  ← relevant search term bonus
  Step 5 (submit_diagnosis):        reward=0.96, done=true   ← final grading
  Accumulated reward: 0.99

Task 2 (test_triage):
  get_test_summary:                 reward=0.00
  get_test_details (failed test):   reward=0.03  ← inspection bonus
  get_test_history (failed test):   reward=0.05  ← history bonus
  5x submit_classification:         done=true after last one
  Accumulated reward: 0.78

Task 3 (outage_rca):
  get_service_status:               reward=0.08  ← 4 degraded services * 0.02
  get_alert_history:                reward=0.00
  trace_request (trace-001):        reward=0.05  ← trace bonus
  submit_report (correct):          reward=1.00  ← perfect score
  Accumulated reward: 1.13
```

### Server Tests

```
Health endpoint:     GET  /health → 200 {"status": "healthy"}
Reset endpoint:      POST /reset  → 200 {"observation": {}, "reward": 0.0, "done": false}
Step endpoint:       POST /step   → 200 (with action wrapper)
State endpoint:      GET  /state  → 200 {"episode_id": "...", "step_count": 0}
```

### Validation

```
$ openenv validate
[OK] openenv: Ready for multi-mode deployment
```

### Docker

```
$ docker build -t devops-triage .  → Success (20s build)
$ docker run -p 8001:8000 devops-triage
$ curl http://localhost:8001/health → {"status":"healthy"}
```

---

## 11. Design Decisions

### Why MCP Tools Instead of Custom Actions?

OpenEnv's `MCPEnvironment` pattern (used by echo_env, finqa_env, calendar_env) is the canonical approach. The agent discovers tools via `ListToolsAction` and calls them via `CallToolAction`. This mirrors real LLM tool-use APIs and avoids defining custom Action/Observation Pydantic models for every tool.

### Why Python Dicts for Scenario Data?

Three options were considered:
1. **Python dicts in code** (chosen) — Self-contained, no file I/O, simplest to debug. The data IS the code.
2. **JSON files** — More separation but adds path management and file I/O.
3. **HuggingFace dataset** — Overkill for synthetic data we author ourselves.

Since the scenarios are synthetic (not an external benchmark like FinQA's 290 questions), embedding them in Python is the simplest approach.

### Why Keyword Matching for Grading?

Semantic similarity (embeddings) would be more flexible but requires an additional model dependency and is non-deterministic. Keyword matching with aliases is:
- **Deterministic**: Same inputs always produce the same score
- **Transparent**: Easy to verify why a score is what it is
- **Lightweight**: No additional model required (critical for 2 vCPU constraint)
- **Fair**: Aliases handle reasonable variations in phrasing

### Why LCS for Failure Chain Scoring?

The failure chain is an ordered list (A → B → C → D). We need to reward:
- Getting the right services in the right order (even if incomplete)
- Not penalizing extra services (the agent might include more context)

Longest Common Subsequence (LCS) naturally handles this. If expected is `[A, B, C, D]` and submitted is `[A, C, D]`, LCS is 3/4 = 0.75 (B was missed but the rest are in order).

### Why Separate Incremental vs. Terminal Rewards?

The hackathon requires "reward throughout the trajectory, not just at completion." Incremental rewards serve two purposes:
1. **Signal during training**: RL algorithms learn faster with dense rewards
2. **Discourage degenerate strategies**: Step penalties prevent infinite loops; duplicate penalties prevent the same call over and over

---

## 12. Extending the Environment

### Adding a New Scenario

1. Open the appropriate data file (e.g., `server/data/task1_log_diagnosis.py`)
2. Add a new dict to the `SCENARIOS` list following the existing pattern
3. Include `ground_truth`, `relevant_services`, and `relevant_search_terms`
4. If the incident type is new, add aliases to `INCIDENT_TYPE_ALIASES` in `rewards.py`

### Adding a New Task

1. Create `server/data/task4_new_task.py` with scenario data
2. Add grading function to `server/rewards.py`
3. Register new tools in `DevOpsEnvironment._register_tools()`
4. Add the task name to `TASK_NAMES` set
5. Handle the new task in `reset()` and `_compute_step_reward()`
6. Add a new entry to `TASKS` in `inference.py` with system prompt

### Adjusting Difficulty

- **Easier**: Reduce number of services/distractors, make error messages more explicit, lower step thresholds
- **Harder**: Add more services with subtle log differences, require cross-referencing multiple evidence types, tighten step thresholds
