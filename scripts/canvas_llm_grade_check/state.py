#!/usr/bin/env python3
"""Local persistent flag state (gitignored under .local/canvas-llm/grade-check/).

State is machine-readable JSON keyed by stable identities (course_id +
student_id + assignment_id + flag type). Student names are never used as
identifiers. Grade snapshots remain local and are never committed to Git.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_grade_check.engine import Flag, flag_from_dict, flag_to_dict

STATE_VERSION = 2


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_state() -> dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "last_scan_at": None,
        "last_send": None,
        "active_flags": {},
        "out_of_scope_flags": {},
        "not_eligible_flags": {},
        "resolved_flags": {},
        "one_time_issued": {},
    }


class StateStore:
    """Load/save local alert state. No grades are committed to Git."""

    def __init__(self, directory: str | Path, filename: str = "state.json") -> None:
        if not isinstance(directory, Path):
            directory = Path(directory)
        if not directory.is_absolute():
            # Resolve relative to the repo root.
            from scripts.canvas_llm_grade_check.config import REPO_ROOT

            directory = REPO_ROOT / directory
        self.directory = directory
        self.path = directory / filename

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return empty_state()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return empty_state()
        data.setdefault("active_flags", {})
        data.setdefault("out_of_scope_flags", {})
        data.setdefault("not_eligible_flags", {})
        data.setdefault("resolved_flags", {})
        data.setdefault("one_time_issued", {})
        data.setdefault("last_scan_at", None)
        data.setdefault("last_send", None)
        data["version"] = STATE_VERSION
        return data

    def save(self, state: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)

    # Convenience helpers ----------------------------------------------------
    def active_flags(self) -> dict[str, Flag]:
        return {k: flag_from_dict(v) for k, v in self.load()["active_flags"].items()}

    def out_of_scope_flags(self) -> dict[str, Flag]:
        return {k: flag_from_dict(v) for k, v in self.load().get("out_of_scope_flags", {}).items()}

    def resolved_flags(self) -> dict[str, Flag]:
        return {k: flag_from_dict(v) for k, v in self.load()["resolved_flags"].items()}

    def one_time_issued(self) -> set[str]:
        return set(self.load()["one_time_issued"].keys())


def write_state(
    store: StateStore,
    *,
    active_persistent: dict[str, Flag],
    resolved_flags: dict[str, Flag],
    one_time_issued: set[str],
    out_of_scope_flags: dict[str, Flag] | None = None,
    not_eligible_flags: dict[str, Flag] | None = None,
    last_send: dict[str, Any] | None = None,
) -> None:
    """Persist a post-send state snapshot (append-only for resolved/one-time).

    The write is atomic (tmp file + os.replace). ``last_send`` metadata is only
    recorded here, i.e. after a confirmed successful email send.
    """
    state = empty_state()
    state["last_scan_at"] = utc_now()
    state["last_send"] = last_send
    state["active_flags"] = {k: flag_to_dict(f) for k, f in active_persistent.items()}
    state["out_of_scope_flags"] = {k: flag_to_dict(f) for k, f in (out_of_scope_flags or {}).items()}
    state["not_eligible_flags"] = {k: flag_to_dict(f) for k, f in (not_eligible_flags or {}).items()}
    state["resolved_flags"] = {k: flag_to_dict(f) for k, f in resolved_flags.items()}
    state["one_time_issued"] = {k: True for k in sorted(one_time_issued)}
    store.save(state)


def command_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        store = StateStore(Path(tmp), "state.json")
        assert store.load()["active_flags"] == {}
        flag = Flag(
            key="26404:1:10:MISSING_ASSIGNMENT",
            flag_type="MISSING_ASSIGNMENT",
            course_id=26404,
            course_name="Math",
            student_id=1,
            student_name="Student Alpha",
            first_name="Student",
            assignment_id=10,
            assignment_title="SM5: Lesson 26 Homework",
            raw_status="MI",
        )
        write_state(
            store,
            active_persistent={flag.key: flag},
            resolved_flags={},
            one_time_issued={"26404:1:20:LOW_ASSESSMENT_SCORE"},
        )
        loaded = store.load()
        assert loaded["active_flags"][flag.key]["student_name"] == "Student Alpha"
        assert "26404:1:20:LOW_ASSESSMENT_SCORE" in loaded["one_time_issued"]
        assert loaded["out_of_scope_flags"] == {}
        assert loaded["last_scan_at"] is not None

        roundtrip = store.active_flags()[flag.key]
        assert roundtrip == flag

        # Out-of-scope flags round-trip through their own bucket.
        oos = Flag(
            key="28165:1:100:MISSING_ASSIGNMENT", flag_type="MISSING_ASSIGNMENT",
            course_id=28165, course_name="History", student_id=1, student_name="Student Gamma",
            first_name="Student", assignment_id=100, assignment_title="HIST 4B: Ch. 2 Assessment",
            raw_status="MI",
        )
        write_state(
            store,
            active_persistent={},
            resolved_flags={},
            one_time_issued=set(),
            out_of_scope_flags={oos.key: oos},
        )
        assert store.out_of_scope_flags()[oos.key] == oos
    print("PASS grade-check state self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
