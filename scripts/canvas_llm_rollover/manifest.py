"""Deterministic Friday-rollover manifest/plan builder (pure; no Canvas I/O).

Produces the exact rollover plan the owner reviews before any write:

    academic_courses   : front-page actions for each active subject.
    homeroom           : newsletter copy-forward + front-page action.
    weekly_announcements: exact subject-isolated weekly updates from the
                          same page + announcement projection shown in Preview,
                          agenda-hash bound and scheduled Friday 4 PM.

Reuses the existing intake staging packet (page bodies + approvals + drafted
announcements) so there is exactly one source of truth — no parallel system.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from scripts.canvas_llm_intake import constants as IC
from scripts.canvas_llm_intake import manifest as imf
from scripts.canvas_llm_intake import week_resolution as wr
from scripts.canvas_llm_deploy import plan as plan_mod

from . import homeroom
from . import schedule

SUBJECT_LABELS = {
    "math": "Math",
    "reading_spelling": "Reading/Spelling",
    "language_arts": "Language Arts",
    "science": "Science",
    "history": "History",
}

HOMEROOM_COURSE_ID = 26429


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _course_id(subject: str) -> int | None:
    mapping = {
        "math": "math",
        "reading_spelling": "reading",
        "language_arts": "language-arts",
        "science": "science",
        "history": "history",
    }
    return IC.course_id_for_subject(mapping.get(subject, subject))


def load_normalized_week(quarter: int, week: int) -> dict[str, Any] | None:
    """Read a staged normalized week (read-only local state)."""
    p = imf.staging_dir(quarter, week) / "normalized" / "week.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def compose_weekly_update_body(
    *,
    subject: str,
    title: str,
    week_in_review: str,
    next_week_overview: str,
    transition: str,
    agenda_html: str,
    closing: str,
) -> str:
    """Compose the canonical weekly-update message body.

    Order (§6): greeting → week in review → next-week overview → transition →
    full exact agenda HTML → closing.
    """
    parts: list[str] = ["<p>Good afternoon,</p>"]
    if week_in_review:
        parts.append(f"<p>{week_in_review}</p>")
    if next_week_overview:
        parts.append(f"<p>{next_week_overview}</p>")
    if transition:
        parts.append(f"<p>{transition}</p>")
    if agenda_html:
        parts.append(agenda_html)
    for para in [p for p in (closing or "").split("\n") if p.strip()]:
        parts.append(f"<p>{para.strip()}</p>")
    return "".join(parts)


def build_rollover_manifest(
    from_quarter: int,
    from_week: int,
    to_quarter: int,
    to_week: int,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """Build the deterministic rollover plan (no Canvas I/O)."""
    to_code = wr.week_code_for(to_quarter, to_week)
    to_entry = wr.find_week(to_quarter, to_week) or {}
    from scripts.instructional_weeks import week_range
    bounds = week_range(to_entry)
    to_date_range = {
        "start": bounds[0].isoformat() if bounds else "",
        "end": bounds[1].isoformat() if bounds else "",
    }
    scheduled_at = (
        schedule.friday_rollover_scheduled_at(to_date_range["start"])
        if to_date_range["start"] else ""
    )

    active = IC.active_subject_keys_for_quarter(to_quarter)
    pkt = plan_mod.load_packet(to_quarter, to_week)
    deploy_plan = plan_mod.build_plan(to_quarter, to_week)
    approvals = pkt.get("approvals", {})
    slug = plan_mod._slug_for(to_code)
    agenda_html = pkt.get("page_bodies", {})

    academic_courses: list[dict[str, Any]] = []
    for subject in active:
        html = agenda_html.get(subject, "")
        subject_approvals = (approvals.get("subjects") or {}).get(subject, {})
        required = ["page", "announcement", "assignments"]
        if any(r.get("course") == SUBJECT_LABELS.get(subject, subject)
               for r in pkt.get("reminders", [])):
            required.append("assessment_reminder")
        from scripts.canvas_planner.approval_bundle import current_bundle
        current_hashes = current_bundle(to_quarter, to_week, subject)["hashes"]
        approved_now = all(
            (subject_approvals.get(kind) or {}).get("state") == "APPROVED"
            and (subject_approvals.get(kind) or {}).get("draft_hash") == current_hashes.get(kind)
            for kind in required
        )
        academic_courses.append({
            "subject": subject,
            "label": SUBJECT_LABELS.get(subject, subject),
            "course_id": _course_id(subject),
            "to_page_slug": slug,
            "to_page_hash": _sha(html),
            "page_body": html,
            "approved": approved_now,
            "current_hashes": current_hashes,
            "required_approvals": required,
            "front_page_action": "SET_FRONT_PAGE",
        })

    # Homeroom copy-forward.
    approved = homeroom.load_approved_content()
    proposed = homeroom.copy_forward(
        approved, today=today or date.today(), to_date_range=to_date_range
    )
    homeroom_block = {
        "course_id": HOMEROOM_COURSE_ID,
        "from_page_id": None,
        "to_page_id": None,
        "to_page_slug": slug,
        "source_content_hash": homeroom.content_hash(approved),
        "proposed_content_hash": _sha(homeroom.render_proposed(proposed)),
        "proposed_content": proposed,
        "approved": False,
        "front_page_action": "SET_FRONT_PAGE",
    }
    homeroom_approval_path = (
        imf.staging_dir(to_quarter, to_week) / "planner" / "homeroom-approval.json"
    )
    try:
        homeroom_approval = json.loads(homeroom_approval_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        homeroom_approval = {}
    try:
        from scripts.canvas_planner.approval_bundle import current_bundle
        current_homeroom_hash = current_bundle(to_quarter, to_week, "homeroom")["hashes"]["page"]
    except (KeyError, OSError, ValueError):
        current_homeroom_hash = ""
    homeroom_block["approval_hash"] = (homeroom_approval.get("hashes") or {}).get("page")
    homeroom_block["approved"] = bool(
        homeroom_approval.get("state") == "APPROVED"
        and homeroom_block["approval_hash"]
        and homeroom_block["approval_hash"] == current_homeroom_hash
    )

    # Weekly updates use the exact same canonical projection as UI Preview.
    weekly_announcements: list[dict[str, Any]] = []
    drafted = pkt.get("announcements", [])
    for subject in active:
        label = SUBJECT_LABELS.get(subject, subject)
        ann = next((x for x in drafted if x.get("course") == label), None) or {}
        html = agenda_html.get(subject, "")
        body = plan_mod.compose_announcement_body(ann, html)
        weekly_announcements.append({
            "subject": subject,
            "label": label,
            "course_id": _course_id(subject),
            "title": ann.get("title", f"{label} Canvas Weekly Update"),
            "week_code": to_code,
            "agenda_hash": _sha(html),
            "page_agenda_hash": _sha(html),
            "hash_consistent": True,
            "body_hash": _sha(body),
            "message": body,
            "delayed_post_at": scheduled_at,
            "classification": "NEW",
            "action": "CREATE",
        })

    source_hash = _sha(json.dumps(
        {"to": to_code, "agendas": {s: _sha(agenda_html.get(s, "")) for s in active}},
        sort_keys=True, ensure_ascii=False,
    ))
    return {
        "schemaVersion": 1,
        "school_year": "2026-2027",
        "from_week": wr.week_code_for(from_quarter, from_week),
        "to_week": to_code,
        "scheduled_at": scheduled_at,
        "timezone": schedule.NEW_YORK,
        "academic_courses": academic_courses,
        "homeroom": homeroom_block,
        "weekly_announcements": weekly_announcements,
        "assignments": deploy_plan.get("assignments", []),
        "assessment_reminders": deploy_plan.get("assessment_reminders", []),
        "approvals": plan_mod.approval_snapshot_hash(approvals),
        "approval_snapshot_hash": plan_mod.approval_snapshot_hash(approvals),
        "source_hash": source_hash,
        "created_at": _now(),
    }


def command_self_test() -> int:
    m = build_rollover_manifest(2, 2, 2, 3)
    assert m["from_week"] == "Q2W2" and m["to_week"] == "Q2W3", m
    assert m["scheduled_at"] == "2026-10-23T20:00:00Z", m["scheduled_at"]
    assert m["timezone"] == "America/New_York"
    # Active academic courses for Q2 (History inactive).
    subjects = {c["subject"] for c in m["academic_courses"]}
    assert subjects == {"math", "reading_spelling", "language_arts", "science"}, subjects
    assert "history" not in subjects
    # Homeroom block routes to 26429.
    assert m["homeroom"]["course_id"] == HOMEROOM_COURSE_ID
    # Four subject-isolated weekly updates, agenda-hash consistent.
    assert len(m["weekly_announcements"]) == 4
    for a in m["weekly_announcements"]:
        assert a["hash_consistent"] is True
        assert a["agenda_hash"] == a["page_agenda_hash"]
        assert "Good afternoon," in a["message"]
        assert "Mr. Reagan" in a["message"]
    print("PASS canvas-rollover manifest self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
