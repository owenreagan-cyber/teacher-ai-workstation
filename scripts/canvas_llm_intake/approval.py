"""Approval model + READY_TO_PUBLISH gate for the Canvas Weekly Intake.

Approval is explicit and granular (subject page / assignments / announcement).
States: PENDING / NEEDS_CHANGES / APPROVED / BLOCKED. Approval binds to a draft
hash; any change to an artifact invalidates the prior approval (reverts to
PENDING). A week may reach READY_TO_PUBLISH only when all required artifacts are
approved against their CURRENT draft hash and no blockers remain.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import constants as C
from . import manifest as mf

GRANULARITIES = ("page", "assignments", "announcement")
STATES = ("PENDING", "NEEDS_CHANGES", "APPROVED", "BLOCKED")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def approval_path(quarter: int, week: int) -> Path:
    return mf.staging_dir(quarter, week) / "approvals" / "approval-manifest.json"


def new_manifest(subjects: list[str]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "subjects": {
            s: {g: {"state": "PENDING"} for g in GRANULARITIES} for s in subjects
        },
        "updated_at": _now(),
    }


def load_approvals(quarter: int, week: int, subjects: list[str]) -> dict[str, Any]:
    path = approval_path(quarter, week)
    if not path.exists():
        return new_manifest(subjects)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return new_manifest(subjects)
    # Ensure every subject/granularity is present.
    data.setdefault("subjects", {})
    for s in subjects:
        data["subjects"].setdefault(s, {})
        for g in GRANULARITIES:
            data["subjects"][s].setdefault(g, {"state": "PENDING"})
    return data


def save_approvals(quarter: int, week: int, data: dict[str, Any]) -> Path:
    data["updated_at"] = _now()
    path = approval_path(quarter, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def set_state(
    quarter: int,
    week: int,
    subject: str,
    granularity: str,
    state: str,
    *,
    draft_hash: str,
    subjects: list[str],
) -> dict[str, Any]:
    """Set an approval state, binding it to the current draft hash."""
    if granularity not in GRANULARITIES:
        raise ValueError(f"unknown granularity {granularity!r}")
    if state not in STATES:
        raise ValueError(f"unknown approval state {state!r}")
    data = load_approvals(quarter, week, subjects)
    data["subjects"].setdefault(subject, {})
    data["subjects"][subject][granularity] = {
        "state": state,
        "approved_by": "OWNER" if state == "APPROVED" else None,
        "approved_at": _now() if state == "APPROVED" else None,
        "draft_hash": draft_hash if state == "APPROVED" else None,
    }
    save_approvals(quarter, week, data)
    return data["subjects"][subject][granularity]


def invalidate_if_stale(
    data: dict[str, Any],
    *,
    subject: str,
    draft_hashes: dict[str, str],
) -> bool:
    """Invalidate an approved artifact whose draft hash no longer matches.

    Returns True if any approval was reverted.
    """
    changed = False
    entry = data.get("subjects", {}).get(subject, {})
    for g in GRANULARITIES:
        rec = entry.get(g, {})
        if rec.get("state") == "APPROVED":
            if rec.get("draft_hash") != draft_hashes.get(g):
                rec["state"] = "PENDING"
                rec["approved_by"] = None
                rec["approved_at"] = None
                rec["draft_hash"] = None
                changed = True
    return changed


def ready_to_publish(
    data: dict[str, Any],
    *,
    subjects: list[str],
    has_blocking_questions: bool,
    artifacts: dict[str, set[str]],
) -> tuple[bool, list[str]]:
    """Evaluate the READY_TO_PUBLISH gate.

    ``artifacts`` maps subject -> set of granularities that exist/apply for that
    subject (page always; assignments if proposed; announcement always). Only
    required artifacts must be APPROVED. No BLOCKED states allowed.
    """
    blockers: list[str] = []
    if has_blocking_questions:
        blockers.append("unresolved blocking questions")
    for s in subjects:
        entry = data.get("subjects", {}).get(s, {})
        required = artifacts.get(s, set())
        for g in required:
            rec = entry.get(g, {})
            if rec.get("state") == "BLOCKED":
                blockers.append(f"{s}:{g} is BLOCKED")
            elif rec.get("state") != "APPROVED":
                blockers.append(f"{s}:{g} not approved")
    return (len(blockers) == 0, blockers)


def command_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        import scripts.canvas_llm_intake.manifest as mf
        orig = mf.staging_dir
        mf.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            subjects = ["math", "reading_spelling", "language_arts", "science"]
            set_state(2, 2, "math", "page", "APPROVED", draft_hash="h1", subjects=subjects)
            set_state(2, 2, "math", "assignments", "APPROVED", draft_hash="h2", subjects=subjects)
            set_state(2, 2, "math", "announcement", "APPROVED", draft_hash="h3", subjects=subjects)

            data = load_approvals(2, 2, subjects)
            assert data["subjects"]["math"]["page"]["state"] == "APPROVED"

            # Hash binding: stale hash invalidates.
            assert invalidate_if_stale(data, subject="math", draft_hashes={"page": "changed"}) is True
            assert data["subjects"]["math"]["page"]["state"] == "PENDING"

            # Partial approval: only math approved -> NOT ready.
            artifacts = {s: {"page", "assignments", "announcement"} for s in subjects}
            ready, blockers = ready_to_publish(data, subjects=subjects,
                                               has_blocking_questions=False, artifacts=artifacts)
            assert ready is False and any("reading_spelling:page" in b for b in blockers)

            # Blocking question -> never ready.
            ready2, blockers2 = ready_to_publish(data, subjects=subjects,
                                                 has_blocking_questions=True, artifacts=artifacts)
            assert ready2 is False and any("question" in b for b in blockers2)
        finally:
            mf.staging_dir = orig
    print("PASS intake approval self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
