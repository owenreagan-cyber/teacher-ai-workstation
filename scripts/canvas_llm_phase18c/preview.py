"""Read-only Teacher Preview assembly (Phase 18C).

``assemble_teacher_preview(weekly_plan, runtime_context)`` validates the
canonical plan, translates it through Phase 18B, runs collision + drift
detection, evaluates readiness, and returns a deterministic ``TeacherPreview``.

No writes. No Canvas mutation. No token use. No network.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from scripts.canvas_llm_phase18a.models import KNOWN_COURSES, WEEKDAYS, DayEntry, WeeklyPlan
from scripts.canvas_llm_phase18a.validation import validate_plan
from scripts.canvas_llm_phase18b.translation import (
    SUBJECT_KEYS,
    TranslationResult,
    stable_plan_id,
    translate_weekly_plan,
)

from .contracts import (
    Derivation,
    PreviewCourse,
    PreviewDay,
    ReadinessState,
    RuntimeContext,
    TeacherPreview,
)
from .drift import detect_drift

# Required live Canvas configuration fields per requested artifact type. Missing
# any of these for a non-protected course blocks preview with
# BLOCKED_MISSING_CONFIG; IDs are never guessed.
REQUIRED_CONFIG_FIELDS: dict[str, list[str]] = {
    "page": ["course_id", "module_id"],
    "assignment": ["course_id", "assignment_group_id"],
    "announcement": ["course_id"],
    "newsletter-front-page": ["course_id"],
}

AUTHORITATIVE_SOURCES = frozenset({"teacher_instruction", "live_pacing", "canonical_rule"})


def _day_status(day: DayEntry, protected: bool) -> str:
    if protected:
        return "protected"
    if day.blank:
        return "blank"
    if day.ambiguity and not day.in_class and not day.homework:
        return "unresolved"
    return "content"


def _day_derivation(day: DayEntry, protected: bool) -> str:
    if protected:
        return Derivation.PROTECTED.value
    if day.blank:
        return Derivation.BLANK.value
    if day.ambiguity and not day.in_class and not day.homework:
        return Derivation.UNRESOLVED.value
    return Derivation.CANONICAL.value


def _detect_collisions(plan: WeeklyPlan) -> list[str]:
    """Detect two canonical course names mapping to the same downstream key."""
    collisions: list[str] = []
    seen: dict[str, str] = {}
    for course_name in plan.courses:
        if course_name not in SUBJECT_KEYS:
            continue
        subject = SUBJECT_KEYS[course_name]
        if subject in seen and seen[subject] != course_name:
            collisions.append(
                f"subject key collision: {seen[subject]!r} and {course_name!r} both map to {subject!r}"
            )
        seen[subject] = course_name
    return collisions


def _missing_config(plan: WeeklyPlan, runtime: RuntimeContext) -> list[str]:
    """Return diagnostics for missing live Canvas configuration (never guess)."""
    missing: list[str] = []
    for course_name, course in plan.courses.items():
        if course.protected:
            continue
        if not course.requested_artifacts:
            continue
        subject = SUBJECT_KEYS.get(course_name, course_name)
        cfg = runtime.canvas_config.get(subject) or {}
        for artifact in course.requested_artifacts:
            for field in REQUIRED_CONFIG_FIELDS.get(artifact, []):
                if not str(cfg.get(field) or "").strip():
                    missing.append(
                        f"missing {field} for {course_name} ({subject}) to satisfy requested artifact {artifact!r}"
                    )
    return missing


def evaluate_readiness(
    missing_config: list[str],
    unresolved_policy: list[str],
    unresolved: list[dict[str, Any]],
    protected: list[str],
    advisory_only: bool,
) -> str:
    if missing_config:
        return ReadinessState.BLOCKED_MISSING_CONFIG.value
    if unresolved_policy:
        return ReadinessState.BLOCKED_POLICY.value
    if unresolved:
        return ReadinessState.BLOCKED_UNRESOLVED.value
    if protected:
        return ReadinessState.BLOCKED_PROTECTED.value
    if advisory_only:
        return ReadinessState.ADVISORY_ONLY.value
    return ReadinessState.READY_FOR_REVIEW.value


def _week_title(plan: WeeklyPlan) -> str:
    if plan.week_code:
        return f"Quarter {plan.quarter}, Week {plan.week_number} | {plan.monday_date} .. {plan.friday_date}"
    return f"Week of {plan.monday_date}"


def _build_courses(plan: WeeklyPlan) -> list[PreviewCourse]:
    courses: list[PreviewCourse] = []
    for course_name in KNOWN_COURSES:
        course = plan.courses.get(course_name)
        if course is None:
            continue
        subject = SUBJECT_KEYS.get(course_name, course_name)
        days: list[PreviewDay] = []
        for day in course.days:
            days.append(
                PreviewDay(
                    weekday=day.weekday,
                    date=day.date,
                    in_class=day.in_class,
                    homework=day.homework,
                    raw=day.raw,
                    source=day.decided_source or "canonical_rule",
                    derivation=_day_derivation(day, course.protected),
                    evidence=[e.to_dict() for e in day.evidence],
                    status=_day_status(day, course.protected),
                    protected=course.protected,
                )
            )
        if course.protected:
            readiness = "Blocked"
            policy = "disabled"
        else:
            readiness = "Ready"
            policy = "enabled"
        courses.append(
            PreviewCourse(
                course=course_name,
                subject_key=subject,
                protected=course.protected,
                days=days,
                requested_artifacts=list(course.requested_artifacts),
                readiness=readiness,
                assignment_policy=policy,
            )
        )
    return courses


def _build_day_view(plan: WeeklyPlan) -> list[dict[str, Any]]:
    """Aggregate a deterministic Mon-Fri view of per-course content."""
    day_view: list[dict[str, Any]] = []
    for weekday in WEEKDAYS:
        entries: dict[str, dict[str, Any]] = {}
        for course_name in KNOWN_COURSES:
            course = plan.courses.get(course_name)
            if course is None:
                continue
            day = next((d for d in course.days if d.weekday == weekday), None)
            if day is None:
                continue
            entries[course_name] = {
                "in_class": day.in_class,
                "homework": day.homework,
                "status": _day_status(day, course.protected),
                "source": day.decided_source or "canonical_rule",
            }
        day_view.append({"weekday": weekday, "courses": entries})
    return day_view


def assemble_teacher_preview(plan: WeeklyPlan, runtime: RuntimeContext | None = None) -> TeacherPreview:
    """Assemble a deterministic, read-only Teacher Preview.

    Raises ValueError (fails closed) if the canonical plan is invalid or if
    downstream subject-key collisions are detected.
    """
    runtime = runtime or RuntimeContext()
    report = validate_plan(plan)
    if not report.ok:
        raise ValueError("invalid WeeklyPlan: " + "; ".join(report.errors))

    plan_id = stable_plan_id(plan)
    translation: TranslationResult = translate_weekly_plan(plan)

    warnings: list[str] = list(plan.warnings) + list(report.warnings)
    collisions = _detect_collisions(plan)
    if collisions:
        raise ValueError("downstream subject-key collision: " + "; ".join(collisions))

    missing = _missing_config(plan, runtime)

    unresolved_policy: list[str] = []
    if runtime.due_time_policy != "resolved":
        reason = runtime.due_time_reason or "Canvas assignment due-time convention unresolved"
        unresolved_policy.append(reason)
        warnings.append(reason)

    # Protected / unresolved / blank canonical state.
    protected = list(dict.fromkeys(translation.protected))
    unresolved = list(translation.unresolved)

    # Advisory-only: no authoritative canonical decision among concrete days.
    concrete_decided = [
        day.decided_source
        for course in plan.courses.values()
        for day in course.days
        if not course.protected and not day.blank
        and not (day.ambiguity and not day.in_class and not day.homework)
        and day.decided_source
    ]
    advisory_only = bool(concrete_decided) and not any(
        src in AUTHORITATIVE_SOURCES for src in concrete_decided
    )

    blocked_reasons: list[str] = []
    if missing:
        blocked_reasons.append("Missing live Canvas configuration")
    if unresolved_policy:
        blocked_reasons.append("Owner policy unresolved (due-time convention)")
    if unresolved:
        blocked_reasons.append("Canonical content remains unresolved")
    if protected:
        blocked_reasons.append("Protected course(s) remain write-blocked")

    readiness = evaluate_readiness(
        missing, unresolved_policy, unresolved, protected, advisory_only
    )

    drift = detect_drift(plan, translation)

    preview = TeacherPreview(
        week_code=plan.week_code,
        monday_date=plan.monday_date,
        friday_date=plan.friday_date,
        timezone=plan.timezone,
        week_title=_week_title(plan),
        courses=_build_courses(plan),
        days=_build_day_view(plan),
        agenda=translation.agenda,
        prediction=translation.prediction,
        workstation={"subjects": translation.subjects},
        unresolved=unresolved,
        protected=protected,
        missing_config=sorted(set(missing)),
        unresolved_policy=unresolved_policy,
        warnings=sorted(set(warnings)),
        blocked_reasons=blocked_reasons,
        readiness=readiness,
        provenance=[
            {"sourceType": "canonical-weekly-plan", "sourceRef": plan_id, "details": "Phase 18A canonical WeeklyPlan"},
            {"sourceType": "translation", "sourceRef": translation.plan_id, "details": "Phase 18B validated translation"},
            {"sourceType": "drift-report", "sourceRef": "detect_drift", "details": f"exact_matches={drift.exact_matches} expected_derivations={drift.expected_derivations} invalid_drift={len(drift.invalid_drift)}"},
        ],
        drift=asdict(drift),
    )
    return preview
