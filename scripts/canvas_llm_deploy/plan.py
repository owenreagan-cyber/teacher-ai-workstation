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


def _load_assignment_reconciliation(quarter: int, week: int) -> dict[str, Any]:
    """Read the staged GET-only assignment reconciliation (local, read-only).

    Absent or unreadable reconciliation data leaves every proposal on the
    historical CREATE path; it never fabricates an UPDATE identity.
    """
    path = imf.staging_dir(quarter, week) / "planner" / "assignment-reconciliation.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _slug_for(week_code: str) -> str:
    return intake._slug_for(week_code)


def _reminder_plan_entry(
    reminder: dict[str, Any],
    *,
    label: str,
    subject: str,
    week_code: str,
    date_range: dict[str, Any],
    now: datetime | None = None,
    notice_times: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Schedule a reminder. A missing delay never becomes an immediate post."""
    from scripts.canvas_llm_intake import assessment_announcements as aa
    from scripts.canvas_llm_phase3 import pacing_announcement as pa

    item = dict(reminder)
    identity = item.get("duplicate_identity") or ""
    if not item.get("schedule_state"):
        aa.annotate_unscheduled_reminders([item], now=now, notice_times=notice_times)
    elif item.get("schedule_state") == "OWNER_TIME_REQUIRED" and identity in (notice_times or {}):
        try:
            timing = pa.classify_notice_schedule(
                item.get("proposed_post_date") or item.get("assessment_date") or "",
                pa.load_config(), now=now, owner_selected_at=(notice_times or {})[identity],
            )
            item.update(timing)
            item["publication_blocked"] = False
        except ValueError as exc:
            item["schedule_state"] = "BLOCKED"
            item["scheduled"] = False
            item["delayed_post_at"] = None
            item["publication_blocked"] = True
            item["schedule_error"] = str(exc)
    state = item.get("schedule_state")
    delayed = item.get("delayed_post_at")
    entry = {
        "type": item.get("type"),
        "notice_type": item.get("notice_type"),
        "course": label,
        "course_id": item.get("course_id"),
        "subject": subject,
        "title": item.get("title"),
        "message": item.get("message") or item.get("body") or "",
        "week_code": week_code,
        "date_range": date_range,
        "artifact_type": "assessment_reminder",
        "duplicate_identity": identity,
        "duplicate_status": item.get("duplicate_status"),
        "content_status": item.get("content_status"),
        "schedule_state": state,
        "assessment_date": item.get("assessment_date"),
    }
    publishable = (
        state == "FUTURE_SCHEDULED"
        and bool(delayed)
        and item.get("content_status", "READY") == "READY"
        and item.get("duplicate_status", "UNIQUE") != "AMBIGUOUS"
        and not item.get("publication_blocked")
    )
    if publishable:
        entry.update({"scheduled": True, "delayed_post_at": delayed, "action": "CREATE"})
    else:
        entry.update({
            "scheduled": False,
            "delayed_post_at": None,
            "action": "BLOCKED",
            "block_reason": (
                "owner-selected future publication time required"
                if state in (None, "OWNER_TIME_REQUIRED")
                else item.get("schedule_error") or item.get("blocked_sections") or "assessment notice is not publishable"
            ),
        })
    return entry


def agenda_composite_hash(week_code: str, agendas: dict[str, str]) -> str:
    """Hash the week code and each subject's page agenda. This is not the intake source hash."""
    return _sha(json.dumps(
        {"to": week_code, "agendas": agendas},
        sort_keys=True, ensure_ascii=False,
    ))


def plan_fingerprint(plan: dict[str, Any]) -> str:
    """Hash the publish actions a reviewer actually approved."""
    def _rows(items: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
        rows = []
        for item in items or []:
            row = {field: item.get(field) for field in fields}
            message = item.get("message") or ""
            if message:
                row["message_hash"] = _sha(message)
            rows.append(row)
        return rows

    payload = {
        "assignments": _rows(plan.get("assignments") or [], (
            "title", "action", "course_id", "due_date", "assignment_id",
        )),
        "weekly_announcements": _rows(plan.get("weekly_announcements") or [], (
            "title", "action", "course_id", "page_id", "delayed_post_at", "schedule_state",
        )),
        "assessment_reminders": _rows(plan.get("assessment_reminders") or [], (
            "title", "action", "course_id", "delayed_post_at", "schedule_state", "duplicate_identity",
        )),
    }
    return _sha(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str))


def build_plan(
    quarter: int,
    week: int,
    *,
    now: datetime | None = None,
    owner_publication_time: str | None = None,
    notice_times: dict[str, str] | None = None,
) -> dict[str, Any]:
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
    stored_times = intake.load_owner_publication_times(quarter, week)
    if owner_publication_time is None:
        owner_publication_time = stored_times.get("release")
    if notice_times is None:
        notice_times = dict(stored_times.get("notices") or {})

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

    # Assignments: approved bundle only. The staged GET-only reconciliation
    # binds each proposal to its live identity and the exact correction, so an
    # existing assignment is updated in place instead of duplicated.
    reconciliation = _load_assignment_reconciliation(quarter, week)
    reconciled = {
        (str(rec.get("course")), str(rec.get("title"))): rec
        for rec in reconciliation.get("results", [])
    }
    assignments: list[dict[str, Any]] = []
    for subject in active:
        if subjects.get(subject, {}).get("assignments", {}).get("state") != "APPROVED":
            continue
        for a in pkt["assignments"]:
            if a.get("course") != subject:
                continue
            entry = {
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
                "description": a.get("description", ""),
                "action": "CREATE",
            }
            rec = reconciled.get((subject, str(a.get("title"))))
            if rec:
                classification = rec.get("classification")
                live = rec.get("live") or {}
                if classification == "UPDATE_REQUIRED":
                    entry["action"] = "UPDATE"
                    entry["assignment_id"] = live.get("assignment_id")
                    entry["corrections"] = rec.get("corrections") or {}
                    entry["live_due_at"] = live.get("due_at")
                elif classification == "MATCH":
                    entry["action"] = "SKIP"
                    entry["assignment_id"] = live.get("assignment_id")
                elif classification == "CREATE_REQUIRED":
                    entry["action"] = "CREATE"
                else:
                    entry["action"] = "BLOCKED"
                    entry["block_reason"] = rec.get("reason") or str(classification)
            assignments.append(entry)

    # Weekly announcements: CREATE only for approved announcement artifact.
    # A missed Friday 4:00 PM window is not backdated. Without an explicit
    # owner-selected time the announcement is blocked.
    publication = None
    if week_start:
        from scripts.canvas_llm_rollover.schedule import resolve_publication_time
        try:
            publication = resolve_publication_time(
                week_start, now=now, owner_selected_at=owner_publication_time,
            )
        except ValueError:
            publication = {
                "requires_owner_time": True,
                "scheduled_at": None,
                "canonical_scheduled_at": None,
            }
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
        if publication and publication.get("requires_owner_time"):
            scheduled = False
            delayed_post_at = None
            schedule_state = "OWNER_TIME_REQUIRED"
            action = "BLOCKED"
        elif publication:
            scheduled = True
            delayed_post_at = publication.get("scheduled_at")
            schedule_state = "FUTURE_SCHEDULED"
            action = "CREATE"
        else:
            scheduled = True
            delayed_post_at = weekly_update_delayed_post_at(week_start) if week_start else None
            schedule_state = "FUTURE_SCHEDULED" if delayed_post_at else None
            action = "CREATE"
        if ann.get("hash_consistent") is False:
            action = "BLOCKED"
            scheduled = False
            delayed_post_at = None
            schedule_state = "BLOCKED"
        announcements_plan.append({
            "course": label,
            "course_id": _course_id(subject),
            "subject": subject,
            "page_id": ann.get("page_id"),
            "title": ann.get("title", f"{label} Canvas Weekly Update"),
            "message": body,
            "scheduled": scheduled,
            "delayed_post_at": delayed_post_at,
            "canonical_delayed_post_at": (publication or {}).get("canonical_scheduled_at"),
            "schedule_state": schedule_state,
            "agenda_hash": ann.get("agenda_hash", ""),
            "page_agenda_hash": ann.get("page_agenda_hash", ""),
            "hash_consistent": ann.get("hash_consistent", False),
            "week_code": week_code,
            "date_range": date_range,
            "artifact_type": "weekly_update",
            "action": action,
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
            reminders_plan.append(_reminder_plan_entry(
                r, label=label, subject=subject, week_code=week_code, date_range=date_range,
                now=now, notice_times=notice_times,
            ))

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

    result = {
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
        "owner_publication_time": owner_publication_time,
    }
    result["agenda_hash"] = agenda_composite_hash(week_code, {
        subject: _sha(pkt["page_bodies"].get(subject, "")) for subject in active
    })
    result["plan_fingerprint"] = plan_fingerprint(result)
    _stamp_plan_approval(
        result,
        approvals=approvals,
        quarter=quarter,
        week=week,
        source_hash=summary.get("source_hash") or "",
        owner_publication_time=owner_publication_time,
    )
    return result


def _stamp_plan_approval(
    plan: dict[str, Any],
    *,
    approvals: dict[str, Any],
    quarter: int,
    week: int,
    source_hash: str,
    owner_publication_time: str | None,
) -> None:
    """Copy granular approval onto the items the prewrite gate checks.

    Schedule fields stay as built. A stale or missing record cannot become
    ``approved``.
    """
    from scripts.canvas_llm_intake import approval as approval_mod
    from scripts.canvas_planner.approval_bundle import current_bundle

    fingerprint = plan.get("plan_fingerprint")
    subjects = approvals.get("subjects") or {}
    bundles: dict[str, dict[str, Any]] = {}

    def bundle_for(subject: str) -> dict[str, Any]:
        if subject not in bundles:
            bundles[subject] = current_bundle(quarter, week, subject)
        return bundles[subject]

    def apply(item: dict[str, Any], subject: str, granularity: str) -> None:
        if not subject:
            item["approved"] = False
            item["approval_state"] = "PENDING"
            return
        record = (subjects.get(subject) or {}).get(granularity)
        item.update(approval_mod.resolve_artifact_approval(
            record,
            draft_hash=(bundle_for(subject).get("hashes") or {}).get(granularity, ""),
            source_hash=source_hash,
            subject=subject,
            granularity=granularity,
            quarter=quarter,
            week=week,
            course_id=item.get("course_id"),
            plan_fingerprint=fingerprint,
            owner_publication_time=owner_publication_time,
        ))

    for item in plan.get("assignments") or []:
        apply(item, item.get("course") or item.get("subject") or "", "assignments")
    for item in plan.get("weekly_announcements") or []:
        apply(item, item.get("subject") or "", "announcement")
    for item in plan.get("assessment_reminders") or []:
        apply(item, item.get("subject") or "", "assessment_reminder")
    for item in plan.get("pages") or []:
        apply(item, item.get("subject") or "", "page")


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
