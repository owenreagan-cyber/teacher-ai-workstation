"""Deterministic deployment-plan builder (pure; no Canvas I/O).

``build_plan`` reads the locally staged + approved packet and produces the exact
write plan the owner reviews before any write. It performs NO network access and
NO writes; it is the single source of truth for both the UI preflight and the
CLI ``--dry-run``.

Plan semantics (all derived canonically from staging; nothing invented):

- pages      : one ``UPDATE`` per active subject that has an approved page draft
               (never create a normal weekly page).
- assignments: one ``CREATE`` per approved assignment proposal (subject-level
               bundle), routed via the canonical assignment_group already present
               in the draft.
- weekly announcements: one ``CREATE`` per active subject, embedding the exact
               staged page agenda HTML (agenda-hash bound).
- assessment reminders: one ``CREATE`` per drafted reminder.
- deletes    : always [] unless an owner-rejected artifact is explicitly marked
               for deletion in the plan (not inferred).
- untouched  : subjects with no approved artifacts.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scripts.canvas_llm_intake import approval as iap
from scripts.canvas_llm_intake import intake
from scripts.canvas_llm_intake import manifest as imf

SUBJECT_LABELS = {
    "math": "Math",
    "reading_spelling": "Reading/Spelling",
    "language_arts": "Language Arts",
    "science": "Science",
    "history": "History",
}

PAGE_FILENAMES = {
    "math": "math-page.html",
    "reading_spelling": "reading-page.html",
    "language_arts": "language_arts-page.html",
    "science": "science-page.html",
    "history": "history-page.html",
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def due_utc(date_str: str, timezone_name: str = "America/New_York") -> str:
    """Convert an intake due_date (YYYY-MM-DD) + canonical 11:59 PM local to UTC.

    Canonical assignment due time is 11:59 PM America/New_York (see
    ``constants.ASSIGNMENT_DEFAULTS``). DST-aware conversion.
    """
    y, m, d = (int(x) for x in date_str.split("-"))
    local = datetime(y, m, d, 23, 59, tzinfo=ZoneInfo(timezone_name))
    return local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")


def weekly_update_delayed_post_at(week_start_date: str) -> str:
    """Canonical weekly-update schedule: the Friday before the week at 4:00 PM ET.

    OWNER_POLICY weeklyUpdateDay (assessment-announcement-policy). The weekly
    update is scheduled for the prior Friday 4:00 PM America/New_York.
    """
    y, m, d = (int(x) for x in week_start_date.split("-"))
    from datetime import date, timedelta
    start = date(y, m, d)
    # Prior Friday: walk back from Monday (start) to the previous Friday.
    friday = start + timedelta(days=-3)
    local = datetime(friday.year, friday.month, friday.day, 16, 0, tzinfo=ZoneInfo("America/New_York"))
    return local.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")


def compose_announcement_body(ann: dict[str, Any], agenda_html: str) -> str:
    """Compose the full weekly-update message.

    Canonical order (§6): greeting → week in review → next-week overview →
    transition → full exact agenda → closing. ``week_in_review`` /
    ``next_week_overview`` are optional (absent in older staged drafts), so this
    remains backward compatible.
    """
    greeting = ann.get("greeting") or "Good afternoon,"
    week_in_review = ann.get("week_in_review") or ""
    next_week_overview = ann.get("next_week_overview") or ""
    transition = ann.get("transition") or ""
    closing = ann.get("closing") or ""
    parts: list[str] = []
    if greeting:
        parts.append(f"<p>{greeting}</p>")
    if week_in_review:
        parts.append(f"<p>{week_in_review}</p>")
    if next_week_overview:
        parts.append(f"<p>{next_week_overview}</p>")
    if transition:
        parts.append(f"<p>{transition}</p>")
    if agenda_html:
        parts.append(agenda_html)
    if closing:
        # closing already contains newlines ("Have a great weekend!\n\nMr. Reagan")
        for para in [p for p in closing.split("\n") if p.strip()]:
            parts.append(f"<p>{para.strip()}</p>")
    return "".join(parts)


def approval_snapshot_hash(approvals: dict[str, Any]) -> str:
    """Stable hash of the current approval state (subject -> granularity -> state)."""
    subjects = approvals.get("subjects", {})
    norm = {
        s: {g: rec.get("state", "PENDING") for g, rec in (entry or {}).items()}
        for s, entry in sorted(subjects.items())
    }
    return _sha(json.dumps(norm, sort_keys=True, ensure_ascii=False))


def load_packet(quarter: int, week: int) -> dict[str, Any]:
    """Read the already-staged packet (read-only; no regeneration, no Canvas).

    The staging packet is authoritative and always consistent because every
    mutation path (owner input, overrides, approvals) regenerates it through
    ``intake.build_intake``. Preflight/deploy read that staged state directly.
    """
    from scripts.canvas_llm_intake import constants as IC

    d = imf.staging_dir(quarter, week)

    def _read(name: str) -> Any:
        p = d / "drafts" / name
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    assignments = _read("assignments.json") or []
    announcements = _read("announcements.json") or []
    reminders = _read("assessment-reminders.json") or []
    active = IC.active_subject_keys_for_quarter(quarter)
    page_bodies: dict[str, str] = {}
    for subject in active:
        fname = PAGE_FILENAMES.get(subject, f"{subject}-page.html")
        p = d / "drafts" / fname
        page_bodies[subject] = p.read_text(encoding="utf-8") if p.exists() else ""

    manifest = imf.load_manifest(quarter, week) or {}
    approvals = iap.load_approvals(quarter, week, active)
    return {
        "quarter": quarter,
        "week": week,
        "summary": {
            "active_subjects": active,
            "status": manifest.get("status"),
            "source_hash": manifest.get("source_hash"),
            "ready_to_publish": bool(manifest.get("ready_to_publish")),
            "publish_blockers": manifest.get("publish_blockers", []),
            "date_range": manifest.get("date_range", {}),
            "week_code": manifest.get("week_code"),
        },
        "manifest": manifest,
        "assignments": assignments,
        "announcements": announcements,
        "reminders": reminders,
        "page_bodies": page_bodies,
        "approvals": approvals,
    }


def _slug_for(week_code: str) -> str:
    return intake._slug_for(week_code)


def build_plan(quarter: int, week: int) -> dict[str, Any]:
    """Produce the deterministic, reviewable write plan (no Canvas I/O)."""
    pkt = load_packet(quarter, week)
    summary = pkt["summary"]
    manifest = pkt["manifest"]
    approvals = pkt["approvals"]
    week_code = summary.get("week_code", "")
    slug = _slug_for(week_code)
    date_range = manifest.get("date_range", {})
    week_start = date_range.get("start", "")

    active = summary["active_subjects"]
    subjects = approvals.get("subjects", {})

    # Pages: UPDATE only for approved page artifacts.
    pages: list[dict[str, Any]] = []
    for subject in active:
        rec = subjects.get(subject, {}).get("page", {})
        state = rec.get("state", "PENDING")
        if state == "NOT_REQUIRED":
            continue
        if state != "APPROVED":
            continue
        pages.append({
            "subject": subject,
            "course_id": _course_id(subject),
            "slug": slug,
            "title": _page_title(week_code),
            "action": "UPDATE",
            "file": PAGE_FILENAMES.get(subject, f"{subject}-page.html"),
            "body_sha256": _sha(pkt["page_bodies"].get(subject, "")),
        })

    # Assignments: CREATE only for approved assignment bundle.
    assignments: list[dict[str, Any]] = []
    for subject in active:
        if subjects.get(subject, {}).get("assignments", {}).get("state") != "APPROVED":
            continue
        for a in pkt["assignments"]:
            if a.get("course") != subject:
                continue
            assignments.append({
                "course": subject,
                "course_id": a.get("course_id"),
                "title": a.get("title"),
                "assignment_group": a.get("assignment_group"),
                "due_date": a.get("due_date"),
                "due_utc": due_utc(a.get("due_date", "")) if a.get("due_date") else "",
                "points_possible": a.get("points_possible", 100),
                "grading_type": a.get("grading_type", "percent"),
                "submission_types": a.get("submission_types", ["on_paper"]),
                "omit_from_final_grade": a.get("omit_from_final_grade", False),
                "action": "CREATE",
            })

    # Weekly announcements: CREATE only for approved announcement artifact.
    announcements_plan: list[dict[str, Any]] = []
    for subject in active:
        if subjects.get(subject, {}).get("announcement", {}).get("state") != "APPROVED":
            continue
        label = SUBJECT_LABELS.get(subject, subject)
        ann = next((x for x in pkt["announcements"] if x.get("course") == label), None)
        if ann is None:
            continue
        agenda_html = pkt["page_bodies"].get(subject, "")
        body = compose_announcement_body(ann, agenda_html)
        announcements_plan.append({
            "course": label,
            "course_id": _course_id(subject),
            "subject": subject,
            "title": ann.get("title", f"{label} Canvas Weekly Update"),
            "message": body,
            "scheduled": True,
            "delayed_post_at": weekly_update_delayed_post_at(week_start) if week_start else None,
            "agenda_hash": ann.get("agenda_hash", ""),
            "page_agenda_hash": ann.get("page_agenda_hash", ""),
            "hash_consistent": ann.get("hash_consistent", False),
            "week_code": week_code,
            "date_range": date_range,
            "artifact_type": "weekly_update",
            "action": "CREATE",
        })

    # Assessment reminders: CREATE only for approved assessment_reminder artifact.
    reminders_plan: list[dict[str, Any]] = []
    for subject in active:
        if subjects.get(subject, {}).get("assessment_reminder", {}).get("state") != "APPROVED":
            continue
        label = SUBJECT_LABELS.get(subject, subject)
        for r in pkt["reminders"]:
            if r.get("course") != label:
                continue
            reminders_plan.append({
                "type": r.get("type"),
                "course": label,
                "course_id": r.get("course_id"),
                "subject": subject,
                "title": r.get("title"),
                "message": r.get("body", ""),
                "scheduled": False,
                "delayed_post_at": None,
                "week_code": week_code,
                "date_range": date_range,
                "artifact_type": "assessment_reminder",
                "action": "CREATE",
            })

    untouched = {
        s: True for s in SUBJECT_LABELS
        if s not in active
        or all(subjects.get(s, {}).get(g, {}).get("state") != "APPROVED"
               for g in ("page", "assignments", "announcement", "assessment_reminder"))
    }

    counts = {
        "pages_update": len(pages),
        "assignments_create": len(assignments),
        "assignments_update": 0,
        "announcements_create": len(announcements_plan) + len(reminders_plan),
        "announcements_update": 0,
        "deletes": 0,
    }

    return {
        "quarter": quarter,
        "week": week,
        "week_code": week_code,
        "slug": slug,
        "date_range": date_range,
        "generated_at": _now(),
        "status": summary.get("status"),
        "ready_to_publish": bool(summary.get("ready_to_publish")),
        "publish_blockers": summary.get("publish_blockers", []),
        "source_hash": summary.get("source_hash"),
        "approval_snapshot_hash": approval_snapshot_hash(approvals),
        "pages": pages,
        "assignments": assignments,
        "weekly_announcements": announcements_plan,
        "assessment_reminders": reminders_plan,
        "deletes": [],
        "untouched": untouched,
        "counts": counts,
    }


def _course_id(subject: str) -> int | None:
    from scripts.canvas_llm_intake import constants as C
    mapping = {
        "math": "math",
        "reading_spelling": "reading",
        "language_arts": "language-arts",
        "science": "science",
        "history": "history",
    }
    return C.course_id_for_subject(mapping.get(subject, subject))


def _page_title(week_code: str) -> str:
    """Canonical page title from the instructional-weeks export."""
    import json as _json
    from scripts.canvas_llm_phase3 import constants as P3
    weeks = _json.loads(P3.WEEKS_PATH.read_text(encoding="utf-8")).get("weeks", [])
    entry = next((w for w in weeks if w.get("code") == week_code), None)
    return entry.get("pageTitle", "") if entry else ""


def command_self_test() -> int:
    import tempfile
    from scripts.canvas_llm_intake import manifest as mfmod

    orig = mfmod.staging_dir
    with tempfile.TemporaryDirectory() as tmp:
        mfmod.staging_dir = lambda q, w: Path(tmp) / f"q{q}w{w}"
        try:
            # due_utc DST-aware.
            assert due_utc("2026-10-26") == "2026-10-27T03:59:00Z", due_utc("2026-10-26")
            # announcement body composition + closing preservation.
            ann = {"greeting": "Good afternoon,", "transition": "The page is updated.",
                   "closing": "Have a great weekend!\n\nMr. Reagan"}
            body = compose_announcement_body(ann, "<div id='kl_wrapper_3'>agenda</div>")
            assert "kl_wrapper_3" in body and "Mr. Reagan" in body and "Have a great weekend!" in body
            # approval snapshot hash is deterministic.
            a1 = {"subjects": {"math": {"page": {"state": "APPROVED"}}}}
            a2 = {"subjects": {"math": {"page": {"state": "APPROVED"}}}}
            assert approval_snapshot_hash(a1) == approval_snapshot_hash(a2)
            # weekly update schedule = prior Friday 4 PM ET.
            assert weekly_update_delayed_post_at("2026-10-26").startswith("2026-10-23T20:00")
        finally:
            mfmod.staging_dir = orig
    print("PASS canvas-deploy plan self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
