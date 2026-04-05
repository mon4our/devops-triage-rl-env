"""Pydantic models for the DevOps Triage environment."""

from __future__ import annotations

try:
    from openenv.core.env_server.types import State
except ImportError:
    from openenv.core.env_server.interfaces import State


class DevOpsState(State):
    """State for the DevOps Triage environment."""

    task: str = ""
    scenario_id: str = ""
    accumulated_reward: float = 0.0
