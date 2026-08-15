"""Canonical-vs-downstream drift detector (Phase 18C).

Validates that downstream preparation (Phase 18B translation + preview assembly)
preserved canonical meaning. Fail-closed: any semantic drift produces
``invalid_drift`` entries and ``DriftReport.ok == False``.
"""

from __future__ import annotations

from typing import Any

from scripts.canvas_llm_phase18a.models import KNOWN_COURSES, WEEKDAYS, WeeklyPlan
from scripts.canvas_llm_phase18b.translation import SUBJECT_KEYS, TranslationResult

from .contracts import DriftFinding, DriftReport

# Strings that must never appear as downstream defaults for a blank canonical day.
_FORBIDDEN_BLANK_DEFAULTS = (
    "no homework",
    "no class",
    "continue",
    "tbd",
    "to be determined",
    "none",
)


def _key(subject: str, weekday: str) -> tuple[str, str]:
    return (subject, weekday)


def detect_drift(plan: WeeklyPlan, result: TranslationResult) -> DriftReport:
    findings: list[DriftFinding] = []
    invalid: list[str] = []
    exact_matches = 0
    expected_derivations = 0
    unresolved_differences = 0

    # 1. Date/week identity did not drift.
    if result.week_code != plan.week_code:
        invalid.append(f"week_code drifted: canonical={plan.week_code!r} downstream={result.week_code!r}")
    for expected_date, label in ((plan.monday_date, "monday"), (plan.friday_date, "friday")):
        if expected_date and expected_date not in (result.agenda.get("schedule_summary") or ""):
            # schedule summary embeds the date range; verify against agenda title too.
            title = result.agenda.get("title") or ""
            if expected_date not in title and expected_date not in (result.agenda.get("schedule_summary") or ""):
                invalid.append(f"{label} date drifted from canonical {expected_date!r}")
    findings.append(DriftFinding("exact_match", "week", f"week_code={plan.week_code}"))

    # Index downstream prediction events by (subject, weekday).
    events = result.prediction.get("predictions", [])
    event_index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for event in events:
        event_index.setdefault(_key(event.get("subject", ""), event.get("weekday", "")), []).append(event)

    # Index blanks and unresolved by canonical reference.
    blank_index = {(b["course"], b["weekday"]) for b in result.blanks}
    unresolved_index = {(u["course"], u["weekday"]) for u in result.unresolved}

    for course_name in KNOWN_COURSES:
        course = plan.courses.get(course_name)
        if course is None:
            continue
        subject = SUBJECT_KEYS.get(course_name, course_name)
        for day in course.days:
            key = _key(subject, day.weekday)
            if day.blank:
                # Blank must stay blank: no downstream event, no default text.
                if key in event_index:
                    invalid.append(f"blank {course_name} {day.weekday} gained a downstream event")
                elif (course_name, day.weekday) not in blank_index:
                    invalid.append(f"blank {course_name} {day.weekday} not recorded downstream")
                else:
                    findings.append(DriftFinding("exact_match", f"{subject}:{day.weekday}", "blank preserved"))
                    exact_matches += 1
                continue

            ambiguous = bool(day.ambiguity) and not day.in_class and not day.homework
            if ambiguous:
                if (course_name, day.weekday) not in unresolved_index:
                    invalid.append(f"unresolved {course_name} {day.weekday} lost its unresolved record")
                # If an event exists for a non-protected course, it must be marked unresolved.
                for event in event_index.get(key, []):
                    if event.get("decision_layer") != "unresolved":
                        invalid.append(f"unresolved {course_name} {day.weekday} became {event.get('decision_layer')!r}")
                    elif event.get("in_class_title") or event.get("at_home_title"):
                        invalid.append(f"unresolved {course_name} {day.weekday} was guessed with content")
                unresolved_differences += 1
                findings.append(DriftFinding("unresolved_difference", f"{subject}:{day.weekday}", "ambiguity preserved as unresolved"))
                continue

            # Concrete, non-blank, non-ambiguous day.
            if course.protected:
                # Protected course: no write-eligible downstream event may exist.
                if key in event_index:
                    invalid.append(f"protected {course_name} {day.weekday} produced a downstream event")
                else:
                    findings.append(DriftFinding("exact_match", f"{subject}:{day.weekday}", "protected content blocked"))
                    exact_matches += 1
                continue

            matching = event_index.get(key, [])
            if len(matching) != 1:
                invalid.append(
                    f"{course_name} {day.weekday} maps to {len(matching)} downstream events (expected exactly 1)"
                )
                continue
            event = matching[0]

            # Canonical text must not be replaced.
            if event.get("in_class_title") != day.in_class:
                invalid.append(
                    f"{course_name} {day.weekday} in_class replaced: "
                    f"canonical={day.in_class!r} downstream={event.get('in_class_title')!r}"
                )
            if event.get("at_home_title") != day.homework:
                invalid.append(
                    f"{course_name} {day.weekday} homework replaced: "
                    f"canonical={day.homework!r} downstream={event.get('at_home_title')!r}"
                )

            # Teacher-decided state must remain teacher-decided.
            if day.decided_source == "teacher_instruction":
                if event.get("decision_layer") != "teacher_instruction":
                    invalid.append(f"{course_name} {day.weekday} lost teacher_instruction decision layer")
                if event.get("manual_override_state") != "teacher":
                    invalid.append(f"{course_name} {day.weekday} lost teacher override state")
            elif event.get("decision_layer") != day.decided_source:
                invalid.append(
                    f"{course_name} {day.weekday} decision layer drifted: "
                    f"canonical={day.decided_source!r} downstream={event.get('decision_layer')!r}"
                )

            # No fabricated identifiers / unauthorized defaults.
            if event.get("lesson_number") is not None or event.get("assessment_number") is not None:
                invalid.append(f"{course_name} {day.weekday} fabricated a lesson/assessment number")

            exact_matches += 1
            expected_derivations += 1
            findings.append(DriftFinding("expected_derivation", f"{subject}:{day.weekday}", "canonical content preserved downstream"))

    # 2. No unexpected downstream course/day appears (cross-course leakage check).
    valid_keys = set()
    for course_name in KNOWN_COURSES:
        course = plan.courses.get(course_name)
        if course is None:
            continue
        subject = SUBJECT_KEYS.get(course_name, course_name)
        for day in course.days:
            if day.blank or course.protected:
                continue
            valid_keys.add(_key(subject, day.weekday))
    for event in events:
        event_key = _key(event.get("subject", ""), event.get("weekday", ""))
        if event_key not in valid_keys:
            invalid.append(f"unexpected downstream event for {event_key!r} (not in canonical plan)")

    # 3. No downstream subject workspace leaks across courses.
    canonical_subjects = {SUBJECT_KEYS[c] for c in plan.courses if c in SUBJECT_KEYS}
    workspace_subjects = {s.get("subject") for s in result.subjects}
    if workspace_subjects != canonical_subjects:
        invalid.append(
            f"subject workspace set drifted: canonical={sorted(canonical_subjects)} downstream={sorted(workspace_subjects)}"
        )

    # 4. Protected courses remain blocked downstream.
    for course_name in plan.protected_courses:
        if course_name not in SUBJECT_KEYS:
            continue
        subject = SUBJECT_KEYS[course_name]
        snapshot = next((s for s in result.subjects if s.get("subject") == subject), None)
        if snapshot is None:
            invalid.append(f"protected {course_name} missing its subject snapshot")
        elif snapshot.get("assignmentPolicy") != "disabled" or snapshot.get("readinessState") != "Blocked":
            invalid.append(f"protected {course_name} is not blocked downstream")

    report = DriftReport(
        exact_matches=exact_matches,
        expected_derivations=expected_derivations,
        unresolved_differences=unresolved_differences,
        invalid_drift=invalid,
        findings=findings,
    )
    return report
