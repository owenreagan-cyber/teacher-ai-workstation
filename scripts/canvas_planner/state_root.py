"""One configured state root for Canvas Planner runtime state.

Production defaults to the installed Teacher AI Workstation checkout's
``.local`` directory. Tests must set ``TAW_STATE_ROOT`` to a fixture or pass a
fixture root explicitly to higher-level services.
"""
from __future__ import annotations

import os
from pathlib import Path

STATE_ROOT_ENV = "TAW_STATE_ROOT"
DEFAULT_STATE_ROOT = Path("/Users/owen/Projects/teacher-ai-workstation/.local")


def state_root() -> Path:
    """Return the single configured local-state root."""
    configured = os.environ.get(STATE_ROOT_ENV)
    return Path(configured).expanduser() if configured else DEFAULT_STATE_ROOT


def intake_root() -> Path:
    return state_root() / "canvas-llm" / "intake"


def deployment_root() -> Path:
    return state_root() / "canvas-llm" / "deployments"


def planner_root() -> Path:
    return state_root() / "canvas-planner"
