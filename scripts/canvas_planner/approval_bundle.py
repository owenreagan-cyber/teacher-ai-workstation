"""Atomic per-course approval and human-readable reapproval diffs."""
from __future__ import annotations

import copy
import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_intake import approval, constants, manifest, questions

from . import ai_review
from .events import append_event

LABELS = {
    "math": "Math", "reading_spelling": "Reading/Spelling",
    "language_arts": "Language Arts", "science": "Science", "history": "History",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _hash(value: Any) -> str:
    if isinstance(value, str):
        body = value
    else:
        body = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def current_bundle(quarter: int, week: int, course: str) -> dict[str, Any]:
    d = manifest.staging_dir(quarter, week)
    label = LABELS.get(course, course)
    page_name = "reading-page.html" if course == "reading_spelling" else f"{course}-page.html"
    try:
        page = (d / "drafts" / page_name).read_text(encoding="utf-8")
    except OSError:
        page = ""
    assignments = [a for a in _read(d / "drafts/assignments.json", []) if a.get("course") == course]
    announcement = next((a for a in _read(d / "drafts/announcements.json", []) if a.get("course") == label), {})
    reminders = [r for r in _read(d / "drafts/assessment-reminders.json", []) if r.get("course") == label]
    artifacts = {
        "page": page,
        "announcement": announcement,
        "assignments": assignments,
        "assessment_reminder": reminders,
    }
    hashes = {name: _hash(value) if (value or name in ("page", "announcement", "assignments")) else ""
              for name, value in artifacts.items()}
    return {"course": course, "artifacts": artifacts, "hashes": hashes}


def approve_course(
    quarter: int,
    week: int,
    *,
    course: str,
    expected_hashes: dict[str, str] | None = None,
    confirm_without_ai: bool = False,
) -> dict[str, Any]:
    """Approve every applicable course artifact in one file replacement."""
    m = manifest.load_manifest(quarter, week)
    if not m:
        raise ValueError("no canonical packet")
    active = constants.active_subject_keys_for_quarter(quarter)
    if course not in active:
        raise ValueError("course is not active for this week")
    open_questions = [q for q in questions.load_questions(quarter, week)
                      if q.get("subject") == course and q.get("status") != "ANSWERED"]
    if open_questions:
        raise ValueError("course has unresolved needs-you items")
    review = ai_review.load(quarter, week)
    if review and review.get("state") == "UNAVAILABLE" and not confirm_without_ai:
        raise ValueError("confirm_without_ai is required while AI review is unavailable")
    bundle = current_bundle(quarter, week, course)
    if expected_hashes:
        mismatches = [name for name, value in expected_hashes.items() if bundle["hashes"].get(name) != value]
        if mismatches:
            raise ValueError(f"client hash cross-check failed: {', '.join(sorted(mismatches))}")
    data = approval.load_approvals(quarter, week, active)
    before = copy.deepcopy((data.get("subjects") or {}).get(course, {}))
    target = data["subjects"][course]
    now = _now()
    for artifact in approval.GRANULARITIES:
        applicable = bool(bundle["artifacts"][artifact]) or artifact in ("page", "announcement")
        prior = target.get(artifact) or {}
        history = list(prior.get("history") or [])
        state = "APPROVED" if applicable else "NOT_REQUIRED"
        history.append({
            "at": now, "action": f"set_{state.lower()}", "source": "OWNER_UI",
            "reason": "atomic course approval",
        })
        target[artifact] = {
            "state": state,
            "approved_by": "OWNER_UI" if applicable else None,
            "approved_at": now if applicable else None,
            "draft_hash": bundle["hashes"][artifact] if applicable else None,
            "source_hash": m.get("source_hash") if applicable else None,
            "invalidated_at": None,
            "history": history,
        }
    approval.save_approvals(quarter, week, data)
    snapshot = {**bundle, "approved_at": now, "source_hash": m.get("source_hash")}
    path = snapshot_path(quarter, week, course)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    append_event(
        manifest.staging_dir(quarter, week), action="course_approved", actor="owner",
        reason=f"Owen approved the exact {LABELS[course]} bundle.", before=before,
        after={"course": course, "hashes": bundle["hashes"]},
        undo={"action": "restore_course_approvals", "course": course, "value": before},
    )
    return {"course": course, "state": "APPROVED", "hashes": bundle["hashes"], "approved_at": now}


def snapshot_path(quarter: int, week: int, course: str) -> Path:
    return manifest.staging_dir(quarter, week) / "planner" / "approved-snapshots" / f"{course}.json"


def reapproval_diff(quarter: int, week: int, course: str) -> dict[str, Any]:
    old = _read(snapshot_path(quarter, week, course), {})
    current = current_bundle(quarter, week, course)
    if not old:
        return {"required": True, "reason": "This course has not been approved yet.", "changes": []}
    changes = []
    for artifact in approval.GRANULARITIES:
        old_hash = (old.get("hashes") or {}).get(artifact)
        new_hash = current["hashes"].get(artifact)
        if old_hash == new_hash:
            continue
        before = json.dumps((old.get("artifacts") or {}).get(artifact), indent=2, ensure_ascii=False, sort_keys=True)
        after = json.dumps(current["artifacts"].get(artifact), indent=2, ensure_ascii=False, sort_keys=True)
        changes.append({
            "artifact": artifact,
            "summary": f"{artifact.replace('_', ' ').title()} changed after approval.",
            "diff": "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(),
                                                     fromfile="approved", tofile="current", lineterm="")),
        })
    return {
        "required": bool(changes),
        "reason": "Family-visible content changed after approval." if changes else "The approved content is current.",
        "changes": changes,
        "current_hashes": current["hashes"],
    }
