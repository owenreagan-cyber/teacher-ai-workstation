"""Validation for the canonical WeeklyPlan (Phase 18A).

Validation is strict about structural and provenance integrity:

- required Monday-Friday week/date consistency
- known course names only
- blank remains blank (no guessing)
- unresolved ambiguity can be represented without guessing
- invalid/contradictory plans fail validation
- protected courses remain explicit
- a value decided by a lower-precedence source must not override a
  higher-precedence source (precedent never overrides pacing or instruction)
- anomalies are never promoted into deciding rules
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .models import (
    KNOWN_COURSES,
    REQUESTED_ARTIFACT_TYPES,
    SCHEMA,
    VERSION,
    WEEKDAYS,
    WeeklyPlan,
)
from .precedent import is_anomaly, is_valid_precedent_class
from .source_precedence import VALID_SOURCE_CLASSES, precedence_rank


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _parse_date(value: str) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _validate_day(course_name: str, day, errors: list[str], warnings: list[str]) -> None:
    if day.weekday not in WEEKDAYS:
        errors.append(f"course {course_name!r} has invalid weekday {day.weekday!r}")
        return

    day_index = WEEKDAYS.index(day.weekday)
    parsed = _parse_date(day.date)
    if day.date and parsed is None:
        errors.append(f"course {course_name!r} {day.weekday} date {day.date!r} is invalid")
    elif parsed is not None and parsed.weekday() != day_index:
        errors.append(
            f"course {course_name!r} {day.weekday} date {day.date} does not fall on {day.weekday}"
        )

    # Blank remains blank.
    if day.blank and (day.in_class or day.homework or day.raw):
        errors.append(
            f"course {course_name!r} {day.weekday} is marked blank but has content"
        )

    # Unresolved shorthand must be represented explicitly, not guessed.
    if not day.blank and day.raw and not day.in_class and not day.homework and not day.ambiguity:
        warnings.append(
            f"course {course_name!r} {day.weekday} has raw shorthand {day.raw!r} "
            "but no normalized interpretation or ambiguity note"
        )

    if day.decided_source:
        if day.decided_source not in VALID_SOURCE_CLASSES:
            errors.append(
                f"course {course_name!r} {day.weekday} decided_source "
                f"{day.decided_source!r} is not a valid source class"
            )
        else:
            higher = [
                e.source_class
                for e in day.evidence
                if e.source_class in VALID_SOURCE_CLASSES
                and precedence_rank(e.source_class) < precedence_rank(day.decided_source)
            ]
            if higher:
                errors.append(
                    f"course {course_name!r} {day.weekday} decided_source "
                    f"{day.decided_source!r} is lower precedence than evidence source(s) "
                    f"{sorted(set(higher))}"
                )

    for e in day.evidence:
        if e.source_class and e.source_class not in VALID_SOURCE_CLASSES:
            errors.append(
                f"course {course_name!r} {day.weekday} has evidence with invalid "
                f"source_class {e.source_class!r}"
            )
        if e.source_class == "precedent":
            if not e.precedent_class:
                errors.append(
                    f"course {course_name!r} {day.weekday} precedent evidence is "
                    "missing precedent_class"
                )
            elif not is_valid_precedent_class(e.precedent_class):
                errors.append(
                    f"course {course_name!r} {day.weekday} precedent evidence has "
                    f"invalid precedent_class {e.precedent_class!r}"
                )
            elif is_anomaly(e.precedent_class) and day.decided_source == "precedent":
                errors.append(
                    f"course {course_name!r} {day.weekday} promotes an anomaly "
                    "precedent to a deciding rule"
                )


def validate_plan(plan: WeeklyPlan) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    if plan.schema != SCHEMA:
        errors.append(f"schema must be {SCHEMA!r}, got {plan.schema!r}")
    if plan.version != VERSION:
        errors.append(f"version must be {VERSION}, got {plan.version!r}")

    if not plan.school_year:
        errors.append("school_year is required")
    if not (1 <= plan.quarter <= 4):
        errors.append(f"quarter must be 1-4, got {plan.quarter!r}")
    if plan.week_number < 1:
        errors.append(f"week_number must be >= 1, got {plan.week_number!r}")
    if not plan.timezone:
        errors.append("timezone is required")

    expected_code = f"Q{plan.quarter}W{plan.week_number}" if plan.quarter and plan.week_number else ""
    if plan.week_code and expected_code and plan.week_code != expected_code:
        errors.append(
            f"week_code {plan.week_code!r} does not match quarter/week {expected_code!r}"
        )

    monday = _parse_date(plan.monday_date)
    friday = _parse_date(plan.friday_date)
    if monday is None:
        errors.append(f"monday_date must be YYYY-MM-DD, got {plan.monday_date!r}")
    elif monday.weekday() != 0:
        errors.append(f"monday_date {plan.monday_date} is not a Monday")
    if friday is None:
        errors.append(f"friday_date must be YYYY-MM-DD, got {plan.friday_date!r}")
    elif friday.weekday() != 4:
        errors.append(f"friday_date {plan.friday_date} is not a Friday")
    if monday is not None and friday is not None and (friday - monday).days != 4:
        errors.append(
            f"friday_date must be monday_date + 4 days, got "
            f"{plan.monday_date} .. {plan.friday_date}"
        )

    if not plan.courses:
        errors.append("at least one course is required")

    for course_name, course in plan.courses.items():
        if course_name not in KNOWN_COURSES:
            errors.append(
                f"unknown course name {course_name!r}; known courses are {KNOWN_COURSES}"
            )
        if course.course and course.course != course_name:
            errors.append(
                f"course key {course_name!r} does not match course.course {course.course!r}"
            )
        day_names = [d.weekday for d in course.days]
        if day_names != WEEKDAYS:
            errors.append(
                f"course {course_name!r} must have exactly Monday-Friday in order; "
                f"got {day_names}"
            )
        for day in course.days:
            _validate_day(course_name, day, errors, warnings)
        for artifact in course.requested_artifacts:
            if artifact not in REQUESTED_ARTIFACT_TYPES:
                errors.append(
                    f"course {course_name!r} requests unknown artifact type {artifact!r}"
                )
        if course.protected and course_name not in plan.protected_courses:
            errors.append(
                f"course {course_name!r} is protected but not listed in protected_courses"
            )

    for protected in plan.protected_courses:
        if protected in KNOWN_COURSES and protected not in plan.courses:
            errors.append(f"protected course {protected!r} is missing from courses")
        elif protected in plan.courses and not plan.courses[protected].protected:
            errors.append(
                f"protected course {protected!r} is not marked protected=True"
            )

    return ValidationReport(errors=errors, warnings=warnings)
