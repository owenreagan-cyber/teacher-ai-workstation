from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from scripts.canvas_llm_phase22 import phase22_workstation as phase22  # noqa: E402

from .correction_memory import apply_teacher_corrections, compact
from .models import (
    Confidence,
    PredictedAssessment,
    PredictedHomework,
    PredictedInstructionalEvent,
    PredictedLesson,
    PredictedResourceRequirement,
    RuleExplanation,
    SourceEvidence,
    TeacherCorrection,
    TeacherOverride,
    UnresolvedDecision,
    WeekPrediction,
)
from .pacing_knowledge import DEFAULT_SOURCE_HIERARCHY, build_pattern_records, load_pacing_knowledge


def subject_prefix(subject: str) -> str:
    subject = compact(subject).lower()
    return {
        "math": "SM5",
        "reading": "RM4",
        "spelling": "SPELL",
        "shurley": "SHURLEY",
        "history": "HIST",
        "science": "SCI",
    }.get(subject, compact(subject).upper() or "GEN")


def lesson_title(subject: str, number: int | None) -> str:
    if number is None:
        return ""
    return f"{subject_prefix(subject)}: Lesson {number}" if subject == "math" else f"{subject_prefix(subject)} Lesson {number}"


def math_homework_title(lesson_number: int, weekday: str, hint_override: str | None = None) -> str:
    homework = phase22.math_homework_for_weekday(weekday)
    if homework == "No Homework":
        return "No Homework"
    if weekday in phase22.MATH_HOMEWORK_GRADE_DAYS:
        return phase22.math_homework_assignment_title(weekday, lesson_number)
    return phase22.math_homework_assignment_title(weekday, lesson_number) if weekday in phase22.MATH_HOMEWORK_GRADE_DAYS else "No Homework"


def math_homework_for_weekday(weekday: str) -> str:
    return phase22.math_homework_for_weekday(weekday)


def pacing_rows_from_knowledge(knowledge: dict[str, Any], week_code: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in knowledge.get("pacingGuideEntries", []):
        if compact(raw.get("weekCode") or week_code) != compact(week_code):
            continue
        lesson = raw.get("lessonNumber")
        assessment = raw.get("assessmentNumber")
        weekday = raw.get("weekday") or "Monday"
        subject = compact(raw.get("subject")).lower()
        rows.append(
            {
                "subject": subject,
                "weekday": weekday,
                "lesson": str(lesson or ""),
                "tests": str(assessment or "") if raw.get("eventType") == "assessment" else "",
                "entry_date": "",
                "title": "",
                "resolver_output": json.dumps({"gradedSelectionOverride": raw.get("manualOverride") or {}}),
            }
        )
    return rows


def annotate_graded_selection(predictions: list[PredictedInstructionalEvent], knowledge: dict[str, Any], week_code: str) -> tuple[list[PredictedInstructionalEvent], list[str], list[UnresolvedDecision]]:
    warnings: list[str] = []
    unresolved: list[UnresolvedDecision] = []
    week = phase22.instructional_week_by_code(week_code) or {"code": week_code}
    rows = pacing_rows_from_knowledge(knowledge, week_code)
    ctx = phase22.build_week_graded_selection_context(rows, week)
    specs = phase22.selected_graded_assignment_specs(rows, week)
    selected_keys = {
        (compact(spec["subject"]).lower(), spec["row"].get("weekday"), compact((spec.get("payload") or {}).get("metadata", {}).get("gradeRole")))
        for spec in specs
        if spec.get("kind") == "assignment" and (spec.get("payload") or {}).get("metadata", {}).get("gradeCategory") == "instructional"
    }
    for item in predictions:
        subject = compact(item.subject).lower()
        weekday = item.weekday
        if item.event_type == "assessment":
            item.rules_applied = list(dict.fromkeys([*item.rules_applied, "graded.assessment-event"]))
            item.explanation = [*item.explanation, "Assessment events remain separate from weekly instructional grade selections."]
            continue
        if item.event_type != "lesson":
            continue
        roles: list[str] = []
        if subject == "math":
            if weekday in phase22.MATH_HOMEWORK_GRADE_DAYS and phase22.math_homework_for_weekday(weekday) != "No Homework":
                roles.append("homework")
            if weekday == ctx["mathClassworkDay"]:
                roles.append("classwork")
        if subject == "reading":
            if weekday in phase22.READING_HOMEWORK_GRADE_DAYS and phase22.reading_homework_for_weekday(weekday) != "No Homework":
                roles.append("homework")
            if weekday == ctx["readingClassworkDay"]:
                roles.append("classwork")
        selected_roles = [role for role in roles if (subject, weekday, role) in selected_keys]
        if selected_roles:
            item.rules_applied = list(dict.fromkeys([*item.rules_applied, "graded.selected", *[f"graded.role.{role}" for role in selected_roles]]))
            item.explanation = [*item.explanation, f"Selected instructional grade preview(s): {', '.join(selected_roles)} on {weekday}."]
            meta = phase22.graded_selection_metadata(
                selection_reason=f"owner-confirmed-{weekday.lower()}-selection",
                grade_role=selected_roles[0],
                selection_source=ctx["mathClassworkSelectionSource"] if subject == "math" and "classwork" in selected_roles else (ctx["readingClassworkSelectionSource"] if subject == "reading" and "classwork" in selected_roles else "default"),
                teacher_override_applied=ctx["mathClassworkSelectionSource"] == "teacher-override" or ctx["readingClassworkSelectionSource"] == "teacher-override",
                default_selection=True,
                selected_day=weekday,
            )
            item.explanation.append(json.dumps({"gradedSelection": meta}, ensure_ascii=False))
        else:
            item.rules_applied = list(dict.fromkeys([*item.rules_applied, "graded.non-selected-instructional"]))
            item.explanation = [*item.explanation, "Instructional agenda item only; no Canvas assignment preview selected for this occurrence."]
    for bad in ctx.get("overrides", {}).get("invalid") or []:
        unresolved.append(
            UnresolvedDecision(
                decision_id=f"graded-selection-override-{bad.get('field')}",
                subject="math" if bad.get("field") == "mathClassworkDay" else "reading",
                week_code=week_code,
                day="",
                reason=f"Invalid graded-selection override value: {bad.get('value')}",
                candidates=[{"field": bad.get("field"), "value": bad.get("value"), "status": "rejected"}],
            )
        )
        warnings.append(f"Invalid graded-selection override for {bad.get('field')}: {bad.get('value')}")
    return predictions, warnings, unresolved


def pacing_rows_for_announcements(knowledge: dict[str, Any], week_code: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    week = phase22.instructional_week_by_code(week_code) or {}
    weekday_offsets = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}
    starts_on = week.get("startsOn") or ""
    for raw in knowledge.get("pacingGuideEntries", []):
        if compact(raw.get("weekCode") or week_code) != compact(week_code):
            continue
        if compact(raw.get("eventType")).lower() != "assessment":
            continue
        weekday = raw.get("weekday") or "Monday"
        entry_date = compact(raw.get("entryDate") or raw.get("date") or "")
        if not entry_date and starts_on and weekday in weekday_offsets:
            entry_date = (date.fromisoformat(starts_on) + timedelta(days=weekday_offsets[weekday])).isoformat()
        rows.append(
            {
                "subject": compact(raw.get("subject")).lower(),
                "weekday": raw.get("weekday") or "Monday",
                "lesson": str(raw.get("lessonNumber") or ""),
                "tests": str(raw.get("assessmentNumber") or ""),
                "entry_date": entry_date,
                "title": compact(raw.get("title") or ""),
                "coverage": compact(raw.get("coverage") or ""),
                "notes": compact(raw.get("notes") or ""),
                "resolver_output": json.dumps(
                    {
                        "coverage": raw.get("coverage"),
                        "topic": raw.get("topic"),
                        "announcementNoteSafe": raw.get("announcementNoteSafe"),
                        "announcementScheduleOverride": raw.get("announcementScheduleOverride") or {},
                    },
                    ensure_ascii=False,
                ),
            }
        )
    return rows


def annotate_announcement_drafts(
    knowledge: dict[str, Any],
    week_code: str,
    predictions: list[PredictedInstructionalEvent],
) -> tuple[list[dict[str, Any]], list[str], list[UnresolvedDecision]]:
    warnings: list[str] = []
    unresolved: list[UnresolvedDecision] = []
    week = phase22.instructional_week_by_code(week_code) or {"code": week_code}
    rows = pacing_rows_for_announcements(knowledge, week_code)
    if not rows:
        for item in predictions:
            if item.event_type != "assessment":
                continue
            rows.append(
                {
                    "subject": compact(item.subject).lower(),
                    "weekday": item.weekday,
                    "lesson": str(item.lesson_number or ""),
                    "tests": str(item.assessment_number or ""),
                    "entry_date": (date.fromisoformat(week.get("startsOn") or "") + timedelta(days={"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}.get(item.weekday, 0))).isoformat() if week.get("startsOn") and item.weekday in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"} else "",
                    "title": compact(item.in_class_title or ""),
                    "coverage": "",
                    "notes": "",
                    "resolver_output": "{}",
                }
            )
    drafts = phase22.build_week_announcement_drafts(rows, week)
    for draft in drafts:
        draft["predictionMetadata"] = {
            "triggerAssessmentType": draft.get("assessment_type"),
            "triggerAssessmentNumber": draft.get("assessment_number"),
            "coverageStatus": draft.get("coverage_status"),
            "needsReview": draft.get("needs_review"),
            "generationReason": draft.get("generation_reason"),
            "scheduleIntent": (draft.get("schedule_metadata") or {}).get("scheduleIntent"),
            "teacherOverrideApplied": (draft.get("schedule_metadata") or {}).get("teacherOverrideApplied"),
        }
        for warning in draft.get("warnings") or []:
            if "calendar disruption" in warning.lower():
                unresolved.append(
                    UnresolvedDecision(
                        decision_id=f"announcement-schedule-{draft.get('announcement_id')}",
                        subject=draft.get("subject") or "",
                        week_code=week_code,
                        day="Friday",
                        reason=warning,
                        candidates=[{"scheduleIntent": phase22.ANNOUNCEMENT_SCHEDULE_INTENT, "status": "intent-preserved"}],
                    )
                )
    return drafts, warnings, unresolved


def annotate_newsletter_metadata(
    week_code: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str], list[UnresolvedDecision]]:
    week = phase22.instructional_week_by_code(week_code) or {}
    starts_on = compact(week.get("startsOn") or "")
    if not starts_on:
        return None, None, [], []
    _, newsletter, update = phase22.resolve_newsletter_for_week_start(
        starts_on,
        db=None,
        school_year="2026-2027",
        week_code=week_code,
    )
    warnings = list(newsletter.get("warnings") or []) + list(update.get("warnings") or [])
    newsletter["predictionMetadata"] = {
        "resolvedMonthCode": newsletter.get("month_code"),
        "resolvedMonthLabel": newsletter.get("month_label"),
        "cadence": newsletter.get("cadence"),
        "needsReview": newsletter.get("needs_review"),
        "blockers": newsletter.get("blockers"),
        "contentHash": newsletter.get("content_hash"),
    }
    update["predictionMetadata"] = {
        "dependsOn": update.get("depends_on"),
        "verificationStatus": update.get("verification_status"),
        "blockers": update.get("blockers"),
        "scheduleMetadata": update.get("schedule_metadata"),
    }
    return newsletter, update, warnings, []


def annotate_daily_teacher_briefs(
    week_code: str,
    knowledge: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], list[UnresolvedDecision]]:
    week = phase22.instructional_week_by_code(week_code) or {}
    starts_on = compact(week.get("startsOn") or "")
    if not starts_on:
        return [], [], []
    rows = pacing_rows_for_announcements(knowledge, week_code)
    briefs = phase22.build_daily_teacher_briefs_for_week(
        starts_on,
        rows,
        week,
        school_year="2026-2027",
        db=None,
        plan_payload=knowledge.get("weeklyPlanPayload") or {},
    )
    warnings: list[str] = []
    for brief in briefs:
        brief["predictionMetadata"] = {
            "entryDate": brief.get("entry_date"),
            "needsReview": brief.get("needs_review"),
            "deliveryStatus": brief.get("delivery_status"),
            "scheduleIntentOnly": True,
        }
        for warning in brief.get("warnings") or []:
            warnings.append(warning)
        if any("Weather not provided" in item for section in brief.get("sections", []) for item in section.get("items", [])):
            warnings.append("Daily Brief weather input is absent")
        if brief.get("needs_review"):
            warnings.append("Daily Brief contains unresolved planning alerts")
    if len(briefs) < 5:
        warnings.append("Shortened instructional week has fewer Daily Brief previews")
    warnings.append("Daily Brief is preview-only and delivery remains blocked")
    return briefs, list(dict.fromkeys(warnings)), []


def reading_homework_for_weekday(weekday: str) -> str:
    return phase22.reading_homework_for_weekday(weekday)


def subject_active_for_week_code(subject: str, week_code: str) -> bool:
    week = phase22.instructional_week_by_code(week_code) or {}
    return phase22.subject_active_for_quarter(subject, week)


def math_investigation_number(lesson_number: int | None) -> int | None:
    if not lesson_number:
        return None
    if lesson_number < 10 or lesson_number % 10:
        return None
    return lesson_number // 10


def verified_resource(resource_type: str, lesson_ref: str | None = None, variant: str | None = None, verified: bool = False) -> dict[str, Any]:
    return asdict(
        PredictedResourceRequirement(
            resource_type=resource_type,
            lesson_ref=lesson_ref,
            variant=variant,
            resolution_status="verified" if verified else "unresolved",
            requires_review=not verified,
        )
    )


def confidence(level: str, score: float, rationale: str) -> Confidence:
    return Confidence(level=level, score=score, rationale=rationale)


def base_prediction(entry: dict[str, Any], event_type: str, in_class_title: str = "", at_home_title: str = "", *, requires_review: bool = False, decision_layer: str = "", confidence_obj: Confidence | None = None, rules_applied: list[str] | None = None, explanation: list[str] | None = None, resource_requirements: list[dict[str, Any]] | None = None, manual_override_state: str = "none", review_state: str = "approved", teacher_override: TeacherOverride | None = None, teacher_correction: TeacherCorrection | None = None, source_evidence: list[SourceEvidence] | None = None, rule_explanations: list[RuleExplanation] | None = None) -> PredictedInstructionalEvent:
    cls = {
        "lesson": PredictedLesson,
        "homework": PredictedHomework,
        "assessment": PredictedAssessment,
    }.get(event_type, PredictedInstructionalEvent)
    return cls(
        week_code=entry["weekCode"],
        subject=entry["subject"],
        weekday=entry["weekday"],
        event_type=event_type,
        lesson_number=entry.get("lessonNumber"),
        assessment_number=entry.get("assessmentNumber"),
        in_class_title=in_class_title,
        at_home_title=at_home_title,
        resource_requirements=[PredictedResourceRequirement(**item) for item in (resource_requirements or [])],
        source_pacing_reference=entry.get("sourcePacingReference") or entry.get("id") or "",
        previous_instructional_state=dict(entry.get("previousInstructionalState") or {}),
        rules_applied=list(rules_applied or []),
        explanation=list(explanation or []),
        confidence=confidence_obj or confidence("medium", 0.5, "Default prediction confidence"),
        requires_review=requires_review,
        manual_override_state=manual_override_state,
        review_state=review_state,
        source_evidence=list(source_evidence or []),
        rule_explanations=list(rule_explanations or []),
        decision_layer=decision_layer,
        canonical_week_code=entry["weekCode"],
        teacher_override=teacher_override,
        teacher_correction=teacher_correction,
    )


def math_prediction(entry: dict[str, Any], knowledge: dict[str, Any]) -> tuple[list[PredictedInstructionalEvent], list[UnresolvedDecision], list[str]]:
    predictions: list[PredictedInstructionalEvent] = []
    unresolved: list[UnresolvedDecision] = []
    warnings: list[str] = []
    lesson_number = entry.get("lessonNumber")
    assessment_number = entry.get("assessmentNumber")
    manual_override = entry.get("manualOverride") or {}
    teacher_override_state = "applied" if manual_override else "none"
    if entry.get("eventType") == "lesson":
        if math_investigation_number(lesson_number):
            investigation = math_investigation_number(lesson_number)
            in_class = f"SM5: Investigation {investigation}"
            at_home = math_homework_for_weekday(entry.get("weekday") or "")
            rules = ["math.investigation.sequence", "math.homework.weekday"]
            explanation = [
                f"Lesson {lesson_number} is on an investigation boundary.",
                f"Investigation {investigation} follows Lesson {lesson_number}.",
                "Weekday policy determines investigation-day homework.",
            ]
            resources = [verified_resource("student-book", f"SM5-L{lesson_number}", None, False)]
            predictions.append(base_prediction(entry, "lesson", in_class, at_home, decision_layer="owner-confirmed hard rules", confidence_obj=confidence("high", 0.96, "Owner-confirmed investigation sequence"), rules_applied=rules, explanation=explanation, resource_requirements=resources, manual_override_state=teacher_override_state))
            return predictions, unresolved, warnings
        in_class = f"SM5: Lesson {lesson_number}"
        at_home = math_homework_for_weekday(entry.get("weekday") or "")
        rules = ["math.lesson.increment", "math.homework.weekday"]
        explanation = [
            f"Previous completed Math lesson was {entry.get('previousLessonNumber') or lesson_number - 1}.",
            f"Normal progression advances to Lesson {lesson_number}.",
            "Weekday policy determines Math homework.",
        ]
        resources = [verified_resource("student-book", f"SM5-L{lesson_number}", None, False)]
        decision_layer = "approved teacher correction" if manual_override else "owner-confirmed hard rules"
        confidence_level = "high" if not manual_override else "medium"
        confidence_score = 0.97 if not manual_override else 0.92
        predictions.append(base_prediction(entry, "lesson", in_class, at_home, decision_layer=decision_layer, confidence_obj=confidence(confidence_level, confidence_score, "Math lesson progression uses weekday homework policy" if not manual_override else "Teacher override recorded"), rules_applied=rules, explanation=explanation, resource_requirements=resources, manual_override_state=teacher_override_state))
        return predictions, unresolved, warnings
    if entry.get("eventType") == "assessment":
        if entry.get("weekday") == "Monday":
            lesson_number = entry.get("lessonNumber") or entry.get("assessmentNumber") or int(entry.get("previousLessonNumber") or 0) + 1
            lesson_entry = {
                **entry,
                "eventType": "lesson",
                "lessonNumber": lesson_number,
                "previousLessonNumber": int(entry.get("previousLessonNumber") or lesson_number - 1),
            }
            displaced_lesson = base_prediction(
                lesson_entry,
                "lesson",
                f"SM5: Lesson {lesson_number}",
                math_homework_for_weekday(entry.get("weekday") or "Monday"),
                decision_layer="owner-confirmed hard rules",
                confidence_obj=confidence("high", 0.95, "Monday assessment displacement preserves instruction"),
                rules_applied=["math.lesson.increment", "math.monday-test-displacement", "math.homework.weekday"],
                explanation=[
                    "A calculated Math test would have occurred on Monday.",
                    "Monday advances instruction to the next available lesson.",
                    "Weekday policy determines homework on the displaced lesson day.",
                ],
                resource_requirements=[verified_resource("student-book", f"SM5-L{lesson_number}", None, False)],
                manual_override_state=teacher_override_state,
                review_state="needs_review",
            )
            predictions.append(displaced_lesson)
            assessment_day = "Tuesday"
        else:
            assessment_day = entry.get("weekday")
        if compact(entry.get("testCadenceProfile")) == "owner-unresolved":
            unresolved.append(
                UnresolvedDecision(
                    decision_id=f"math-cadence-{entry.get('assessmentNumber') or lesson_number}",
                    subject="math",
                    week_code=entry["weekCode"],
                    day=assessment_day,
                    reason="Math test cadence remains owner-unresolved.",
                    candidates=[
                        {"profile": "after-every-five-lessons-after-10", "day": assessment_day, "status": "candidate"},
                        {"profile": "after-each-ten-lesson-block", "day": assessment_day, "status": "candidate"},
                    ],
                )
            )
            warnings.append("Math test cadence remains owner-unresolved")
        title = f"SM5: Written Assessment {assessment_number or lesson_number} and SM5: Fact Assessment {assessment_number or lesson_number}"
        resources = [verified_resource("fact-practice", f"SM5-T{assessment_number or lesson_number}", None, False)]
        explanations = [
            f"Math assessment is predicted for {assessment_day}.",
            "Monday assessments shift to Tuesday to preserve instruction.",
        ]
        predictions.append(base_prediction({**entry, "weekday": assessment_day}, "assessment", title, "", requires_review=True, decision_layer="owner-confirmed hard rules", confidence_obj=confidence("medium", 0.6, "Assessment cadence depends on unresolved profile"), rules_applied=["math.assessment.cadence", "math.monday-displacement"], explanation=explanations, resource_requirements=resources, manual_override_state=teacher_override_state, review_state="needs_review"))
        return predictions, unresolved, warnings
    return predictions, unresolved, warnings


def reading_prediction(entry: dict[str, Any], knowledge: dict[str, Any]) -> tuple[list[PredictedInstructionalEvent], list[UnresolvedDecision], list[str]]:
    predictions: list[PredictedInstructionalEvent] = []
    unresolved: list[UnresolvedDecision] = []
    warnings: list[str] = []
    test_number = entry.get("assessmentNumber") or entry.get("lessonNumber")
    if entry.get("eventType") == "assessment":
        day = "Tuesday" if entry.get("weekday") == "Monday" else entry.get("weekday")
        if entry.get("weekday") == "Monday":
            predictions.append(
                base_prediction(
                    {**entry, "eventType": "lesson", "weekday": entry.get("weekday"), "eventType": "lesson"},
                    "lesson",
                    f"Reading Lesson {entry.get('lessonNumber') or test_number}",
                    "",
                    decision_layer="owner-confirmed hard rules",
                    confidence_obj=confidence("high", 0.92, "Reading lessons advance one step at a time"),
                    rules_applied=["reading.lesson.increment", "reading.monday-displacement"],
                    explanation=["Monday assessment moves to Tuesday.", "Monday becomes a normal lesson day."],
                )
            )
        title = f"RM4: Mastery Test {test_number}"
        checkout_title = f"RM4: Fluency Checkout {test_number}" if test_number and 1 <= int(test_number) <= 13 else ""
        if int(test_number or 0) == 14:
            explanation = ["Reading Test 14 has no companion checkout.", "No checkout companion exists for Test 14."]
            resources = []
        else:
            explanation = [f"Reading Test {test_number} maps to Fluency Checkout {test_number}." if checkout_title else "Reading assessments do not invent Checkouts."]
            resources = []
            if checkout_title:
                resources.append(verified_resource("reading-checkout-passage", f"RM4-C{test_number}", None, False))
        predictions.append(
            base_prediction(
                {**entry, "weekday": day},
                "assessment",
                title,
                checkout_title,
                requires_review=False,
                decision_layer="owner-confirmed hard rules",
                confidence_obj=confidence("high", 0.96 if checkout_title else 0.98, "Reading checkout mapping is owner-confirmed"),
                rules_applied=["reading.assessment.block", "reading.checkout.mapping"],
                explanation=explanation,
                resource_requirements=resources,
                manual_override_state="none",
                review_state="approved",
            )
        )
    elif entry.get("eventType") == "lesson":
        predictions.append(
            base_prediction(
                entry,
                "lesson",
                f"RM4: Lesson {entry.get('lessonNumber')}",
                reading_homework_for_weekday(entry.get("weekday") or ""),
                decision_layer="explicit current-year pacing-guide entry",
                confidence_obj=confidence("high", 0.9, "Reading lesson progression is based on the current-year pacing guide"),
                rules_applied=["reading.lesson.increment", "reading.homework.weekday"],
                explanation=[f"Reading lesson advances to {entry.get('lessonNumber')}.", "Weekday policy determines Reading homework."],
                review_state="approved",
            )
        )
    return predictions, unresolved, warnings


def spelling_prediction(entry: dict[str, Any], knowledge: dict[str, Any]) -> tuple[list[PredictedInstructionalEvent], list[UnresolvedDecision], list[str]]:
    predictions: list[PredictedInstructionalEvent] = []
    closed = set(compact(day) for day in (entry.get("calendar") or {}).get("closedWeekdays", []))
    manual = entry.get("manualOverride") or {}
    day = compact(manual.get("scheduledDay") or entry.get("weekday"))
    if not day:
        day = "Friday"
    if day == "Friday" and "Friday" in closed and not manual.get("scheduledDay"):
        day = "Thursday"
    if manual.get("scheduledDay"):
        decision_layer = "approved teacher correction"
    elif entry.get("weekday") == "Friday" and "Friday" not in closed:
        decision_layer = "owner-confirmed hard rules"
    else:
        decision_layer = "repeated FPK pacing-guide pattern"
    explanation = [f"Spelling Test {entry.get('assessmentNumber') or entry.get('lessonNumber')} prefers Friday.", f"Scheduled on {day} after calendar review."]
    if "Friday" in closed and day != "Friday":
        explanation.append("Friday is unavailable, so the nearest valid instructional day is used.")
    title = f"RM4: Spelling Test {entry.get('assessmentNumber') or entry.get('lessonNumber')}"
    predictions.append(
        base_prediction(
            {**entry, "weekday": day},
            "assessment",
            title,
            "",
            decision_layer=decision_layer,
            confidence_obj=confidence("high" if decision_layer != "repeated FPK pacing-guide pattern" else "medium", 0.94 if decision_layer != "repeated FPK pacing-guide pattern" else 0.72, "Spelling Friday preference is pattern-backed"),
            rules_applied=["spelling.fifth-lesson.test", "spelling.friday.preference"],
            explanation=explanation,
            resource_requirements=[],
            manual_override_state="applied" if manual.get("scheduledDay") else "none",
            review_state="approved" if decision_layer != "repeated FPK pacing-guide pattern" else "needs_review",
        )
    )
    return predictions, [], []


def shurley_prediction(entry: dict[str, Any], knowledge: dict[str, Any]) -> tuple[list[PredictedInstructionalEvent], list[UnresolvedDecision], list[str]]:
    predictions: list[PredictedInstructionalEvent] = []
    if entry.get("chapter") or entry.get("lesson"):
        title = f"Shurley Chapter {entry.get('chapter')} Lesson {entry.get('lesson')}" if entry.get("lesson") else f"Shurley Chapter {entry.get('chapter')}"
        predictions.append(
            base_prediction(
                entry,
                "lesson",
                title,
                "",
                decision_layer="explicit current-year pacing-guide entry",
                confidence_obj=confidence("high", 0.88, "Shurley explicit pacing entry is available"),
                rules_applied=["shurley.explicit-entry"],
                explanation=["Explicit Shurley pacing entry supplied by the source.", "Lesson is not inferred from a blind +1 progression."],
                review_state="approved",
            )
        )
        return predictions, [], []
    predictions.append(
        base_prediction(
            entry,
            "lesson",
            "Shurley pacing suggestion",
            "",
            requires_review=True,
            decision_layer="predictive suggestion",
            confidence_obj=confidence("low", 0.42, "Unsupported Shurley progression requires review"),
            rules_applied=["shurley.unsupported-progression"],
            explanation=["No explicit Shurley pacing entry is available.", "A conservative suggestion is produced for review only."],
            review_state="needs_review",
        )
    )
    return predictions, [], []


def history_science_prediction(entry: dict[str, Any], knowledge: dict[str, Any]) -> tuple[list[PredictedInstructionalEvent], list[UnresolvedDecision], list[str]]:
    subject = compact(entry.get("subject")).lower()
    week_code = entry.get("weekCode") or ""
    if not subject_active_for_week_code(subject, week_code):
        return [], [], [f"{subject.title()} is inactive this quarter and remains untouched."]
    predictions: list[PredictedInstructionalEvent] = []
    title = compact(entry.get("title") or f"{subject.title()} pacing suggestion")
    explicit = bool(entry.get("title"))
    predictions.append(
        base_prediction(
            entry,
            entry.get("eventType") or "lesson",
            title,
            "",
            requires_review=not explicit,
            decision_layer="explicit current-year pacing-guide entry" if explicit else "predictive suggestion",
            confidence_obj=confidence("medium", 0.72 if explicit else 0.47, "Active quarter subject uses explicit pacing when available"),
            rules_applied=["history-science.quarter-activation", "history-science.no-assignment-prediction"],
            explanation=[f"{subject.title()} is active this quarter.", "Assignment prediction remains disabled; agenda content only."],
            review_state="approved" if explicit else "needs_review",
        )
    )
    return predictions, [], []


def predict_entry(entry: dict[str, Any], knowledge: dict[str, Any]) -> tuple[list[PredictedInstructionalEvent], list[UnresolvedDecision], list[str]]:
    subject = compact(entry.get("subject")).lower()
    if subject == "math":
        return math_prediction(entry, knowledge)
    if subject == "reading":
        return reading_prediction(entry, knowledge)
    if subject == "spelling":
        return spelling_prediction(entry, knowledge)
    if subject == "shurley":
        return shurley_prediction(entry, knowledge)
    if subject in {"history", "science"}:
        return history_science_prediction(entry, knowledge)
    prediction = base_prediction(
        entry,
        entry.get("eventType") or "lesson",
        compact(entry.get("title")),
        "",
        requires_review=True,
        decision_layer="unresolved",
        confidence_obj=confidence("low", 0.3, "Unsupported subject"),
        rules_applied=["subject.unsupported"],
        explanation=["Unsupported subjects remain reviewable only."],
        review_state="needs_review",
    )
    return [prediction], [], [f"{subject} prediction requires review"]


def predict_week_data(week_code: str, source_path: str | Path, correction_state: dict[str, Any] | None = None) -> WeekPrediction:
    knowledge = load_pacing_knowledge(source_path)
    week = phase22.instructional_week_by_code(week_code) or {"code": week_code}
    corrections = list((correction_state or {}).get("records", []))
    predictions: list[PredictedInstructionalEvent] = []
    unresolved_decisions: list[UnresolvedDecision] = []
    warnings: list[str] = list(knowledge.get("warnings", []))
    teacher_overrides: list[TeacherOverride] = []
    teacher_corrections: list[TeacherCorrection] = []
    for raw in knowledge.get("pacingGuideEntries", []):
        entry = {
            **raw,
            "weekCode": week_code,
            "sourcePacingReference": raw.get("sourcePacingReference") or raw.get("id") or "",
            "previousInstructionalState": raw.get("previousInstructionalState") or {},
        }
        entry = apply_teacher_corrections(entry, corrections)
        if entry.get("approvedCorrection"):
            approved = entry["approvedCorrection"]
            approved_value = compact(approved.get("approvedValue"))
            manual_override = dict(entry.get("manualOverride") or {})
            low = approved_value.lower()
            if "thursday classwork" in low or ("thursday" in low and "classwork" in low):
                manual_override["classworkDay"] = "Thursday"
            elif "tuesday classwork" in low or ("tuesday" in low and "classwork" in low):
                manual_override["classworkDay"] = "Tuesday"
            elif "wednesday workbook" in low or ("wednesday" in low and "workbook" in low):
                manual_override["classworkDay"] = "Wednesday"
            elif "monday workbook" in low or ("monday" in low and "workbook" in low):
                manual_override["classworkDay"] = "Monday"
            if manual_override:
                entry["manualOverride"] = manual_override
            teacher_corrections.append(
                TeacherCorrection(
                    subject=approved.get("subject", ""),
                    week_code=approved.get("weekCode", ""),
                    day=approved.get("day", ""),
                    predicted_value=approved.get("predictedValue", ""),
                    approved_value=approved.get("approvedValue", ""),
                    correction_scope=approved.get("correctionScope", ""),
                    timestamp=approved.get("timestamp", ""),
                    reason=approved.get("reason", ""),
                    source_rule=approved.get("sourceRule", ""),
                    revision=int(approved.get("revision", 1)),
                )
            )
        if entry.get("manualOverride"):
            override_field = "classworkDay" if entry["manualOverride"].get("classworkDay") else ("scheduledDay" if entry["manualOverride"].get("scheduledDay") else "classworkDay")
            override_value = str(entry["manualOverride"].get("classworkDay") or entry["manualOverride"].get("scheduledDay") or "")
            teacher_overrides.append(TeacherOverride(
                subject=entry.get("subject", ""),
                week_code=week_code,
                day=entry.get("weekday", ""),
                field=override_field,
                value=override_value,
                scope=entry["manualOverride"].get("scope", "this occurrence only"),
                timestamp=entry["manualOverride"].get("timestamp") or "2026-07-11T00:00:00Z",
                reason=entry["manualOverride"].get("reason", ""),
                revision=int(entry["manualOverride"].get("revision", 1)),
            ))
        item_predictions, item_unresolved, item_warnings = predict_entry(entry, knowledge)
        predictions.extend(item_predictions)
        unresolved_decisions.extend(item_unresolved)
        warnings.extend(item_warnings)
    predictions, selection_warnings, selection_unresolved = annotate_graded_selection(predictions, knowledge, week_code)
    unresolved_decisions.extend(selection_unresolved)
    warnings.extend(selection_warnings)
    announcement_drafts, announcement_warnings, announcement_unresolved = annotate_announcement_drafts(knowledge, week_code, predictions)
    unresolved_decisions.extend(announcement_unresolved)
    warnings.extend(announcement_warnings)
    newsletter_draft, newsletter_update, newsletter_warnings, newsletter_unresolved = annotate_newsletter_metadata(week_code)
    unresolved_decisions.extend(newsletter_unresolved)
    warnings.extend(newsletter_warnings)
    daily_briefs, daily_brief_warnings, daily_brief_unresolved = annotate_daily_teacher_briefs(week_code, knowledge)
    unresolved_decisions.extend(daily_brief_unresolved)
    warnings.extend(daily_brief_warnings)
    if "Math test cadence remains owner-unresolved" not in warnings:
        warnings.append("Math test cadence remains owner-unresolved")
    warnings = list(dict.fromkeys(warnings))
    provenance = [
        {"sourceType": "fixture", "sourceRef": str(source_path), "details": "Phase 24 synthetic teacher-brain fixture"},
        {"sourceType": "canonical-calendar", "sourceRef": "config/curriculum/canvas/instructional-weeks-2026-2027.json", "details": "instructional week authority"},
        {"sourceType": "phase22-rules", "sourceRef": "scripts/canvas_llm_phase22/phase22_workstation.py", "details": "calendar and reading checkout authority"},
    ]
    review_state = "needs_review" if unresolved_decisions or warnings else "approved"
    return WeekPrediction(
        week_code=week_code if isinstance(week, dict) else week["code"],
        source_hierarchy=list(knowledge.get("sourceHierarchy") or DEFAULT_SOURCE_HIERARCHY),
        predictions=predictions,
        unresolved_decisions=unresolved_decisions,
        teacher_overrides=teacher_overrides,
        teacher_corrections=teacher_corrections,
        pattern_records=list(knowledge.get("patternRecords", [])),
        warnings=warnings,
        review_state=review_state,
        provenance=provenance,
        announcement_drafts=announcement_drafts,
        newsletter_draft=newsletter_draft,
        newsletter_update_announcement=newsletter_update,
        daily_teacher_briefs=daily_briefs,
    )


def validate_week_prediction(payload: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    warnings = list(payload.get("warnings", []))
    source_hierarchy = payload.get("sourceHierarchy") or []
    if source_hierarchy[:6] == DEFAULT_SOURCE_HIERARCHY:
        findings.append({"severity": "pass", "code": "source-hierarchy", "message": "Source hierarchy matches the owner-approved order", "target": "week"})
    else:
        findings.append({"severity": "fail", "code": "source-hierarchy", "message": "Source hierarchy is incorrect", "target": "week"})
    warnings = list(dict.fromkeys(warnings))
    if any("Canvas assignment due-time convention remains owner-unresolved" in w for w in warnings):
        findings.append({"severity": "warn", "code": "due-time.unresolved", "message": "Canvas assignment due-time convention remains owner-unresolved", "target": "week"})
    else:
        findings.append({"severity": "pass", "code": "due-time.resolved", "message": "Canvas assignment due-time warnings removed", "target": "week"})
    if any("Math test cadence remains owner-unresolved" in w for w in warnings):
        findings.append({"severity": "warn", "code": "math-test-cadence.unresolved", "message": "Math test cadence remains owner-unresolved", "target": "week"})
    else:
        findings.append({"severity": "pass", "code": "math-test-cadence.unresolved", "message": "Math test cadence resolved", "target": "week"})
    week = phase22.instructional_week_by_code(payload.get("weekCode") or "") or {"code": payload.get("weekCode")}
    rows = []
    for item in payload.get("predictions", []):
        if item.get("event_type") == "lesson":
            rows.append({"subject": item.get("subject"), "weekday": item.get("weekday"), "lesson": str(item.get("lesson_number") or ""), "tests": "", "entry_date": "", "title": ""})
        elif item.get("event_type") == "assessment":
            rows.append({"subject": item.get("subject"), "weekday": item.get("weekday"), "lesson": "", "tests": str(item.get("assessment_number") or ""), "entry_date": "", "title": ""})
    window_findings = phase22.validate_assessment_schedule_windows(rows, week)
    if any(item.get("severity") == "pass" and item.get("code") == "math-written.window" for item in window_findings):
        findings.append({"severity": "pass", "code": "assessment-window.math-written", "message": "Math Written Assessment window validation recorded", "target": "week"})
    if any(item.get("severity") == "pass" and item.get("code") == "reading-mastery.window" for item in window_findings):
        findings.append({"severity": "pass", "code": "assessment-window.reading-mastery", "message": "Reading Mastery Test window validation recorded", "target": "week"})
    if any(item.get("severity") == "pass" and item.get("code") == "spelling-test.window" for item in window_findings):
        findings.append({"severity": "pass", "code": "assessment-window.spelling", "message": "Spelling Test window validation recorded", "target": "week"})
    reading14 = [item for item in payload.get("predictions", []) if compact(item.get("subject")).lower() == "reading" and int(item.get("assessment_number") or 0) == 14]
    has_checkout14 = any(
        compact(item.get("at_home_title")).lower().startswith("reading checkout 14")
        or "checkout 14" in json.dumps(item, ensure_ascii=False).lower()
        for item in reading14
    )
    if reading14 and not has_checkout14 and all(not compact(item.get("at_home_title")) for item in reading14):
        findings.append({"severity": "pass", "code": "reading.checkout14", "message": "Checkout 14 is absent without warning", "target": "predictions"})
    else:
        findings.append({"severity": "fail", "code": "reading.checkout14", "message": "Checkout 14 must not be produced", "target": "predictions"})
    raw_blob = json.dumps(payload, ensure_ascii=False)
    if "https://" in raw_blob or "http://" in raw_blob:
        findings.append({"severity": "fail", "code": "links.external", "message": "External URLs are forbidden in Phase 24 predictions", "target": "predictions"})
    announcement_blob = json.dumps(payload.get("announcementDrafts") or [], ensure_ascii=False)
    if any(title in announcement_blob for title in ("RM4: Fluency Checkout 14", "Checkout 14")):
        findings.append({"severity": "fail", "code": "announcement.checkout14", "message": "Checkout 14 announcement must not be produced", "target": "announcementDrafts"})
    elif payload.get("announcementDrafts"):
        findings.append({"severity": "pass", "code": "announcement.checkout14", "message": "Announcement layer excludes Checkout 14", "target": "announcementDrafts"})
    if payload.get("announcementDrafts") and all(item.get("teacherApprovalRequired") is not False for item in payload.get("announcementDrafts", [])):
        findings.append({"severity": "pass", "code": "announcement.approval-required", "message": "Announcement drafts require teacher approval", "target": "announcementDrafts"})
    if payload.get("announcementDrafts") and all((item.get("schedule_metadata") or {}).get("scheduleIntent") == phase22.ANNOUNCEMENT_SCHEDULE_INTENT for item in payload.get("announcementDrafts", [])):
        findings.append({"severity": "pass", "code": "announcement.schedule-intent", "message": "Announcement schedule intent is Friday 4:00 PM America/New_York", "target": "announcementDrafts"})
    newsletter = payload.get("newsletterDraft") or {}
    update = payload.get("newsletterUpdateAnnouncement") or {}
    if newsletter.get("course_id") == 26427 and newsletter.get("cadence") == "monthly":
        findings.append({"severity": "pass", "code": "newsletter.monthly", "message": "Homeroom newsletter metadata is monthly on course 26427", "target": "newsletterDraft"})
    else:
        findings.append({"severity": "fail", "code": "newsletter.monthly", "message": "Homeroom newsletter metadata is missing or incorrect", "target": "newsletterDraft"})
    if update.get("body_text") == phase22.newsletter_update_body(update.get("month_label") or ""):
        findings.append({"severity": "pass", "code": "newsletter-update.wording", "message": "Newsletter update announcement uses canonical wording", "target": "newsletterUpdateAnnouncement"})
    else:
        findings.append({"severity": "fail", "code": "newsletter-update.wording", "message": "Newsletter update announcement wording is incorrect", "target": "newsletterUpdateAnnouncement"})
    if update.get("depends_on") == newsletter.get("local_object_id") and not update.get("page_url"):
        findings.append({"severity": "pass", "code": "newsletter-update.dependency", "message": "Newsletter update announcement depends on blocked newsletter page", "target": "newsletterUpdateAnnouncement"})
    else:
        findings.append({"severity": "fail", "code": "newsletter-update.dependency", "message": "Newsletter update announcement dependency is incorrect", "target": "newsletterUpdateAnnouncement"})
    if update and update.get("schedule_metadata") is None:
        findings.append({"severity": "pass", "code": "newsletter-update.schedule", "message": "Newsletter update announcement does not inherit assessment schedule", "target": "newsletterUpdateAnnouncement"})
    else:
        findings.append({"severity": "fail", "code": "newsletter-update.schedule", "message": "Newsletter update announcement must not inherit assessment schedule", "target": "newsletterUpdateAnnouncement"})
    briefs = payload.get("dailyTeacherBriefs") or []
    if briefs and all(item.get("delivery_status") == "blocked_preview" for item in briefs):
        findings.append({"severity": "pass", "code": "daily-brief.preview-only", "message": "Daily Brief previews remain blocked", "target": "dailyTeacherBriefs"})
    else:
        findings.append({"severity": "fail", "code": "daily-brief.preview-only", "message": "Daily Brief previews must remain blocked", "target": "dailyTeacherBriefs"})
    if briefs and all(item.get("recipientConfigured") is not False and item.get("recipientDisplay") == "Teacher" for item in briefs):
        findings.append({"severity": "pass", "code": "daily-brief.recipient", "message": "Daily Brief recipient metadata remains redacted", "target": "dailyTeacherBriefs"})
    else:
        findings.append({"severity": "fail", "code": "daily-brief.recipient", "message": "Daily Brief recipient metadata must remain redacted", "target": "dailyTeacherBriefs"})
    if briefs and all((item.get("schedule_metadata") or {}).get("scheduleIntentOnly") for item in briefs):
        findings.append({"severity": "pass", "code": "daily-brief.schedule-intent", "message": "Daily Brief scheduling intent is preview-only", "target": "dailyTeacherBriefs"})
    else:
        findings.append({"severity": "fail", "code": "daily-brief.schedule-intent", "message": "Daily Brief scheduling intent must remain preview-only", "target": "dailyTeacherBriefs"})
    pass_count = sum(1 for item in findings if item["severity"] == "pass")
    warn_count = sum(1 for item in findings if item["severity"] == "warn")
    fail_count = sum(1 for item in findings if item["severity"] == "fail")
    return {"passCount": pass_count, "warnCount": warn_count, "failCount": fail_count, "findings": findings}, warnings
