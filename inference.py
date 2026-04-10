"""
Inference Script — DevOps Triage Environment
=============================================
Runs an LLM agent through all 3 DevOps tasks using the OpenAI client.

Required environment variables:
    API_BASE_URL   API endpoint for the LLM (default: https://router.huggingface.co/v1)
    MODEL_NAME     Model identifier (default: Qwen/Qwen2.5-72B-Instruct)
    HF_TOKEN       Hugging Face API token (required)
    LOCAL_IMAGE_NAME  Docker image name for the environment (optional, for from_docker_image())
"""

import asyncio
import json
import os
import re
import textwrap
from typing import Any, Optional

from openai import OpenAI

from client import DevOpsTriageEnv
from openenv.core.env_server.mcp_types import CallToolAction

# ── Environment Variables ──

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
HF_TOKEN = os.getenv("HF_TOKEN")
IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

BENCHMARK = "devops_triage"

# ── Task Configurations ──

TASKS = [
    {
        "name": "log_diagnosis",
        "max_steps": 25,
        "system_prompt": textwrap.dedent("""\
            You are a Site Reliability Engineer investigating a production incident.
            You have access to logs from multiple services. Your goal is to diagnose the incident.

            Available tools (use exactly these function names):
            - get_services() — list all services
            - get_logs(service, level="ALL", limit=20) — get logs from a service (level: ERROR/WARN/INFO/ALL)
            - search_logs(keyword) — search all logs for a keyword
            - get_runbook(incident_type) — look up operations runbook for an incident type
            - submit_diagnosis(incident_type, severity, affected_services, root_cause) — submit your diagnosis
              - severity: P1 (critical), P2 (major), P3 (minor), P4 (low)
              - affected_services: comma-separated service names

            Strategy:
            1. List services first
            2. Check logs of each service for errors
            3. Search for specific error patterns
            4. Submit your diagnosis when confident

            Respond with a JSON tool call: {"tool": "<name>", "args": {<arguments>}}
        """),
    },
    {
        "name": "test_triage",
        "max_steps": 35,
        "system_prompt": textwrap.dedent("""\
            You are a QA Engineer triaging CI/CD test failures.
            A test suite has run and some tests failed. Classify each failure.

            Available tools:
            - get_test_summary() — overview of test results
            - get_test_details(test_id) — error output, stack trace, console logs, DOM snapshot
            - get_test_history(test_id, num_runs=10) — pass/fail history
            - get_source_code(file_path) — view source code
            - get_recent_changes() — recent git commits and diffs
            - get_ci_config() — CI/CD pipeline configuration (runner, timeouts, environment)
            - submit_classification(test_id, category, evidence, recommendation)
              - category: genuine_bug | flaky_test | environment_issue | stale_test
              - recommendation: fix_code | rerun | update_test | check_infra

            Strategy:
            1. Get the test summary to see which tests failed
            2. For each failed test, check its details and history
            3. Look at recent code changes and source code for context
            4. Submit a classification for EACH failed test

            Respond with a JSON tool call: {"tool": "<name>", "args": {<arguments>}}
        """),
    },
    {
        "name": "outage_rca",
        "max_steps": 40,
        "system_prompt": textwrap.dedent("""\
            You are an SRE performing Root Cause Analysis on a production outage.
            Multiple services are affected. Find the root cause, trace the failure cascade, and propose remediation.

            Available tools:
            - get_service_status() — health of all services
            - get_service_metrics(service, metric) — metric: cpu|memory|latency_ms|error_rate|throughput|connections
            - get_service_logs(service, level="ALL", limit=20) — service logs
            - get_service_config(service) — service configuration
            - get_dependency_graph() — service dependency map
            - trace_request(trace_id) — distributed trace
            - get_alert_history() — recent alerts and available trace IDs
            - get_deployment_history(service) — recent deployments, optionally filtered by service
            - submit_report(root_cause_service, root_cause_description, failure_chain, remediation_steps)
              - failure_chain: comma-separated service names in causal order
              - remediation_steps: newline-separated steps in priority order

            Strategy:
            1. Check service status to find unhealthy/degraded services
            2. Check alerts for timeline and traces
            3. Investigate metrics, logs, and configs of affected services
            4. Use dependency graph and traces to map the failure cascade
            5. Submit your report

            Respond with a JSON tool call: {"tool": "<name>", "args": {<arguments>}}
        """),
    },
]


# ── Logging Helpers ──

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_clean = action.replace("\n", " ")[:200]
    print(
        f"[STEP] step={step} action={action_clean} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── LLM Interaction ──

def parse_tool_call(text: str) -> tuple[str, dict]:
    """Extract tool name and args from LLM response."""
    # Try to find JSON in the response
    json_patterns = [
        r'\{[^{}]*"tool"\s*:\s*"[^"]+"\s*,\s*"args"\s*:\s*\{[^{}]*\}[^{}]*\}',
        r'\{[^{}]*"tool"\s*:\s*"[^"]+"\s*\}',
    ]

    for pattern in json_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                tool = data.get("tool", "")
                args = data.get("args", {})
                return tool, args
            except json.JSONDecodeError:
                continue

    # Fallback: try to parse the entire response as JSON
    try:
        data = json.loads(text.strip())
        if "tool" in data:
            return data["tool"], data.get("args", {})
    except json.JSONDecodeError:
        pass

    return "", {}


def get_llm_action(
    client: OpenAI,
    system_prompt: str,
    observation: str,
    history: list[dict],
) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-10:])  # Keep last 10 exchanges
    messages.append({"role": "user", "content": observation})

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.2,
            max_tokens=500,
            stream=False,
        )
        return (completion.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[DEBUG] LLM request failed: {exc}", flush=True)
        return '{"tool": "get_services", "args": {}}'


# ── Main Inference Loop ──

async def run_task(
    client: OpenAI,
    env: DevOpsTriageEnv,
    task_config: dict,
) -> tuple[float, int, list[float]]:
    """Run a single task and return (score, steps, rewards)."""
    task_name = task_config["name"]
    max_steps = task_config["max_steps"]
    system_prompt = task_config["system_prompt"]

    rewards: list[float] = []
    steps_taken = 0
    score = 0.0
    final_submission_reward = 0.0
    submission_done = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task=task_name)
        obs_text = json.dumps(
            result.observation if isinstance(result.observation, dict) else
            (result.observation.metadata if hasattr(result.observation, 'metadata') and result.observation.metadata else {"info": "Environment reset"}),
            indent=2, default=str,
        )

        history: list[dict] = []
        done = result.done

        for step in range(1, max_steps + 1):
            if done:
                break

            # Get LLM decision
            llm_response = get_llm_action(client, system_prompt, obs_text, history)
            tool_name, tool_args = parse_tool_call(llm_response)

            if not tool_name:
                # If parsing failed, try a default action
                history.append({"role": "user", "content": obs_text})
                history.append({"role": "assistant", "content": llm_response})
                obs_text = "Could not parse your response. Please respond with a JSON tool call: {\"tool\": \"<name>\", \"args\": {<arguments>}}"
                log_step(step=step, action="parse_error", reward=0.0, done=False, error="Could not parse tool call")
                rewards.append(0.0)
                steps_taken = step
                continue

            # Execute the tool
            action_str = f"{tool_name}({json.dumps(tool_args)})"
            try:
                result = await env.step(CallToolAction(tool_name=tool_name, arguments=tool_args))

                reward = result.reward if result.reward is not None else 0.0
                done = result.done
                error = None

                if done and reward > 0:
                    submission_done = True
                    final_submission_reward = reward

                # Build observation text for the LLM
                obs = result.observation
                if isinstance(obs, dict):
                    # Extract structured tool result
                    tool_result = obs.get("result")
                    if tool_result is not None:
                        if isinstance(tool_result, dict) and "structured_content" in tool_result:
                            obs_text = json.dumps(tool_result["structured_content"].get("result", tool_result), indent=2, default=str)
                        elif isinstance(tool_result, dict) and "data" in tool_result:
                            obs_text = json.dumps(tool_result["data"], indent=2, default=str)
                        else:
                            obs_text = json.dumps(tool_result, indent=2, default=str)
                    else:
                        obs_text = json.dumps(obs, indent=2, default=str)
                elif hasattr(obs, 'metadata') and obs.metadata:
                    obs_text = json.dumps(obs.metadata, indent=2, default=str)
                else:
                    obs_text = str(obs)

            except Exception as exc:
                reward = 0.0
                done = False
                error = str(exc)
                obs_text = f"Error executing {tool_name}: {error}"

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            history.append({"role": "user", "content": obs_text})
            history.append({"role": "assistant", "content": llm_response})

            if done:
                break

        # Use the submission reward directly when available; fall back to
        # the sum of positive exploration rewards if no submission happened.
        if submission_done:
            score = final_submission_reward
        elif rewards:
            score = max(sum(r for r in rewards if r > 0), 0)
        score = min(max(score, 0.0), 1.0)

    except Exception as exc:
        print(f"[DEBUG] Task error: {exc}", flush=True)
        score = 0.0

    finally:
        success = score > 0.1
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score, steps_taken, rewards


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    if IMAGE_NAME:
        env = await DevOpsTriageEnv.from_docker_image(IMAGE_NAME)
    else:
        base_url = os.getenv("ENV_BASE_URL", "http://localhost:8000")
        env = DevOpsTriageEnv(base_url=base_url)

    try:
        total_score = 0.0
        for task_config in TASKS:
            score, steps, rewards = await run_task(client, env, task_config)
            total_score += score

        avg_score = total_score / len(TASKS)
        print(f"\n[SUMMARY] average_score={avg_score:.2f}", flush=True)

    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
