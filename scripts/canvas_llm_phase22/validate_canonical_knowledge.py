#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def load_json(relative: str) -> dict:
    path = ROOT / relative
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


checks: list[tuple[bool, str]] = []

courses = load_json("config/curriculum/canvas-course-mappings.json")
power = load_json(
    "config/curriculum/math/saxon-math-5/lesson-power-up-map.json"
)
facts = load_json(
    "config/curriculum/math/saxon-math-5/fact-test-practice-map.json"
)
reading = load_json(
    "config/curriculum/reading/reading-mastery-4/"
    "comprehension-location-map.json"
)
spelling = load_json(
    "config/curriculum/spelling/cumulative-test-word-lists.json"
)
agenda = load_json("config/curriculum/canvas/agenda-page-rules.json")
quarter_activation = load_json(
    "config/curriculum/canvas/quarter-subject-activation-2026-2027.json"
)
weekly_agenda = load_json(
    "config/curriculum/canvas/weekly-agenda-standard-2026-2027.json"
)
checkout_map = load_json(
    "config/curriculum/reading/reading-mastery-4/checkout-passage-map.json"
)

from scripts.canvas_llm_phase22 import phase22_workstation as p

current = {
    item["subjectId"]: item
    for item in courses["currentProduction"]["courses"]
}

archived_by_year = {
    item["schoolYear"]: item
    for item in courses["archivedReference"]
}

checks.extend(
    [
        (
            courses["status"]
            == "owner-approved-2026-2027-operating-contract",
            "course mappings are owner-approved for the 2026-2027 contract",
        ),
        (
            current["math"]["courseId"] == 26404,
            "2026-2027 Math resolves to course 26404",
        ),
        (
            current["math"]["canonicalPrefix"] == "SM5",
            "2026-2027 Math prefix is SM5",
        ),
        (
            current["reading"]["courseId"] == 26442,
            "2026-2027 Reading resolves to course 26442",
        ),
        (
            current["reading"]["canonicalPrefix"] == "RM4",
            "2026-2027 Reading prefix is RM4",
        ),
        (
            current["spelling"]["courseId"] == 26442,
            "2026-2027 Spelling shares Reading course 26442",
        ),
        (
            current["spelling"]["canonicalPrefix"] == "RM4",
            "2026-2027 Spelling prefix is RM4",
        ),
        (
            current["spelling"]["gradingCourseSubject"] == "reading",
            "2026-2027 Spelling grades route through Reading",
        ),
        (
            current["language-arts"]["courseId"] == 26495,
            "2026-2027 Language Arts resolves to course 26495",
        ),
        (
            current["language-arts"]["canonicalPrefix"] == "ELA4",
            "2026-2027 Language Arts prefix is ELA4",
        ),
        (
            current["history"]["canonicalPrefix"] == "HIST4",
            "2026-2027 History prefix is HIST4",
        ),
        (
            current["history"]["assignmentPolicy"] == "quarter-gated",
            "History assignment generation is quarter-gated",
        ),
        (
            current["history"]["activeQuarters"] == [1, 3],
            "History is active in Q1 and Q3",
        ),
        (
            current["history"]["inactivePolicy"] == "untouched",
            "Inactive History policy is untouched",
        ),
        (
            current["science"]["canonicalPrefix"] == "SCI4",
            "2026-2027 Science prefix is SCI4",
        ),
        (
            current["science"]["assignmentPolicy"] == "quarter-gated",
            "Science assignment generation is quarter-gated",
        ),
        (
            current["science"]["activeQuarters"] == [2, 4],
            "Science is active in Q2 and Q4",
        ),
        (
            current["science"]["inactivePolicy"] == "untouched",
            "Inactive Science policy is untouched",
        ),
        (
            current["homeroom"]["courseId"] == 26427,
            "2026-2027 Homeroom resolves to course 26427",
        ),
        (
            current["homeroom"]["newsletterCadence"] == "monthly",
            "Homeroom newsletter cadence is monthly",
        ),
        (
            current["homeroom"]["schoolAndEventLinksAllowed"] is True,
            "Homeroom school and event links are allowed",
        ),
        (
            courses["demoSandbox"]["courses"][0]["courseId"] == 24399,
            "Math sandbox resolves to course 24399",
        ),
        (
            archived_by_year["2025-2026"]["readOnly"] is True,
            "2025-2026 mappings are read-only",
        ),
        (
            archived_by_year["2025-2026"]["writesBlocked"] is True,
            "2025-2026 archived writes are blocked",
        ),
        (
            archived_by_year["2024-2025"]["readOnly"] is True,
            "2024-2025 mappings are read-only",
        ),
        (
            "science"
            in archived_by_year["2024-2025"]["knownMissingMappings"],
            "2024-2025 Science remains explicitly unresolved",
        ),
        (
            len(power["lessonToPowerUp"]) == 120,
            "Math Power Up map contains 120 lessons",
        ),
        (
            set(power["lessonToPowerUp"])
            == {str(number) for number in range(1, 121)},
            "Math Power Up map covers lessons 1-120 exactly",
        ),
        (
            power["lessonToPowerUp"]["5"] == "A",
            "Math Lesson 5 maps to Power Up A",
        ),
        (
            power["lessonToPowerUp"]["25"] == "D",
            "Math Lesson 25 maps to Power Up D",
        ),
        (
            power["lessonToPowerUp"]["90"] == "F",
            "Math Lesson 90 maps to Power Up F",
        ),
        (
            len(facts["tests"]) == 23,
            "Fact Test map contains Tests 1-23",
        ),
        (
            facts["tests"]["12"]["powerUpCode"] == "E",
            "Fact Test 12 maps to Power Up E",
        ),
        (
            "81/9" in facts["tests"]["12"]["practiceDescription"],
            "Fact Test 12 includes the approved division practice",
        ),
        (
            len(reading["lessons"]) == 140,
            "Reading comprehension map contains Lessons 1-140",
        ),
        (
            reading["lessons"]["25"]
            == {"comprehensionLetter": "D", "page": 114},
            "Reading Lesson 25 maps to D, page 114",
        ),
        (
            reading["lessons"]["140"]
            == {"comprehensionLetter": "E", "page": 750},
            "Reading Lesson 140 maps to E, page 750",
        ),
        (
            len(checkout_map["checkouts"]) == 13,
            "Reading Checkout map contains Checkouts 1-13",
        ),
        (
            set(checkout_map["checkouts"]) == {str(number) for number in range(1, 14)},
            "Reading Checkout map covers Checkouts 1-13 exactly",
        ),
        (
            p.resolve_checkout(1)["fluency"] == {"wpm": 100, "maxErrors": 2},
            "Checkout 1 fluency is 100 WPM / 2 errors",
        ),
        (
            p.resolve_checkout(7)["fluency"] == {"wpm": 100, "maxErrors": 2},
            "Checkout 7 fluency is 100 WPM / 2 errors",
        ),
        (
            p.resolve_checkout(8)["fluency"] == {"wpm": 115, "maxErrors": 2},
            "Checkout 8 fluency is 115 WPM / 2 errors",
        ),
        (
            p.resolve_checkout(10)["fluency"] == {"wpm": 115, "maxErrors": 2},
            "Checkout 10 fluency is 115 WPM / 2 errors",
        ),
        (
            p.resolve_checkout(11)["fluency"] == {"wpm": 130, "maxErrors": 2},
            "Checkout 11 fluency is 130 WPM / 2 errors",
        ),
        (
            p.resolve_checkout(13)["fluency"] == {"wpm": 130, "maxErrors": 2},
            "Checkout 13 fluency is 130 WPM / 2 errors",
        ),
        (
            len(spelling["tests"]) == 24,
            "Spelling map contains Tests 1-24",
        ),
        (
            all(
                len(test["words"]) == 25
                for test in spelling["tests"].values()
            ),
            "Every Spelling test contains 25 words",
        ),
        (
            all(
                len(test["focusWords"]) == 5
                for test in spelling["tests"].values()
            ),
            "Every Spelling test contains 5 focus words",
        ),
        (
            spelling["tests"]["24"]["focusWords"]
            == [
                "Refreshing",
                "Light",
                "Should",
                "Planned",
                "Undefeated",
            ],
            "Spelling Test 24 uses approved focus words 21-25",
        ),
        (
            agenda["timezone"] == "America/New_York",
            "Scheduling timezone is America/New_York",
        ),
        (
            agenda["rules"]["fridayInstructionAllowed"] is True,
            "Friday instruction remains allowed",
        ),
        (
            agenda["rules"]["fridayHomeworkDefault"] == "No Homework",
            "Friday homework defaults to No Homework",
        ),
        (
            agenda["rules"]["readingAndSpellingShareAgenda"] is True,
            "Reading and Spelling share an agenda",
        ),
        (
            agenda["rules"]["fakeLinksForbidden"] is True,
            "Fake links are forbidden",
        ),
        (
            agenda["confirmedPolicies"]["readingTest14CheckoutAbsence"]["checkoutExists"]
            is False,
            "Reading Test 14 has no Checkout",
        ),
        (
            agenda["confirmedPolicies"]["readingTest14CheckoutAbsence"]["checkoutNumber"]
            == 14,
            "Checkout 14 does not exist",
        ),
        (
            p.reading_assessment_family(14, "2026-07-21")["checkout"] is None,
            "Reading Test 14 returns no Checkout",
        ),
        (
            p.reading_assessment_family(14, "2026-07-21")["warnings"] == [],
            "Reading Test 14 produces no checkout warning",
        ),
        (
            "Checkout 14" not in p.reading_announcement_body(
                p.reading_assessment_family(14, "2026-07-21")
            ),
            "Reading Test 14 announcement omits Checkout 14",
        ),
        (
            courses["rules"]["sameDayDueTime"] == "23:59",
            "Canvas assignments use same-day 11:59 PM due time",
        ),
        (
            agenda["confirmedPolicies"]["canvasAssignmentDueTime"]["localTime"]
            == "23:59",
            "Agenda policy confirms 11:59 PM due time",
        ),
        (
            agenda["rules"]["resourceSectionAllowed"] is False,
            "Subject agenda resource sections are forbidden",
        ),
        (
            agenda["rules"]["subjectAgendaLinksAllowed"] is False,
            "Subject agenda links are forbidden",
        ),
        (
            agenda["rules"]["homeworkLabel"] == "Homework",
            "Subject agenda uses Homework label",
        ),
        (
            weekly_agenda["sections"]["remindersOnly"] is True,
            "Weekly agenda uses reminders-only section",
        ),
        (
            weekly_agenda["sections"]["resourceSectionAllowed"] is False,
            "Weekly agenda standard forbids resource sections",
        ),
        (
            weekly_agenda["dailyLayout"]["rightColumn"] == "Homework",
            "Weekly agenda right column is Homework",
        ),
        (
            weekly_agenda["contentRules"]["studyGuidesAllowed"] is False,
            "Weekly agenda standard forbids study guides",
        ),
        (
            quarter_activation["quarters"]["Q1"]["activeSubject"] == "history"
            and quarter_activation["quarters"]["Q1"]["inactiveSubject"]
            == "science",
            "Q1 activates History and leaves Science untouched",
        ),
        (
            quarter_activation["quarters"]["Q2"]["activeSubject"] == "science"
            and quarter_activation["quarters"]["Q2"]["inactiveSubject"]
            == "history",
            "Q2 activates Science and leaves History untouched",
        ),
        (
            quarter_activation["quarters"]["Q3"]["activeSubject"] == "history"
            and quarter_activation["quarters"]["Q3"]["inactiveSubject"]
            == "science",
            "Q3 activates History and leaves Science untouched",
        ),
        (
            quarter_activation["quarters"]["Q4"]["activeSubject"] == "science"
            and quarter_activation["quarters"]["Q4"]["inactiveSubject"]
            == "history",
            "Q4 activates Science and leaves History untouched",
        ),
        (
            quarter_activation["rules"]["inactiveSubjectPolicy"] == "untouched",
            "Inactive quarter subject must remain untouched",
        ),
    ]
)

failures = 0

for passed, message in checks:
    if passed:
        print(f"PASS: {message}")
    else:
        failures += 1
        print(f"FAIL: {message}")

print()
print(f"PASS: {len(checks) - failures}")
print("WARN: 0")
print(f"FAIL: {failures}")

raise SystemExit(1 if failures else 0)
