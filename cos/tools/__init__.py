"""M1 tools. All read-only (side_effect "none"). web.search is also fast_path_only.

Tools receive a ToolContext so tests can inject a clock, a command runner,
an HTTP function, and paths. build_registry() registers every M1 tool.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from cos import egress
from cos.config import Config
from cos.registry import Registry

MAX_CMD_OUTPUT = 64_000


@dataclass
class CmdResult:
    returncode: int
    stdout: str
    stderr: str = ""


def run_cmd(argv: list[str], timeout: float, cwd: Path | None = None) -> CmdResult:
    """Run a fixed argv (never a shell) with a timeout and a minimal environment."""
    env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin", "LANG": "en_US.UTF-8",
           "HOME": os.environ.get("HOME", ""), "GIT_OPTIONAL_LOCKS": "0"}
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, cwd=cwd,
                          env=env, stdin=subprocess.DEVNULL, check=False)
    return CmdResult(proc.returncode, proc.stdout[:MAX_CMD_OUTPUT], proc.stderr[:4000])


@dataclass
class ToolContext:
    config: Config
    clock: Callable[[], datetime] = field(default=lambda: datetime.now().astimezone())
    run: Callable[..., CmdResult] = run_cmd
    http: Callable[..., bytes] = egress.request
    audit: Callable | None = None
    eventkit_app: Path | None = None
    loaded_models: Callable[[], list[str]] | None = None


def build_registry(ctx: ToolContext) -> Registry:
    from cos.tools import calendar, mac_status, reminders, status_scripts, time_tool, weather, web_search

    registry = Registry()
    for module in (time_tool, weather, mac_status, calendar, reminders, web_search):
        for tool in module.tools(ctx):
            registry.register(tool)
    for tool in status_scripts.tools(ctx, on_disabled=registry.disable):
        registry.register(tool)
    return registry
