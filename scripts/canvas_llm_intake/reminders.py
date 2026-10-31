"""Assessment reminder drafting for the Canvas Weekly Intake.

Drafts family-facing assessment reminders locally (never posts). Detects
approved assessment types from normalized pacing and resolves authoritative
practice resources (e.g. Math Fact Assessment -> Power Up letter) from canonical
config. Source markers (like ``FA6*``) are never exposed.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import constants as C
from scripts.canvas_llm_phase3 import constants as P3

FACT_TEST_MAP = P3.REPO_ROOT / "config" / "curriculum" / "math" / "saxon-math-5" / "fact-test-practice-map.json"
SPELLING_MAP = P3.REPO_ROOT / "config" / "curriculum" / "spelling" / "cumulative-test-word-lists.json"


def load_fact_test_map() -> dict[str, Any]:
    return json.loads(FACT_TEST_MAP.read_text(encoding="utf-8")).get("tests", {})


def load_spelling_map() -> dict[str, Any]:
    return json.loads(SPELLING_MAP.read_text(encoding="utf-8"))


def resolve_fact_test(n: int) -> dict[str, Any] | None:
    """Fact Test N -> {powerUp, practiceDescription, resourceStatus}."""
    m = load_fact_test_map().get(str(n))
    if not m:
        return None
    return {
        "factTestNumber": n,
        "powerUpCode": m.get("powerUpCode"),
        "practiceDescription": m.get("practiceDescription"),
        "resourceStatus": "UNVERIFIED",  # GET-only file verification happens at deploy time
    }


def draft_math_assessment_reminders(week: dict[str, Any]) -> list[dict[str, Any]]:
    """Draft Math assessment reminder(s) from normalized pacing.

    Detects a Written Assessment + Fact Assessment pair (same day per policy)
    and drafts a combined reminder. Returns [] if no assessment this week.
    """
    from scripts.canvas_llm_phase3 import pacing_announcement as pa

    try:
        facts = pa.resolve_assessment_facts(week)
    except Exception:  # noqa: BLE001
        return []
    reminders: list[dict[str, Any]] = []
    for ev in facts:
        if ev.get("family") != "math_assessment":
            continue
        written = None
        fact = None
        for a in ev.get("assignments") or []:
            if a and a.get("kind") == "written_assessment":
                written = a
            if a and a.get("kind") == "fact_assessment":
                fact = a
        if not written and not fact:
            continue
        fact_n = fact.get("number") if fact else None
        power = resolve_fact_test(fact_n) if fact_n is not None else None
        date = ev.get("assessmentDate", "")
        # Format date -> "Tuesday, October 20"
        date_display = _display_date(date)

        # The review day is the explicit Math "Review" token day, NOT a
        # hardcoded weekday. The owner At Home override ("Study for tomorrow's
        # test.") lands on that review day's evening.
        review_weekday = _math_review_weekday(week)

        body = _math_body(date_display, written, fact, power, review_weekday=review_weekday)
        reminders.append({
            "type": "math_assessment",
            "title": f"Math Assessment Reminder — {date_display}",
            "course": "Math",
            "course_id": 26404,
            "assessment_date": date,
            "written": written.get("title") if written else None,
            "fact": fact.get("title") if fact else None,
            "power_up": power.get("powerUpCode") if power else None,
            "body": body,
            "requires_teacher_approval": True,
            "source_marker_exposed": False,
        })
    return reminders


def draft_spelling_reminders(week: dict[str, Any]) -> list[dict[str, Any]]:
    """Draft Spelling test reminder from normalized pacing.

    Detects a Spelling Test token and resolves the exact test number/date.
    Owen's standing instruction is to study the spelling word lists through the
    tested lesson (not only the current list). The verified cumulative map is
    referenced only when its ``lessonsCovered`` range matches the test number;
    otherwise the announcement preserves the study instruction and records the
    missing list instead of inventing words.
    """
    test_number = None
    test_date = None
    for wd in C.WEEKDAYS:
        day = (week.get("days") or {}).get(wd, {})
        raw = day.get("subjects", {}).get("spelling", {}).get("raw", "")
        low = raw.lower()
        if low.startswith("test"):
            test_date = day.get("date", "")
            # "Test 40" or bare "Test"
            import re
            m = re.search(r"(\d+)", raw)
            if m:
                test_number = int(m.group(1))
            break
    if test_date is None:
        return []
    date_display = _display_date(test_date)
    num_txt = f" {test_number}" if test_number is not None else ""
    title = f"Spelling Test{num_txt} Reminder"
    verified, list_meta = _verified_word_list(test_number)
    body = (
        "Good afternoon,\n\n"
        f"I wanted to send a quick reminder that students will be taking Spelling Test{num_txt} on {date_display}.\n\n"
        "We have covered a lot of spelling material so far this year, and this is a good "
        "opportunity for students to show how much they have learned. Spending a few minutes "
        "reviewing at home can make a big difference and help students feel confident going "
        "into the test.\n\n"
        + (_list_range(test_number) if test_number is not None else "")
        + (_verified_list_text(test_number, list_meta) if verified else "")
        + "\nThank you for your continued support at home!\n\nOwen Reagan"
    )
    return [{
        "type": "spelling",
        "title": title,
        "course": "Reading/Spelling",
        "course_id": 26442,
        "assessment_date": test_date,
        "test_number": test_number,
        "body": body,
        "word_list_status": "VERIFIED" if verified else "UNVERIFIED",
        "word_list_lessons_covered": list_meta.get("lessonsCovered", "") if verified else "",
        "word_list": list_meta.get("words", []) if verified else [],
        "focus_words": list_meta.get("focusWords", []) if verified else [],
        "requires_teacher_approval": True,
    }]


def _verified_word_list(test_number: int | None) -> tuple[bool, dict[str, Any]]:
    """Resolve the verified cumulative list for a lesson-numbered spelling test.

    The canonical map is keyed by cumulative-test ordinal (1..24), and each
    ordinal covers lessons 1 through 5*N. Spelling Test 50 therefore maps to
    ordinal 10 (lessons 1-50). Only an exact ``lessonsCovered`` match counts.
    """
    if test_number is None or test_number <= 0 or test_number % 5 != 0:
        return False, {}
    ordinal = test_number // 5
    try:
        entry = load_spelling_map().get("tests", {}).get(str(ordinal), {})
    except (OSError, json.JSONDecodeError):
        return False, {}
    if not entry:
        return False, {}
    if str(entry.get("lessonsCovered", "")) != f"1-{test_number}":
        return False, {}
    if not entry.get("words"):
        return False, {}
    return True, entry


def _verified_list_text(test_number: int, entry: dict[str, Any]) -> str:
    words = [str(w) for w in entry.get("words", []) if str(w).strip()]
    focus = [str(w) for w in entry.get("focusWords", []) if str(w).strip()]
    lines = [
        f"Verified word list for Spelling Test {test_number} (Lessons 1\u2013{test_number}):",
        ", ".join(words),
        "",
    ]
    if focus:
        lines.append("Focus words: " + ", ".join(focus))
    return "\n".join(lines) + "\n"


def _list_range(test_number: int) -> str:
    """Cumulative study instruction; never claims an unverified word list."""
    return (
        f"Students should study the spelling word lists through Lesson {test_number} "
        f"(Lists 1\u2013{test_number}). This is a cumulative review, so please look back over "
        "the full list rather than only the most recent lesson.\n"
    )


def _join_and(parts: list[str]) -> str:
    parts = [p for p in parts if p]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


def _lesson_span(lessons: list[int]) -> str:
    unique = sorted({n for n in lessons if n})
    if not unique:
        return ""
    if len(unique) == 1:
        return f"Lesson {unique[0]}"
    return f"Lessons {unique[0]}\u2013{unique[-1]}"


def _chapter_span(chapters: list[int]) -> str:
    """List distinct chapters without implying a continuous range."""
    unique = sorted({n for n in chapters if n})
    if not unique:
        return ""
    if len(unique) == 1:
        return f"Chapter {unique[0]}"
    return "Chapters " + _join_and([str(n) for n in unique])


def instructional_focus_reminder(week: dict[str, Any], subject: str) -> str:
    """A short, deterministic, source-derived instructional reminder.

    Used only when the week has no assessment reminder for that subject, so a
    Reminders section is never an empty placeholder. Nothing is invented: the
    sentence is derived from the week's own pacing cells.
    """
    if subject == "math":
        from scripts.canvas_llm_phase3 import pacing_math as pm

        lessons: list[int] = []
        for wd in C.WEEKDAYS:
            raw = ((week.get("days") or {}).get(wd, {}).get("subjects", {}).get("math", {}) or {}).get("raw", "")
            if not raw:
                continue
            for token in pm.parse_math_tokens(raw)["tokens"]:
                if token.get("kind") == "lesson" and token.get("number"):
                    lessons.append(int(token["number"]))
        phrase = _lesson_span(lessons)
        if phrase:
            return f"This week we will continue working through {phrase}."
        return "This week we will continue working through this week's Math lessons."

    if subject == "language_arts":
        from scripts.canvas_llm_phase3 import pacing_translation as pt

        chapters: list[int] = []
        for wd in C.WEEKDAYS:
            raw = ((week.get("days") or {}).get(wd, {}).get("subjects", {}).get("language_arts", {}) or {}).get("raw", "")
            if not raw:
                continue
            for item in pt.translate_shurley_cell(raw)["items"]:
                chapter = item.get("chapter")
                if chapter and int(chapter) not in chapters:
                    chapters.append(int(chapter))
        if chapters:
            if len(chapters) == 1:
                return f"This week we will continue working in Chapter {chapters[0]}."
            return f"This week we will continue working in Chapters {_join_and([str(c) for c in chapters])}."
        return "This week we will continue our Shurley grammar work."

    if subject == "reading_spelling":
        from scripts.canvas_llm_phase3 import pacing_reading as prd

        reading: list[int] = []
        spelling: list[int] = []
        for wd in C.WEEKDAYS:
            day = (week.get("days") or {}).get(wd, {})
            subs = day.get("subjects", {})
            rtok = prd.parse_reading_token(((subs.get("reading") or {}).get("raw") or ""))
            if rtok.get("kind") == "lesson" and rtok.get("number"):
                reading.append(int(rtok["number"]))
            stok = prd.parse_spelling_token(((subs.get("spelling") or {}).get("raw") or ""))
            if stok.get("kind") == "lesson" and stok.get("number"):
                spelling.append(int(stok["number"]))
        parts = []
        if reading:
            parts.append(f"Reading {_lesson_span(reading)}")
        if spelling:
            parts.append(f"Spelling {_lesson_span(spelling)}")
        if parts:
            return "This week we will continue working through " + _join_and(parts) + "."
        return "This week we will continue our reading and spelling work."

    if subject == "science":
        from scripts.canvas_llm_phase3 import pacing_translation as pt

        units: list[int] = []
        chapters: list[int] = []
        for wd in C.WEEKDAYS:
            raw = ((week.get("days") or {}).get(wd, {}).get("subjects", {}).get("science", {}) or {}).get("raw", "")
            if not raw:
                continue
            import re

            for match in re.finditer(r"\bU\s*(\d+)", raw, re.IGNORECASE):
                if int(match.group(1)) not in units:
                    units.append(int(match.group(1)))
            for match in re.finditer(r"\bCh\.?\s*(\d+)", raw, re.IGNORECASE):
                if int(match.group(1)) not in chapters:
                    chapters.append(int(match.group(1)))
        unit_name = ""
        try:
            unit_name = pt.resolve_science_unit_name(pt.load_config(), (week.get("unitContext") or {}).get("science")) or ""
        except Exception:  # noqa: BLE001 - reminder is advisory
            unit_name = ""
        # Never apply the canonical Unit 1 name to a different unit number.
        if units and units != [1]:
            unit_name = ""
        head = f"our {unit_name} unit" if unit_name else (f"Unit {units[0]}" if units else "our current unit")
        if chapters:
            return f"This week we will continue {head} as we work through {_chapter_span(chapters)}."
        return f"This week we will continue {head}."

    return ""


def weekly_reminders(
    week: dict[str, Any], subject: str, *, science_override: dict[str, Any] | None = None,
) -> list[str]:
    """Compose the Reminders block for one subject.

    Assessment facts come first (source-derived). A Science owner override
    replaces a stale canonical test label and adds the approved test format.
    When no assessment exists, a source-derived instructional-focus sentence is
    used so the block is never an empty placeholder.
    """
    from scripts.canvas_llm_phase3 import pacing_announcement as pa

    labels = {
        "math": "Math",
        "reading_spelling": "Reading/Spelling",
        "language_arts": "Language Arts",
        "science": "Science",
        "history": "History",
    }
    label = labels.get(subject, subject)
    reminders: list[str] = []
    try:
        facts = pa.resolve_assessment_facts(week)
    except Exception:  # noqa: BLE001 - reminders are best-effort
        facts = []

    for event in facts:
        if event.get("course") != label:
            continue
        date_display = _display_date(event.get("assessmentDate", ""))
        names = [a for a in (event.get("assessments") or []) if a]
        if subject == "science" and science_override is not None:
            names = [science_override.get("owner_value") or "Science Unit Test"]
        for name in names:
            reminders.append(f"{name} — {date_display}")

    if subject == "science" and science_override is not None:
        parts = []
        if science_override.get("open_book", True):
            parts.append("Open Book")
        if science_override.get("open_notes", True):
            parts.append("Open Notes")
        if parts:
            reminders.append(" / ".join(parts) + ".")

    if not reminders:
        focus = instructional_focus_reminder(week, subject)
        if focus:
            reminders.append(focus)

    # Never duplicate the same line.
    seen: set[str] = set()
    unique: list[str] = []
    for line in reminders:
        if line and line not in seen:
            seen.add(line)
            unique.append(line)
    return unique


def _display_date(iso_date: str) -> str:
    if not iso_date:
        return ""
    try:
        d = datetime.strptime(iso_date, "%Y-%m-%d")
        return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}"
    except ValueError:
        return iso_date


def _math_review_weekday(week: dict[str, Any]) -> str | None:
    """Return the weekday whose Math cell is an explicit "Review" token.

    The review day drives both the in-class review sentence and the At Home
    "review this evening" sentence. Returns None if there is no explicit Review
    day (the reminder then uses a generic, non-day-specific phrase).
    """
    for wd in C.WEEKDAYS:
        day = (week.get("days") or {}).get(wd, {})
        raw = day.get("subjects", {}).get("math", {}).get("raw", "")
        if (raw or "").strip().lower() == "review":
            return wd
    return None


def _math_body(date_display: str, written: dict[str, Any] | None, fact: dict[str, Any] | None,
               power: dict[str, Any] | None, *, review_weekday: str | None = None) -> str:
    wa = written.get("number") if written else None
    fa = fact.get("number") if fact else None
    lines = ["Good afternoon,", ""]
    if wa is not None and fa is not None:
        lines.append(
            f"I wanted to send a quick reminder that students will be completing "
            f"Written Assessment {wa} and Fact Assessment {fa} on {date_display}."
        )
    lines.append("")
    if review_weekday:
        lines.append(
            f"We will spend time on {review_weekday} reviewing and preparing for the assessments, "
            f"and students should continue reviewing at home {review_weekday} evening. "
            "Looking back over recent lesson work, practice problems, and corrections is a great "
            "way to prepare."
        )
    else:
        lines.append(
            "We will spend time in class reviewing and preparing for the assessments, and "
            "students should continue reviewing at home the evening before. Looking back over "
            "recent lesson work, practice problems, and corrections is a great way to prepare."
        )
    if power is not None:
        lines.append("")
        lines.append(
            f"For Fact Assessment {fa}, students should practice using Power Up "
            f"{power.get('powerUpCode')}. A few minutes of focused fact practice at home "
            f"can be very helpful for building speed and confidence."
        )
        # Only claim a Canvas practice sheet when a resource is actually verified.
        # The Power Up resource is UNRESOLVED (no verified Canvas file ID), so the
        # "available in Canvas" claim is omitted (fail closed).
        if power.get("resourceStatus") == "VERIFIED":
            lines.append("")
            lines.append(
                "The Power Up practice sheet is available in Canvas for anyone who would like some "
                "extra practice."
            )
    lines.append("")
    lines.append("Thank you for your support at home!")
    lines.append("")
    lines.append("Owen Reagan")
    return "\n".join(lines)


def command_self_test() -> int:
    # Fact Test 6 -> Power Up B (verified).
    r = resolve_fact_test(6)
    assert r["powerUpCode"] == "B", r
    assert r["resourceStatus"] == "UNVERIFIED"

    # No map entry -> None (fail closed).
    assert resolve_fact_test(999) is None

    # Spelling reminder: bare "Test" with no number resolves no range.
    week = {
        "week": {"code": "Q2W2"},
        "days": {
            "Friday": {"date": "2026-10-23", "subjects": {"spelling": {"raw": "Test 40"}}},
        },
    }
    s = draft_spelling_reminders(week)
    assert len(s) == 1 and s[0]["test_number"] == 40
    assert "Lists 1\u201340" in s[0]["body"]
    assert s[0]["course_id"] == 26442
    assert s[0]["word_list_status"] == "VERIFIED"
    assert len(s[0]["word_list"]) == 25

    # Q2W4 Spelling Test 50: cumulatively through Lesson 50, never "current list".
    week_50 = {
        "week": {"code": "Q2W4"},
        "days": {"Friday": {"date": "2026-11-06", "subjects": {"spelling": {"raw": "test 50"}}}},
    }
    s50 = draft_spelling_reminders(week_50)
    assert len(s50) == 1 and s50[0]["test_number"] == 50
    assert "through Lesson 50" in s50[0]["body"]
    assert "current spelling list" not in s50[0]["body"]
    assert "Planner" in s50[0]["body"]

    # Instructional focus reminders are source-derived and deterministic.
    q2w4_days = {
        "Monday": {"date": "2026-11-02", "subjects": {"math": {"raw": "41"}, "reading": {"raw": "L50"}, "spelling": {"raw": "46"}, "language_arts": {"raw": "Ch 7 L2 + CP26"}, "science": {"raw": "F&M Ch. 7"}}},
        "Tuesday": {"date": "2026-11-03", "subjects": {"math": {"raw": "42"}, "reading": {"raw": "RMT 5+ CO 5"}, "spelling": {"raw": "47"}, "language_arts": {"raw": "Ch.7 L3 CP27"}, "science": {"raw": "F&M Ch. 7"}}},
        "Wednesday": {"date": "2026-11-04", "subjects": {"math": {"raw": "43"}, "reading": {"raw": "L51"}, "spelling": {"raw": "48"}, "language_arts": {"raw": "Ch.7 L3 CP27"}, "science": {"raw": "Review"}}},
        "Thursday": {"date": "2026-11-05", "subjects": {"math": {"raw": "44"}, "reading": {"raw": "L52"}, "spelling": {"raw": "49"}, "language_arts": {"raw": "7.4"}, "science": {"raw": "Test"}}},
        "Friday": {"date": "2026-11-06", "subjects": {"math": {"raw": "45"}, "reading": {"raw": "L53"}, "spelling": {"raw": "test 50"}, "language_arts": {"raw": "7.4 CP 27"}, "science": {"raw": "U2 Ch1 Renewable / Nonrenewable"}}},
    }
    q2w4 = {"week": {"code": "Q2W4"}, "days": q2w4_days}
    assert instructional_focus_reminder(q2w4, "math") == "This week we will continue working through Lessons 41\u201345."
    assert instructional_focus_reminder(q2w4, "language_arts") == "This week we will continue working in Chapter 7."
    assert instructional_focus_reminder(q2w4, "reading_spelling").startswith("This week we will continue working through Reading Lessons 50\u201353")
    assert weekly_reminders(q2w4, "math") == ["This week we will continue working through Lessons 41\u201345."]
    assert weekly_reminders(q2w4, "language_arts") == ["This week we will continue working in Chapter 7."]
    science_override = {"owner_value": "Energy Transformations Unit Test", "open_book": True, "open_notes": True}
    sci = weekly_reminders(q2w4, "science", science_override=science_override)
    assert "Energy Transformations Unit Test \u2014 Thursday, November 5" in sci, sci
    assert "Open Book / Open Notes." in sci, sci

    # Math reminder review day: derives from the explicit "Review" token day,
    # never a hardcoded weekday, and never claims an unverified Canvas resource.
    math_week = {
        "week": {"code": "Q2W3"},
        "days": {
            "Monday": {"date": "2026-10-26", "subjects": {"math": {"raw": "L39"}}},
            "Tuesday": {"date": "2026-10-27", "subjects": {"math": {"raw": "L40"}}},
            "Wednesday": {"date": "2026-10-28", "subjects": {"math": {"raw": "Review"}}},
            "Thursday": {"date": "2026-10-29", "subjects": {"math": {"raw": "WA7/ FA7*"}}},
            "Friday": {"date": "2026-10-30", "subjects": {"math": {"raw": "INV 4"}}},
        },
    }
    ms = draft_math_assessment_reminders(math_week)
    assert len(ms) == 1, ms
    body = ms[0]["body"]
    assert "Wednesday reviewing" in body, body          # review day, not hardcoded Monday
    assert "Wednesday evening" in body, body
    assert "Monday" not in body, body
    assert "Power Up B" in body, body                   # canonical FA7 -> B
    assert "available in Canvas" not in body, body      # resource UNVERIFIED -> fail closed
    assert ms[0]["power_up"] == "B"

    print("PASS intake reminders self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
