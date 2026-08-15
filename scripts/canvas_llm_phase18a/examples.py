"""Canonical example WeeklyPlan builders (Phase 18A).

These builders produce deterministic, in-memory example plans for demonstration,
status proof, and tests. They never read live Canvas data, never write, and
never load the August 15 evidence bundle.
"""

from __future__ import annotations

from .models import (
    CoursePlan,
    DayEntry,
    Evidence,
    RequestedArtifacts,
    WeeklyPlan,
)

_Q1W3_DATES = {
    "Monday": "2026-08-03",
    "Tuesday": "2026-08-04",
    "Wednesday": "2026-08-05",
    "Thursday": "2026-08-06",
    "Friday": "2026-08-07",
}

_PACING = Evidence(
    source_class="live_pacing",
    reference='FPK pacing guide tab "4B - Reagan"',
    note="current live 2026-2027 pacing",
)


def _day(weekday: str, in_class: str = "", homework: str = "", raw: str = "",
         decided_source: str = "live_pacing", evidence=None, blank: bool = False,
         ambiguity: str = "") -> DayEntry:
    if blank:
        decided_source = ""
        evidence = []
    return DayEntry(
        weekday=weekday,
        date=_Q1W3_DATES[weekday],
        in_class=in_class,
        homework=homework,
        raw=raw,
        blank=blank,
        decided_source=decided_source,
        evidence=evidence or ([_PACING] if decided_source else []),
        ambiguity=ambiguity,
    )


def build_example_plan() -> WeeklyPlan:
    """Build a fully populated, valid canonical Q1W3 example plan.

    Demonstrates: teacher override over pacing (Math Thursday), unknown
    shorthand preserved with ambiguity (History Wednesday), protected inactive
    Science and Homeroom, requested artifacts, assessments, and provenance.
    """
    math = CoursePlan(
        course="Math",
        requested_artifacts=["page", "assignment"],
        days=[
            _day("Monday", "Lesson 11", "Odd problems", "Lesson 11"),
            _day("Tuesday", "Lesson 12", "Even problems", "Lesson 12"),
            _day("Wednesday", "Lesson 13", "Odd problems", "Lesson 13"),
            _day(
                "Thursday",
                "Review Lessons 12-13",
                "No Homework",
                "Lesson 14",
                decided_source="teacher_instruction",
                evidence=[
                    _PACING,
                    Evidence(source_class="teacher_instruction", reference="teacher instruction", note="override Lesson 14 with review"),
                ],
            ),
            _day("Friday", "Lesson 15", "No Homework", "Lesson 15"),
        ],
    )

    reading = CoursePlan(
        course="Reading/Spelling",
        requested_artifacts=["page", "announcement"],
        days=[
            _day("Monday", "Lesson 13", "Read 20 min", "Lesson 13"),
            _day("Tuesday", "Lesson 14", "Read 20 min", "Lesson 14"),
            _day("Wednesday", "Lesson 15", "Read 20 min", "Lesson 15"),
            _day("Thursday", "Lesson 16", "Read 20 min", "Lesson 16"),
            _day("Friday", "Spelling Test 5", "No Homework", "Spelling Test 5"),
        ],
    )

    language_arts = CoursePlan(
        course="Language Arts",
        requested_artifacts=["page", "assignment"],
        days=[
            _day("Monday", "Shurley Chapter 3", "Worksheet", "Chapter 3"),
            _day("Tuesday", "Shurley Chapter 3", "Worksheet", "Chapter 3"),
            _day("Wednesday", "Shurley Chapter 3", "Worksheet", "Chapter 3"),
            _day("Thursday", "Shurley Chapter 3", "Worksheet", "Chapter 3"),
            _day("Friday", "Shurley Chapter 3", "No Homework", "Chapter 3"),
        ],
    )

    history = CoursePlan(
        course="History",
        requested_artifacts=["page"],
        days=[
            _day("Monday", "Unit 1 Lesson 1", "", "Unit 1 Lesson 1"),
            _day("Tuesday", "Unit 1 Lesson 2", "", "Unit 1 Lesson 2"),
            _day(
                "Wednesday",
                "",
                "",
                "S9 L3",
                decided_source="live_pacing",
                evidence=[_PACING],
                ambiguity="shorthand 'S9 L3' not in rule catalog",
            ),
            _day("Thursday", "Unit 1 Lesson 3", "", "Unit 1 Lesson 3"),
            _day("Friday", "Unit 1 Review", "", "Unit 1 Review"),
        ],
    )

    science = CoursePlan(
        course="Science",
        protected=True,
        days=[_day(w, blank=True) for w in _Q1W3_DATES],
        notes=["Inactive in Q1; untouched per quarter-subject activation."],
    )

    plan = WeeklyPlan(
        school_year="2026-2027",
        quarter=1,
        week_number=3,
        week_code="Q1W3",
        monday_date="2026-08-03",
        friday_date="2026-08-07",
        source_metadata=[
            _PACING,
            Evidence(source_class="canonical_rule", reference="config/curriculum/canvas/quarter-subject-activation-2026-2027.json"),
        ],
        teacher_instructions=["Use a review lesson for Math on Thursday instead of Lesson 14."],
        teacher_overrides=[
            {"subject": "Math", "weekday": "Thursday", "field": "in_class", "value": "Review Lessons 12-13", "reason": "teacher instruction"},
        ],
        courses={
            "Reading/Spelling": reading,
            "Math": math,
            "Language Arts": language_arts,
            "History": history,
            "Science": science,
        },
        assessments_reminders=[
            {"name": "Spelling Test 5", "date": "2026-08-07", "subject": "Reading/Spelling"},
        ],
        requested_artifacts=RequestedArtifacts(
            pages=True, assignments=True, announcements=True, newsletter_front_page=True
        ),
        protected_courses=["Science", "Homeroom"],
        unresolved_ambiguities=[
            {"subject": "History", "weekday": "Wednesday", "raw": "S9 L3", "reason": "shorthand not in rule catalog"},
        ],
        provenance=[
            _PACING,
            Evidence(source_class="canonical_rule", reference="config/curriculum/canvas/quarter-subject-activation-2026-2027.json"),
        ],
    )
    return plan
