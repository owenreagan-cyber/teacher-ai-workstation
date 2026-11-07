"""Reusable assessment-announcement engine (deterministic; draft-only).

Builds family/student-facing assessment announcements for the assessments that
the canonical pacing + owner decisions actually support:

* Reading Mastery Test N       (one artifact)
* Fluency Checkout N           (a separate artifact, never merged)
* Spelling Test N              (verified cumulative list when available)
* Science unit/chapter test     (only when explicitly supported; owner override
                                 may replace a stale canonical unit name)

Every artifact is a separate preview object with its own title, course,
assessment date, source references, provenance, draft hash, approval
requirement, and duplicate identity. Nothing is posted; nothing is approved
automatically. These artifacts are intentionally separate from the four weekly
agenda-update announcements (``drafts/announcements.json``).

Canonical constraints enforced here:

* Reading announcements may include the test number, date, teacher-entered
  coverage range, and approved general fluency language. They MUST NOT expose
  the Checkout passage title or page location.
* Never invent story titles, vocabulary lists, skills, or comprehension items.
  Reading Test preparation comes from Owen's explicit workbook/story instruction.
* Spelling announcements must never claim a word list that is not verified.
* Science announcements only exist for explicit test/quiz evidence or an
  auditable owner override that preserves both source and owner values.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from scripts.canvas_llm_phase3 import constants as P3
from scripts.canvas_llm_phase3 import pacing_announcement as pa
from scripts.canvas_llm_phase3 import pacing_reading as prd
from scripts.canvas_llm_phase3 import pacing_translation as pt

from . import constants as C
from . import reminders as rem

REPO_ROOT = Path(P3.REPO_ROOT)

CHECKOUT_MAP_PATH = REPO_ROOT / "config" / "curriculum" / "reading" / "reading-mastery-4" / "checkout-passage-map.json"
COMPREHENSION_MAP_PATH = REPO_ROOT / "config" / "curriculum" / "reading" / "reading-mastery-4" / "comprehension-location-map.json"
SPELLING_MAP_PATH = REPO_ROOT / "config" / "curriculum" / "spelling" / "cumulative-test-word-lists.json"
READING_PATTERNS_PATH = REPO_ROOT / "config" / "curriculum" / "canvas" / "reading-spelling-work-patterns-2026-2027.json"
ANNOUNCEMENT_POLICY_PATH = REPO_ROOT / "config" / "curriculum" / "canvas" / "assessment-announcement-policy-2026-2027.json"
ASSIGNMENT_ROUTING_PATH = REPO_ROOT / "config" / "curriculum" / "canvas" / "assignment-routing-contract-2026-2027.json"

SCIENCE_COURSE_ID = 28166
READING_SPELLING_COURSE_ID = 26442


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    try:
        return _sha(path.read_text(encoding="utf-8"))
    except OSError:
        return ""


def _display_date(iso: str) -> str:
    return rem._display_date(iso)


def _draft_hash(item: dict[str, Any]) -> str:
    payload = {
        "title": item.get("title", ""),
        "course": item.get("course", ""),
        "course_id": item.get("course_id"),
        "assessment_date": item.get("assessment_date", ""),
        "body": item.get("body", ""),
    }
    return _sha(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def _base(
    *,
    family: str,
    type_: str,
    subject: str,
    course: str,
    course_id: int,
    title: str,
    assessment_title: str,
    assessment_date: str,
    body: str,
    preparation: list[str],
    source_refs: list[str],
    source_hashes: dict[str, str],
    provenance: dict[str, Any],
    content_status: str = "READY",
    blocked_sections: list[str] | None = None,
    source_event: str = "",
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "artifact_type": "assessment_announcement",
        "family": family,
        "type": type_,
        "subject": subject,
        "course": course,
        "course_id": course_id,
        "title": title,
        "assessment_title": assessment_title,
        "assessment_date": assessment_date,
        "date_display": _display_date(assessment_date),
        "greeting": "Good afternoon,",
        "body": body,
        "preparation": preparation,
        "source_refs": source_refs,
        "source_hashes": source_hashes,
        "provenance": provenance,
        "content_status": content_status,
        "blocked_sections": list(blocked_sections or []),
        "requires_teacher_approval": True,
        "approval_state": "PENDING",
        "preview_only": True,
        "duplicate_identity": pa.announcement_identity(
            course, family, source_event or assessment_title, assessment_date, "ANNOUNCEMENT"
        ),
    }
    item["draft_hash"] = _draft_hash(item)
    item["approval_record"] = {
        "granularity": "assessment_reminder",
        "bundle_subject": subject,
        "state": "PENDING",
        "draft_hash": item["draft_hash"],
        "source_hash": (source_hashes or {}).get("pacing_source", ""),
        "approved_by": None,
    }
    return item


# --------------------------------------------------------------------------- #
# Reading Mastery Test + Fluency Checkout
# --------------------------------------------------------------------------- #


def _reading_mastery_announcement(
    *, number: int, assessment_date: str, lesson_range: tuple[int, int] | None,
    source_hash: str,
) -> dict[str, Any]:
    lo, hi = lesson_range if lesson_range else (0, 0)
    range_text = f"Lessons {lo}\u2013{hi}" if lo and hi else "the recent Reading Mastery lessons"
    preparation_sentence = (
        f"To prepare for Reading Mastery Test {number}, students should review their Reading Workbook pages "
        f"and revisit the stories from {range_text}. They should take time to reread the stories and review "
        "the work practiced throughout these lessons."
    )
    body = (
        "Good afternoon,\n\n"
        f"Reading Mastery Test {number} will be given on {_display_date(assessment_date)}.\n\n"
        f"{preparation_sentence}\n\n"
        "Thank you for your continued support at home!\n\n"
        "Owen Reagan"
    )
    return _base(
        family="reading_assessment",
        type_="reading_mastery_test",
        subject="reading_spelling",
        course="Reading/Spelling",
        course_id=READING_SPELLING_COURSE_ID,
        title=f"Reading Mastery Test {number} \u2014 {_display_date(assessment_date)}",
        assessment_title=f"Reading Mastery Test {number}",
        assessment_date=assessment_date,
        body=body,
        preparation=[
            "Review Reading Workbook pages.",
            f"Revisit and reread the stories from {range_text}.",
            "Review the work practiced throughout those lessons.",
        ],
        source_refs=[
            "config/curriculum/reading/reading-mastery-4/checkout-passage-map.json#lessonRange",
            "config/curriculum/reading/reading-mastery-4/comprehension-location-map.json#lessons",
            "config/curriculum/canvas/reading-spelling-work-patterns-2026-2027.json#testToCheckout",
        ],
        source_hashes={
            "checkout_map": _file_hash(CHECKOUT_MAP_PATH),
            "comprehension_map": _file_hash(COMPREHENSION_MAP_PATH),
            "reading_patterns": _file_hash(READING_PATTERNS_PATH),
            "pacing_source": source_hash,
        },
        provenance={
            "authority": "OWNER_INSTRUCTION + PACING_SOURCE",
            "owner_instruction": preparation_sentence,
            "separation_instruction": "Two separate Reading assessment announcements (Mastery Test and Fluency Checkout), not one combined announcement.",
            "coverage_source": "checkout-passage-map lessonRange for the matching Checkout",
            "announcement_rule": "May include test number, date, coverage range, and approved general fluency language; must not expose the Checkout passage title or page location.",
        },
        content_status="READY",
        blocked_sections=[],
        source_event=f"Reading Mastery Test {number}",
    )


def _fluency_checkout_announcement(
    *, number: int, assessment_date: str, fluency: dict[str, Any] | None, source_hash: str,
) -> dict[str, Any]:
    wpm = (fluency or {}).get("wpm")
    max_errors = (fluency or {}).get("maxErrors")
    practice = (
        f"Students should practice reading approximately {wpm} words in under one minute "
        f"with no more than {max_errors} errors."
        if wpm is not None and max_errors is not None
        else "Students should practice reading aloud with accuracy, expression, and a steady pace."
    )
    body = (
        "Good afternoon,\n\n"
        f"Fluency Checkout {number} will be given on {_display_date(assessment_date)}. "
        "Students will read a short passage aloud so we can check fluency: accuracy, pace, and expression.\n\n"
        f"{practice}\n\n"
        "Thank you for your continued support at home!\n\n"
        "Owen Reagan"
    )
    readiness = "READY" if wpm is not None and max_errors is not None else "PARTIAL"
    return _base(
        family="reading_assessment",
        type_="fluency_checkout",
        subject="reading_spelling",
        course="Reading/Spelling",
        course_id=READING_SPELLING_COURSE_ID,
        title=f"Fluency Checkout {number} \u2014 {_display_date(assessment_date)}",
        assessment_title=f"Fluency Checkout {number}",
        assessment_date=assessment_date,
        body=body,
        preparation=[practice],
        source_refs=[
            "config/curriculum/reading/reading-mastery-4/checkout-passage-map.json#checkouts",
            "config/curriculum/canvas/assessment-announcement-policy-2026-2027.json#readingAssessment",
        ],
        source_hashes={
            "checkout_map": _file_hash(CHECKOUT_MAP_PATH),
            "announcement_policy": _file_hash(ANNOUNCEMENT_POLICY_PATH),
            "pacing_source": source_hash,
        },
        provenance={
            "authority": "OWNER_POLICY",
            "fluency_targets": "Checkouts 1-7: 100 WPM / max 2 errors (OWNER_POLICY)",
            "privacy": "No Checkout passage title or page location is included in this announcement.",
        },
        content_status=readiness,
        blocked_sections=[] if readiness == "READY" else ["Verified fluency WPM/error target missing for this Checkout."],
        source_event=f"Fluency Checkout {number}",
    )


# --------------------------------------------------------------------------- #
# Spelling Test
# --------------------------------------------------------------------------- #


def _spelling_announcement(*, number: int, assessment_date: str, source_hash: str) -> dict[str, Any]:
    reminder = rem.draft_spelling_reminders({
        "week": {"code": ""},
        "days": {"Friday": {"date": assessment_date, "subjects": {"spelling": {"raw": f"Test {number}"}}}},
    })[0]
    words = reminder.get("word_list") or []
    focus = reminder.get("focus_words") or []
    list_verified = bool(reminder.get("word_list_status") == "VERIFIED")
    preparation = [
        f"Study the spelling word lists through Lesson {number}.",
        "Review the full cumulative list, not only the most recent lesson.",
    ]
    if list_verified and focus:
        preparation.append("Focus words: " + ", ".join(focus) + ".")
    return _base(
        family="spelling_assessment",
        type_="spelling_test",
        subject="reading_spelling",
        course="Reading/Spelling",
        course_id=READING_SPELLING_COURSE_ID,
        title=f"Spelling Test {number} \u2014 {_display_date(assessment_date)}",
        assessment_title=f"Spelling Test {number}",
        assessment_date=assessment_date,
        body=reminder["body"],
        preparation=preparation,
        source_refs=[
            "config/curriculum/spelling/cumulative-test-word-lists.json",
            "config/curriculum/canvas/assessment-announcement-policy-2026-2027.json#spellingAssessment",
        ],
        source_hashes={
            "spelling_map": _file_hash(SPELLING_MAP_PATH),
            "announcement_policy": _file_hash(ANNOUNCEMENT_POLICY_PATH),
            "pacing_source": source_hash,
        },
        provenance={
            "authority": "OWNER_POLICY + OWNER_INSTRUCTION",
            "owner_instruction": f"Students should study the spelling word lists through Lesson {number}.",
            "word_list_status": reminder.get("word_list_status", "UNVERIFIED"),
            "word_list_lessons_covered": reminder.get("word_list_lessons_covered", ""),
            "word_count": len(words),
        },
        content_status="READY" if list_verified else "PARTIAL",
        blocked_sections=[] if list_verified else [
            "Verified cumulative word list for this test number is not present in the authorized spelling source."
        ],
        source_event=f"Spelling Test {number}",
    )


# --------------------------------------------------------------------------- #
# Science assessment (owner override)
# --------------------------------------------------------------------------- #


def _science_announcement(
    *, override: dict[str, Any], assessment_date: str, source_hash: str,
) -> dict[str, Any]:
    owner_value = override.get("owner_value") or "Science Unit Test"
    open_book = bool(override.get("open_book", True))
    open_notes = bool(override.get("open_notes", True))
    test_format = " / ".join(
        part for part in ("Open Book" if open_book else "", "Open Notes" if open_notes else "") if part
    ) or "Teacher-directed format"
    body = (
        "Good afternoon,\n\n"
        f"The {owner_value} will be given on {_display_date(assessment_date)}. "
        f"This test is {test_format}. Students may use their book and notes during the test.\n\n"
        "Students should review the unit materials and class notes we have completed together. "
        "Looking back over the unit work is the best way to prepare.\n\n"
        "Thank you for your continued support at home!\n\n"
        "Owen Reagan"
    )
    return _base(
        family="science_assessment",
        type_="science_unit_test",
        subject="science",
        course="Science",
        course_id=SCIENCE_COURSE_ID,
        title=f"Science: {owner_value} \u2014 {_display_date(assessment_date)}",
        assessment_title=owner_value,
        assessment_date=assessment_date,
        body=body,
        preparation=[
            f"Review the {owner_value.replace(' Unit Test', '')} unit materials and class notes.",
            f"Test format: {test_format}.",
        ],
        source_refs=[
            "owner-decisions.json#science-assessment-override",
            "config/curriculum/canvas/assignment-routing-contract-2026-2027.json#science",
        ],
        source_hashes={
            "assignment_routing": _file_hash(ASSIGNMENT_ROUTING_PATH),
            "pacing_source": source_hash,
        },
        provenance={
            "authority": "OWNER_INSTRUCTION",
            "source_value": override.get("source_value", ""),
            "owner_value": owner_value,
            "reason": override.get("reason", ""),
            "acknowledgement": override.get("acknowledgement", ""),
            "decision_id": override.get("decision_id", ""),
            "recorded_at": override.get("recorded_at", ""),
            "note": "The original pacing snapshot is preserved unchanged; this announcement consumes the auditable owner decision.",
        },
        content_status="READY",
        source_event=owner_value,
    )


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def draft_assessment_announcements(
    week: dict[str, Any],
    *,
    source_hash: str = "",
    decisions: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Draft every supported assessment announcement for one week."""
    events = pa.resolve_assessment_facts(week)
    out: list[dict[str, Any]] = []

    science_override = None
    for decision in decisions or []:
        if not decision.get("active", True):
            continue
        if decision.get("kind") == "assessment_override" and decision.get("subject") == "science":
            science_override = decision
            break

    for event in events:
        family = event.get("family")
        assessment_date = event.get("assessmentDate", "")
        if family == "reading_assessment":
            number = None
            for assignment in event.get("assignments") or []:
                if assignment and assignment.get("kind") == "mastery_test":
                    number = assignment.get("number")
            if number is None:
                continue
            checkout = prd.resolve_checkout(number) or {}
            lesson_range = None
            mapped = prd.load_checkout_map().get("checkouts", {}).get(str(number), {})
            if mapped.get("lessonRange"):
                lesson_range = (mapped["lessonRange"]["start"], mapped["lessonRange"]["end"])
            out.append(_reading_mastery_announcement(
                number=number, assessment_date=assessment_date,
                lesson_range=lesson_range, source_hash=source_hash,
            ))
            checkout_exists = any(
                a and a.get("kind") == "fluency_checkout" for a in (event.get("assignments") or [])
            )
            if checkout_exists:
                out.append(_fluency_checkout_announcement(
                    number=number, assessment_date=assessment_date,
                    fluency=checkout.get("fluency"), source_hash=source_hash,
                ))
        elif family == "spelling_assessment":
            number = None
            for assignment in event.get("assignments") or []:
                if assignment and assignment.get("kind") == "spelling_test":
                    number = assignment.get("number")
            if number is None:
                continue
            out.append(_spelling_announcement(
                number=number, assessment_date=assessment_date, source_hash=source_hash,
            ))
        elif family == "science_assessment" and science_override is not None:
            out.append(_science_announcement(
                override=science_override,
                assessment_date=science_override.get("date") or assessment_date,
                source_hash=source_hash,
            ))

    # Deterministic order: by date, then title.
    out.sort(key=lambda item: (item.get("assessment_date", ""), item.get("title", "")))
    return out


def science_assignment_proposal(
    week: dict[str, Any], override: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Build the owner-directed Science assessment assignment proposal.

    Only produced when an auditable owner decision exists; the Science course
    remains manual-only otherwise. Routing comes from the canonical assignment
    routing contract (``science.chapter_test -> Assignments``).
    """
    if not override or not override.get("active", True):
        return None
    due_date = override.get("date") or ""
    if not due_date:
        due_date = _science_assessment_date(week)
    if not due_date:
        return None
    owner_value = override.get("owner_value") or "Science Unit Test"
    open_book = bool(override.get("open_book", True))
    open_notes = bool(override.get("open_notes", True))
    test_format = " / ".join(
        part for part in ("Open Book" if open_book else "", "Open Notes" if open_notes else "") if part
    ) or "Teacher-directed format"
    description = (
        f"{test_format}. Students may use their book and notes during the test."
        if open_book and open_notes else f"{test_format}."
    )
    return {
        "course": "science",
        "course_id": SCIENCE_COURSE_ID,
        "title": f"Science: {owner_value}",
        "assignment_group": "Assignments",
        "assignment_group_source": "config/curriculum/canvas/assignment-routing-contract-2026-2027.json#science.routing.chapter_test",
        "due_date": due_date,
        "points_possible": 100,
        "grading_type": "percent",
        "submission_types": "on_paper",
        "omit_from_final_grade": False,
        "description": description,
        "student_instructions": description,
        "authority": "OWNER_POLICY",
        "source_reason": "OWNER_INSTRUCTION",
        "owner_decision_id": override.get("decision_id", ""),
        "provenance": {
            "source_value": override.get("source_value", ""),
            "owner_value": owner_value,
            "reason": override.get("reason", ""),
            "acknowledgement": override.get("acknowledgement", ""),
        },
        "preview_only": True,
    }


def _science_assessment_date(week: dict[str, Any]) -> str:
    for weekday in C.WEEKDAYS:
        day = (week.get("days") or {}).get(weekday, {})
        raw = (day.get("subjects", {}).get("science", {}) or {}).get("raw", "")
        if not raw:
            continue
        unit = pt.resolve_science_unit_name(pt.load_config(), (week.get("unitContext") or {}).get("science"))
        cell = pt.translate_science_cell(raw, unit)
        if cell.get("assessment"):
            return day.get("date", "")
    return ""


MATH_COURSE_ID = 26404
LANGUAGE_ARTS_COURSE_ID = 28171


def _matching_decision(
    decisions: list[dict[str, Any]] | None,
    *,
    subject: str,
    date_value: str,
    kind: str | None = None,
) -> dict[str, Any] | None:
    found = None
    for decision in decisions or []:
        if not decision.get("active", True):
            continue
        if decision.get("subject") != subject:
            continue
        if kind is not None and decision.get("kind") != kind:
            continue
        if decision.get("date") and date_value and decision.get("date") != date_value:
            continue
        found = decision
    return found


def _mark_duplicate_identities(items: list[dict[str, Any]]) -> None:
    counts: dict[str, int] = {}
    for item in items:
        identity = item.get("duplicate_identity") or ""
        counts[identity] = counts.get(identity, 0) + 1
    for item in items:
        identity = item.get("duplicate_identity") or ""
        if identity and counts.get(identity, 0) > 1:
            item["duplicate_status"] = "AMBIGUOUS"
            item["schedule_state"] = pa.BLOCKED
            item["scheduled"] = False
            item["delayed_post_at"] = None
            item["publication_blocked"] = True
            item["blocked_sections"] = list(item.get("blocked_sections") or []) + [
                "announcement identity is ambiguous",
            ]
        else:
            item["duplicate_status"] = "UNIQUE"


def _notice_draft_hash(item: dict[str, Any]) -> str:
    payload = {
        "title": item.get("title", ""),
        "course_id": item.get("course_id"),
        "assessment_date": item.get("assessment_date", ""),
        "notice_type": item.get("notice_type", ""),
        "body": item.get("body", ""),
        "proposed_post_date": item.get("proposed_post_date", ""),
        "delayed_post_at": item.get("delayed_post_at") or "",
    }
    return _sha(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def _finish_notice(item: dict[str, Any], *, source_hash: str) -> dict[str, Any]:
    item["draft_hash"] = _notice_draft_hash(item)
    item["approval_state"] = "PENDING"
    item["preview_only"] = True
    item["requires_teacher_approval"] = True
    item["approval_record"] = {
        "granularity": "assessment_reminder",
        "bundle_subject": item.get("subject", ""),
        "state": "PENDING",
        "draft_hash": item["draft_hash"],
        "source_hash": source_hash,
        "approved_by": None,
    }
    return item


def _verified_resource(decision: dict[str, Any] | None, *, role: str) -> dict[str, Any] | None:
    for resource in (decision or {}).get("resources") or []:
        if resource.get("role") == role:
            return resource
    return None


def _resource_blocks(
    resource: dict[str, Any] | None, *, label: str, require_metadata: bool = False,
) -> list[str]:
    if not resource or not resource.get("verified") or not resource.get("file_id") or not resource.get("url"):
        return [f"{label} is not a verified owner-supplied Canvas resource"]
    if str(resource.get("file_id")) not in str(resource.get("url")):
        return [f"{label} URL does not reference file {resource.get('file_id')}"]
    if require_metadata and resource.get("source") != "CANVAS_FILE_METADATA":
        return [f"{label} URL was not read from Canvas file metadata"]
    return []


def _math_notice_body(
    *,
    notice_type: str,
    date_display: str,
    written_title: str,
    fact_title: str,
    fact_count: int | None,
    power_up: str | None,
    resource: dict[str, Any] | None,
) -> str:
    if notice_type == "FIRST_NOTICE":
        lead = f"Students will take {written_title} and {fact_title} on {date_display}."
    else:
        lead = f"This is a reminder that {written_title} and {fact_title} are {date_display}."
    lines = [
        "Good afternoon,",
        "",
        lead,
        "",
        f"{written_title} and {fact_title} will both be given {date_display}.",
    ]
    if fact_count:
        lines.append(f"{fact_title} covers {fact_count} multiplication facts.")
    if power_up:
        lines.append(f"Students should practice Power Up {power_up}.")
    if resource and resource.get("url"):
        name = resource.get("display_name") or f"Power Up {power_up}"
        lines.append(f"{name}: {resource['url']}")
    lines.extend(["", "Thank you for your continued support at home!", "", "Owen Reagan"])
    return "\n".join(lines)


def _language_arts_notice_body(
    *,
    notice_type: str,
    title: str,
    date_display: str,
    preparation: list[str],
    resources: list[dict[str, Any]],
) -> str:
    if notice_type == "FIRST_NOTICE":
        lead = (
            "I hope you are having a wonderful weekend! I wanted to send a quick reminder that "
            f"we are having our {title} on {date_display}."
        )
    else:
        lead = (
            f"Our {title} will take place {date_display}. "
            "Please review the following material to prepare:"
        )
    lines = ["Good afternoon,", "", lead, ""]
    lines.extend(preparation)
    verified = [resource for resource in resources if resource.get("url")]
    if verified:
        lines.append("")
        lines.append("Practice Resources")
        for resource in verified:
            label = resource.get("label") or resource.get("display_name") or "Practice resource"
            lines.append(f"{label}: {resource['url']}")
    lines.extend(["", "Thank you for your continued support!", "", "Owen Reagan"])
    return "\n".join(lines)


def _apply_owner_notice_time(
    timing: dict[str, Any],
    *,
    proposed: str,
    config: dict[str, Any],
    now: datetime | None,
    owner_time: str | None,
) -> dict[str, Any]:
    """Apply an owner time only to a notice that is not already future-scheduled.

    A future policy time is preserved. A time that fails validation blocks the
    notice instead of being invented or backdated.
    """
    if timing.get("schedule_state") == pa.FUTURE_SCHEDULED and timing.get("delayed_post_at"):
        return timing
    if not owner_time:
        return timing
    try:
        return pa.classify_notice_schedule(proposed, config, now=now, owner_selected_at=owner_time)
    except ValueError as exc:
        return {
            **timing,
            "schedule_state": pa.BLOCKED,
            "scheduled": False,
            "delayed_post_at": None,
            "schedule_error": str(exc),
        }


def _math_notices(
    event: dict[str, Any],
    *,
    decision: dict[str, Any] | None,
    source_hash: str,
    config: dict[str, Any],
    now: datetime | None,
    notice_times: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    written = next((a for a in event.get("assignments") or [] if a and a.get("kind") == "written_assessment"), None)
    fact = next((a for a in event.get("assignments") or [] if a and a.get("kind") == "fact_assessment"), None)
    if written is None or fact is None:
        return []
    assessment_date = event.get("assessmentDate") or ""
    number = fact.get("number")
    mapped = rem.resolve_fact_test(int(number)) if number is not None else None
    power_up = (mapped or {}).get("powerUpCode")
    written_title = (decision or {}).get("written_title") or f"Cumulative Test {written.get('number')}"
    fact_title = (decision or {}).get("fact_title") or f"Fact Test {fact.get('number')}"
    fact_count = (decision or {}).get("fact_count")
    resource = _verified_resource(decision, role="power_up")
    blocks = []
    if mapped is None or not power_up:
        blocks.append("Fact Test practice map has no Power Up for this assessment")
    elif decision and decision.get("power_up") and str(decision.get("power_up")).upper() not in {
        str(power_up).upper(), f"POWER UP {str(power_up).upper()}",
    }:
        blocks.append("owner Power Up does not match the canonical fact-test practice map")
    blocks.extend(_resource_blocks(
        resource, label=f"Power Up {power_up or ''}", require_metadata=True,
    ))
    if not fact_count:
        blocks.append("owner-confirmed fact count is missing")
    source_event = pa.source_event_label(event)
    schedule = pa.schedule_notices(assessment_date, config)
    notices = []
    for notice_type, proposed in (("FIRST_NOTICE", schedule["firstNotice"]), ("REMINDER", schedule["reminder"])):
        identity = pa.announcement_identity(
            "Math", "math_assessment", source_event, assessment_date, notice_type,
        )
        timing = pa.classify_notice_schedule(proposed, config, now=now)
        timing = _apply_owner_notice_time(
            timing, proposed=proposed, config=config, now=now,
            owner_time=(notice_times or {}).get(identity),
        )
        if blocks:
            timing = {
                **timing,
                "schedule_state": pa.BLOCKED,
                "scheduled": False,
                "delayed_post_at": None,
            }
        title = (
            f"Math {written_title} and {fact_title}"
            if notice_type == "FIRST_NOTICE"
            else f"Math Assessment Reminder — {_month_day(assessment_date)}"
        )
        body = _math_notice_body(
            notice_type=notice_type,
            date_display=_display_date(assessment_date),
            written_title=written_title,
            fact_title=fact_title,
            fact_count=int(fact_count) if fact_count else None,
            power_up=power_up,
            resource=resource if not blocks else None,
        )
        item = {
            "artifact_type": "assessment_announcement",
            "family": "math_assessment",
            "type": "math_assessment",
            "notice_type": notice_type,
            "subject": "math",
            "course": "Math",
            "course_id": MATH_COURSE_ID,
            "title": title,
            "assessment_title": f"{written_title} and {fact_title}",
            "assessment_date": assessment_date,
            "date_display": _display_date(assessment_date),
            "body": body,
            "message": body,
            "preparation": [
                line for line in (
                    f"{fact_title} covers {fact_count} multiplication facts." if fact_count else "",
                    f"Students should practice Power Up {power_up}." if power_up else "",
                ) if line
            ],
            "fact_packet": {
                "assessmentDate": assessment_date,
                "assessments": [written_title, fact_title],
                "factCount": fact_count,
                "powerUp": power_up,
                "resourceFileId": None if blocks else (resource or {}).get("file_id"),
                "sourceHash": source_hash,
            },
            "source_refs": [
                "config/curriculum/math/saxon-math-5/fact-test-practice-map.json",
                "config/curriculum/canvas/assessment-announcement-policy-2026-2027.json#twoNoticePolicy",
                "owner-decisions.json#semantic_interpretation",
            ],
            "source_hashes": {"pacing_source": source_hash, "announcement_policy": _file_hash(ANNOUNCEMENT_POLICY_PATH)},
            "source_hash": source_hash,
            "provenance": {
                "authority": "OWNER_INSTRUCTION",
                "source_value": (decision or {}).get("source_value", ""),
                "owner_value": (decision or {}).get("owner_value", ""),
                "decision_id": (decision or {}).get("decision_id", ""),
            },
            "content_status": "PARTIAL" if blocks else "READY",
            "blocked_sections": blocks,
            "publication_blocked": bool(blocks),
            "duplicate_identity": identity,
            "schedule_warnings": schedule.get("warnings") or [],
            **timing,
        }
        notices.append(_finish_notice(item, source_hash=source_hash))
    return notices


def _month_day(iso: str) -> str:
    if not iso:
        return ""
    value = date.fromisoformat(iso)
    return f"{value.strftime('%B')} {value.day}"


def _language_arts_notices(
    event: dict[str, Any],
    *,
    decision: dict[str, Any] | None,
    source_hash: str,
    config: dict[str, Any],
    now: datetime | None,
    notice_times: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    assignment = next((a for a in event.get("assignments") or [] if a and a.get("kind") == "chapter_test"), None)
    if assignment is None:
        return []
    assessment_date = event.get("assessmentDate") or ""
    chapter = assignment.get("number")
    assessment_name = (decision or {}).get("assessment_title") or f"Chapter {chapter} Test"
    preparation = [str(line) for line in ((decision or {}).get("preparation") or []) if str(line).strip()]
    resources = [item for item in ((decision or {}).get("resources") or []) if item.get("role") == "practice"]
    blocks: list[str] = []
    if not preparation:
        blocks.append("owner-supplied Chapter review content is missing")
    if len([item for item in resources if item.get("verified") and item.get("file_id") and item.get("url")]) < 2:
        blocks.append("both verified Language Arts practice resources are required")
    source_event = pa.source_event_label(event)
    schedule = pa.schedule_notices(assessment_date, config)
    notices = []
    for notice_type, proposed in (("FIRST_NOTICE", schedule["firstNotice"]), ("REMINDER", schedule["reminder"])):
        identity = pa.announcement_identity(
            "Language Arts", "language_arts_assessment", source_event, assessment_date, notice_type,
        )
        timing = pa.classify_notice_schedule(proposed, config, now=now)
        timing = _apply_owner_notice_time(
            timing, proposed=proposed, config=config, now=now,
            owner_time=(notice_times or {}).get(identity),
        )
        if blocks:
            timing = {**timing, "schedule_state": pa.BLOCKED, "scheduled": False, "delayed_post_at": None}
        title = assessment_name if notice_type == "FIRST_NOTICE" else f"Reminder — {assessment_name}"
        body = _language_arts_notice_body(
            notice_type=notice_type,
            title=assessment_name,
            date_display=_display_date(assessment_date),
            preparation=preparation,
            resources=resources if not blocks else [],
        )
        item = {
            "artifact_type": "assessment_announcement",
            "family": "language_arts_assessment",
            "type": "language_arts_assessment",
            "notice_type": notice_type,
            "subject": "language_arts",
            "course": "Language Arts",
            "course_id": LANGUAGE_ARTS_COURSE_ID,
            "title": title,
            "assessment_title": assessment_name,
            "assessment_date": assessment_date,
            "date_display": _display_date(assessment_date),
            "body": body,
            "message": body,
            "preparation": preparation,
            "fact_packet": {
                "assessmentDate": assessment_date,
                "assessments": [assessment_name],
                "resourceFileIds": [item.get("file_id") for item in resources],
                "sourceHash": source_hash,
            },
            "source_refs": [
                "config/curriculum/canvas/assessment-announcement-policy-2026-2027.json#languageArtsAssessment",
                "owner-decisions.json#language_arts",
            ],
            "source_hashes": {"pacing_source": source_hash, "announcement_policy": _file_hash(ANNOUNCEMENT_POLICY_PATH)},
            "source_hash": source_hash,
            "provenance": {
                "authority": "OWNER_INSTRUCTION",
                "source_value": (decision or {}).get("source_value", ""),
                "owner_value": (decision or {}).get("owner_value", ""),
                "decision_id": (decision or {}).get("decision_id", ""),
            },
            "content_status": "PARTIAL" if blocks else "READY",
            "blocked_sections": blocks,
            "publication_blocked": bool(blocks),
            "duplicate_identity": identity,
            "schedule_warnings": schedule.get("warnings") or [],
            **timing,
        }
        notices.append(_finish_notice(item, source_hash=source_hash))
    return notices


def draft_two_notice_announcements(
    week: dict[str, Any],
    *,
    source_hash: str = "",
    decisions: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
    notice_times: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Draft FIRST_NOTICE and REMINDER for Math and Language Arts assessments.

    Math written and fact assessments stay one combined family announcement per
    notice type. Nothing here is approved or posted.
    """
    config = pa.load_config()
    notices: list[dict[str, Any]] = []
    for event in pa.resolve_assessment_facts(week):
        family = event.get("family")
        assessment_date = event.get("assessmentDate") or ""
        if family == "math_assessment":
            decision = _matching_decision(
                decisions, subject="math", date_value=assessment_date, kind="semantic_interpretation",
            )
            # Without an auditable semantic decision, Math keeps its existing
            # single reminder. The two-notice pair is the owner-confirmed path.
            if decision is None:
                continue
            notices.extend(_math_notices(
                event, decision=decision, source_hash=source_hash, config=config, now=now,
                notice_times=notice_times,
            ))
        elif family == "language_arts_assessment":
            decision = _matching_decision(decisions, subject="language_arts", date_value=assessment_date)
            if not decision or not decision.get("preparation"):
                continue
            notices.extend(_language_arts_notices(
                event, decision=decision, source_hash=source_hash, config=config, now=now,
                notice_times=notice_times,
            ))
    _mark_duplicate_identities(notices)
    return notices


def annotate_unscheduled_reminders(
    reminders: list[dict[str, Any]],
    *,
    now: datetime | None = None,
    notice_times: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Give every reminder an explicit schedule. Null delay never means post now."""
    config = pa.load_config()
    for item in reminders:
        if item.get("notice_type") in ("FIRST_NOTICE", "REMINDER") and item.get("schedule_state"):
            continue
        assessment_date = item.get("assessment_date") or ""
        identity = item.get("duplicate_identity") or ""
        if not assessment_date:
            item["schedule_state"] = pa.BLOCKED
            item["scheduled"] = False
            item["delayed_post_at"] = None
            item["publication_blocked"] = True
            item["schedule_error"] = "reminder has no assessment date"
            continue
        proposed = pa.schedule_notices(assessment_date, config)["reminder"]
        timing = pa.classify_notice_schedule(proposed, config, now=now)
        timing = _apply_owner_notice_time(
            timing, proposed=proposed, config=config, now=now,
            owner_time=(notice_times or {}).get(identity),
        )
        if timing.get("schedule_state") != pa.FUTURE_SCHEDULED:
            item["publication_blocked"] = True
        item.update(timing)
    return reminders


def command_self_test() -> int:
    # Deterministic Q2W4-like week (no network, no Canvas).
    week = {
        "week": {"code": "Q2W4", "startDate": "2026-11-02", "endDate": "2026-11-06"},
        "unitContext": {"science": None},
        "days": {
            "Monday": {"date": "2026-11-02", "subjects": {"reading": {"raw": "L50"}, "spelling": {"raw": "46"}, "science": {"raw": "F&M Ch. 7"}}},
            "Tuesday": {"date": "2026-11-03", "subjects": {"reading": {"raw": "RMT 5+ CO 5"}, "spelling": {"raw": "47"}, "science": {"raw": "F&M Ch. 7"}}},
            "Wednesday": {"date": "2026-11-04", "subjects": {"reading": {"raw": "L51"}, "spelling": {"raw": "48"}, "science": {"raw": "Review"}}},
            "Thursday": {"date": "2026-11-05", "subjects": {"reading": {"raw": "L52"}, "spelling": {"raw": "49"}, "science": {"raw": "Test"}}},
            "Friday": {"date": "2026-11-06", "subjects": {"reading": {"raw": "L53"}, "spelling": {"raw": "test 50"}, "science": {"raw": "U2 Ch1 Renewable / Nonrenewable"}}},
        },
    }
    override = {
        "decision_id": "assessment_override|science|Thursday|2026-11-05",
        "kind": "assessment_override",
        "subject": "science",
        "day": "Thursday",
        "date": "2026-11-05",
        "source_value": "Test",
        "owner_value": "Energy Transformations Unit Test",
        "reason": "explicit Owen instruction",
        "acknowledgement": "canonical unit config may be stale",
        "open_book": True,
        "open_notes": True,
        "active": True,
    }
    items = draft_assessment_announcements(week, source_hash="src", decisions=[override])
    titles = [i["title"] for i in items]
    assert len(items) == 4, titles
    assert any("Reading Mastery Test 5" in t for t in titles), titles
    assert any("Fluency Checkout 5" in t for t in titles), titles
    assert any("Spelling Test 50" in t for t in titles), titles
    assert any("Energy Transformations Unit Test" in t for t in titles), titles

    mastery = next(i for i in items if i["type"] == "reading_mastery_test")
    assert "Lessons 41\u201350" in mastery["body"], mastery["body"]
    assert "Reading Workbook pages" in mastery["body"]
    assert "reread the stories" in mastery["body"]
    assert "Cat That Walked" not in mastery["body"]  # no passage leakage
    assert mastery["content_status"] == "READY"
    assert mastery["blocked_sections"] == []

    fluency = next(i for i in items if i["type"] == "fluency_checkout")
    assert "100 words" in fluency["body"] and "2 errors" in fluency["body"]
    assert "Cat That Walked" not in fluency["body"]
    assert "page 17" not in fluency["body"].lower()

    spelling = next(i for i in items if i["type"] == "spelling_test")
    assert "through Lesson 50" in spelling["body"]
    assert "current spelling list" not in spelling["body"]
    assert "Planner" in spelling["body"]  # verified cumulative list

    science = next(i for i in items if i["type"] == "science_unit_test")
    assert science["title"].startswith("Science: Energy Transformations Unit Test")
    assert "Open Book / Open Notes" in science["body"]
    assert science["provenance"]["source_value"] == "Test"
    assert science["provenance"]["owner_value"] == "Energy Transformations Unit Test"

    # Every artifact is separately identified and preview-only.
    assert len({i["duplicate_identity"] for i in items}) == 4
    assert all(i["preview_only"] is True and i["approval_state"] == "PENDING" for i in items)
    assert all(i["draft_hash"] for i in items)

    proposal = science_assignment_proposal(week, override)
    assert proposal["title"] == "Science: Energy Transformations Unit Test"
    assert proposal["assignment_group"] == "Assignments"
    assert proposal["due_date"] == "2026-11-05"
    assert proposal["points_possible"] == 100 and proposal["grading_type"] == "percent"
    assert proposal["submission_types"] == "on_paper"
    assert proposal["omit_from_final_grade"] is False
    assert "Open Book / Open Notes" in proposal["description"]

    # No override -> no Science assignment proposal.
    assert science_assignment_proposal(week, None) is None

    print("PASS assessment-announcement engine self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
