from __future__ import annotations

import json
from dataclasses import asdict
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


def math_homework_title(lesson_number: int, hint_override: str | None = None) -> str:
    base = f"SM5: Lesson {lesson_number}"
    hint = compact(hint_override).lower()
    if hint in {"evens", "even"}:
        return f"{base} Evens"
    if hint in {"odds", "odd"}:
        return f"{base} Odds"
    if hint in {"none", "no", "off"}:
        return base
    return f"{base} {'Evens' if lesson_number % 2 == 0 else 'Odds'}"


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
            at_home = f"SM5: Investigation {investigation} Study Guide"
            rules = ["math.investigation.sequence", "math.investigation.study-guide"]
            explanation = [
                f"Lesson {lesson_number} is on an investigation boundary.",
                f"Investigation {investigation} follows Lesson {lesson_number}.",
                "Investigation homework is the applicable Study Guide.",
            ]
            resources = [
                verified_resource("investigation-study-guide", f"SM5-I{investigation}", None, False),
                verified_resource("student-book", f"SM5-L{lesson_number}", None, False),
            ]
            predictions.append(base_prediction(entry, "lesson", in_class, at_home, decision_layer="owner-confirmed hard rules", confidence_obj=confidence("high", 0.96, "Owner-confirmed investigation sequence"), rules_applied=rules, explanation=explanation, resource_requirements=resources, manual_override_state=teacher_override_state))
            return predictions, unresolved, warnings
        in_class = f"SM5: Lesson {lesson_number}"
        at_home = math_homework_title(lesson_number, manual_override.get("homeworkParity") or entry.get("hintOverride"))
        rules = ["math.lesson.increment", "math.homework.parity"]
        if compact(manual_override.get("homeworkParity")).lower() in {"evens", "odds"}:
            rules.append("math.homework.parity.override")
        explanation = [
            f"Previous completed Math lesson was {entry.get('previousLessonNumber') or lesson_number - 1}.",
            f"Normal progression advances to Lesson {lesson_number}.",
            "Parity determines the homework suffix unless a teacher override applies.",
        ]
        resources = [
            verified_resource("student-book", f"SM5-L{lesson_number}", None, False),
            verified_resource("homework-recording-sheet", f"SM5-L{lesson_number}", "even" if lesson_number % 2 == 0 else "odd", False),
        ]
        decision_layer = "approved teacher correction" if manual_override else "owner-confirmed hard rules"
        confidence_level = "high" if not manual_override else "medium"
        confidence_score = 0.97 if not manual_override else 0.92
        predictions.append(base_prediction(entry, "lesson", in_class, at_home, decision_layer=decision_layer, confidence_obj=confidence(confidence_level, confidence_score, "Math lesson progression and parity are owner-confirmed" if not manual_override else "Teacher override changes the homework parity"), rules_applied=rules, explanation=explanation, resource_requirements=resources, manual_override_state=teacher_override_state))
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
                "Study Guide only",
                decision_layer="owner-confirmed hard rules",
                confidence_obj=confidence("high", 0.95, "Monday assessment displacement preserves instruction"),
                rules_applied=["math.lesson.increment", "math.monday-test-displacement"],
                explanation=[
                    "A calculated Math test would have occurred on Monday.",
                    "Monday advances instruction to the next available lesson.",
                    "Ordinary Odds/Evens homework is suppressed and Study Guide only is assigned.",
                ],
                resource_requirements=[
                    verified_resource("student-book", f"SM5-L{lesson_number}", None, False),
                    verified_resource("study-guide", f"SM5-T{assessment_number or lesson_number}", "only", False),
                ],
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
        title = f"Math Written Test {assessment_number or lesson_number} and Fact Test {assessment_number or lesson_number}"
        resources = [
            verified_resource("study-guide", f"SM5-T{assessment_number or lesson_number}", "blank", False),
            verified_resource("study-guide", f"SM5-T{assessment_number or lesson_number}", "completed", False),
            verified_resource("fact-practice", f"SM5-T{assessment_number or lesson_number}", None, False),
        ]
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
        title = f"Reading Mastery Test {test_number}"
        checkout_title = f"Reading Checkout {test_number}" if test_number and 1 <= int(test_number) <= 13 else ""
        if int(test_number or 0) == 14:
            explanation = ["Reading Test 14 has no companion checkout.", "No checkout companion exists for Test 14."]
            resources = [verified_resource("reading-study-guide", f"RM4-T14", None, False)]
        else:
            explanation = [f"Reading Test {test_number} maps to Checkout {test_number}." if checkout_title else "Reading assessments do not invent Checkouts."]
            resources = [verified_resource("reading-study-guide", f"RM4-T{test_number}", None, False)]
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
                f"Reading Lesson {entry.get('lessonNumber')}",
                "",
                decision_layer="explicit current-year pacing-guide entry",
                confidence_obj=confidence("high", 0.9, "Reading lesson progression is based on the current-year pacing guide"),
                rules_applied=["reading.lesson.increment"],
                explanation=[f"Reading lesson advances to {entry.get('lessonNumber')}.", "No checkout is created for lesson predictions."],
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
    title = f"Spelling Test {entry.get('assessmentNumber') or entry.get('lessonNumber')}"
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
            resource_requirements=[verified_resource("spelling-focus-words", f"SPELL-{entry.get('assessmentNumber') or entry.get('lessonNumber')}", None, False)],
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
    predictions: list[PredictedInstructionalEvent] = []
    title = compact(entry.get("title") or f"{entry.get('subject', '').title()} pacing suggestion")
    explicit = bool(entry.get("title"))
    predictions.append(
        base_prediction(
            entry,
            entry.get("eventType") or "lesson",
            title,
            "",
            requires_review=True,
            decision_layer="explicit current-year pacing-guide entry" if explicit else "predictive suggestion",
            confidence_obj=confidence("low", 0.47 if not explicit else 0.67, "History and Science stay conservative and reviewable"),
            rules_applied=["history-science.no-assignment-prediction"],
            explanation=["History and Science use explicit current-year entries when available.", "Assignment prediction remains disabled."],
            review_state="needs_review",
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
            if "odds" in approved_value.lower():
                manual_override["homeworkParity"] = "odds"
            elif "evens" in approved_value.lower():
                manual_override["homeworkParity"] = "evens"
            if "thursday" in approved_value.lower():
                manual_override["scheduledDay"] = "Thursday"
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
            teacher_overrides.append(TeacherOverride(
                subject=entry.get("subject", ""),
                week_code=week_code,
                day=entry.get("weekday", ""),
                field="scheduledDay" if entry["manualOverride"].get("scheduledDay") else "homeworkParity",
                value=str(entry["manualOverride"].get("scheduledDay") or entry["manualOverride"].get("homeworkParity") or ""),
                scope=entry["manualOverride"].get("scope", "this occurrence only"),
                timestamp=entry["manualOverride"].get("timestamp") or "2026-07-11T00:00:00Z",
                reason=entry["manualOverride"].get("reason", ""),
                revision=int(entry["manualOverride"].get("revision", 1)),
            ))
        item_predictions, item_unresolved, item_warnings = predict_entry(entry, knowledge)
        predictions.extend(item_predictions)
        unresolved_decisions.extend(item_unresolved)
        warnings.extend(item_warnings)
    if "Math test cadence remains owner-unresolved" not in warnings:
        warnings.append("Math test cadence remains owner-unresolved")
    if "Canvas assignment due-time convention remains owner-unresolved" not in warnings:
        warnings.append("Canvas assignment due-time convention remains owner-unresolved")
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
        findings.append({"severity": "fail", "code": "due-time.unresolved", "message": "Canvas assignment due-time warning missing", "target": "week"})
    if any("Math test cadence remains owner-unresolved" in w for w in warnings):
        findings.append({"severity": "warn", "code": "math-test-cadence.unresolved", "message": "Math test cadence remains owner-unresolved", "target": "week"})
    else:
        findings.append({"severity": "pass", "code": "math-test-cadence.unresolved", "message": "Math test cadence resolved", "target": "week"})
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
    pass_count = sum(1 for item in findings if item["severity"] == "pass")
    warn_count = sum(1 for item in findings if item["severity"] == "warn")
    fail_count = sum(1 for item in findings if item["severity"] == "fail")
    return {"passCount": pass_count, "warnCount": warn_count, "failCount": fail_count, "findings": findings}, warnings
