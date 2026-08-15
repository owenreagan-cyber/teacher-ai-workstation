"""Canonical WeeklyPlan → downstream translation layer (Phase 18B).

This module is the single integration boundary between the Phase 18A canonical
`WeeklyPlan` and the existing Phase 22-27 planning/publishing stack.

Principles:

- `WeeklyPlan` is the canonical human/evidence-facing representation.
- Phase 22-27 models remain the downstream execution/prediction/publication
  representations; this module adapts to their serialized contract shapes and
  does not create competing model classes.
- Translation only ever reads validated canonical state. Invalid plans fail
  closed before any translation.
- No Canvas write execution lives here. The module imports no writer, connector,
  gate, or publisher execution module. It produces plain dicts in the exact
  shapes consumed downstream:

    agenda      -> compatible with WeeklyAgendaPage.to_dict()  (publisher input)
    prediction  -> compatible with WeekPrediction.to_dict()    (Phase 24 boundary)
    subjects    -> compatible with SubjectSnapshot.to_dict()   (Phase 26 boundary)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from scripts.canvas_llm_phase18a.models import KNOWN_COURSES, WEEKDAYS, DayEntry, WeeklyPlan
from scripts.canvas_llm_phase18a.source_precedence import SOURCE_PRECEDENCE
from scripts.canvas_llm_phase18a.validation import validate_plan

# Canonical course display name -> downstream Phase 26 subject key.
SUBJECT_KEYS: dict[str, str] = {
    "Math": "math",
    "Reading/Spelling": "reading-spelling",
    "Language Arts": "language-arts",
    "History": "history",
    "Science": "science",
}
SUBJECT_TITLES: dict[str, str] = {v: k for k, v in SUBJECT_KEYS.items()}

# Source classes considered authoritative enough to be "owner confirmed" when
# they appear as the deciding source of a downstream action.
AUTHORITATIVE_SOURCES = frozenset(
    {"teacher_instruction", "live_pacing", "canonical_rule"}
)

# Assessment keywords used only to derive a light event_type classification.
# No content is invented; a non-matching day stays a lesson event.
_ASSESSMENT_MARKERS = ("test", "assessment", "checkout", "quiz")


def compact(value: Any) -> str:
    return " ".join(str(value or "").replace("\xa0", " ").split())


def stable_plan_id(plan: WeeklyPlan) -> str:
    payload = plan.week_code + "|" + json.dumps(plan.to_dict(), sort_keys=True, default=str)
    return "wp-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:18]


def content_hash(title: str, body: str) -> str:
    return hashlib.sha256(f"{compact(title)}|{compact(body)}".encode("utf-8")).hexdigest()[:16]


def _event_type(day: DayEntry) -> str:
    blob = compact(f"{day.in_class} {day.raw}").lower()
    if any(marker in blob for marker in _ASSESSMENT_MARKERS):
        return "assessment"
    return "lesson"


def _source_evidence(day: DayEntry, plan: WeeklyPlan) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for e in day.evidence:
        evidence.append(
            {
                "source_type": e.source_class,
                "source_ref": e.reference,
                "details": e.note,
                "owner_confirmed": e.source_class in AUTHORITATIVE_SOURCES,
            }
        )
    for e in plan.provenance:
        if any(item["source_type"] == e.source_class and item["source_ref"] == e.reference for item in evidence):
            continue
        evidence.append(
            {
                "source_type": e.source_class,
                "source_ref": e.reference,
                "details": e.note,
                "owner_confirmed": e.source_class in AUTHORITATIVE_SOURCES,
            }
        )
    if not evidence:
        evidence.append(
            {
                "source_type": day.decided_source or "canonical_rule",
                "source_ref": "canonical WeeklyPlan",
                "details": "no explicit evidence attached",
                "owner_confirmed": False,
            }
        )
    return evidence


def _event(
    plan: WeeklyPlan,
    course_name: str,
    day: DayEntry,
    *,
    ambiguous: bool = False,
) -> dict[str, Any]:
    subject = SUBJECT_KEYS[course_name]
    if ambiguous:
        return {
            "week_code": plan.week_code,
            "subject": subject,
            "weekday": day.weekday,
            "event_type": "lesson",
            "lesson_number": None,
            "assessment_number": None,
            "in_class_title": "",
            "at_home_title": "",
            "resource_requirements": [],
            "source_pacing_reference": day.raw,
            "previous_instructional_state": {},
            "rules_applied": ["canonical-weekly-plan", "ambiguity.unresolved"],
            "explanation": [f"Unresolved canonical content for {course_name} {day.weekday}"],
            "confidence": {"level": "low", "score": 0.2, "rationale": "unresolved canonical ambiguity"},
            "requires_review": True,
            "manual_override_state": "none",
            "review_state": "needs_review",
            "source_evidence": _source_evidence(day, plan),
            "rule_explanations": [],
            "decision_layer": "unresolved",
            "canonical_week_code": plan.week_code,
            "teacher_override": None,
            "teacher_correction": None,
        }

    decided = day.decided_source or "canonical_rule"
    is_teacher = decided == "teacher_instruction"
    review_state = "teacher_decided" if is_teacher else "approved"
    level = "high" if decided in AUTHORITATIVE_SOURCES else "medium"
    score = 0.95 if decided in AUTHORITATIVE_SOURCES else 0.6
    rules = ["canonical-weekly-plan"]
    if is_teacher:
        rules.append("teacher.override")
    override = None
    if is_teacher:
        override = {
            "subject": subject,
            "week_code": plan.week_code,
            "day": day.weekday,
            "field": "in_class",
            "value": day.in_class,
            "scope": "this occurrence only",
            "timestamp": "",
            "reason": "teacher instruction",
            "revision": 1,
        }
    return {
        "week_code": plan.week_code,
        "subject": subject,
        "weekday": day.weekday,
        "event_type": _event_type(day),
        "lesson_number": None,
        "assessment_number": None,
        "in_class_title": day.in_class,
        "at_home_title": day.homework,
        "resource_requirements": [],
        "source_pacing_reference": day.raw,
        "previous_instructional_state": {},
        "rules_applied": rules,
        "explanation": [f"Canonical WeeklyPlan content for {course_name} {day.weekday}"],
        "confidence": {"level": level, "score": score, "rationale": f"canonical source: {decided}"},
        "requires_review": False,
        "manual_override_state": "teacher" if is_teacher else "none",
        "review_state": review_state,
        "source_evidence": _source_evidence(day, plan),
        "rule_explanations": [],
        "decision_layer": decided,
        "canonical_week_code": plan.week_code,
        "teacher_override": override,
        "teacher_correction": None,
    }


@dataclass
class TranslationResult:
    plan_id: str
    week_code: str
    agenda: dict[str, Any]
    prediction: dict[str, Any]
    subjects: list[dict[str, Any]]
    trace: list[dict[str, Any]]
    blanks: list[dict[str, Any]]
    unresolved: list[dict[str, Any]]
    protected: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _week_title(plan: WeeklyPlan) -> str:
    if plan.week_code:
        return f"Quarter {plan.quarter}, Week {plan.week_number} | {plan.monday_date} .. {plan.friday_date}"
    return f"Week of {plan.monday_date}"


def translate_weekly_plan(plan: WeeklyPlan) -> TranslationResult:
    """Translate a validated canonical WeeklyPlan into downstream-compatible dicts.

    Raises ValueError (fails closed) if the plan does not validate.
    """
    report = validate_plan(plan)
    if not report.ok:
        raise ValueError("invalid WeeklyPlan: " + "; ".join(report.errors))

    plan_id = stable_plan_id(plan)
    source_hierarchy = list(SOURCE_PRECEDENCE)

    agenda_days: dict[str, dict[str, Any]] = {
        wd: {"name": wd, "subjects": {}, "homework": []} for wd in WEEKDAYS
    }
    events: list[dict[str, Any]] = []
    subjects: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    blanks: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    protected: list[str] = []
    warnings: list[str] = list(plan.warnings)
    teacher_overrides: list[dict[str, Any]] = []

    for course_name in KNOWN_COURSES:
        course = plan.courses.get(course_name)
        if course is None:
            continue
        subject = SUBJECT_KEYS[course_name]
        course_events: list[dict[str, Any]] = []
        course_unresolved: list[dict[str, Any]] = []
        course_teacher_edits: list[dict[str, Any]] = []
        if course.protected:
            protected.append(course_name)

        for day in course.days:
            if day.blank:
                blanks.append(
                    {"course": course_name, "weekday": day.weekday, "date": day.date}
                )
                trace.append(
                    {
                        "canonical_plan_id": plan_id,
                        "canonical_week_code": plan.week_code,
                        "canonical_course": course_name,
                        "canonical_day": day.weekday,
                        "canonical_source": "blank",
                        "canonical_reference": "",
                        "canonical_precedent_class": "",
                        "downstream_kind": "none",
                        "downstream_ref": f"{subject}:{day.weekday}:blank",
                    }
                )
                continue

            ambiguous = bool(day.ambiguity) and not day.in_class and not day.homework
            if ambiguous:
                unresolved.append(
                    {
                        "course": course_name,
                        "weekday": day.weekday,
                        "raw": day.raw,
                        "ambiguity": day.ambiguity,
                    }
                )
                course_unresolved.append(
                    {
                        "decision_id": f"{plan_id}:{subject}:{day.weekday}",
                        "subject": subject,
                        "week_code": plan.week_code,
                        "day": day.weekday,
                        "reason": day.ambiguity,
                        "candidates": [],
                    }
                )
                trace.append(
                    {
                        "canonical_plan_id": plan_id,
                        "canonical_week_code": plan.week_code,
                        "canonical_course": course_name,
                        "canonical_day": day.weekday,
                        "canonical_source": day.decided_source or "unresolved",
                        "canonical_reference": day.raw,
                        "canonical_precedent_class": "",
                        "downstream_kind": "unresolved",
                        "downstream_ref": f"{subject}:{day.weekday}",
                    }
                )
                if not course.protected:
                    ambiguous_event = _event(plan, course_name, day, ambiguous=True)
                    events.append(ambiguous_event)
                    course_events.append(ambiguous_event)
                continue

            # Concrete, non-blank, non-ambiguous day.
            event = _event(plan, course_name, day)
            trace.append(
                {
                    "canonical_plan_id": plan_id,
                    "canonical_week_code": plan.week_code,
                    "canonical_course": course_name,
                    "canonical_day": day.weekday,
                    "canonical_source": day.decided_source or "canonical_rule",
                    "canonical_reference": day.raw or day.in_class,
                    "canonical_precedent_class": next(
                        (
                            e.precedent_class
                            for e in day.evidence
                            if e.source_class == "precedent" and e.precedent_class
                        ),
                        "",
                    ),
                    "downstream_kind": "prediction-event",
                    "downstream_ref": f"{subject}:{day.weekday}",
                }
            )
            if day.decided_source == "teacher_instruction":
                teacher_overrides.append(event["teacher_override"])
                course_teacher_edits.append(
                    {
                        "subject": subject,
                        "weekday": day.weekday,
                        "field": "in_class",
                        "value": day.in_class,
                        "reason": "teacher instruction",
                    }
                )

            if course.protected:
                # Protected course content must never become a writable action.
                continue

            events.append(event)
            course_events.append(event)

            if day.in_class:
                agenda_days[day.weekday]["subjects"].setdefault(course_name, []).append(
                    day.in_class
                )
            if day.homework:
                agenda_days[day.weekday]["homework"].append(
                    f"{course_name}: {day.homework}"
                )

        # Subject workspace (Phase 26 SubjectSnapshot-compatible).
        if course.protected:
            readiness_state = "Blocked"
            approval_state = "Blocked"
            production_preview = "Needs Review"
            assignment_policy = "disabled"
        elif course_unresolved:
            readiness_state = "Needs Review"
            approval_state = "Needs Review"
            production_preview = "Needs Review"
            assignment_policy = "enabled"
        else:
            readiness_state = "Ready"
            approval_state = "Approved"
            production_preview = "Ready"
            assignment_policy = "enabled"
        subjects.append(
            {
                "subject": subject,
                "title": course_name,
                "readinessState": readiness_state,
                "approvalState": approval_state,
                "confidence": round(
                    sum(float(e["confidence"]["score"]) for e in course_events)
                    / len(course_events)
                    if course_events
                    else 0.0,
                    2,
                ),
                "sourceHierarchy": source_hierarchy,
                "predictedInstruction": course_events,
                "resolvedResources": [],
                "unresolvedResources": course_unresolved,
                "blockedResources": [],
                "teacherEdits": course_teacher_edits,
                "productionPreviewStatus": production_preview,
                "assignmentPolicy": assignment_policy,
                "why": (
                    f"Canonical WeeklyPlan source for {course_name}"
                ),
            }
        )

    agenda = {
        "week_code": plan.week_code,
        "title": _week_title(plan),
        "days": [agenda_days[wd] for wd in WEEKDAYS],
        "assignments": [],
        "assessments": [
            compact(a.get("name") or "")
            for a in plan.assessments_reminders
            if compact(a.get("name") or "")
        ],
        "reminders": [
            compact(a.get("name") or "")
            for a in plan.assessments_reminders
            if compact(a.get("name") or "")
        ],
        "schedule_summary": _week_title(plan),
        "content_hash": content_hash(
            _week_title(plan), json.dumps(agenda_days, sort_keys=True)
        ),
        "approval_state": "draft",
        "deployment_status": "draft",
        "page_url": f"weekly-agenda-{plan.week_code.lower()}",
    }

    prediction = {
        "weekCode": plan.week_code,
        "sourceHierarchy": source_hierarchy,
        "predictions": events,
        "unresolvedDecisions": [
            {
                "decision_id": f"{plan_id}:{u['course']}:{u['weekday']}",
                "subject": SUBJECT_KEYS[u["course"]],
                "week_code": plan.week_code,
                "day": u["weekday"],
                "reason": u["ambiguity"],
                "candidates": [],
            }
            for u in unresolved
        ],
        "teacherOverrides": teacher_overrides,
        "teacherCorrections": [],
        "patternRecords": [],
        "warnings": warnings,
        "reviewState": "needs_review" if (unresolved or warnings) else "approved",
        "provenance": [
            {"sourceType": "canonical-weekly-plan", "sourceRef": "scripts/canvas_llm_phase18a", "details": "Phase 18A canonical WeeklyPlan"},
            {"sourceType": "canonical-calendar", "sourceRef": "config/curriculum/canvas/instructional-weeks-2026-2027.json", "details": "instructional week authority"},
        ],
        "announcementDrafts": [],
        "newsletterDraft": None,
        "newsletterUpdateAnnouncement": None,
        "dailyTeacherBriefs": [],
    }

    return TranslationResult(
        plan_id=plan_id,
        week_code=plan.week_code,
        agenda=agenda,
        prediction=prediction,
        subjects=subjects,
        trace=trace,
        blanks=blanks,
        unresolved=unresolved,
        protected=protected,
        warnings=warnings,
    )
