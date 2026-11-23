"""Canonical Reading assignment policy regression.

Local-only: no Canvas API access, publishing, or network writes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.canvas_llm_phase3 import pacing_reading
from scripts.canvas_llm_phase3 import assignment_policy
from scripts.canvas_llm_phase3 import pacing_routing
from scripts.canvas_llm_deploy import preflight


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print("PASS:", message)


config = pacing_reading.load_config()

cases = [
    ("Monday", "2026-11-16", 59,
     "RM4: Lesson 59 Workbook", "reading_classwork"),

    ("Tuesday", "2026-11-17", 60,
     "RM4: Lesson 60 Workbook and Comprehension",
     "reading_homework"),

    ("Wednesday", "2026-11-11", 56,
     "RM4: Lesson 56 Workbook", "reading_classwork"),

    ("Thursday", "2026-11-19", 61,
     "RM4: Lesson 61 Workbook and Comprehension",
     "reading_homework"),
]

for weekday, date, number, title, family in cases:
    day = pacing_reading.reading_day_plan(
        f"L{number}", weekday, date, config
    )

    assignments = day["assignments"]

    check(
        len(assignments) == 1,
        f"{weekday}: exactly one standard Reading assignment",
    )

    actual = assignments[0]

    check(
        actual["title"] == title,
        f"{weekday}: canonical title",
    )

    check(
        assignment_policy.classify_assignment(title=title) == family,
        f"{weekday}: correct classification",
    )

    check(
        assignment_policy.semantic_identity(title) ==
        (family, number),
        f"{weekday}: correct semantic identity",
    )

    check(
        actual["assignment_group"] == "Homework",
        f"{weekday}: Homework group",
    )


friday = pacing_reading.reading_day_plan(
    "L62", "Friday", "2026-11-20", config
)

check(
    friday["assignments"] == [],
    "Friday: no standard Reading assignment",
)


check(
    pacing_routing._POLICY_KIND["workbook_and_comprehension"]
    == "reading_homework",
    "Workbook and Comprehension routes to reading_homework",
)


historical = [
    (
        "RM4: Monday Workbook Classwork — Lesson 59",
        "RM4: Lesson 59 Workbook",
    ),
    (
        "RM4: Tuesday Comprehension Questions — Lesson 60",
        "RM4: Lesson 60 Workbook and Comprehension",
    ),
]

for old_title, new_title in historical:
    check(
        assignment_policy.semantic_identity(old_title)
        == assignment_policy.semantic_identity(new_title),
        f"Historical compatibility: {new_title}",
    )

    check(
        preflight.classify_assignment(
            new_title, [old_title]
        ) == "SEMANTIC_MATCH",
        f"Semantic duplicate protection: {new_title}",
    )



# Whole-week generation must not add a duplicate workbook grade.
days = {}
for weekday, date, number in [
    ("Monday", "2026-11-16", 59),
    ("Tuesday", "2026-11-17", 60),
    ("Wednesday", "2026-11-18", 61),
    ("Thursday", "2026-11-19", 62),
    ("Friday", "2026-11-20", 63),
]:
    days[weekday] = {
        "date": date,
        "subjects": {
            "reading": {"raw": f"L{number}"},
            "spelling": {"raw": ""},
        },
    }

weekly = pacing_reading.translate_reading_spelling_week(
    {"week": {"code": "Q2W6"}, "days": days},
    config,
)

titles = [
    item["title"]
    for item in weekly["reading"]["assignments"]
]

expected_titles = [
    "RM4: Lesson 59 Workbook",
    "RM4: Lesson 60 Workbook and Comprehension",
    "RM4: Lesson 61 Workbook",
    "RM4: Lesson 62 Workbook and Comprehension",
]

check(
    titles == expected_titles,
    "Whole week: exactly four canonical Reading assignments",
)

check(
    len(titles) == len(set(titles)),
    "Whole week: no duplicate assignment titles",
)

check(
    weekly["reading"]["days"]["Friday"]["assignments"] == [],
    "Whole week: Friday has no regular Reading assignment",
)

print()
print("PASS: Canonical Reading policy regression")
print("PASS: No Canvas API calls or writes")
