"""Part G — weekly item lifecycle state machine.

States: SOURCE -> PROPOSED -> TEACHER_APPROVED -> PUBLISHED_VERIFIED.

Phase 3 may reach TEACHER_APPROVED but must NOT enter PUBLISHED_VERIFIED (Canvas
publishing requires the existing explicit deployment workflow). Every transition
preserves provenance.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import constants as C

_VALID_TRANSITIONS = {
    "SOURCE": {"PROPOSED"},
    "PROPOSED": {"TEACHER_APPROVED", "SOURCE"},
    "TEACHER_APPROVED": {"PROPOSED", "SOURCE"},
    "PUBLISHED_VERIFIED": {"TEACHER_APPROVED"},
}

# PUBLISHED_VERIFIED cannot be entered in Phase 3.
_PHASE3_BLOCKED_TARGETS = {"PUBLISHED_VERIFIED"}


class LifecycleError(RuntimeError):
    pass


def validate_transition(current: str, target: str) -> None:
    if current not in C.LIFECYCLE_STATES:
        raise LifecycleError(f"unknown state {current!r}")
    if target not in C.LIFECYCLE_STATES:
        raise LifecycleError(f"unknown state {target!r}")
    if target in _PHASE3_BLOCKED_TARGETS:
        raise LifecycleError(
            "PUBLISHED_VERIFIED cannot be entered in Phase 3; publishing requires the "
            "explicit Canvas deployment workflow"
        )
    if target not in _VALID_TRANSITIONS[current]:
        raise LifecycleError(f"invalid transition {current} -> {target}")


def transition(item: dict[str, Any], target: str, *, reason: str, actor: str = "teacher") -> dict[str, Any]:
    current = item.get("state", "SOURCE")
    validate_transition(current, target)
    history = list(item.get("history", []))
    history.append({
        "from": current,
        "to": target,
        "at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "actor": actor,
    })
    item["state"] = target
    item["history"] = history
    return item


def new_item(week_code: str, subject: str, weekday: str, raw: str) -> dict[str, Any]:
    return {
        "state": "SOURCE",
        "week_code": week_code,
        "subject": subject,
        "weekday": weekday,
        "raw": raw,
        "history": [],
    }


def command_self_test() -> int:
    item = new_item("Q2W1", "math", "Monday", "L31")
    assert item["state"] == "SOURCE"

    item = transition(item, "PROPOSED", reason="local model proposal", actor="local-model")
    assert item["state"] == "PROPOSED"
    assert len(item["history"]) == 1

    item = transition(item, "TEACHER_APPROVED", reason="Owen approved", actor="Owen Reagan")
    assert item["state"] == "TEACHER_APPROVED"

    # Publishing is blocked in Phase 3.
    try:
        transition(item, "PUBLISHED_VERIFIED", reason="would publish")
        raise AssertionError("expected LifecycleError")
    except LifecycleError:
        pass
    assert item["state"] == "TEACHER_APPROVED"

    # Provenance preserved.
    assert [h["to"] for h in item["history"]] == ["PROPOSED", "TEACHER_APPROVED"]

    # Teacher can revert to SOURCE for rework.
    item2 = transition(item, "SOURCE", reason="rework", actor="Owen Reagan")
    assert item2["state"] == "SOURCE"

    print("PASS lifecycle state machine self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
