"""Change-detection engine.

Compares a current observation against the previous persisted snapshot and
produces structured ``SourceChangeEvent`` records. Every event carries a stable
``event_id`` derived from the underlying identity + old/new values, so repeated
polling of the same change yields the same identity (dedup upstream) and a
genuinely new change (different old/new) yields a new identity.

Change classifications (a superset of the required minimum).
"""
from __future__ import annotations

import hashlib
from typing import Any

from .models import Confidence, SourceChangeEvent
from . import snapshot as snap

# Pacing-side classifications.
CHANGE_LESSON = "lesson_changed"
CHANGE_CHAPTER = "chapter_changed"
CHANGE_HOMEWORK = "homework_changed"
CHANGE_CLASSWORK = "classwork_changed"
CHANGE_ASSESSMENT_DATE = "assessment_date_changed"
CHANGE_ASSESSMENT_IDENTITY = "assessment_identity_changed"
CHANGE_ASSESSMENT_ADDED = "assessment_added"
CHANGE_ASSESSMENT_REMOVED = "assessment_removed"
CHANGE_SOURCE_IDENTITY = "source_identity_changed"
CHANGE_SOURCE_STALE = "source_stale"

# Canvas-side classifications.
CHANGE_ASSIGNMENT_DUE = "assignment_due_changed"
CHANGE_ASSIGNMENT_MISSING = "assignment_missing"
CHANGE_ASSIGNMENT_PRESENT = "assignment_present_unexpectedly"
CHANGE_ANNOUNCEMENT = "announcement_changed"
CHANGE_REMINDER_MISSING = "reminder_missing"
CHANGE_REMINDER_DUPLICATED = "reminder_duplicated"
CHANGE_REMINDER_OBSOLETE = "reminder_obsolete"
CHANGE_PAGE_BODY = "page_body_changed"
CHANGE_FRONT_PAGE = "front_page_changed"
CHANGE_CANVAS_CONFLICT = "canvas_conflict"

REMINDER_TITLE_HINTS = ("reminder", "assessment", "test")


def stable_event_id(
    *,
    week_id: str,
    source: str,
    subject: str,
    classification: str,
    object_identity: str,
    old_value: str | None,
    new_value: str | None,
) -> str:
    """Deterministic, dedup-able event identity."""
    body = "|".join([
        str(week_id), str(source), str(subject), str(classification),
        str(object_identity), str(old_value), str(new_value),
    ])
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:20]


def _ev(
    *,
    week_id: str,
    source: str,
    subject: str,
    classification: str,
    object_type: str,
    object_identity: str,
    old_value: str | None,
    new_value: str | None,
    severity: str = "info",
    affected: list[str] | None = None,
    requires_approval: bool = True,
    live_stale: bool = False,
    family_comms: bool = False,
    source_identity: str = "",
) -> SourceChangeEvent:
    return SourceChangeEvent(
        source=source,
        subject=subject,
        object_type=object_type,
        old_value=old_value,
        new_value=new_value,
        classification=classification,
        object_identity=object_identity,
        source_identity=source_identity,
        week_id=week_id,
        severity=severity,
        affected_artifacts=affected or [],
        requires_teacher_approval=requires_approval,
        live_canvas_stale=live_stale,
        family_comms_affected=family_comms,
        event_id=stable_event_id(
            week_id=week_id, source=source, subject=subject,
            classification=classification, object_identity=object_identity,
            old_value=old_value, new_value=new_value,
        ),
    )


def _cell_key(subject: str, day: str) -> str:
    return f"{subject}|{day}"


def _diff_pacing_cell(
    *,
    week_id: str,
    subject: str,
    day: str,
    prev: dict[str, Any] | None,
    curr: dict[str, Any] | None,
    source_identity: str,
) -> list[SourceChangeEvent]:
    events: list[SourceChangeEvent] = []
    identity = _cell_key(subject, day)
    prev = prev or {}
    curr = curr or {}

    if prev and not curr:
        # Cell removed entirely.
        events.append(_ev(
            week_id=week_id, source="pacing", subject=subject,
            classification=CHANGE_LESSON, object_type="lesson", object_identity=identity,
            old_value=prev.get("lesson"), new_value=None, severity="medium",
            affected=[f"{subject.title()} weekly page"], requires_approval=True,
            source_identity=source_identity,
        ))
        return events

    for field, classification, object_type, label in (
        ("lesson", CHANGE_LESSON, "lesson", "lesson"),
        ("chapter", CHANGE_CHAPTER, "chapter", "chapter"),
    ):
        old = prev.get(field)
        new = curr.get(field)
        if (old or "") != (new or ""):
            events.append(_ev(
                week_id=week_id, source="pacing", subject=subject,
                classification=classification, object_type=object_type, object_identity=identity,
                old_value=old, new_value=new, severity="medium",
                affected=[f"{subject.title()} weekly page"], requires_approval=True,
                source_identity=source_identity,
            ))

    for field, classification, object_type, label in (
        ("homework", CHANGE_HOMEWORK, "homework", "homework"),
        ("classwork", CHANGE_CLASSWORK, "classwork", "classwork"),
    ):
        old = list(prev.get(field) or [])
        new = list(curr.get(field) or [])
        if old != new:
            events.append(_ev(
                week_id=week_id, source="pacing", subject=subject,
                classification=classification, object_type=object_type, object_identity=identity,
                old_value="; ".join(old) or None, new_value="; ".join(new) or None,
                severity="medium",
                affected=[f"{subject.title()} weekly page"],
                requires_approval=True, source_identity=source_identity,
            ))

    # Assessment comparison (date + identity).
    old_ass = prev.get("assessment")
    new_ass = curr.get("assessment")
    old_name = (old_ass or {}).get("name")
    new_name = (new_ass or {}).get("name")
    old_date = (old_ass or {}).get("date")
    new_date = (new_ass or {}).get("date")
    if old_ass and new_ass:
        if old_name != new_name:
            events.append(_ev(
                week_id=week_id, source="pacing", subject=subject,
                classification=CHANGE_ASSESSMENT_IDENTITY, object_type="assessment",
                object_identity=f"{identity}|{new_name or old_name}",
                old_value=old_name, new_value=new_name, severity="high",
                affected=[f"{subject.title()} weekly page",
                          f"{subject.title()} assessment assignment",
                          f"{subject.title()} first parent announcement",
                          f"{subject.title()} day-before reminder",
                          f"{subject.title()} weekly update"],
                requires_approval=True, live_stale=True, family_comms=True,
                source_identity=source_identity,
            ))
        elif old_date != new_date:
            events.append(_ev(
                week_id=week_id, source="pacing", subject=subject,
                classification=CHANGE_ASSESSMENT_DATE, object_type="assessment_date",
                object_identity=f"{identity}|{new_name or old_name}",
                old_value=old_date, new_value=new_date, severity="high",
                affected=[f"{subject.title()} weekly page",
                          f"{subject.title()} assessment assignment",
                          f"{subject.title()} first parent announcement",
                          f"{subject.title()} day-before reminder",
                          f"{subject.title()} weekly update"],
                requires_approval=True, live_stale=True, family_comms=True,
                source_identity=source_identity,
            ))
    elif old_ass and not new_ass:
        events.append(_ev(
            week_id=week_id, source="pacing", subject=subject,
            classification=CHANGE_ASSESSMENT_REMOVED, object_type="assessment",
            object_identity=f"{identity}|{old_name}", old_value=old_name, new_value=None,
            severity="high", affected=[f"{subject.title()} weekly page"],
            requires_approval=True, family_comms=True, source_identity=source_identity,
        ))
    elif new_ass and not old_ass:
        events.append(_ev(
            week_id=week_id, source="pacing", subject=subject,
            classification=CHANGE_ASSESSMENT_ADDED, object_type="assessment",
            object_identity=f"{identity}|{new_name}", old_value=None, new_value=new_name,
            severity="high",
            affected=[f"{subject.title()} weekly page",
                      f"{subject.title()} assessment assignment",
                      f"{subject.title()} first parent announcement",
                      f"{subject.title()} day-before reminder"],
            requires_approval=True, family_comms=True, source_identity=source_identity,
        ))

    return events


def _keyed(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        k = str(item.get(key) or "")
        if k:
            out[k] = item
    return out


def _diff_canvas_course(
    *,
    week_id: str,
    subject: str,
    prev: dict[str, Any] | None,
    curr: dict[str, Any] | None,
) -> list[SourceChangeEvent]:
    events: list[SourceChangeEvent] = []
    prev = prev or {}
    curr = curr or {}

    # Front page state.
    prev_fp = prev.get("front_page") or {}
    curr_fp = curr.get("front_page") or {}
    if prev_fp and curr_fp and (prev_fp.get("page_id") or prev_fp.get("title")) != (curr_fp.get("page_id") or curr_fp.get("title")):
        events.append(_ev(
            week_id=week_id, source="canvas", subject=subject,
            classification=CHANGE_FRONT_PAGE, object_type="front_page",
            object_identity=f"{subject}:front_page",
            old_value=str(prev_fp.get("page_id") or prev_fp.get("title")),
            new_value=str(curr_fp.get("page_id") or curr_fp.get("title")),
            severity="medium", affected=[f"{subject.title()} front page"],
            requires_approval=True, live_stale=False,
        ))

    # Pages: body-hash drift is a direct Canvas edit (conflict with approved plan).
    prev_pages = _keyed(prev.get("pages") or [], "page_id") or _keyed(prev.get("pages") or [], "title")
    curr_pages = _keyed(curr.get("pages") or [], "page_id") or _keyed(curr.get("pages") or [], "title")
    for pk, p_page in prev_pages.items():
        c_page = curr_pages.get(pk)
        if c_page is None:
            events.append(_ev(
                week_id=week_id, source="canvas", subject=subject,
                classification=CHANGE_CANVAS_CONFLICT, object_type="page",
                object_identity=f"{subject}:page:{pk}",
                old_value=pk, new_value=None, severity="medium",
                affected=[f"{subject.title()} weekly page"], requires_approval=True,
            ))
            continue
        if (p_page.get("body_hash") or "") != (c_page.get("body_hash") or ""):
            events.append(_ev(
                week_id=week_id, source="canvas", subject=subject,
                classification=CHANGE_PAGE_BODY, object_type="page",
                object_identity=f"{subject}:page:{pk}",
                old_value=p_page.get("body_hash"), new_value=c_page.get("body_hash"),
                severity="high", affected=[f"{subject.title()} weekly page"],
                requires_approval=True, live_stale=True,
            ))

    # Assignments.
    prev_asn = _keyed(prev.get("assignments") or [], "name")
    curr_asn = _keyed(curr.get("assignments") or [], "name")
    for name, p_a in prev_asn.items():
        c_a = curr_asn.get(name)
        if c_a is None:
            events.append(_ev(
                week_id=week_id, source="canvas", subject=subject,
                classification=CHANGE_ASSIGNMENT_MISSING, object_type="assignment",
                object_identity=f"{subject}:assignment:{name}",
                old_value=name, new_value=None, severity="high",
                affected=[f"{subject.title()} assignments"], requires_approval=True,
            ))
            continue
        if (p_a.get("due_at") or "") != (c_a.get("due_at") or ""):
            events.append(_ev(
                week_id=week_id, source="canvas", subject=subject,
                classification=CHANGE_ASSIGNMENT_DUE, object_type="assignment",
                object_identity=f"{subject}:assignment:{name}",
                old_value=p_a.get("due_at"), new_value=c_a.get("due_at"),
                severity="high", affected=[f"{subject.title()} assignments"],
                requires_approval=True, live_stale=True,
            ))
    for name in curr_asn.keys() - prev_asn.keys():
        events.append(_ev(
            week_id=week_id, source="canvas", subject=subject,
            classification=CHANGE_ASSIGNMENT_PRESENT, object_type="assignment",
            object_identity=f"{subject}:assignment:{name}",
            old_value=None, new_value=name, severity="medium",
            affected=[f"{subject.title()} assignments"], requires_approval=True,
        ))

    # Announcements.
    prev_ann = _keyed(prev.get("announcements") or [], "title")
    curr_ann = _keyed(curr.get("announcements") or [], "title")
    for title, p_a in prev_ann.items():
        c_a = curr_ann.get(title)
        if c_a is None:
            events.append(_ev(
                week_id=week_id, source="canvas", subject=subject,
                classification=CHANGE_ANNOUNCEMENT, object_type="announcement",
                object_identity=f"{subject}:announcement:{title}",
                old_value=title, new_value=None, severity="medium",
                affected=[f"{subject.title()} announcement"], requires_approval=True,
            ))
            continue
        if (p_a.get("message") or "") != (c_a.get("message") or "") or \
           (p_a.get("delayed_post_at") or "") != (c_a.get("delayed_post_at") or ""):
            events.append(_ev(
                week_id=week_id, source="canvas", subject=subject,
                classification=CHANGE_ANNOUNCEMENT, object_type="announcement",
                object_identity=f"{subject}:announcement:{title}",
                old_value=p_a.get("delayed_post_at") or p_a.get("posted_at"),
                new_value=c_a.get("delayed_post_at") or c_a.get("posted_at"),
                severity="medium", affected=[f"{subject.title()} announcement"],
                requires_approval=True, live_stale=True,
            ))

    return events


def _reminder_hint(title: str) -> bool:
    low = (title or "").lower()
    return any(hint in low for hint in REMINDER_TITLE_HINTS)


def detect_changes(prev: dict[str, Any], curr: dict[str, Any]) -> list[SourceChangeEvent]:
    """Compare two snapshots and return classified SourceChangeEvents."""
    events: list[SourceChangeEvent] = []
    week_id = curr.get("week_id") or prev.get("week_id") or ""
    source_identity = json_identity((curr.get("pacing") or {}).get("identity") or {})

    # Source identity change (pacing sheet identity changed).
    prev_identity = json_identity((prev.get("pacing") or {}).get("identity") or {})
    if prev_identity and source_identity and prev_identity != source_identity:
        events.append(_ev(
            week_id=week_id, source="pacing", subject="*",
            classification=CHANGE_SOURCE_IDENTITY, object_type="source_identity",
            object_identity="pacing:identity",
            old_value=prev_identity, new_value=source_identity, severity="high",
            affected=["all subjects"], requires_approval=True,
            source_identity=source_identity,
        ))

    # Source outage / staleness (non-destructive; never treated as deletion).
    for section in ("pacing", "canvas"):
        p_status = (prev.get(section) or {}).get("status", snap.SNAPSHOT_UNAVAILABLE)
        c_status = (curr.get(section) or {}).get("status", snap.SNAPSHOT_UNAVAILABLE)
        if c_status in (snap.SNAPSHOT_STALE, snap.SNAPSHOT_UNAVAILABLE) and p_status == snap.SNAPSHOT_OK:
            events.append(_ev(
                week_id=week_id, source=section, subject="*",
                classification=CHANGE_SOURCE_STALE, object_type="source_availability",
                object_identity=f"{section}:availability",
                old_value=p_status, new_value=c_status, severity="medium",
                affected=[], requires_approval=False, live_stale=False,
            ))

    # Pacing cell diffs.
    prev_cells = (prev.get("pacing") or {}).get("cells") or {}
    curr_cells = (curr.get("pacing") or {}).get("cells") or {}
    all_keys = set(prev_cells) | set(curr_cells)
    for key in sorted(all_keys):
        subject, _, day = key.partition("|")
        events.extend(_diff_pacing_cell(
            week_id=week_id, subject=subject, day=day,
            prev=prev_cells.get(key), curr=curr_cells.get(key),
            source_identity=source_identity,
        ))

    # Canvas course diffs.
    prev_courses = (prev.get("canvas") or {}).get("courses") or {}
    curr_courses = (curr.get("canvas") or {}).get("courses") or {}
    for subject in sorted(set(prev_courses) | set(curr_courses)):
        events.extend(_diff_canvas_course(
            week_id=week_id, subject=subject,
            prev=prev_courses.get(subject), curr=curr_courses.get(subject),
        ))

    # Reminder duplication (same reminder title twice in current Canvas).
    for subject, course in curr_courses.items():
        titles = [a.get("title") for a in (course.get("announcements") or []) if _reminder_hint(a.get("title") or "")]
        seen: dict[str, int] = {}
        for t in titles:
            seen[t] = seen.get(t, 0) + 1
        for t, count in seen.items():
            prev_titles = [a.get("title") for a in ((prev_courses.get(subject) or {}).get("announcements") or [])]
            if count >= 2 and prev_titles.count(t) < 2:
                events.append(_ev(
                    week_id=week_id, source="canvas", subject=subject,
                    classification=CHANGE_REMINDER_DUPLICATED, object_type="reminder",
                    object_identity=f"{subject}:reminder:{t}",
                    old_value=None, new_value=t, severity="high",
                    affected=[f"{subject.title()} day-before reminder"], requires_approval=True,
                ))

    # Reminder missing (present before, gone now).
    for subject in sorted(set(prev_courses) | set(curr_courses)):
        prev_titles = [a.get("title") for a in ((prev_courses.get(subject) or {}).get("announcements") or []) if _reminder_hint(a.get("title") or "")]
        curr_titles = [a.get("title") for a in ((curr_courses.get(subject) or {}).get("announcements") or []) if _reminder_hint(a.get("title") or "")]
        for t in prev_titles:
            if t not in curr_titles:
                events.append(_ev(
                    week_id=week_id, source="canvas", subject=subject,
                    classification=CHANGE_REMINDER_MISSING, object_type="reminder",
                    object_identity=f"{subject}:reminder:{t}",
                    old_value=t, new_value=None, severity="high",
                    affected=[f"{subject.title()} day-before reminder"], requires_approval=True,
                ))

    # Reminder scheduled for an obsolete date (cross-reference current pacing assessments).
    assessment_dates = set()
    for cell in curr_cells.values():
        ass = cell.get("assessment")
        if ass and ass.get("date"):
            assessment_dates.add(str(ass.get("date")))
    for subject, course in curr_courses.items():
        for a in (course.get("announcements") or []):
            if not _reminder_hint(a.get("title") or ""):
                continue
            scheduled = str(a.get("delayed_post_at") or "")
            if scheduled and assessment_dates and scheduled[:10] not in assessment_dates and \
               not any(d.startswith(scheduled[:10]) for d in assessment_dates):
                events.append(_ev(
                    week_id=week_id, source="canvas", subject=subject,
                    classification=CHANGE_REMINDER_OBSOLETE, object_type="reminder",
                    object_identity=f"{subject}:reminder:{a.get('title')}",
                    old_value=scheduled, new_value=sorted(assessment_dates) or None,
                    severity="high",
                    affected=[f"{subject.title()} day-before reminder"], requires_approval=True,
                    live_stale=True,
                ))

    return events


def json_identity(identity: dict[str, Any]) -> str:
    if not identity:
        return ""
    parts = [f"{k}={identity.get(k)}" for k in sorted(identity) if identity.get(k)]
    return "; ".join(parts)


def command_self_test() -> int:
    base = snap.blank_snapshot(2, 3, "Q2W3")
    base["pacing"]["status"] = snap.SNAPSHOT_OK
    base["pacing"]["cells"] = {
        "math|Thursday": {"lesson": "WA8", "chapter": None, "classwork": ["WA8"],
                          "homework": [], "assessment": {"name": "Written Assessment 8", "date": "2026-11-05", "day": "Thursday"}},
    }
    cur = json_loads(json_dumps(base))
    cur["pacing"]["cells"]["math|Thursday"]["assessment"]["date"] = "2026-11-06"
    events = detect_changes(base, cur)
    kinds = {e.classification for e in events}
    assert CHANGE_ASSESSMENT_DATE in kinds, kinds
    ev = next(e for e in events if e.classification == CHANGE_ASSESSMENT_DATE)
    assert ev.event_id and ev.family_comms_affected and ev.live_canvas_stale
    # Stable id: same change -> same id.
    again = detect_changes(base, cur)
    assert again[0].event_id == ev.event_id
    print("PASS weekly-planner-agent change-detection self-test")
    return 0


def json_dumps(obj: Any) -> str:
    import json as _json
    return _json.dumps(obj, sort_keys=True, ensure_ascii=False)


def json_loads(text: str) -> Any:
    import json as _json
    return _json.loads(text)


if __name__ == "__main__":
    raise SystemExit(command_self_test())
