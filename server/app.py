"""FastAPI application for the DevOps Triage environment."""

from __future__ import annotations

import json

from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.mcp_types import CallToolAction, CallToolObservation

from pydantic import field_validator

from .devops_environment import DevOpsEnvironment


class DevOpsCallToolAction(CallToolAction):
    """Extends CallToolAction to handle JSON string arguments from the web UI."""

    @field_validator("arguments", mode="before")
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return v
        return v


app = create_app(
    DevOpsEnvironment,
    DevOpsCallToolAction,
    CallToolObservation,
    "devops_triage",
)


def main():
    """Run the server directly.

    Usage:
        python -m server.app
        uvicorn server.app:app --host 0.0.0.0 --port 8000
    """
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
