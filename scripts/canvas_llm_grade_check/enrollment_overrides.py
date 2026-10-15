#!/usr/bin/env python3
"""Local teacher-authored late-enrollment eligibility overrides (gitignored).

Canvas does not always expose a reliable effective-enrollment date. When a
teacher knows a student joined late and Canvas's enrollment metadata is
ambiguous or wrong, the teacher records an authoritative local override.

Store: ``.local/canvas-llm/grade-check/enrollment-overrides.json``

Shape (an object keyed by ``"<course_id>:<student_id>"``):

    {
      "28165:44023": {
        "course_id": 28165,
        "student_id": 44023,
        "eligible_from": "2026-09-12",
        "reason": "late_enrollment"
      }
    }

This file is gitignored and teacher-owned. It is never committed and never
contains real student identities in tracked fixtures.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.canvas_llm_grade_check.config import GradeCheckConfig, REPO_ROOT

DEFAULT_FILENAME = "enrollment-overrides.json"


def override_path(cfg: GradeCheckConfig) -> Path:
    """Resolve the local override store path from config state directory."""
    directory = Path(cfg.state_directory)
    if not directory.is_absolute():
        directory = REPO_ROOT / directory
    return directory / cfg.enrollment_overrides_file


def load_overrides(cfg: GradeCheckConfig) -> dict[str, Any]:
    """Load the raw override store (empty dict when absent/unreadable)."""
    path = override_path(cfg)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def eligible_from_map_for_course(cfg: GradeCheckConfig, course_id: int) -> dict[int, str]:
    """Return ``{student_id: eligible_from}`` overrides for one course."""
    result: dict[int, str] = {}
    for key, entry in load_overrides(cfg).items():
        if not isinstance(entry, dict):
            continue
        if int(entry.get("course_id") or -1) != int(course_id):
            continue
        student_id = entry.get("student_id")
        eligible_from = entry.get("eligible_from")
        if student_id is None or not eligible_from:
            continue
        result[int(student_id)] = str(eligible_from)
    return result


def command_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        class _Cfg:
            state_directory = tmp
            enrollment_overrides_file = DEFAULT_FILENAME

        cfg = _Cfg()  # type: ignore[assignment]
        assert load_overrides(cfg) == {}
        assert eligible_from_map_for_course(cfg, 28165) == {}

        path = override_path(cfg)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "28165:44023": {
                "course_id": 28165, "student_id": 44023,
                "eligible_from": "2026-09-12", "reason": "late_enrollment",
            },
            "26404:99999": {
                "course_id": 26404, "student_id": 99999,
                "eligible_from": "2026-10-01", "reason": "late_enrollment",
            },
        }), encoding="utf-8")

        m = eligible_from_map_for_course(cfg, 28165)
        assert m == {44023: "2026-09-12"}
        assert eligible_from_map_for_course(cfg, 26404) == {99999: "2026-10-01"}
        assert eligible_from_map_for_course(cfg, 28166) == {}

        # A corrupt store fails closed to empty (never crashes a run).
        path.write_text("{not json", encoding="utf-8")
        assert load_overrides(cfg) == {}
        assert eligible_from_map_for_course(cfg, 28165) == {}

    print("PASS grade-check enrollment-overrides self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
