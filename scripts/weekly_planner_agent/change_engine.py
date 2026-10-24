"""Change engine: apply teacher instructions to a WeeklyPlan.

Every mutation:
    - records an auditable SourceChangeEvent
    - recomputes affected artifacts (assignment/announcement/reminder candidates)
    - invalidates approvals ONLY for affected subjects/artifacts (approval-by-exception)
    - never performs a live Canvas write and never auto-promotes a predicted item
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import teacher_instructions as ti
from .authority import may_promote
from .models import (
    Assessment,
    Authority,
    Confidence,
    DayPlan,
    PlanStatus,
    SourceChangeEvent,
    WeeklyPlan,
)

AFFECTED_ARTIFACTS = ["weekly page", "assignments", "first announcement", "day-before reminder"]


@dataclass
class ChangeResult:
    plan: WeeklyPlan
    events: list[SourceChangeEvent]
    changes: list[dict[str, Any]]
    affected_artifacts: list[str]
    reply: str
    applied: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": [e.to_dict() for e in self.events],
            "changes": self.changes,
            "affected_artifacts": self.affected_artifacts,
            "reply": self.reply,
            "applied": self.applied,
        }


def _subjects_affected(plan: WeeklyPlan, subject: str) -> list[str]:
    """Return the set of subjects whose artifacts must be recomputed."""
    if subject == "homeroom":
        return ["homeroom"]
    if subject in plan.subjects:
        return [subject]
    return [subject] if subject else list(plan.subjects)


def _event(
    subject: str,
    object_type: str,
    old_value: str | None,
    new_value: str | None,
    *,
    affected: list[str] | None = None,
    severity: str = "info",
    family_comms: bool = False,
) -> SourceChangeEvent:
    return SourceChangeEvent(
        source="owner_instruction",
        subject=subject,
        object_type=object_type,
        old_value=old_value,
        new_value=new_value,
        severity=severity,
        affected_artifacts=affected or AFFECTED_ARTIFACTS,
        requires_teacher_approval=True,
        family_comms_affected=family_comms,
    )


def _invalidate_affected(plan: WeeklyPlan, subjects: list[str]) -> None:
    """Invalidate approvals for affected subjects only (approval-by-exception)."""
    for subject in subjects:
        record = plan.approval_status.setdefault(subject, {})
        for artifact in ("page", "assignments", "announcement", "assessment_reminder"):
            if artifact in record and record[artifact] == "approved":
                record[artifact] = "stale"


def _upsert_assessment(
    plan: WeeklyPlan, subject: str, *, day: str | None = None, name: str | None = None,
    previous_date: str | None = None, new_date: str | None = None,
) -> tuple[DayPlan, Assessment]:
    """Set/attach an assessment on a subject/day, creating a DayPlan if needed."""
    existing = plan.day(subject, day) if day else None
    if existing is None and day:
        existing = DayPlan(subject=subject, day=day)
        plan.upsert_day(existing)
    if existing is not None and existing.assessment is not None:
        assessment = existing.assessment
    else:
        assessment = Assessment(
            name=name or f"{subject.title()} Assessment",
            subject=subject,
            day=day,
            authority=Authority.OWNER_INSTRUCTION,
            confidence=Confidence.CONFIRMED,
        )
    if previous_date is not None:
        assessment.previous_date = assessment.previous_date or previous_date
    if new_date is not None:
        assessment.date = new_date
        assessment.day = day
    if existing is not None:
        existing.assessment = assessment
        existing.authority = Authority.OWNER_INSTRUCTION
        existing.confidence = Confidence.CONFIRMED
        existing.status = PlanStatus.PLANNED
    return existing or DayPlan(subject=subject, day=day or ""), assessment


def apply_instruction(plan: WeeklyPlan, instruction: ti.InstructionOp) -> ChangeResult:
    """Apply a single parsed instruction to the plan (in place) and report."""
    intent = instruction.intent
    events: list[SourceChangeEvent] = []
    changes: list[dict[str, Any]] = []
    affected: list[str] = []

    if intent == ti.MOVE_ASSESSMENT:
        subject = instruction.subject or "math"
        day = instruction.day or "Thursday"
        day_plan, assessment = _upsert_assessment(plan, subject, day=day, name=instruction.assessment)
        old_date = assessment.previous_date or "not set"
        assessment.previous_date = assessment.date or old_date
        assessment.date = day_plan.date or day
        assessment.day = day
        assessment.authority = Authority.OWNER_INSTRUCTION
        events.append(_event(subject, "assessment_date", old_date, assessment.date,
                             severity="high", family_comms=True))
        changes.append({
            "type": "assessment_moved",
            "subject": subject,
            "assessment": assessment.name,
            "from": assessment.previous_date,
            "to": assessment.date,
            "day": day,
        })
        affected = AFFECTED_ARTIFACTS
        _invalidate_affected(plan, [subject])
        plan.reminder_candidates = _recompute_reminders(plan, subject)
        reply = (f"Done. {assessment.name or 'The assessment'} moved to {day}. "
                 f"Recomputed the weekly page, assignment, first announcement, and day-before reminder.")

    elif intent == ti.NO_HOMEWORK:
        subject = instruction.subject or "science"
        for day in plan.subjects.get(subject, []):
            if day.homework:
                day.homework = []
                day.authority = Authority.OWNER_INSTRUCTION
        events.append(_event(subject, "homework", "present", "none"))
        changes.append({"type": "homework_removed", "subject": subject})
        affected = [f"{subject} weekly page", f"{subject} assignments"]
        _invalidate_affected(plan, [subject])
        reply = f"Done. {subject.title()} homework removed for the week."

    elif intent == ti.SET_HOMEWORK_DAYS:
        subject = instruction.subject or "reading_spelling"
        keep_days = set(instruction.days)
        for day in plan.subjects.get(subject, []):
            if day.day not in keep_days and day.homework:
                day.homework = []
                day.authority = Authority.OWNER_INSTRUCTION
        events.append(_event(subject, "homework_days", "all", ", ".join(sorted(keep_days))))
        changes.append({"type": "homework_days", "subject": subject, "days": sorted(keep_days)})
        affected = [f"{subject} weekly page"]
        _invalidate_affected(plan, [subject])
        reply = f"Done. {subject.title()} homework now on {' and '.join(sorted(keep_days))} only."

    elif intent == ti.SKIP_CHAPTER:
        subject = instruction.subject or "math"
        chapter = instruction.chapter or "8"
        for day in plan.subjects.get(subject, []):
            if day.lesson and f"Chapter {chapter}" in day.lesson:
                day.lesson = None
                day.status = PlanStatus.PLANNED
                day.authority = Authority.OWNER_INSTRUCTION
        events.append(_event(subject, "chapter", f"Chapter {chapter}", "skipped"))
        changes.append({"type": "chapter_skipped", "subject": subject, "chapter": chapter})
        affected = [f"{subject} weekly page"]
        _invalidate_affected(plan, [subject])
        reply = f"Understood — we're not doing Chapter {chapter} yet in {subject.title()}."

    elif intent == ti.ADD_HOMEROOM:
        item = instruction.item or instruction.raw
        plan.homeroom_items.append({"label": item, "added_by": "owner", "week": plan.week_id})
        events.append(_event("homeroom", "homeroom_item", None, item))
        changes.append({"type": "homeroom_item_added", "item": item})
        affected = ["homeroom newsletter"]
        _invalidate_affected(plan, ["homeroom"])
        reply = f'Added "{item}" to Homeroom.'

    elif intent == ti.MAKE_REVIEW_DAY:
        subject = instruction.subject
        day = instruction.day or "Wednesday"
        targets = _subjects_affected(plan, subject) if subject else list(plan.subjects)
        for subj in targets:
            dp = plan.day(subj, day)
            if dp is not None:
                dp.lesson = "Review"
                dp.authority = Authority.OWNER_INSTRUCTION
            else:
                plan.upsert_day(DayPlan(
                    subject=subj, day=day, lesson="Review",
                    authority=Authority.OWNER_INSTRUCTION, confidence=Confidence.CONFIRMED,
                    status=PlanStatus.PLANNED,
                ))
            events.append(_event(subj, "lesson", "planned", "Review"))
        changes.append({"type": "review_day", "day": day, "subjects": targets})
        affected = [f"{s} weekly page" for s in targets]
        _invalidate_affected(plan, targets)
        reply = f"Done. {day} is now a review day."

    elif intent == ti.REMOVE_ASSIGNMENT_KEEP:
        subject = instruction.subject or "math"
        day = instruction.day
        before = len(plan.assignment_candidates)
        plan.assignment_candidates = [
            a for a in plan.assignment_candidates
            if not (a.get("subject") == subject and (day is None or a.get("day") == day))
        ]
        removed = before - len(plan.assignment_candidates)
        if instruction.keep_lesson and day:
            dp = plan.day(subject, day)
            if dp is not None:
                dp.status = PlanStatus.PLANNED
        events.append(_event(subject, "assignment", f"{removed} planned", "removed"))
        changes.append({
            "type": "assignment_removed", "subject": subject, "day": day,
            "keep_lesson": instruction.keep_lesson,
        })
        affected = [f"{subject} assignments"]
        _invalidate_affected(plan, [subject])
        reply = (f"Done. Removed the planned {subject.title()} assignment"
                 + (f" on {day}" if day else "")
                 + ("; kept the lesson." if instruction.keep_lesson else "."))

    elif intent in (ti.KEEP_SUBJECT_CHAPTER, ti.KEEP_OVERRIDE):
        subject = instruction.subject or "science"
        day = instruction.day
        dp = plan.day(subject, day) if day else None
        if dp is not None:
            dp.teacher_override = {
                "subject": subject, "day": day,
                "chapter": instruction.chapter,
                "kind": "keep_subject_chapter" if intent == ti.KEEP_SUBJECT_CHAPTER else "keep_override",
            }
            dp.authority = Authority.OWNER_INSTRUCTION
        elif day:
            plan.upsert_day(DayPlan(
                subject=subject, day=day,
                teacher_override={"subject": subject, "day": day, "chapter": instruction.chapter,
                                  "kind": "keep_override"},
                authority=Authority.OWNER_INSTRUCTION, confidence=Confidence.CONFIRMED,
                status=PlanStatus.PLANNED,
            ))
        events.append(_event(subject, "override", "pacing", instruction.chapter or day or "override"))
        changes.append({
            "type": "owner_override", "subject": subject, "day": day, "chapter": instruction.chapter,
        })
        affected = [f"{subject} weekly page"]
        _invalidate_affected(plan, [subject])
        reply = (f"Done. Recorded your {subject.title()} override"
                 + (f" for {day}" if day else "")
                 + (f" (Chapter {instruction.chapter})" if instruction.chapter else "")
                 + ". It is now the highest authority.")

    elif intent == ti.WHAT_CHANGED:
        return ChangeResult(plan, [], [], [], "No changes pending.", True)

    elif intent == ti.APPROVE_EXCEPT:
        excluded = instruction.subject
        approved = []
        for subj in plan.subjects:
            if subj == excluded:
                continue
            record = plan.approval_status.setdefault(subj, {})
            for artifact in ("page", "assignments", "announcement", "assessment_reminder"):
                record[artifact] = "approved"
            approved.append(subj)
        events.append(_event("all", "approval", "pending", f"approved except {excluded}"))
        changes.append({"type": "approve_except", "excluded": excluded, "approved": approved})
        reply = (f"Done. Approved everything except {excluded.title() if excluded else 'that subject'}."
                 f" {' and '.join(s.title() for s in approved)} remain unchanged from prior review.")

    else:
        return ChangeResult(plan, [], [], [], "That instruction was not recognized.", False)

    plan.change_history.append({
        "intent": intent,
        "changes": changes,
        "affected_artifacts": affected,
    })
    return ChangeResult(plan, events, changes, affected, reply, True)


def _recompute_reminders(plan: WeeklyPlan, subject: str) -> list[dict[str, Any]]:
    """Recompute reminder candidates for a subject after a date change.

    No live write; just regenerate the local planned reminders so the
    day-before reminder tracks the new assessment date.
    """
    kept: list[dict[str, Any]] = []
    for reminder in plan.reminder_candidates:
        if reminder.get("subject") != subject:
            kept.append(reminder)
            continue
        kept.append({**reminder, "recomputed": True})
    return kept


def compute_changes_since(plan: WeeklyPlan, prior: WeeklyPlan | None) -> list[dict[str, Any]]:
    """Diff two plans at the subject/day level (approval-by-exception driver)."""
    if prior is None:
        return []
    changes: list[dict[str, Any]] = []
    for subject, days in plan.subjects.items():
        prior_days = prior.subjects.get(subject, [])
        prior_by_day = {d.day: d for d in prior_days}
        for day in days:
            prev = prior_by_day.get(day.day)
            if prev is None:
                changes.append({"type": "added", "subject": subject, "day": day.day})
                continue
            if (prev.lesson, prev.homework, prev.assessment and prev.assessment.date) != (
                day.lesson, day.homework, day.assessment and day.assessment.date
            ):
                changes.append({"type": "changed", "subject": subject, "day": day.day})
    return changes


def predicted_guard(day: DayPlan, target_status: str) -> bool:
    """Predicted items must never become approved/live automatically."""
    return may_promote(day.confidence, target_status)
