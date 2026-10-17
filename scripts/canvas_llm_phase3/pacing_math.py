"""Phase 3.1 — deterministic Math pacing translation (OWNER_POLICY).

Translates raw Math pacing tokens into canonical teacher-facing In Class / At
Home content and graded-assignment previews, strictly from the owner-approved
operating contract (promoted to ``config/curriculum/canvas/math-work-patterns-2026-2027.json``).

Rules implemented (all OWNER_POLICY unless otherwise noted):

* ``L{n}``    -> ``Lesson {n}``
* ``INV {n}`` -> ``Investigation {n}`` (own artifact type; no lesson homework)
* ``WA{n}``   -> ``Written Assessment {n}``
* ``FA{n}``   -> ``Fact Assessment {n}``
* Daily classwork goal ``#1-10`` on lesson days
* Homework schedule: Monday ``#12-30 evens``, Wednesday ``#11-29 odds``,
  Tuesday/Thursday/Friday ``No Homework``
* Three weekly accuracy grades: Monday homework, Wednesday homework,
  Tuesday classwork (default; displaced to Thursday if Tuesday has an assessment)

Historical Canvas behavior (e.g. the "unfinished classwork" wording, bare
``SM5: Lesson N`` titles) is LIVE_CANVAS_PRECEDENT only and is never promoted
here. The local model is skipped when all fields resolve deterministically.

Read-only: no Canvas I/O, no network.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from typing import Any

from . import constants as C

# --------------------------------------------------------------------------- #
# Canonical config
# --------------------------------------------------------------------------- #


def load_config() -> dict[str, Any]:
    return json.loads(C.MATH_WORK_PATTERNS_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Token translation
# --------------------------------------------------------------------------- #

_LESSON_RE = re.compile(r"^(?:L|Lesson)\s*(\d+)\s*$", re.IGNORECASE)
_INV_RE = re.compile(r"^(?:INV|Investigation)\s*(\d+)\s*$", re.IGNORECASE)
_WA_RE = re.compile(r"^(?:WA|Written\s+Assessment)\s*(\d+)\s*$", re.IGNORECASE)
_FA_RE = re.compile(r"^(?:FA|Fact\s+Assessment)\s*(\d+)\s*$", re.IGNORECASE)
_REVIEW_RE = re.compile(r"^Review$", re.IGNORECASE)


def parse_math_tokens(raw: str) -> dict[str, Any]:
    """Parse a Math pacing cell into typed tokens.

    Accepts harmless deterministic variants (``L31``, ``L 31``, ``Lesson 31``).
    A trailing ``*`` is stripped for number extraction but surfaced in
    ``markers`` and ``unresolved`` because its semantics are not owner-defined.

    ``markers`` is a structural record (``{"marker": "*", "token": "FA6*",
    "meaning": "UNKNOWN"}``) so the marker is auditable and independently
    answerable, without changing the fact-assessment identity parsing.
    """
    source = (raw or "").strip()
    if not source:
        return {"source": "", "tokens": [], "unresolved": [], "markers": [], "resolved": True}

    segments = [s.strip() for s in re.split(r"[/,]", source) if s.strip()]
    tokens: list[dict[str, Any]] = []
    unresolved: list[str] = []
    markers: list[dict[str, Any]] = []
    for seg in segments:
        star = seg.endswith("*")
        core = seg[:-1].strip() if star else seg
        m = _LESSON_RE.match(core)
        if m:
            tokens.append({"kind": "lesson", "number": int(m.group(1)), "translation": f"Lesson {m.group(1)}"})
        elif (m := _INV_RE.match(core)):
            tokens.append({"kind": "investigation", "number": int(m.group(1)), "translation": f"Investigation {m.group(1)}"})
        elif (m := _WA_RE.match(core)):
            tokens.append({"kind": "written_assessment", "number": int(m.group(1)), "translation": f"Written Assessment {m.group(1)}"})
        elif (m := _FA_RE.match(core)):
            tokens.append({"kind": "fact_assessment", "number": int(m.group(1)), "translation": f"Fact Assessment {m.group(1)}"})
        elif (m := _REVIEW_RE.match(core)):
            tokens.append({"kind": "review", "number": None, "translation": "Review"})
        else:
            tokens.append({"kind": "unknown", "translation": core, "raw": core})
            unresolved.append(core)
        if star:
            markers.append({"marker": "*", "token": seg, "meaning": "UNKNOWN",
                            "note": "trailing '*' marker; identifier parsed, marker semantics not owner-defined"})
            unresolved.append(f"trailing '*' marker on '{seg}' (semantics not owner-defined)")
    return {"source": source, "tokens": tokens, "unresolved": unresolved,
            "markers": markers, "resolved": len(unresolved) == 0}


# --------------------------------------------------------------------------- #
# Homework + assignment helpers
# --------------------------------------------------------------------------- #


def homework_for_weekday(weekday: str, config: dict[str, Any]) -> tuple[str | None, str]:
    """Return (value|None, kind) for a weekday per the homework schedule."""
    entry = config["homeworkSchedule"].get(weekday, {})
    kind = entry.get("kind", "unresolved")
    value = entry.get("value")
    return value, kind


def assignment_base(config: dict[str, Any], day_date: str) -> dict[str, Any]:
    b = config["assignments"]["base"]
    return {
        "points_possible": b["pointsPossible"],
        "grading_type": b["gradingType"],
        "submission_types": b["submissionTypes"],
        "due_date": day_date,
        "due_date_display": format_due_date(day_date),
        "due_time": b["dueTimeDisplay"],
        "timezone": b["timezone"],
        "preview_only": b["previewOnly"],
        "authority": "OWNER_POLICY",
    }


def format_due_date(iso_date: str) -> str:
    if not iso_date:
        return ""
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{d.strftime('%a %b')} {d.day}, {d.year}"


def _homework_assignment(n: int, day_date: str, config: dict[str, Any]) -> dict[str, Any]:
    tpl = config["assignments"]["titles"]["homework"]
    a = assignment_base(config, day_date)
    a.update({
        "kind": "homework_accuracy_grade",
        "title": tpl["pattern"].format(n=n),
        "assignment_group": config["assignments"]["groups"]["homeworkClasswork"]["name"],
        "title_authority": tpl["authority"],
    })
    return a


def _classwork_assignment(n: int, day_date: str, weekday: str, config: dict[str, Any]) -> dict[str, Any]:
    tpl = config["assignments"]["titles"]["classwork"]
    a = assignment_base(config, day_date)
    a.update({
        "kind": "classwork_accuracy_grade",
        "title": tpl["pattern"].format(n=n),
        "title_authority": tpl["authority"],
        "assignment_group": config["assignments"]["groups"]["homeworkClasswork"]["name"],
        "selected_weekday": weekday,
    })
    return a


def _written_assignment(n: int, day_date: str, config: dict[str, Any]) -> dict[str, Any]:
    tpl = config["assignments"]["titles"]["writtenAssessment"]
    a = assignment_base(config, day_date)
    a.update({
        "kind": "written_assessment",
        "title": tpl["pattern"].format(n=n),
        "assignment_group": config["assignments"]["groups"]["writtenAssessment"]["name"],
        "title_authority": tpl["authority"],
    })
    return a


def _fact_assignment(n: int, day_date: str, config: dict[str, Any]) -> dict[str, Any]:
    tpl = config["assignments"]["titles"]["factAssessment"]
    a = assignment_base(config, day_date)
    a.update({
        "kind": "fact_assessment",
        "title": tpl["pattern"].format(n=n),
        "assignment_group": config["assignments"]["groups"]["factAssessment"]["name"],
        "title_authority": tpl["authority"],
    })
    return a


# --------------------------------------------------------------------------- #
# Day plan
# --------------------------------------------------------------------------- #


def math_day_plan(
    raw: str,
    weekday: str,
    day_date: str,
    week_has_tuesday_assessment: bool,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Deterministic plan for one Math weekday."""
    parsed = parse_math_tokens(raw)
    tokens = parsed["tokens"]
    cw_goal = config["dailyClassworkGoal"]["value"]

    in_class: list[str] = []
    at_home: str | None = None
    at_home_status = "no_homework"
    assignments: list[dict[str, Any]] = []
    token_kind = "unknown" if not tokens else tokens[0]["kind"]

    if token_kind == "lesson":
        n = tokens[0]["number"]
        in_class = [f"Lesson {n}", cw_goal]
        hw, hw_kind = homework_for_weekday(weekday, config)
        if hw_kind == "homework":
            at_home = hw
            at_home_status = "homework"
        else:
            at_home = None
            at_home_status = "no_homework"
        # Weekly accuracy grades.
        if weekday == "Monday":
            assignments.append(_homework_assignment(n, day_date, config))
        elif weekday == "Wednesday":
            assignments.append(_homework_assignment(n, day_date, config))
        elif weekday == "Tuesday" and not week_has_tuesday_assessment:
            assignments.append(_classwork_assignment(n, day_date, weekday, config))
        elif weekday == "Thursday" and week_has_tuesday_assessment:
            assignments.append(_classwork_assignment(n, day_date, weekday, config))
    elif token_kind == "investigation":
        n = tokens[0]["number"]
        in_class = [f"Investigation {n}"]
        at_home = None
        at_home_status = "no_homework"
        # No assignment; not an assessment, not a lesson accuracy grade.
    elif token_kind == "review":
        # Explicit "Review" is an in-class review day. No assignment is created;
        # no At Home is invented (owner may add review text via teacher input).
        in_class = ["Review"]
        at_home = None
        at_home_status = "no_homework"
    elif token_kind in ("written_assessment", "fact_assessment"):
        for t in tokens:
            if t["kind"] == "written_assessment":
                in_class.append(t["translation"])
                assignments.append(_written_assignment(t["number"], day_date, config))
            elif t["kind"] == "fact_assessment":
                in_class.append(t["translation"])
                assignments.append(_fact_assignment(t["number"], day_date, config))
        at_home = None
        at_home_status = "no_homework"
    else:
        # Unknown token: preserve verbatim, mark unresolved, no invented work.
        in_class = [t["translation"] for t in tokens] if tokens else [raw]
        at_home = None
        at_home_status = "unresolved"

    unresolved = list(parsed["unresolved"])
    if at_home_status == "unresolved":
        unresolved.append(f"at-home work for '{raw}'")

    return {
        "source": parsed["source"],
        "translation": ", ".join(t["translation"] for t in tokens) if tokens else "",
        "token_kind": token_kind,
        "in_class": in_class,
        "at_home": at_home,
        "at_home_status": at_home_status,
        "at_home_contract_wording": config["noHomeworkWording"] if at_home_status == "no_homework" else None,
        "assignments": assignments,
        "resolved": parsed["resolved"] and at_home_status != "unresolved",
        "unresolved": unresolved,
    }


# --------------------------------------------------------------------------- #
# Whole-week translation
# --------------------------------------------------------------------------- #


def translate_math_week(week: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Translate Math for one whole week deterministically."""
    config = config or load_config()
    week_code = week.get("week", {}).get("code", "")

    # Tuesday-assessment detection (affects classwork accuracy-grade day).
    tuesday_raw = ""
    tuesday_day = (week.get("days") or {}).get("Tuesday", {})
    if tuesday_day:
        tuesday_raw = tuesday_day.get("subjects", {}).get("math", {}).get("raw", "")
    week_has_tuesday_assessment = any(
        t["kind"] in ("written_assessment", "fact_assessment")
        for t in parse_math_tokens(tuesday_raw)["tokens"]
    )

    days: dict[str, dict[str, Any]] = {}
    assignments: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []

    for wd in C.WEEKDAYS:
        day = (week.get("days") or {}).get(wd, {})
        raw = day.get("subjects", {}).get("math", {}).get("raw", "")
        date = day.get("date", "")
        plan = math_day_plan(raw, wd, date, week_has_tuesday_assessment, config)
        plan["date"] = date
        days[wd] = plan
        assignments.extend(plan["assignments"])
        for u in plan["unresolved"]:
            if u:
                unresolved.append({"weekday": wd, "token": u, "subject": "math"})

    return {
        "subject": "math",
        "deterministic": True,
        "authority": "OWNER_POLICY",
        "week_code": week_code,
        "classwork_grade_day": "Thursday" if week_has_tuesday_assessment else "Tuesday",
        "days": days,
        "assignments": assignments,
        "unresolved": unresolved,
        "needs_owen_decision": _needs_owen_decision(assignments, config),
        "local_model": {
            "status": "SKIPPED",
            "reason": "all semantic fields resolved deterministically (OWNER_POLICY)",
        },
    }


def _needs_owen_decision(assignments: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect decisions that require Owen. Classwork title is now resolved."""
    return []


# --------------------------------------------------------------------------- #
# Human-readable preview
# --------------------------------------------------------------------------- #


def format_math_preview(report: dict[str, Any]) -> str:
    """Compact teacher-readable preview of one Math week."""
    lines = ["MATH — " + report.get("week_code", "")]
    for wd in C.WEEKDAYS:
        day = report.get("days", {}).get(wd, {})
        if not day:
            continue
        date = day.get("date") or ""
        heading = f"{wd}" + (f" — {date}" if date else "")
        lines.append("")
        lines.append(heading)
        lines.append("In Class:")
        for item in day.get("in_class", []):
            lines.append(f"  {item}")
        lines.append("")
        lines.append("At Home:")
        if day.get("at_home_status") == "homework":
            lines.append(f"  {day.get('at_home')}")
        elif day.get("at_home_status") == "no_homework":
            lines.append("  none / omitted")
        else:
            lines.append("  [unresolved]")
        for a in day.get("assignments", []):
            lines.append("")
            lines.append("Assignment:")
            title = a.get("title") or "[title: unresolved]"
            lines.append(f"  {title}")
            lines.append(f"  {a.get('points_possible')} pts / {a.get('grading_type')} / {a.get('submission_types')} / {a.get('assignment_group')}")
            lines.append(f"  due {a.get('due_date_display')} at {a.get('due_time')} {a.get('timezone')}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #


def command_self_test() -> int:
    config = load_config()

    # Token translation.
    assert parse_math_tokens("L31")["tokens"][0]["translation"] == "Lesson 31"
    assert parse_math_tokens("L 31")["tokens"][0]["translation"] == "Lesson 31"
    assert parse_math_tokens("Lesson 31")["tokens"][0]["translation"] == "Lesson 31"
    assert parse_math_tokens("L34")["tokens"][0]["translation"] == "Lesson 34"
    assert parse_math_tokens("INV 3")["tokens"][0]["translation"] == "Investigation 3"
    assert parse_math_tokens("Inv 3")["tokens"][0]["translation"] == "Investigation 3"
    assert parse_math_tokens("Investigation 3")["tokens"][0]["translation"] == "Investigation 3"
    assert parse_math_tokens("WA6")["tokens"][0]["translation"] == "Written Assessment 6"
    assert parse_math_tokens("FA6")["tokens"][0]["translation"] == "Fact Assessment 6"

    # Explicit "Review" is an in-class review day (no assignment, no At Home).
    rev = parse_math_tokens("Review")
    assert rev["tokens"][0]["kind"] == "review" and rev["resolved"] is True, rev
    rev_day = math_day_plan("Review", "Wednesday", "2026-10-28", False, config)
    assert rev_day["in_class"] == ["Review"] and rev_day["at_home_status"] == "no_homework"
    assert rev_day["assignments"] == [] and rev_day["unresolved"] == []

    # Combined assessment token parses both, '*' surfaced as unresolved + marker.
    combined = parse_math_tokens("WA6/ FA6*")
    kinds = [t["kind"] for t in combined["tokens"]]
    assert kinds == ["written_assessment", "fact_assessment"], kinds
    assert any("*" in u for u in combined["unresolved"]), combined
    assert combined["markers"] == [{"marker": "*", "token": "FA6*", "meaning": "UNKNOWN",
                                    "note": "trailing '*' marker; identifier parsed, marker semantics not owner-defined"}], combined
    # Identifier parsed independently of the unknown marker.
    assert combined["tokens"][1]["number"] == 6

    # Unknown token fails closed.
    unknown = parse_math_tokens("XYZ9")
    assert unknown["resolved"] is False and unknown["unresolved"] == ["XYZ9"]

    # Raw pacing preserved.
    assert parse_math_tokens("L31")["source"] == "L31"

    # Normal lesson day: Monday homework.
    mon = math_day_plan("L31", "Monday", "2026-10-12", False, config)
    assert mon["in_class"] == ["Lesson 31", "#1-10"], mon
    assert mon["at_home"] == "#12-30 evens" and mon["at_home_status"] == "homework"
    assert len(mon["assignments"]) == 1
    assert mon["assignments"][0]["title"] == "SM5: Lesson 31 Homework"
    assert mon["assignments"][0]["assignment_group"] == "Homework/Class Work"
    assert mon["assignments"][0]["points_possible"] == 100
    assert mon["assignments"][0]["grading_type"] == "percent"
    assert mon["assignments"][0]["submission_types"] == "on_paper"
    assert mon["assignments"][0]["due_time"] == "11:59 PM"
    assert mon["assignments"][0]["timezone"] == "America/New_York"
    assert mon["assignments"][0]["preview_only"] is True

    # Tuesday (no assessment) -> classwork accuracy grade (title resolved).
    tue = math_day_plan("L32", "Tuesday", "2026-10-13", False, config)
    assert tue["at_home_status"] == "no_homework" and tue["at_home"] is None
    assert len(tue["assignments"]) == 1
    assert tue["assignments"][0]["kind"] == "classwork_accuracy_grade"
    assert tue["assignments"][0]["title"] == "SM5: Lesson 32 Classwork"
    assert tue["assignments"][0]["title_authority"] == "OWNER_POLICY"

    # Wednesday homework.
    wed = math_day_plan("L33", "Wednesday", "2026-10-14", False, config)
    assert wed["at_home"] == "#11-29 odds"
    assert wed["assignments"][0]["title"] == "SM5: Lesson 33 Homework"

    # Thursday (no Tuesday assessment) -> no assignment, no homework.
    thu = math_day_plan("L34", "Thursday", "2026-10-15", False, config)
    assert thu["at_home_status"] == "no_homework" and thu["assignments"] == []

    # Friday Investigation -> own type, no homework, no assignment.
    fri = math_day_plan("INV 3", "Friday", "2026-10-16", False, config)
    assert fri["token_kind"] == "investigation"
    assert fri["in_class"] == ["Investigation 3"]
    assert fri["at_home_status"] == "no_homework" and fri["at_home"] is None
    assert fri["assignments"] == []

    # Investigation does NOT inherit lesson homework even on Monday.
    inv_mon = math_day_plan("INV 3", "Monday", "2026-10-12", False, config)
    assert inv_mon["at_home_status"] == "no_homework" and inv_mon["at_home"] is None

    # Assessment tokens do not inherit lesson homework.
    tue_assess = math_day_plan("WA4/ FA4", "Tuesday", "2026-10-13", False, config)
    assert tue_assess["at_home_status"] == "no_homework"
    assert [a["kind"] for a in tue_assess["assignments"]] == ["written_assessment", "fact_assessment"]
    assert tue_assess["assignments"][0]["title"] == "SM5: Written Assessment 4"
    assert tue_assess["assignments"][1]["title"] == "SM5: Fact Assessment 4"
    assert tue_assess["assignments"][0]["assignment_group"] == "Written Assessments"
    assert tue_assess["assignments"][1]["assignment_group"] == "Fact Assessments"

    # Tuesday assessment displaces classwork grade to Thursday.
    tue2 = math_day_plan("WA6/ FA6", "Tuesday", "2026-10-13", True, config)
    assert tue2["assignments"] == [] or all(a["kind"] != "classwork_accuracy_grade" for a in tue2["assignments"])
    thu2 = math_day_plan("L34", "Thursday", "2026-10-15", True, config)
    assert any(a["kind"] == "classwork_accuracy_grade" for a in thu2["assignments"]), thu2

    # Whole-week translation (synthetic Q2W1-like).
    week = {
        "week": {"code": "Q2W1", "startDate": "2026-10-12", "endDate": "2026-10-16"},
        "days": {
            "Monday": {"date": "2026-10-12", "subjects": {"math": {"raw": "L31"}}},
            "Tuesday": {"date": "2026-10-13", "subjects": {"math": {"raw": "L32"}}},
            "Wednesday": {"date": "2026-10-14", "subjects": {"math": {"raw": "L33"}}},
            "Thursday": {"date": "2026-10-15", "subjects": {"math": {"raw": "L34"}}},
            "Friday": {"date": "2026-10-16", "subjects": {"math": {"raw": "INV 3"}}},
        },
    }
    report = translate_math_week(week, config)
    assert report["deterministic"] is True and report["authority"] == "OWNER_POLICY"
    assert report["classwork_grade_day"] == "Tuesday"
    assert len(report["assignments"]) == 3, report["assignments"]
    titles = [a["title"] for a in report["assignments"] if a.get("title")]
    assert "SM5: Lesson 31 Homework" in titles
    assert "SM5: Lesson 33 Homework" in titles
    assert "SM5: Lesson 32 Classwork" in titles
    assert any(a["kind"] == "classwork_accuracy_grade" for a in report["assignments"])
    assert report["needs_owen_decision"] == []
    assert report["local_model"]["status"] == "SKIPPED"

    print("PASS math pacing translation self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
