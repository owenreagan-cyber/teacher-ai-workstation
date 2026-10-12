#!/usr/bin/env python3
"""Authoritative local teacher absence overrides (local-only, gitignored).

A teacher-controlled source of authoritative assessment absences. Only stable
Canvas IDs are stored (course_id + student_id + assignment_id); names/emails are
never required or persisted. Absence is never inferred from a missing score.

Statuses:
- ABSENT : authoritatively absent; provisional mastery until a score appears
- CLEAR  : resolve a prior override without deleting audit history

Atomic file updates; audit history retained in ``history``.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
OVERRIDES_PATH = REPO_ROOT / ".local" / "canvas-llm" / "mastery" / "absence-overrides.json"

ABSENT = "ABSENT"
CLEAR = "CLEAR"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_key(course_id: int, student_id: int, assignment_id: int) -> str:
    return f"{course_id}:{student_id}:{assignment_id}"


def empty_store() -> dict[str, Any]:
    return {"schemaVersion": 1, "overrides": {}, "history": []}


def load_store(path: Path | None = None) -> dict[str, Any]:
    p = path or OVERRIDES_PATH
    if not p.exists():
        return empty_store()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty_store()
    data.setdefault("overrides", {})
    data.setdefault("history", [])
    data["schemaVersion"] = 1
    return data


def save_store(store: dict[str, Any], path: Path | None = None) -> None:
    p = path or OVERRIDES_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(store, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def add_absence(
    *,
    course_id: int,
    student_id: int,
    assignment_id: int,
    effective_date: str,
    notes: str = "",
    path: Path | None = None,
) -> dict[str, Any]:
    """Record an ABSENT override (idempotent upsert by stable key)."""
    store = load_store(path)
    key = stable_key(course_id, student_id, assignment_id)
    prior = store["overrides"].get(key)
    record = {
        "course_id": course_id,
        "student_id": student_id,
        "assignment_id": assignment_id,
        "status": ABSENT,
        "source": "teacher_override",
        "effective_date": effective_date,
        "notes": notes,
        "created_at": prior.get("created_at", utc_now()) if prior else utc_now(),
        "updated_at": utc_now(),
    }
    store["overrides"][key] = record
    store["history"].append({"at": utc_now(), "action": "ABSENT", "key": key, "effective_date": effective_date})
    save_store(store, path)
    return record


def clear_absence(
    *,
    course_id: int,
    student_id: int,
    assignment_id: int,
    path: Path | None = None,
) -> dict[str, Any]:
    """Resolve a prior ABSENT override (CLEAR). Retains audit history."""
    store = load_store(path)
    key = stable_key(course_id, student_id, assignment_id)
    prior = store["overrides"].pop(key, None)
    if prior is not None:
        store["history"].append({
            "at": utc_now(), "action": "CLEAR", "key": key,
            "resolved_from": prior.get("created_at"),
        })
    save_store(store, path)
    return {"cleared": prior is not None, "key": key}


def list_absences(path: Path | None = None) -> list[dict[str, Any]]:
    store = load_store(path)
    return sorted(store["overrides"].values(), key=lambda r: (r["course_id"], r["student_id"], r["assignment_id"]))


def active_absence_keys(path: Path | None = None) -> set[str]:
    return set(load_store(path)["overrides"].keys())


def absence_user_ids_for_assignment(assignment_id: int, path: Path | None = None) -> set[int]:
    """Return student IDs with an active ABSENT override for one assignment."""
    return {
        r["student_id"] for r in list_absences(path)
        if r["assignment_id"] == assignment_id and r["status"] == ABSENT
    }


def command_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "overrides.json"
        r = add_absence(course_id=26442, student_id=12345, assignment_id=1045694,
                        effective_date="2026-10-16", path=p)
        assert r["status"] == ABSENT
        assert absence_user_ids_for_assignment(1045694, path=p) == {12345}

        # Duplicate ABSENT is idempotent (single override, history grows by one entry only).
        before = len(load_store(p)["overrides"])
        add_absence(course_id=26442, student_id=12345, assignment_id=1045694,
                    effective_date="2026-10-16", path=p)
        assert len(load_store(p)["overrides"]) == before == 1

        # CLEAR removes active override but keeps audit history.
        hist_before = len(load_store(p)["history"])
        clr = clear_absence(course_id=26442, student_id=12345, assignment_id=1045694, path=p)
        assert clr["cleared"] is True
        assert absence_user_ids_for_assignment(1045694, path=p) == set()
        assert len(load_store(p)["history"]) == hist_before + 1

        # CLEAR on non-existent override is a no-op.
        clr2 = clear_absence(course_id=26442, student_id=99999, assignment_id=1045694, path=p)
        assert clr2["cleared"] is False

    print("PASS absence override self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
