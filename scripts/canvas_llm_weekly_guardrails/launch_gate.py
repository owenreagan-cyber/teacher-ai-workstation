"""Explicit-launch guard.

Approving pacing, generating artifacts, and showing the final review are all
*pre-launch* steps. None of them writes to Canvas. A distinct, explicit launch
command ("Launch", "Publish it", "Apply Q1W5", "Go live", ...) is required.
No inferred approval.

Standard library only. No network, no Canvas, no writes.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

BLOCK_LAUNCH_REQUIRED = "launch:explicit_command_required"

# Canonicalized base launch commands the owner may use to start the write.
LAUNCH_COMMANDS = frozenset({"launch", "publish", "publish it", "go live", "ship it"})

# "Apply Q1W5", "apply q1w6", etc. are explicit week-scoped launch commands.
_APPLY_WEEK_RE = re.compile(r"^apply\s+q\d+w\d+$")


@dataclass
class LaunchState:
    final_review_shown: bool = False
    launch_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_command(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def is_launch_command(command: str) -> bool:
    cmd = normalize_command(command)
    return cmd in LAUNCH_COMMANDS or bool(_APPLY_WEEK_RE.match(cmd))


def is_launched(state: LaunchState) -> bool:
    return is_launch_command(state.launch_command)


def launch_blockers(state: LaunchState) -> list[str]:
    if is_launched(state):
        return []
    return [BLOCK_LAUNCH_REQUIRED]


def approval_is_not_launch() -> bool:
    """Approval/final-review alone never satisfies the launch gate."""
    return not is_launched(LaunchState(final_review_shown=True, launch_command=""))


__all__ = [
    "BLOCK_LAUNCH_REQUIRED",
    "LAUNCH_COMMANDS",
    "LaunchState",
    "approval_is_not_launch",
    "is_launch_command",
    "is_launched",
    "launch_blockers",
    "normalize_command",
]
