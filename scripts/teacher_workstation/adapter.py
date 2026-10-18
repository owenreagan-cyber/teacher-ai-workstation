"""Teacher Workstation — read-only data adapter.

Thin adapter between the UI/API and the existing intake/deployment modules.
Reads ONLY from local ``.local/canvas-llm/intake/`` and ``.local/canvas-llm/
deployments/`` files + reuses the existing intake modules for week resolution
and course mapping. No Canvas network I/O. No write methods. No secrets.

Everything returned is a plain-JSON-serializable dict for the local UI.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.canvas_llm_intake import constants as IC
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_intake import questions as iq
from scripts.canvas_llm_intake import week_resolution as iwr
from scripts.canvas_llm_intake import owner_overrides as ioo
from scripts.canvas_llm_intake import teacher_input as iti
from scripts.canvas_llm_intake import approval as iap

REPO = Path(__file__).resolve().parents[2]
INTAKE_ROOT = REPO / ".local" / "canvas-llm" / "intake"
DEPLOY_ROOT = REPO / ".local" / "canvas-llm" / "deployments"

# Academic subject display order (Homeroom separate).
SUBJECT_ORDER = ("math", "reading_spelling", "language_arts", "science", "history")
SUBJECT_LABELS = {
    "math": "Math",
    "reading_spelling": "Reading/Spelling",
    "language_arts": "Language Arts",
    "science": "Science",
    "history": "History",
}
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _staging_dir(quarter: int, week: int) -> Path:
    return INTAKE_ROOT / "2026-2027" / f"q{quarter}" / f"w{week}"


def _deploy_dir(quarter: int, week: int) -> Path:
    return DEPLOY_ROOT / "2026-2027" / f"q{quarter}" / f"w{week}"


def list_weeks() -> list[dict[str, Any]]:
    """Return all staged weeks (completed + prepared), newest first by code."""
    out: list[dict[str, Any]] = []
    if not INTAKE_ROOT.exists():
        return out
    for manifest_path in sorted(INTAKE_ROOT.glob("2026-2027/q*/w*/intake-manifest.json"), reverse=True):
        m = _read_json(manifest_path)
        if not isinstance(m, dict):
            continue
        out.append({
            "quarter": m.get("quarter"),
            "week": m.get("week"),
            "week_code": m.get("week_code"),
            "date_range": m.get("date_range", {}),
            "status": m.get("status"),
            "ready_to_publish": bool(m.get("ready_to_publish")),
            "source_delta": m.get("source_delta"),
            "open_questions": len([q for q in (m.get("questions") or [])]),
            "assignment_count": m.get("assignment_count"),
            "announcement_count": m.get("announcement_count"),
            "assessment_reminder_count": m.get("assessment_reminder_count"),
        })
    return out


def latest_completed() -> dict[str, Any] | None:
    """Return the latest PUBLISHED_VERIFIED week + its deployment ledger."""
    weeks = list_weeks()
    completed = [w for w in weeks if w["status"] == "PUBLISHED_VERIFIED"]
    if not completed:
        return None
    latest = completed[0]  # list_weeks is already newest-first
    q, w = latest["quarter"], latest["week"]
    ledger = _read_json(_deploy_dir(q, w) / "published-verified-ledger.json")
    result = dict(latest)
    if isinstance(ledger, dict):
        result["ledger"] = {
            "pages": ledger.get("pages", []),
            "assignment_count": len(ledger.get("assignments", [])),
            "weekly_announcements": ledger.get("weekly_announcements", []),
            "assessment_reminders": ledger.get("assessment_reminders", []),
            "deleted_assignments": ledger.get("deleted_assignments", []),
            "verified_at": ledger.get("verified_at"),
            "communication": ledger.get("communication", {}),
            "untouched": ledger.get("untouched", {}),
            "notes": ledger.get("notes", []),
        }
    return result


def _subject_day_states(manifest: dict[str, Any], week_norm: dict[str, Any] | None, quarter: int) -> dict[str, dict[str, str]]:
    """Map each subject/day to a UI-friendly state label."""
    active = IC.active_subject_keys_for_quarter(quarter)
    states: dict[str, dict[str, str]] = {}
    days = (week_norm or {}).get("days", {})
    for subject in SUBJECT_ORDER:
        states[subject] = {}
        for wd in WEEKDAYS:
            day = days.get(wd, {})
            raw = day.get("subjects", {}).get(_norm_subject(subject), {}).get("raw", "")
            if subject not in active:
                states[subject][wd] = "NOT_APPLICABLE"
            elif raw == "":
                states[subject][wd] = "PENDING_SOURCE"
            else:
                states[subject][wd] = _classify_day(subject, raw)
    return states


def _norm_subject(subject: str) -> str:
    # intake subject key -> normalized-week subject key
    if subject == "reading_spelling":
        return "reading"  # reading + spelling share; use reading for state presence
    return subject


def _classify_day(subject: str, raw: str) -> str:
    low = raw.lower()
    if subject == "math":
        if low == "review":
            return "REVIEW"
        if any(k in low for k in ("wa", "written assessment", "fact assessment", "test")):
            return "ASSESSMENT"
        if any(k in low for k in ("inv", "investigation")):
            return "PLANNED"
        return "PLANNED"
    if subject in ("science", "history"):
        if any(k in low for k in ("test", "quiz")):
            return "ASSESSMENT"
        if any(k in low for k in ("check", "review")):
            return "REVIEW"
        return "PLANNED"
    if subject == "language_arts":
        if any(k in low for k in ("test", "cp", "classroom practice")):
            return "ASSESSMENT"
        if "review" in low or "checkup" in low:
            return "REVIEW"
        return "PLANNED"
    # reading_spelling
    if low.startswith("test") or "rmt" in low or "checkout" in low or "mastery" in low:
        return "ASSESSMENT"
    if "review" in low:
        return "REVIEW"
    return "PLANNED"


def week_detail(quarter: int, week: int) -> dict[str, Any] | None:
    """Full detail for one week: manifest + normalized + drafts + questions + approvals."""
    manifest = imf.load_manifest(quarter, week)
    if manifest is None:
        return None

    d = _staging_dir(quarter, week)
    week_norm = _read_json(d / "normalized" / "week.json")
    questions = iq.load_questions(quarter, week)
    open_questions = iq.unresolved_questions(questions)
    assignments = _read_json(d / "drafts" / "assignments.json") or []
    announcements = _read_json(d / "drafts" / "announcements.json") or []
    assessment_reminders = _read_json(d / "drafts" / "assessment-reminders.json") or []
    approvals = _read_json(d / "approvals" / "approval-manifest.json")
    teacher_input = _read_json(d / "teacher-input.json")
    review_md = None
    review_path = d / "REVIEW.md"
    if review_path.exists():
        review_md = review_path.read_text(encoding="utf-8")
    changes = _read_json(d / "changes.json")
    pacing_snapshot = _read_json(d / "source" / "pacing-snapshot.json")

    active = IC.active_subject_keys_for_quarter(quarter)
    day_states = _subject_day_states(manifest, week_norm, quarter)

    # page draft file names + presence
    page_files = {}
    for subject in active:
        fname = "reading-page.html" if subject == "reading_spelling" else f"{subject}-page.html"
        p = d / "drafts" / fname
        page_files[subject] = {"file": f"drafts/{fname}", "exists": p.exists(),
                               "chars": len(p.read_text(encoding="utf-8")) if p.exists() else 0}

    overrides = ioo.list_overrides(quarter, week)
    # Augment day_states with any owner-override status (blank/pending/planned).
    for ov in overrides:
        subj = ov.get("subject")
        day = ov.get("day")
        if subj in day_states and day in day_states[subj]:
            day_states[subj][day] = ov.get("status", day_states[subj][day])

    # Full approval records (state + hashes + history) per subject/granularity.
    approval_records = _approval_records(quarter, week, active)
    approval_events = iap.approval_history(quarter, week, active)

    # Draft hashes for approval binding (expose to the UI for confirm + approve).
    draft_hashes = _compute_draft_hashes(quarter, week, active)

    return {
        "quarter": quarter,
        "week": week,
        "week_code": manifest.get("week_code"),
        "date_range": manifest.get("date_range", {}),
        "status": manifest.get("status"),
        "ready_to_publish": bool(manifest.get("ready_to_publish")),
        "publish_blockers": manifest.get("publish_blockers", []),
        "source_hash": manifest.get("source_hash"),
        "source_retrieved_at": manifest.get("source_retrieved_at"),
        "source_delta": manifest.get("source_delta"),
        "owner_override_conflicts": manifest.get("owner_override_conflicts", []),
        "owner_overrides": overrides,
        "subjects": manifest.get("subjects", {}),
        "active_subjects": active,
        "day_states": day_states,
        "week_norm": _week_norm_view(week_norm),
        "questions": questions,
        "open_questions": open_questions,
        "assignments": assignments,
        "weekly_announcements": announcements,
        "assessment_reminders": assessment_reminders,
        "approval_summary": manifest.get("approval_summary", {}),
        "approval_records": approval_records,
        "approval_history": approval_events,
        "draft_hashes": draft_hashes,
        "page_lookup": manifest.get("page_lookup", {}),
        "page_files": page_files,
        "teacher_input": teacher_input or {},
        "review_md": review_md,
        "changes": changes or {},
        "pacing_snapshot": {
            "retrieved_at": (pacing_snapshot or {}).get("retrieved_at"),
            "hash": (pacing_snapshot or {}).get("hash"),
        } if isinstance(pacing_snapshot, dict) else {},
    }


def _week_norm_view(week_norm: dict[str, Any] | None) -> dict[str, Any] | None:
    """Compact normalized-week view: subject -> day -> {raw, blank}."""
    if not isinstance(week_norm, dict):
        return None
    days = week_norm.get("days", {})
    view: dict[str, dict[str, Any]] = {}
    for subject in SUBJECT_ORDER:
        key = _norm_subject(subject)
        view[subject] = {}
        for wd in WEEKDAYS:
            cell = days.get(wd, {}).get("subjects", {}).get(key, {})
            view[subject][wd] = {"raw": cell.get("raw", ""), "blank": cell.get("blank", cell.get("raw", "") == "")}
    return {
        "week": week_norm.get("week", {}),
        "unit_context": week_norm.get("unitContext", {}),
        "subjects": view,
    }


def _approval_records(quarter: int, week: int, active: list[str]) -> dict[str, dict[str, Any]]:
    """Full per-subject approval records (state + hashes + history)."""
    data = iap.load_approvals(quarter, week, active)
    return data.get("subjects", {})


def _compute_draft_hashes(quarter: int, week: int, active: list[str]) -> dict[str, dict[str, str]]:
    """Compute the CURRENT draft hashes for approval binding.

    Reuses the intake engine's hash function via a lightweight reconstruction
    (the engine writes draft files; hashing them is deterministic and mirrors
    ``intake._draft_hashes`` without re-fetching pacing).
    """
    import hashlib
    d = _staging_dir(quarter, week)
    hashes: dict[str, dict[str, str]] = {}
    for subject in active:
        fname = "reading-page.html" if subject == "reading_spelling" else f"{subject}-page.html"
        p = d / "drafts" / fname
        page_body = p.read_text(encoding="utf-8") if p.exists() else ""
        page_hash = hashlib.sha256(page_body.encode("utf-8")).hexdigest()

        assignments = _read_json(d / "drafts" / "assignments.json") or []
        sub_assignments = [a for a in assignments if a.get("course") == subject]
        assign_hash = hashlib.sha256(
            json.dumps(sub_assignments, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

        announcements = _read_json(d / "drafts" / "announcements.json") or []
        label = SUBJECT_LABELS.get(subject, subject)
        ann = next((a for a in announcements if a.get("course") == label), None)
        ann_hash = hashlib.sha256(json.dumps(ann or {}, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

        reminders = _read_json(d / "drafts" / "assessment-reminders.json") or []
        sub_rems = [r for r in reminders if r.get("course") == label]
        rem_hash = hashlib.sha256(json.dumps(sub_rems, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest() if sub_rems else ""

        hashes[subject] = {"page": page_hash, "assignments": assign_hash,
                           "announcement": ann_hash, "assessment_reminder": rem_hash}
    return hashes


def home() -> dict[str, Any]:
    """Aggregate home-screen payload."""
    today = _today_local()
    try:
        cur = iwr.current_week()
        cur_code = iwr.week_code_for(*cur)
    except Exception:  # noqa: BLE001
        cur, cur_code = None, None
    weeks = list_weeks()
    completed = latest_completed()
    prepared = [w for w in weeks if w["status"] != "PUBLISHED_VERIFIED"]
    next_prepared = prepared[0] if prepared else None

    return {
        "today": today,
        "current_week": cur_code,
        "current_quarter_week": cur,
        "latest_completed": completed,
        "next_prepared": next_prepared,
        "weeks": weeks,
    }


def _today_local() -> str:
    import datetime as dt
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=-4))).strftime("%A, %B %-d, %Y")


def system_status() -> dict[str, Any]:
    """Reuse the intake status renderer (text) plus machine-readable summary."""
    from scripts.canvas_llm_intake import status as istatus

    s = istatus.render_status()
    return {"text": s["text"], "overall": s["overall"]}


def self_test() -> int:
    # Pure adapter smoke: no network, no Canvas. Assert only STRUCTURAL
    # invariants that hold regardless of Q2W3 planning state (which changes as
    # owner input advances). Do not hard-code lifecycle/pending state here.
    weeks = list_weeks()
    assert isinstance(weeks, list)
    detail = week_detail(2, 3)
    assert detail is not None and detail["week_code"] == "Q2W3"
    assert detail["status"] in IC.LIFECYCLE_STATES
    # All academic subjects are present in the day-state map.
    for subject in ("math", "reading_spelling", "language_arts", "science", "history"):
        assert subject in detail["day_states"], subject
        assert set(detail["day_states"][subject].keys()) == set(WEEKDAYS)
    # Key payloads are present (list-shaped or dict-shaped as appropriate).
    assert isinstance(detail["open_questions"], list)
    assert isinstance(detail["assignments"], list)
    assert isinstance(detail["weekly_announcements"], list)
    assert isinstance(detail["assessment_reminders"], list)
    assert isinstance(detail["approval_records"], dict)
    assert isinstance(detail["draft_hashes"], dict)
    # Completed week present.
    assert latest_completed() is not None and latest_completed()["week_code"] == "Q2W2"
    print("PASS teacher-workstation adapter self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
