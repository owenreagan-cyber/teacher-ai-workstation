"""Phase 3.3 — deterministic Reading + Spelling translation (OWNER_POLICY).

Translates raw Reading/Spelling pacing tokens into canonical teacher-facing In
Class / At Home content and graded-assignment previews, strictly from the
owner-approved operating contract (promoted to
``config/curriculum/canvas/reading-spelling-work-patterns-2026-2027.json``).

Rules implemented (all OWNER_POLICY unless otherwise noted):

* Reading ``L{n}`` -> ``Lesson {n}``
* Reading ``RMT+FCO`` -> Reading Mastery Test {n} + Fluency Checkout {n},
  resolved from the canonical Test->Checkout map (Test N = Checkout N, N = latest
  lesson / 10). Qwen never guesses test/checkout numbers.
* Reading homework schedule: Tue/Thu ``Comprehension Questions``, else No
  Homework. Daily classwork ``Workbook``.
* Reading Test + Checkout -> TWO separate assignments (Assessments + Check Out).
* Spelling numbered lesson -> ``Spelling Lesson {n}``; ``Test`` -> ``Spelling
  Test {n}`` (n = next fifth lesson, ceil(L/5)*5); ``review`` -> ``Spelling Review``.
* Spelling practice range ``N-4 .. N-1``.
* Spelling assignment course is 26442 (OWNER_POLICY, Phase 3.4; 28171 route superseded).

Read-only: no Canvas I/O, no network.
"""
from __future__ import annotations

import json
import math
import re
import sys
from datetime import datetime
from typing import Any

from . import constants as C

# --------------------------------------------------------------------------- #
# Canonical config + maps
# --------------------------------------------------------------------------- #


def load_config() -> dict[str, Any]:
    return json.loads(C.READING_SPELLING_WORK_PATTERNS_PATH.read_text(encoding="utf-8"))


def _load_json(path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_checkout_map() -> dict[str, Any]:
    return _load_json(C.REPO_ROOT / "config" / "curriculum" / "reading" / "reading-mastery-4" / "checkout-passage-map.json")


def load_spelling_map() -> dict[str, Any]:
    return _load_json(C.REPO_ROOT / "config" / "curriculum" / "spelling" / "cumulative-test-word-lists.json")


_CONFIRMED_FLUENCY = {str(n): {"wpm": 100, "maxErrors": 2} for n in range(1, 8)}


# --------------------------------------------------------------------------- #
# Reading token translation
# --------------------------------------------------------------------------- #

_READING_LESSON_RE = re.compile(r"^(?:L|Lesson)\s*(\d+)\s*$", re.IGNORECASE)
# Bare integer in the Reading pacing field is a Reading Mastery lesson number.
# Evidence: the live sheet sequence runs ``L37 L38 L39 L40`` then ``41 42 43 44
# 45`` then ``46 47 48 49 50`` — bare numbers continue the exact numeric lesson
# progression. Scoped narrowly: only the Reading field calls this parser.
_READING_BARE_NUMBER_RE = re.compile(r"^(\d+)$")
_READING_RMT_FCO_RE = re.compile(r"^(?:RMT\+FCO|RMT\+FCO\b.*|Reading\s*Mastery\s*Test.*Checkout.*)$", re.IGNORECASE)


def parse_reading_token(raw: str) -> dict[str, Any]:
    """Parse a Reading pacing cell. Returns {'kind','number','translation'}.

    Recognizes ``L41``, ``Lesson 41``, and bare ``41`` as ``Lesson 41`` (bare
    integers are canonical Reading lesson identifiers). Blank stays blank; any
    other non-numeric token is preserved as ``unknown``.
    """
    source = (raw or "").strip()
    if not source:
        return {"source": "", "kind": "blank", "number": None, "translation": ""}
    m = _READING_LESSON_RE.match(source)
    if m:
        return {"source": source, "kind": "lesson", "number": int(m.group(1)), "translation": f"Lesson {m.group(1)}"}
    m = _READING_BARE_NUMBER_RE.match(source)
    if m:
        return {"source": source, "kind": "lesson", "number": int(m.group(1)), "translation": f"Lesson {m.group(1)}"}
    if "RMT" in source.upper() or ("Mastery" in source and "Checkout" in source):
        return {"source": source, "kind": "rmt_fco", "number": None, "translation": source}
    return {"source": source, "kind": "unknown", "number": None, "translation": source}


def resolve_reading_test_checkout(latest_lesson: int) -> dict[str, Any]:
    """Resolve Reading Test + Checkout numbers from the latest lesson.

    Reading tests occur every 10 lessons; Checkout N = Test N.
    """
    n = latest_lesson // 10
    checkout = load_checkout_map().get("checkouts", {}).get(str(n)) if 1 <= n <= 13 else None
    flu = _CONFIRMED_FLUENCY.get(str(n)) if checkout else None
    return {
        "readingTestNumber": n,
        "checkoutNumber": n if checkout else None,
        "checkoutExists": checkout is not None,
        "fluency": flu if flu else None,
        "fluencyResolved": flu is not None,
        "resolved": n >= 1,
        "reason": "latest lesson / 10",
    }


def resolve_checkout(n: int) -> dict[str, Any] | None:
    if not 1 <= n <= 13:
        return None
    m = load_checkout_map().get("checkouts", {}).get(str(n))
    if not m:
        return None
    flu = _CONFIRMED_FLUENCY.get(str(n), {"wpm": None, "maxErrors": None})
    return {"checkoutNumber": n, "readingTestNumber": n, "passage": m.get("passage"), "fluency": flu, "fluencyResolved": str(n) in _CONFIRMED_FLUENCY}


# --------------------------------------------------------------------------- #
# Spelling token translation
# --------------------------------------------------------------------------- #

_SPELLING_NUMBER_RE = re.compile(r"^(\d+)$")
_SPELLING_TEST_RE = re.compile(r"^(?:Test|Test\s*\d*)\s*$", re.IGNORECASE)
_SPELLING_REVIEW_RE = re.compile(r"^review$", re.IGNORECASE)


def next_spelling_test_after_lesson(lesson: int) -> int:
    """The Spelling test following lesson L is ceil(L/5)*5 (tests every fifth lesson)."""
    return math.ceil(lesson / 5) * 5


def resolve_spelling_test_number(week: dict[str, Any]) -> int | None:
    """Resolve the Spelling test number for a week from the numbered lessons.

    Uses only the approved rule (tests every fifth lesson). Returns the test
    lesson number (e.g. 35), or None if no numbered lesson precedes a Test token.
    """
    max_lesson = 0
    for wd in C.WEEKDAYS:
        day = (week.get("days") or {}).get(wd, {})
        raw = day.get("subjects", {}).get("spelling", {}).get("raw", "")
        m = _SPELLING_NUMBER_RE.match(raw.strip())
        if m:
            max_lesson = max(max_lesson, int(m.group(1)))
    if max_lesson == 0:
        return None
    return next_spelling_test_after_lesson(max_lesson)


def spelling_practice_range(test_number: int) -> tuple[int, int]:
    return max(1, test_number - 4), test_number - 1


def parse_spelling_token(raw: str) -> dict[str, Any]:
    source = (raw or "").strip()
    if not source:
        return {"source": "", "kind": "blank", "number": None, "translation": ""}
    m = _SPELLING_NUMBER_RE.match(source)
    if m:
        return {"source": source, "kind": "lesson", "number": int(m.group(1)), "translation": f"Spelling Lesson {m.group(1)}"}
    if _SPELLING_REVIEW_RE.match(source):
        return {"source": source, "kind": "review", "number": None, "translation": "Spelling Review"}
    # "Test 40" explicit form first (before the generic "Test" token).
    m = re.match(r"^Test\s*(\d+)$", source, re.IGNORECASE)
    if m:
        return {"source": source, "kind": "test", "number": int(m.group(1)), "translation": f"Spelling Test {m.group(1)}"}
    if _SPELLING_TEST_RE.match(source):
        return {"source": source, "kind": "test", "number": None, "translation": None}
    return {"source": source, "kind": "unknown", "number": None, "translation": source}


# --------------------------------------------------------------------------- #
# Assignment helpers
# --------------------------------------------------------------------------- #


def _base_assignment(day_date: str) -> dict[str, Any]:
    return {
        "points_possible": 100,
        "grading_type": "percent",
        "submission_types": "on_paper",
        "due_date": day_date,
        "due_date_display": _display_date(day_date),
        "due_time": "11:59 PM",
        "timezone": "America/New_York",
        "preview_only": True,
        "authority": "OWNER_POLICY",
    }


def _display_date(iso: str) -> str:
    if not iso:
        return ""
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.strftime('%a %b')} {d.day}, {d.year}"


def reading_assessment_assignments(n: int, day_date: str) -> list[dict[str, Any]]:
    mt = _base_assignment(day_date)
    mt.update({"kind": "mastery_test", "title": f"RM4: Mastery Test {n}", "assignment_group": "Assessments", "number": n})
    co = _base_assignment(day_date)
    co.update({"kind": "fluency_checkout", "title": f"RM4: Fluency Checkout {n}", "assignment_group": "Check Out", "number": n})
    return [mt, co]


def spelling_assignment(n: int, day_date: str) -> dict[str, Any]:
    a = _base_assignment(day_date)
    a.update({
        "kind": "spelling_test",
        "title": f"RM4: Spelling Test {n}",
        "assignment_group": "Assessments",
        "number": n,
        "course": 26442,
        "courseName": "Reading/Spelling",
        "courseAuthority": "OWNER_POLICY (Phase 3.4; 28171 route superseded)",
    })
    return a


# --------------------------------------------------------------------------- #
# Reading day plan
# --------------------------------------------------------------------------- #


def reading_day_plan(raw: str, weekday: str, day_date: str, config: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_reading_token(raw)
    cw_goal = config["reading"]["dailyClassworkGoal"]
    hw = config["reading"]["homeworkSchedule"].get(weekday, {})

    in_class: list[str] = []
    at_home: list[str] | None = None
    at_home_status = "no_homework"
    assignments: list[dict[str, Any]] = []
    token_kind = parsed["kind"]

    if token_kind == "lesson":
        n = parsed["number"]
        agenda = config["reading"]["agendaWorkPattern"]

        # Monday and Wednesday: workbook classwork.
        # Unfinished workbook pages must be completed at home.
        if weekday in agenda["classworkDays"]:
            in_class = [f"Lesson {n}", agenda["classworkLabel"]]
            at_home = [
                agenda["unfinishedClassworkAtHomeWording"]
            ]
            at_home_status = "unfinished_classwork"

        # Tuesday and Thursday: actual homework.
        # Include both workbook and comprehension requirements.
        elif hw.get("kind") == "homework":
            in_class = [f"Lesson {n}"]
            at_home = [
                item.format(n=n)
                for item in agenda["homeworkItems"]
            ]
            at_home_status = "homework"

        # Friday and other no-homework days.
        else:
            in_class = [f"Lesson {n}"]
            at_home = None
            at_home_status = "no_homework"

        # Preserve the existing Tuesday/Thursday comprehension
        # assignment logic.
        if weekday in ("Tuesday", "Thursday"):
            assignments.append(
                _reading_accuracy_assignment(
                    "homework", weekday, n, day_date
                )
            )

    elif token_kind == "rmt_fco":
        in_class = [parsed["translation"]]
        at_home = None
        at_home_status = "no_homework"

    else:
        in_class = (
            [parsed["translation"]]
            if parsed["translation"] else []
        )
        at_home = None
        at_home_status = (
            "unresolved" if parsed["kind"] == "unknown"
            else "no_homework"
        )

    return {
        "source": parsed["source"],
        "translation": parsed["translation"],
        "token_kind": token_kind,
        "number": parsed["number"],
        "in_class": in_class,
        "at_home": at_home,
        "at_home_status": at_home_status,
        "assignments": assignments,
        "resolved": parsed["kind"] != "unknown",
        "unresolved": [] if parsed["kind"] != "unknown" else [raw],
    }


def _reading_accuracy_assignment(role: str, weekday: str, n: int, day_date: str) -> dict[str, Any]:
    a = _base_assignment(day_date)
    if role == "homework":
        a.update({"kind": "reading_homework", "title": f"RM4: {weekday} Comprehension Questions — Lesson {n}", "assignment_group": "Homework", "role": "homework"})
    else:
        a.update({"kind": "reading_classwork", "title": f"RM4: {weekday} Workbook Classwork — Lesson {n}", "assignment_group": "Homework", "role": "classwork"})
    a["title_authority"] = "TEACHER_APPROVED (Phase 22 convention; not explicit in operating contract)"
    return a


# --------------------------------------------------------------------------- #
# Whole-week Reading/Spelling translation
# --------------------------------------------------------------------------- #


def translate_reading_spelling_week(week: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_config()
    week_code = week.get("week", {}).get("code", "")

    # Determine latest Reading lesson + whether RMT+FCO occurs, for test resolution.
    latest_reading_lesson = 0
    rmt_fco_date = None
    rmt_fco_weekday = None
    reading_days: dict[str, dict[str, Any]] = {}
    reading_assignments: list[dict[str, Any]] = []
    for wd in C.WEEKDAYS:
        day = (week.get("days") or {}).get(wd, {})
        raw = day.get("subjects", {}).get("reading", {}).get("raw", "")
        date = day.get("date", "")
        plan = reading_day_plan(raw, wd, date, config)
        reading_days[wd] = plan
        reading_assignments.extend(plan["assignments"])
        if plan["token_kind"] == "lesson" and plan["number"]:
            latest_reading_lesson = max(latest_reading_lesson, plan["number"])
        if plan["token_kind"] == "rmt_fco":
            rmt_fco_date = date
            rmt_fco_weekday = wd

    # Resolve RMT+FCO test/checkout numbers.
    rmt_resolution = None
    if rmt_fco_date and latest_reading_lesson:
        rmt_resolution = resolve_reading_test_checkout(latest_reading_lesson)
        # Replace the rmt_fco day's translation with exact numbers.
        if rmt_fco_weekday and rmt_resolution["readingTestNumber"]:
            n = rmt_resolution["readingTestNumber"]
            reading_days[rmt_fco_weekday]["translation"] = f"Reading Mastery Test {n} + Fluency Checkout {n}" if rmt_resolution["checkoutExists"] else f"Reading Mastery Test {n}"
            reading_days[rmt_fco_weekday]["in_class"] = [
                f"Reading Mastery Test {n}",
                f"Fluency Checkout {n}" if rmt_resolution["checkoutExists"] else None,
            ]
            reading_days[rmt_fco_weekday]["in_class"] = [x for x in reading_days[rmt_fco_weekday]["in_class"] if x]
            reading_days[rmt_fco_weekday]["assignments"] = reading_assessment_assignments(n, rmt_fco_date) if rmt_resolution["checkoutExists"] else reading_assessment_assignments(n, rmt_fco_date)[:1]
            reading_assignments.extend(reading_days[rmt_fco_weekday]["assignments"])

    # Single workbook-classwork accuracy grade: Monday default, displaced to
    # Wednesday when Monday carries a Reading assessment.
    monday_raw = (week.get("days") or {}).get("Monday", {}).get("subjects", {}).get("reading", {}).get("raw", "")
    monday_assessment = parse_reading_token(monday_raw)["kind"] == "rmt_fco"
    classwork_day = "Wednesday" if monday_assessment else "Monday"
    cw_day = reading_days.get(classwork_day)
    if cw_day and cw_day["token_kind"] == "lesson" and cw_day["number"]:
        cw_date = (week.get("days") or {}).get(classwork_day, {}).get("date", "")
        cw_assign = _reading_accuracy_assignment("classwork", classwork_day, cw_day["number"], cw_date)
        cw_day["assignments"] = list(cw_day.get("assignments") or []) + [cw_assign]
        reading_assignments.append(cw_assign)

    # Spelling.
    spelling_days: dict[str, dict[str, Any]] = {}
    spelling_assignments: list[dict[str, Any]] = []
    spelling_test_number = resolve_spelling_test_number(week)
    for wd in C.WEEKDAYS:
        day = (week.get("days") or {}).get(wd, {})
        raw = day.get("subjects", {}).get("spelling", {}).get("raw", "")
        date = day.get("date", "")
        tok = parse_spelling_token(raw)
        if tok["kind"] == "test":
            n = tok["number"] if tok["number"] is not None else spelling_test_number
            tok["translation"] = f"Spelling Test {n}" if n else "Spelling Test (unresolved)"
            tok["resolvedNumber"] = n is not None
            plan = {
                "source": tok["source"], "translation": tok["translation"], "token_kind": "test",
                "number": n, "in_class": [tok["translation"]], "at_home": None, "at_home_status": "no_homework",
                "assignments": [], "resolved": n is not None, "unresolved": [] if n is not None else [raw],
            }
            if n:
                start, end = spelling_practice_range(n)
                plan["practiceRange"] = {"start": start, "end": end, "wording": f"practice Lessons {start} through {end}"}
                plan["assignments"] = [spelling_assignment(n, date)]
                spelling_assignments.extend(plan["assignments"])
        elif tok["kind"] in ("lesson", "review"):
            plan = {
                "source": tok["source"], "translation": tok["translation"], "token_kind": tok["kind"],
                "number": tok["number"], "in_class": [tok["translation"]], "at_home": None, "at_home_status": "no_homework",
                "assignments": [], "resolved": True, "unresolved": [],
            }
        else:
            plan = {
                "source": tok["source"], "translation": tok["translation"], "token_kind": tok["kind"],
                "number": None, "in_class": [tok["translation"]] if tok["translation"] else [], "at_home": None, "at_home_status": "no_homework",
                "assignments": [], "resolved": False, "unresolved": [raw],
            }
        spelling_days[wd] = plan

    reading_unresolved = [u for d in reading_days.values() for u in d["unresolved"] if u]
    spelling_unresolved = [u for d in spelling_days.values() for u in d["unresolved"] if u]
    unresolved = reading_unresolved + spelling_unresolved

    needs_owen = []
    if rmt_resolution and not rmt_resolution["fluencyResolved"] and rmt_resolution["checkoutExists"]:
        needs_owen.append({"field": "checkout_fluency_targets", "status": "UNRESOLVED",
                           "detail": f"Checkout {rmt_resolution['checkoutNumber']} WPM/error targets unresolved"})

    return {
        "subject": "reading_spelling",
        "deterministic": True,
        "authority": "OWNER_POLICY",
        "week_code": week_code,
        "reading": {"days": reading_days, "assignments": reading_assignments, "rmtFco": rmt_resolution},
        "spelling": {"days": spelling_days, "assignments": spelling_assignments, "testNumber": spelling_test_number},
        "unresolved": unresolved,
        "needs_owen_decision": needs_owen,
        "local_model": {"status": "SKIPPED", "reason": "all semantic fields resolved deterministically (OWNER_POLICY)"},
    }


# --------------------------------------------------------------------------- #
# Human-readable preview
# --------------------------------------------------------------------------- #


def format_reading_spelling_preview(report: dict[str, Any]) -> str:
    lines = ["READING / SPELLING — " + report.get("week_code", "")]
    reading = report.get("reading", {})
    spelling = report.get("spelling", {})
    for wd in C.WEEKDAYS:
        rd = reading.get("days", {}).get(wd, {})
        sd = spelling.get("days", {}).get(wd, {})
        if not rd and not sd:
            continue
        lines.append("")
        lines.append(wd)
        if rd.get("in_class"):
            lines.append("  Reading:")
            for x in rd["in_class"]:
                lines.append(f"    {x}")
        if sd.get("in_class"):
            lines.append("  Spelling:")
            for x in sd["in_class"]:
                lines.append(f"    {x}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #


def command_self_test() -> int:
    config = load_config()

    # Owner-approved Reading agenda patterns.
    agenda = config["reading"]["agendaWorkPattern"]

    mon = reading_day_plan(
        "L50", "Monday", "2026-11-02", config
    )
    assert mon["in_class"] == ["Lesson 50", "Workbook"]
    assert mon["at_home"] == [
        agenda["unfinishedClassworkAtHomeWording"]
    ]

    tue = reading_day_plan(
        "L51", "Tuesday", "2026-11-03", config
    )
    assert tue["in_class"] == ["Lesson 51"]
    assert tue["at_home"] == [
        item.format(n=51)
        for item in agenda["homeworkItems"]
    ]

    wed = reading_day_plan(
        "L52", "Wednesday", "2026-11-04", config
    )
    assert wed["in_class"] == ["Lesson 52", "Workbook"]
    assert wed["at_home"] == [
        agenda["unfinishedClassworkAtHomeWording"]
    ]

    thu = reading_day_plan(
        "L52", "Thursday", "2026-11-05", config
    )
    assert thu["at_home"] == [
        item.format(n=52)
        for item in agenda["homeworkItems"]
    ]

    fri = reading_day_plan(
        "L53", "Friday", "2026-11-06", config
    )
    assert fri["in_class"] == ["Lesson 53"]
    assert fri["at_home"] is None

    test_day = reading_day_plan(
        "RMT+FCO", "Tuesday", "2026-11-03", config
    )
    assert test_day["at_home"] is None

    # Reading lesson translation.
    assert parse_reading_token("L37")["translation"] == "Lesson 37"
    assert parse_reading_token("Lesson 40")["translation"] == "Lesson 40"
    assert parse_reading_token("L37")["source"] == "L37"
    assert parse_reading_token("RMT+FCO")["kind"] == "rmt_fco"

    # Bare numeric Reading token is a canonical lesson identifier (Q2W2 evidence:
    # live sheet runs L37..L40 then bare 41..45 then 46..50 — same numeric lesson
    # progression, so bare integers are lessons).
    for n in (41, 42, 43, 44, 45):
        tok = parse_reading_token(str(n))
        assert tok["kind"] == "lesson" and tok["number"] == n and tok["translation"] == f"Lesson {n}", tok
    # Blank remains blank; non-numeric unknown remains unknown.
    assert parse_reading_token("")["kind"] == "blank"
    assert parse_reading_token("Rotations")["kind"] == "unknown"

    # Reading Test + Checkout resolution.
    r = resolve_reading_test_checkout(40)
    assert r["readingTestNumber"] == 4 and r["checkoutNumber"] == 4, r
    assert r["checkoutExists"] is True
    assert r["fluency"]["wpm"] == 100 and r["fluency"]["maxErrors"] == 2
    assert resolve_reading_test_checkout(140)["readingTestNumber"] == 14
    assert resolve_reading_test_checkout(140)["checkoutExists"] is False  # Test 14

    # Checkout resolution independence.
    assert resolve_checkout(4)["fluencyResolved"] is True
    assert resolve_checkout(8)["fluencyResolved"] is False
    assert resolve_checkout(14) is None

    # Spelling translation.
    assert parse_spelling_token("32")["translation"] == "Spelling Lesson 32"
    assert parse_spelling_token("review")["translation"] == "Spelling Review"
    assert parse_spelling_token("Test")["kind"] == "test"
    assert parse_spelling_token("Test 40")["number"] == 40

    # Spelling test number + practice range.
    assert next_spelling_test_after_lesson(34) == 35
    assert next_spelling_test_after_lesson(35) == 35
    assert next_spelling_test_after_lesson(36) == 40
    assert spelling_practice_range(35) == (31, 34)

    # Whole-week (synthetic Q2W1).
    week = {
        "week": {"code": "Q2W1", "startDate": "2026-10-12", "endDate": "2026-10-16"},
        "days": {
            "Monday": {"date": "2026-10-12", "subjects": {"reading": {"raw": "L37"}, "spelling": {"raw": "32"}}},
            "Tuesday": {"date": "2026-10-13", "subjects": {"reading": {"raw": "L38"}, "spelling": {"raw": "33"}}},
            "Wednesday": {"date": "2026-10-14", "subjects": {"reading": {"raw": "L39"}, "spelling": {"raw": "34"}}},
            "Thursday": {"date": "2026-10-15", "subjects": {"reading": {"raw": "L40"}, "spelling": {"raw": "Test"}}},
            "Friday": {"date": "2026-10-16", "subjects": {"reading": {"raw": "RMT+FCO"}, "spelling": {"raw": "review"}}},
        },
    }
    report = translate_reading_spelling_week(week, config)
    assert report["deterministic"] is True
    assert report["reading"]["days"]["Friday"]["in_class"] == ["Reading Mastery Test 4", "Fluency Checkout 4"]
    assert report["reading"]["rmtFco"]["readingTestNumber"] == 4
    assert report["spelling"]["testNumber"] == 35
    assert report["spelling"]["days"]["Thursday"]["translation"] == "Spelling Test 35"
    assert report["spelling"]["days"]["Thursday"]["practiceRange"] == {"start": 31, "end": 34, "wording": "practice Lessons 31 through 34"}
    # Two separate Reading assessment assignments + one Spelling (course 26442).
    reading_assess = [a for a in report["reading"]["days"]["Friday"]["assignments"]]
    assert [a["kind"] for a in reading_assess] == ["mastery_test", "fluency_checkout"], reading_assess
    assert reading_assess[0]["assignment_group"] == "Assessments" and reading_assess[1]["assignment_group"] == "Check Out"
    spelling_assign = report["spelling"]["assignments"]
    assert len(spelling_assign) == 1 and spelling_assign[0]["course"] == 26442
    assert spelling_assign[0]["courseAuthority"] == "OWNER_POLICY (Phase 3.4; 28171 route superseded)"
    # No spelling-course decision remains open.
    assert not any(d["field"] == "spelling_assignment_course" for d in report["needs_owen_decision"])
    assert report["local_model"]["status"] == "SKIPPED"

    print("PASS reading + spelling translation self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
