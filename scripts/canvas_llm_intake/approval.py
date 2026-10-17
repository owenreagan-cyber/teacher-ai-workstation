"""Approval model + READY_TO_PUBLISH gate for the Canvas Weekly Intake.

Approval is explicit and granular (subject page / assignments / weekly
announcement / assessment reminder). States: PENDING / NEEDS_CHANGES / APPROVED
/ BLOCKED / NOT_REQUIRED. Approval binds to BOTH the artifact draft hash and the
source content hash; any change to either invalidates the prior approval
(reverts to PENDING). A week may reach READY_TO_PUBLISH only when all required
artifacts are approved against their CURRENT hashes and no blockers remain.

Every state change records an audit-history entry with source provenance
(``OWNER_UI`` vs ``OWNER``/CLI). Approval is a LOCAL workflow only — no Canvas.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import manifest as mf

GRANULARITIES = ("page", "assignments", "announcement", "assessment_reminder")
STATES = ("PENDING", "NEEDS_CHANGES", "APPROVED", "BLOCKED", "NOT_REQUIRED")

SOURCE_UI = "OWNER_UI"
SOURCE_OWNER = "OWNER"


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


def _append_history(rec: dict[str, Any], action: str, *, source: str, reason: str = "") -> None:
    history = list(rec.get("history", []))
    history.append({"at": _now(), "action": action, "source": source, "reason": reason})
    rec["history"] = history


def set_state(
    quarter: int,
    week: int,
    subject: str,
    granularity: str,
    state: str,
    *,
    draft_hash: str,
    subjects: list[str],
    source_hash: str | None = None,
    source: str = SOURCE_OWNER,
    reason: str = "",
) -> dict[str, Any]:
    """Set an approval state, binding it to the current draft hash (+ source hash).

    Backward compatible with the CLI approve path (``source=OWNER`` default).
    """
    if granularity not in GRANULARITIES:
        raise ValueError(f"unknown granularity {granularity!r}")
    if state not in STATES:
        raise ValueError(f"unknown approval state {state!r}")
    data = load_approvals(quarter, week, subjects)
    data["subjects"].setdefault(subject, {})
    prev = data["subjects"][subject].get(granularity, {})
    rec = {
        "state": state,
        "approved_by": source if state == "APPROVED" else None,
        "approved_at": _now() if state == "APPROVED" else None,
        "draft_hash": draft_hash if state == "APPROVED" else None,
        "source_hash": source_hash if state == "APPROVED" else None,
        "invalidated_at": _now() if state in ("PENDING", "NEEDS_CHANGES", "BLOCKED") and prev.get("state") == "APPROVED" else prev.get("invalidated_at"),
    }
    if prev.get("history"):
        rec["history"] = list(prev.get("history", []))
    data["subjects"][subject][granularity] = rec
    _append_history(rec, f"set_{state.lower()}", source=source, reason=reason)
    save_approvals(quarter, week, data)
    return rec


def approve_artifact(
    quarter: int,
    week: int,
    subject: str,
    granularity: str,
    *,
    draft_hash: str,
    source_hash: str,
    subjects: list[str],
) -> dict[str, Any]:
    """Approve an artifact, binding to the EXACT current draft + source hashes."""
    return set_state(quarter, week, subject, granularity, "APPROVED",
                     draft_hash=draft_hash, source_hash=source_hash,
                     subjects=subjects, source=SOURCE_UI)


def revoke_approval(
    quarter: int,
    week: int,
    subject: str,
    granularity: str,
    *,
    subjects: list[str],
    reason: str = "owner revoked",
) -> dict[str, Any]:
    """Revoke an active approval (local only), preserving audit history."""
    data = load_approvals(quarter, week, subjects)
    rec = data.get("subjects", {}).get(subject, {}).get(granularity, {})
    if rec.get("state") != "APPROVED":
        raise ValueError(f"{subject}:{granularity} is not APPROVED")
    rec["state"] = "PENDING"
    rec["approved_by"] = None
    rec["approved_at"] = None
    rec["draft_hash"] = None
    rec["source_hash"] = None
    rec["invalidated_at"] = _now()
    _append_history(rec, "revoke", source=SOURCE_UI, reason=reason)
    save_approvals(quarter, week, data)
    return rec


def mark_not_required(
    quarter: int,
    week: int,
    subject: str,
    granularity: str,
    *,
    subjects: list[str],
    reason: str = "owner-confirmed blank / not applicable",
) -> dict[str, Any]:
    """Mark an artifact NOT_REQUIRED (no fake content, no approval needed)."""
    return set_state(quarter, week, subject, granularity, "NOT_REQUIRED",
                     draft_hash="", subjects=subjects, source=SOURCE_UI, reason=reason)


def invalidate_if_stale(
    data: dict[str, Any],
    *,
    subject: str,
    draft_hashes: dict[str, str],
    source_hash: str | None = None,
) -> bool:
    """Invalidate an approved artifact whose draft hash or source hash changed.

    Returns True if any approval was reverted.
    """
    changed = False
    entry = data.get("subjects", {}).get(subject, {})
    for g in GRANULARITIES:
        rec = entry.get(g, {})
        if rec.get("state") != "APPROVED":
            continue
        stale = False
        reason = ""
        if rec.get("draft_hash") != draft_hashes.get(g):
            stale = True
            reason = "artifact changed"
        elif (source_hash is not None and rec.get("source_hash") is not None
              and rec.get("source_hash") != source_hash):
            stale = True
            reason = "source changed"
        if stale:
            rec["state"] = "PENDING"
            rec["approved_by"] = None
            rec["approved_at"] = None
            rec["draft_hash"] = None
            rec["source_hash"] = None
            rec["invalidated_at"] = _now()
            _append_history(rec, "invalidated", source="system", reason=reason)
            changed = True
    return changed


def approval_history(quarter: int, week: int, subjects: list[str]) -> list[dict[str, Any]]:
    """Flat, newest-first approval history across all subjects/granularities."""
    data = load_approvals(quarter, week, subjects)
    events: list[dict[str, Any]] = []
    for subject, entry in (data.get("subjects") or {}).items():
        for g, rec in entry.items():
            for h in rec.get("history", []):
                events.append({
                    "subject": subject,
                    "granularity": g,
                    "at": h.get("at"),
                    "action": h.get("action"),
                    "source": h.get("source"),
                    "reason": h.get("reason"),
                })
    events.sort(key=lambda e: e.get("at") or "", reverse=True)
    return events


def ready_to_publish(
    data: dict[str, Any],
    *,
    subjects: list[str],
    has_blocking_questions: bool,
    artifacts: dict[str, set[str]],
) -> tuple[bool, list[str]]:
    """Evaluate the READY_TO_PUBLISH gate.

    ``artifacts`` maps subject -> set of granularities that exist/apply (page
    always; assignments if proposed; announcement always; assessment_reminder if
    drafted). Only required artifacts must be APPROVED. NOT_REQUIRED is
    satisfied; BLOCKED blocks. No BLOCKED states allowed.
    """
    blockers: list[str] = []
    if has_blocking_questions:
        blockers.append("unresolved blocking questions")
    for s in subjects:
        entry = data.get("subjects", {}).get(s, {})
        required = artifacts.get(s, set())
        for g in required:
            rec = entry.get(g, {})
            state = rec.get("state", "PENDING")
            if state == "BLOCKED":
                blockers.append(f"{s}:{g} is BLOCKED")
            elif state not in ("APPROVED", "NOT_REQUIRED"):
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
            # Approve with hash + source binding + provenance + history.
            approve_artifact(2, 2, "math", "page", draft_hash="h1", source_hash="s1", subjects=subjects)
            approve_artifact(2, 2, "math", "assignments", draft_hash="h2", source_hash="s1", subjects=subjects)
            approve_artifact(2, 2, "math", "announcement", draft_hash="h3", source_hash="s1", subjects=subjects)

            data = load_approvals(2, 2, subjects)
            rec = data["subjects"]["math"]["page"]
            assert rec["state"] == "APPROVED"
            assert rec["approved_by"] == "OWNER_UI"
            assert rec["draft_hash"] == "h1" and rec["source_hash"] == "s1"
            assert len(rec["history"]) == 1

            # Draft hash change invalidates.
            assert invalidate_if_stale(data, subject="math", draft_hashes={"page": "changed"}) is True
            assert data["subjects"]["math"]["page"]["state"] == "PENDING"

            # Re-approve, then source hash change invalidates.
            approve_artifact(2, 2, "math", "page", draft_hash="h1", source_hash="s1", subjects=subjects)
            data = load_approvals(2, 2, subjects)  # reload fresh
            assert invalidate_if_stale(data, subject="math", draft_hashes={"page": "h1"}, source_hash="s2") is True
            assert data["subjects"]["math"]["page"]["state"] == "PENDING"

            # Revoke.
            approve_artifact(2, 2, "math", "announcement", draft_hash="h3", source_hash="s1", subjects=subjects)
            revoke_approval(2, 2, "math", "announcement", subjects=subjects)
            assert load_approvals(2, 2, subjects)["subjects"]["math"]["announcement"]["state"] == "PENDING"

            # NOT_REQUIRED satisfies the gate.
            mark_not_required(2, 2, "science", "page", subjects=subjects)
            mark_not_required(2, 2, "science", "announcement", subjects=subjects)
            artifacts = {s: {"page", "announcement"} for s in subjects}
            ready, blockers = ready_to_publish(data, subjects=subjects,
                                               has_blocking_questions=False, artifacts=artifacts)
            assert "science:page" not in blockers, blockers  # NOT_REQUIRED satisfied

            # Approval history is non-empty and newest-first.
            hist = approval_history(2, 2, subjects)
            assert len(hist) > 0 and hist[0]["at"] >= hist[-1]["at"]

            # Partial approval -> NOT ready.
            ready2, blockers2 = ready_to_publish(data, subjects=subjects,
                                                 has_blocking_questions=False, artifacts=artifacts)
            assert ready2 is False, blockers2
        finally:
            mf.staging_dir = orig
    print("PASS intake approval self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
