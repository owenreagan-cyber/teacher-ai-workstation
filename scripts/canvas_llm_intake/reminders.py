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


def load_fact_test_map() -> dict[str, Any]:
    return json.loads(FACT_TEST_MAP.read_text(encoding="utf-8")).get("tests", {})


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

        body = _math_body(date_display, written, fact, power)
        reminders.append({
            "type": "math_assessment",
            "title": f"Math Assessment Reminder — {date_display}",
            "course": "Math",
            "course_id": 26404,
            "assessment_date": date,
            "written": written.get("title") if written else None,
            "fact": fact.get("title") if fact else None,
            "fact_count": "40 subtraction facts" if power else None,
            "power_up": power.get("powerUpCode") if power else None,
            "body": body,
            "requires_teacher_approval": True,
            "source_marker_exposed": False,
        })
    return reminders


def draft_spelling_reminders(week: dict[str, Any]) -> list[dict[str, Any]]:
    """Draft Spelling test reminder from normalized pacing.

    Detects a Spelling Test token and resolves the exact test number/date.
    The list range is authoritative (Lists 1-N) only for cumulative tests;
    do NOT generalize to other test numbers without an authoritative mapping.
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
    body = (
        "Good afternoon,\n\n"
        f"I wanted to send a quick reminder that students will be taking Spelling Test{num_txt} this {date_display}.\n\n"
        "We have covered a lot of spelling material so far this year, and this is a good "
        "opportunity for students to show how much they have learned. Spending a few minutes "
        "reviewing at home can make a big difference and help students feel confident going "
        "into the test.\n\n"
        + (_list_range(test_number) if test_number is not None else "")
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
        "requires_teacher_approval": True,
    }]


def _list_range(test_number: int) -> str:
    """Cumulative list range. Only authoritative for cumulative spelling tests."""
    if test_number == 40:
        return "Students should review Spelling Lists 1\u201340, paying special attention to words or patterns that have been challenging for them along the way.\n"
    return f"Students should review the current spelling list, paying special attention to words or patterns that have been challenging for them.\n"


def _display_date(iso_date: str) -> str:
    if not iso_date:
        return ""
    try:
        d = datetime.strptime(iso_date, "%Y-%m-%d")
        return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}"
    except ValueError:
        return iso_date


def _math_body(date_display: str, written: dict[str, Any] | None, fact: dict[str, Any] | None, power: dict[str, Any] | None) -> str:
    wa = written.get("number") if written else None
    fa = fact.get("number") if fact else None
    lines = ["Good afternoon,", ""]
    if wa is not None and fa is not None:
        lines.append(
            f"I wanted to send a quick reminder that students will be completing "
            f"Written Assessment {wa} and Fact Assessment {fa} on {date_display}."
        )
    lines.append("")
    lines.append(
        "We will spend time on Monday reviewing and preparing for the assessments, and "
        "students should continue reviewing at home Monday evening. Looking back over recent "
        "lesson work, practice problems, and corrections is a great way to prepare."
    )
    if power is not None:
        lines.append("")
        lines.append(
            f"For Fact Assessment {fa}, students should practice using Power Up "
            f"{power.get('powerUpCode')}. The Fact Assessment will include "
            f"40 subtraction facts, so a few minutes of focused fact practice at home can be "
            f"very helpful for building speed and confidence."
        )
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

    print("PASS intake reminders self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
