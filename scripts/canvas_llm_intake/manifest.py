"""Manifest schema + lifecycle for a weekly intake.

A machine-readable ``intake-manifest.json`` is written per week under
``.local/canvas-llm/intake/<year>/q<q>/w<w>/``. The manifest records source
authority, subject drafts, open questions, and approval state, but never marks
anything TEACHER_APPROVED automatically.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import constants as C


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def staging_dir(quarter: int, week: int) -> Path:
    """Return the per-week staging directory under .local."""
    return (
        C.INTAKE_ROOT
        / "2026-2027"
        / f"q{quarter}"
        / f"w{week}"
    )


def new_manifest(
    *,
    quarter: int,
    week: int,
    week_code: str,
    date_range: dict[str, str],
    teacher: str = "4A - Reagan",
    pacing_source: str = "2026-2027 FPK Pacing Guides",
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "school_year": "2026-2027",
        "quarter": quarter,
        "week": week,
        "week_code": week_code,
        "date_range": date_range,
        "teacher": teacher,
        "pacing_source": pacing_source,
        "pacing_tab": "4A - Reagan",
        "source_retrieved_at": None,
        "source_hash": None,
        "status": "SOURCE_FETCHED",
        "subjects": {},
        "questions": [],
        "approval_state": "PENDING",
        "generated_at": _now(),
    }


def load_manifest(quarter: int, week: int) -> dict[str, Any] | None:
    path = staging_dir(quarter, week) / "intake-manifest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(quarter: int, week: int, manifest: dict[str, Any]) -> Path:
    d = staging_dir(quarter, week)
    d.mkdir(parents=True, exist_ok=True)
    path = d / "intake-manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def advance_status(manifest: dict[str, Any], target: str) -> dict[str, Any]:
    """Advance a manifest to a later lifecycle state (monotonic, guarded).

    TEACHER_APPROVED / READY_TO_PUBLISH may only be reached via explicit
    approval (the caller enforces this); this helper only records the move.
    """
    current = manifest.get("status")
    if target not in C.LIFECYCLE_STATES:
        raise ValueError(f"unknown status {target!r}")
    order = {s: i for i, s in enumerate(C.LIFECYCLE_STATES)}
    if current in order and order[target] < order[current]:
        raise ValueError(f"cannot move backward {current} -> {target}")
    manifest["status"] = target
    manifest.setdefault("history", []).append({
        "from": current,
        "to": target,
        "at": _now(),
    })
    return manifest


def command_self_test() -> int:
    m = new_manifest(quarter=2, week=2, week_code="Q2W2",
                     date_range={"start": "2026-10-19", "end": "2026-10-23"})
    assert m["status"] == "SOURCE_FETCHED"
    assert m["approval_state"] == "PENDING"

    advance_status(m, "NORMALIZED")
    advance_status(m, "DRAFTED")
    assert m["status"] == "DRAFTED"
    assert len(m["history"]) == 2

    # Backward transition is rejected.
    try:
        advance_status(m, "NORMALIZED")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass

    # No auto-approval: TEACHER_APPROVED never set by the library.
    assert m["status"] != "TEACHER_APPROVED"

    # staging dir resolves under .local
    d = staging_dir(2, 2)
    assert ".local" in str(d) and d.name == "w2"

    print("PASS intake manifest self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
