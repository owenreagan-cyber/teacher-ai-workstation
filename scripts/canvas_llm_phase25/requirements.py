from __future__ import annotations

from typing import Any

from .models import ResourceRequirement, compact


def lesson_ref(subject: str, number: int | None) -> str | None:
    if number is None:
        return None
    prefix = {"math": "SM5", "reading": "RM4", "spelling": "SPELL", "shurley": "SHURLEY"}.get(compact(subject).lower())
    if not prefix:
        return None
    return f"{prefix}-L{number}" if compact(subject).lower() != "reading" else f"{prefix}-T{number}"


def event_label(event: dict[str, Any]) -> str:
    subject = compact(event.get("subject")).title() or "Event"
    if compact(event.get("event_type")).lower() == "lesson":
        return f"{subject} Lesson {event.get('lesson_number')}"
    if compact(event.get("event_type")).lower() == "assessment":
        return f"{subject} Test {event.get('assessment_number')}"
    return f"{subject} {compact(event.get('event_type')).title()}"


def derive_requirements(event: dict[str, Any]) -> list[ResourceRequirement]:
    subject = compact(event.get("subject")).lower()
    event_type = compact(event.get("event_type")).lower()
    event_id = compact(event.get("source_pacing_reference") or event.get("source_pacing_ref") or event.get("id") or event_label(event))
    week_code = compact(event.get("weekCode") or event.get("week_code"))
    day = compact(event.get("weekday") or event.get("day"))
    lesson_number = event.get("lesson_number")
    assessment_number = event.get("assessment_number")
    requirements: list[ResourceRequirement] = []

    if subject == "math" and event_type == "lesson":
        in_class = compact(event.get("in_class_title"))
        is_investigation = "investigation" in in_class.lower()
        if lesson_number is not None:
            requirements.append(ResourceRequirement("student-book", "math", event_id, week_code, day, lesson_ref=f"SM5-L{lesson_number}", lesson_number=lesson_number, title_hint=f"SM5 Lesson {lesson_number}"))
            requirements.append(ResourceRequirement("homework-recording-sheet", "math", event_id, week_code, day, lesson_ref=f"SM5-L{lesson_number}", lesson_number=lesson_number, variant="even" if "evens" in compact(event.get("at_home_title")).lower() else "odd", title_hint=compact(event.get("at_home_title"))))
            requirements.append(ResourceRequirement("power-up", "math", event_id, week_code, day, lesson_ref=f"SM5-L{lesson_number}", lesson_number=lesson_number, title_hint=f"Power Up for Lesson {lesson_number}"))
            if is_investigation:
                invest_ref = f"SM5-I{lesson_number // 10 if lesson_number else ''}"
                requirements.append(ResourceRequirement("investigation-resource", "math", event_id, week_code, day, lesson_ref=invest_ref, lesson_number=lesson_number, title_hint=compact(event.get("in_class_title"))))
                requirements.append(ResourceRequirement("study-guide", "math", event_id, week_code, day, lesson_ref=invest_ref, lesson_number=lesson_number, title_hint="Investigation Study Guide"))
            else:
                requirements.append(ResourceRequirement("worksheet", "math", event_id, week_code, day, lesson_ref=f"SM5-L{lesson_number}", lesson_number=lesson_number, title_hint="Worksheet"))
        return requirements

    if subject == "math" and event_type == "assessment":
        if assessment_number is not None:
            requirements.extend(
                [
                    ResourceRequirement("study-guide", "math", event_id, week_code, day, lesson_ref=f"SM5-T{assessment_number}", assessment_number=assessment_number, title_hint=f"Math Study Guide {assessment_number}"),
                    ResourceRequirement("written-test", "math", event_id, week_code, day, lesson_ref=f"SM5-T{assessment_number}", assessment_number=assessment_number, required_visibility="student-facing", title_hint=f"Math Written Test {assessment_number}"),
                    ResourceRequirement("fact-test", "math", event_id, week_code, day, lesson_ref=f"SM5-T{assessment_number}", assessment_number=assessment_number, required_visibility="student-facing", title_hint=f"Math Fact Test {assessment_number}"),
                    ResourceRequirement("teacher-answer-key", "math", event_id, week_code, day, lesson_ref=f"SM5-T{assessment_number}", assessment_number=assessment_number, required_visibility="teacher-only", title_hint=f"Math Answer Key {assessment_number}"),
                    ResourceRequirement("secure-assessment", "math", event_id, week_code, day, lesson_ref=f"SM5-T{assessment_number}", assessment_number=assessment_number, required_visibility="student-facing", title_hint=f"Math Secure Assessment {assessment_number}"),
                ]
            )
        return requirements

    if subject == "reading" and event_type == "assessment":
        if assessment_number is not None:
            requirements.append(ResourceRequirement("reading-test", "reading", event_id, week_code, day, lesson_ref=f"RM4-T{assessment_number}", assessment_number=assessment_number, title_hint=f"Reading Test {assessment_number}"))
            if int(assessment_number) <= 13:
                requirements.append(ResourceRequirement("checkout-passage", "reading", event_id, week_code, day, lesson_ref=f"RM4-C{assessment_number}", assessment_number=assessment_number, title_hint=f"Reading Checkout {assessment_number}"))
                requirements.append(ResourceRequirement("fluency-directions", "reading", event_id, week_code, day, assessment_family="checkout", assessment_number=assessment_number, title_hint="Reading Fluency Directions"))
        return requirements

    if subject == "reading" and event_type == "lesson":
        if lesson_number is not None:
            requirements.extend(
                [
                    ResourceRequirement("student-text", "reading", event_id, week_code, day, lesson_ref=f"RM4-L{lesson_number}", lesson_number=lesson_number, title_hint=f"Reading Lesson {lesson_number}"),
                    ResourceRequirement("workbook", "reading", event_id, week_code, day, lesson_ref=f"RM4-L{lesson_number}", lesson_number=lesson_number, title_hint="Reading Workbook"),
                    ResourceRequirement("comprehension-questions", "reading", event_id, week_code, day, lesson_ref=f"RM4-L{lesson_number}", lesson_number=lesson_number, title_hint="Comprehension Questions"),
                    ResourceRequirement("teacher-guide", "reading", event_id, week_code, day, lesson_ref=f"RM4-L{lesson_number}", lesson_number=lesson_number, required_visibility="teacher-only", title_hint="Teacher Guide"),
                ]
            )
        return requirements

    if subject == "spelling" and event_type == "assessment":
        if assessment_number is not None:
            requirements.extend(
                [
                    ResourceRequirement("word-list", "spelling", event_id, week_code, day, lesson_ref=f"SPELL-T{assessment_number}", assessment_number=assessment_number, title_hint=f"Spelling Word List {assessment_number}"),
                    ResourceRequirement("practice-material", "spelling", event_id, week_code, day, lesson_ref=f"SPELL-T{assessment_number}", assessment_number=assessment_number, title_hint=f"Spelling Practice {assessment_number}"),
                    ResourceRequirement("test-resource", "spelling", event_id, week_code, day, lesson_ref=f"SPELL-T{assessment_number}", assessment_number=assessment_number, required_visibility="assessment-secure", title_hint=f"Spelling Test {assessment_number}"),
                ]
            )
        return requirements

    if subject in {"history", "science"}:
        requirements.append(ResourceRequirement("page-resource", subject, event_id, week_code, day, lesson_ref=lesson_ref(subject, lesson_number), lesson_number=lesson_number, title_hint=compact(event.get("title"))))
        return requirements

    if subject == "shurley":
        requirements.append(ResourceRequirement("classroom-practice", subject, event_id, week_code, day, lesson_ref=lesson_ref(subject, lesson_number), lesson_number=lesson_number, title_hint=compact(event.get("in_class_title") or event.get("title"))))
        return requirements

    return requirements
