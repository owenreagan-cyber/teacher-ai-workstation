"""Part A2 — deterministic pacing translation (OWNER_POLICY).

Translates raw pacing tokens into canonical teacher-facing wording before any
local model is consulted. Reads the canonical config
``config/curriculum/canvas/pacing-translation-rules-2026-2027.json`` and never
invents curriculum meaning or unit names.

Shurley / Language Arts (OWNER_POLICY, approved by Owen Reagan):

* ``N.M``       -> ``Chapter N, Lesson M``
* ``Ch N L M``  -> ``Chapter N, Lesson M``
* ``CP<number>`` -> ``Classroom Practice <number>`` (+ graded assignment)
* ``Ch N Checkup`` -> ``Chapter N Checkup`` (no assignment)
* ``Ch N Test``    -> ``Chapter N Test`` (+ graded assignment)
* ``Ch N Review``  -> ``Chapter N Review`` (no assignment)
* bare ``Review`` / ``Checkup`` -> resolved with chapter context when known

Assignment policy: auto-create ONLY Chapter Tests and Classroom Practices.
Checkups, Reviews, and ordinary lessons are teacher-managed manually.

Science / History shared engine (OWNER_POLICY):

* Always include the authoritative unit name.
* Chapter-based entries use the word "Chapter".
* Unknown unit name fails closed; never model general knowledge.
* Assignment policy: auto-create ONLY Chapter Tests and Quizzes. A "Check" is
  NOT a quiz. Q2W1 Science produces agenda only (assignments = 0).

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
    """Load the canonical pacing translation rules."""
    return json.loads(C.PACING_TRANSLATION_RULES_PATH.read_text(encoding="utf-8"))


def format_due_date(iso_date: str) -> str:
    """Format an ISO date like '2026-10-15' as 'Thu Oct 15, 2026'."""
    if not iso_date:
        return ""
    d = datetime.strptime(iso_date, "%Y-%m-%d")
    return f"{d.strftime('%a %b')} {d.day}, {d.year}"


# --------------------------------------------------------------------------- #
# Shurley / Language Arts
# --------------------------------------------------------------------------- #

_SHURLEY_CP_RE = re.compile(r"^CP\s*(\d+)$", re.IGNORECASE)
_SHURLEY_LESSON_RE = re.compile(r"^(\d+)\s*\.\s*(\d+)$")
_SHURLEY_CH_LESSON_RE = re.compile(r"^Ch\.?\s*(\d+)\s*L\.?\s*(\d+)$", re.IGNORECASE)
_SHURLEY_CHECKUP_RE = re.compile(r"^(?:Ch\.?|CH|Chapter)\s*(\d+)\s*Checkup$", re.IGNORECASE)
_SHURLEY_TEST_RE = re.compile(r"^(?:Ch\.?|CH|Chapter)\s*(\d+)\s*Test$", re.IGNORECASE)
_SHURLEY_REVIEW_RE = re.compile(r"^(?:Ch\.?|CH|Chapter)\s*(\d+)\s*Review$", re.IGNORECASE)


def _shurley_assignment(kind: str, number: Any, day_date: str, config: dict[str, Any]) -> dict[str, Any]:
    """Build a Shurley assignment preview (Chapter Test or Classroom Practice)."""
    policy = config["subjects"]["language_arts"]["assignmentPolicy"]
    spec = policy[kind]
    return {
        "kind": kind,
        "title": spec["title"].format(N=number, number=number),
        "assignment_group": spec["group"],
        "points_possible": spec["points"],
        "grading_type": spec["gradingType"],
        "submission_types": spec["submissionType"],
        "counts_toward_final_grade": spec.get("countsTowardFinalGrade", True),
        "due_date": day_date,
        "due_date_display": format_due_date(day_date),
        "due_time": "11:59 PM",
        "timezone": "America/New_York",
        "authority": "OWNER_POLICY",
        "preview_only": True,
    }


def translate_shurley_cell(raw: str) -> dict[str, Any]:
    """Translate one Shurley/Language Arts pacing cell.

    Returns ``{source, lines, items, cp_numbers, test_numbers, assignments,
    resolved, unresolved}``. A cell like ``"5.2, CP19"`` renders both
    ``Chapter 5, Lesson 2`` and ``Classroom Practice 19`` and preserves both
    source tokens via ``source``.
    """
    source = (raw or "").strip()
    if not source:
        return {"source": "", "lines": [], "items": [], "cp_numbers": [], "test_numbers": [],
                "assignments": [], "resolved": True, "unresolved": []}

    tokens = [t.strip() for t in re.split(r"[,/]", source) if t.strip()]
    lines: list[str] = []
    items: list[dict[str, Any]] = []
    cp_numbers: list[int] = []
    test_numbers: list[int] = []
    unresolved: list[str] = []
    assignments: list[dict[str, Any]] = []
    # chapter context tracked by caller via translate_subject_week
    for token in tokens:
        m = _SHURLEY_CP_RE.match(token)
        if m:
            n = int(m.group(1))
            cp_numbers.append(n)
            lines.append(f"Classroom Practice {n}")
            items.append({"kind": "classroom_practice", "number": n, "translation": f"Classroom Practice {n}"})
            continue
        m = _SHURLEY_LESSON_RE.match(token) or _SHURLEY_CH_LESSON_RE.match(token)
        if m:
            lines.append(f"Chapter {m.group(1)}, Lesson {m.group(2)}")
            items.append({"kind": "lesson", "chapter": int(m.group(1)), "lesson": int(m.group(2)),
                          "translation": f"Chapter {m.group(1)}, Lesson {m.group(2)}"})
            continue
        m = _SHURLEY_CHECKUP_RE.match(token)
        if m:
            n = int(m.group(1))
            lines.append(f"Chapter {n} Checkup")
            items.append({"kind": "checkup", "chapter": n, "translation": f"Chapter {n} Checkup"})
            continue
        m = _SHURLEY_TEST_RE.match(token)
        if m:
            n = int(m.group(1))
            test_numbers.append(n)
            lines.append(f"Chapter {n} Test")
            items.append({"kind": "chapter_test", "chapter": n, "translation": f"Chapter {n} Test"})
            continue
        m = _SHURLEY_REVIEW_RE.match(token)
        if m:
            n = int(m.group(1))
            lines.append(f"Chapter {n} Review")
            items.append({"kind": "review", "chapter": n, "translation": f"Chapter {n} Review"})
            continue
        lowered = token.lower()
        if lowered == "review":
            lines.append("Review")
            items.append({"kind": "review", "chapter": None, "translation": "Review"})
            continue
        if lowered == "checkup":
            lines.append("Checkup")
            items.append({"kind": "checkup", "chapter": None, "translation": "Checkup"})
            continue
        if lowered == "test":
            lines.append("Test")
            items.append({"kind": "chapter_test", "chapter": None, "translation": "Test"})
            continue
        # No established meaning: preserve verbatim and mark unresolved.
        unresolved.append(token)
        lines.append(token)
        items.append({"kind": "unknown", "translation": token, "raw": token})

    return {
        "source": source,
        "lines": lines,
        "items": items,
        "cp_numbers": cp_numbers,
        "test_numbers": test_numbers,
        "assignments": assignments,
        "resolved": len(unresolved) == 0,
        "unresolved": unresolved,
    }


def classroom_practice_assignment(cp_number: int, day_date: str, config: dict[str, Any]) -> dict[str, Any]:
    """Build the Classroom Practice graded-assignment preview from canonical config."""
    return _shurley_assignment("classroomPractice", cp_number, day_date, config)


def chapter_test_assignment(chapter: int, day_date: str, config: dict[str, Any]) -> dict[str, Any]:
    """Build the Chapter Test graded-assignment preview."""
    return _shurley_assignment("chapterTest", chapter, day_date, config)


# --------------------------------------------------------------------------- #
# Shared History / Science unit-chapter-activity engine
# --------------------------------------------------------------------------- #

_SCIENCE_RANGE_RE = re.compile(
    r"^(?:Ch\.?|CH)\s*(\d+)\s*-\s*(\d+)\s*(Review|Check|Test|Quiz)?\s*$", re.IGNORECASE
)
_SCIENCE_SINGLE_RE = re.compile(
    r"^(?:Ch\.?|CH)\s*(\d+)\s*(Review|Check|Test|Quiz)?\s*$", re.IGNORECASE
)
_SCIENCE_FM_RE = re.compile(
    r"^F&M\s*:\s*CH\s*(\d+)\s*(Review|Check|Test|Quiz)?\s*$", re.IGNORECASE
)
_HISTORY_CHAPTER_RE = re.compile(
    r"^(?:Ch\.?|CH)\s*(\d+)\s*(Worksheet|Review|Test|Quiz)?\s*$", re.IGNORECASE
)


def resolve_science_unit_name(config: dict[str, Any], pacing_unit_context: str | None) -> str | None:
    """Resolve the Science unit name by owner-approved authority order.

    1. canonical unit config, 2. explicit pacing-guide context, 3. unresolved.
    Never model general knowledge.
    """
    canonical = config.get("subjects", {}).get("science", {}).get("unitName")
    if canonical:
        return canonical
    if pacing_unit_context:
        return pacing_unit_context.strip()
    return None


def resolve_history_unit_name(config: dict[str, Any], pacing_unit_context: str | None) -> str | None:
    """Resolve the History unit name by owner-approved authority order (fail-closed)."""
    canonical = config.get("subjects", {}).get("history", {}).get("unitName")
    if canonical:
        return canonical
    if pacing_unit_context:
        return pacing_unit_context.strip()
    return None


def _unit_result(source: str, lines: list[str], unit_name: str | None, resolved: bool,
                 unresolved: list[str], *, kind: str | None = None, assessment: bool = False) -> dict[str, Any]:
    return {
        "source": source,
        "lines": lines,
        "resolved": resolved,
        "unresolved": unresolved,
        "unitName": unit_name,
        "kind": kind,
        "assessment": assessment,
        "assignmentIntent": "NONE",  # History/Science: only test/quiz creates assignments; none here.
    }


def translate_science_cell(raw: str, unit_name: str | None) -> dict[str, Any]:
    """Translate one Science pacing cell using the shared unit engine.

    Splits on ``/`` so a cell like ``"Ch. 3 / 30cm"`` resolves ``Ch. 3`` and
    marks ``30cm`` as an unresolved component (never guessed).
    """
    source = (raw or "").strip()
    if not source:
        return {"source": "", "lines": [], "resolved": True, "unresolved": [], "unitName": unit_name, "kind": None, "assessment": False, "assignmentIntent": "NONE"}
    if not unit_name:
        return _unit_result(source, [source], None, False, [source], kind="unknown")

    segments = [s.strip() for s in re.split(r"/", source) if s.strip()]
    lines: list[str] = []
    unresolved: list[str] = []
    resolved = True
    assessment = False

    for seg in segments:
        m = _SCIENCE_RANGE_RE.match(seg)
        if m:
            a, b = m.group(1), m.group(2)
            tail = f" {m.group(3)}" if m.group(3) else ""
            lines.append(f"{unit_name} Chapters {a}-{b}{tail}")
            if m.group(3) and m.group(3).lower() in ("test", "quiz"):
                assessment = True
            continue
        m = _SCIENCE_SINGLE_RE.match(seg) or _SCIENCE_FM_RE.match(seg)
        if m:
            n = m.group(1)
            tail = f" {m.group(2)}" if m.group(2) else ""
            lines.append(f"{unit_name} Chapter {n}{tail}")
            if m.group(2) and m.group(2).lower() in ("test", "quiz"):
                assessment = True
            continue
        lowered = seg.lower()
        if lowered in ("review", "test", "quiz"):
            lines.append(f"{unit_name} {seg}")
            if lowered in ("test", "quiz"):
                assessment = True
            continue
        # Named activity or unknown component: prefix known activities with unit.
        if _looks_like_activity(seg):
            lines.append(f"{unit_name} {seg}")
        else:
            # Unknown component (e.g. "30cm"): preserve + mark unresolved.
            unresolved.append(seg)
            resolved = False
            lines.append(seg)

    return _unit_result(source, lines, unit_name, resolved, unresolved,
                        kind="chapter" if any("Chapter" in ln for ln in lines) else "activity",
                        assessment=assessment)


def _looks_like_activity(seg: str) -> bool:
    """Heuristic: a non-code token is an activity worth unit-prefixing.

    Keeps code-like fragments (numbers, measurements) out of the invented
    wording path.
    """
    if not seg:
        return False
    if re.fullmatch(r"[0-9./cm\s]+", seg, re.IGNORECASE):
        return False
    return True


def translate_history_cell(raw: str, unit_name: str | None) -> dict[str, Any]:
    """Translate one History pacing cell using the shared unit engine."""
    source = (raw or "").strip()
    if not source:
        return {"source": "", "lines": [], "resolved": True, "unresolved": [], "unitName": unit_name, "kind": None, "assessment": False, "assignmentIntent": "NONE"}
    if not unit_name:
        return _unit_result(source, [], None, False, [source], kind="unknown")

    m = _HISTORY_CHAPTER_RE.match(source)
    if m:
        n = m.group(1)
        tail = f" {m.group(2)}" if m.group(2) else ""
        assessment = bool(m.group(2) and m.group(2).lower() in ("test", "quiz"))
        return _unit_result(source, [f"{unit_name} Chapter {n}{tail}"], unit_name, True, [],
                            kind="chapter", assessment=assessment)

    lowered = source.lower()
    if lowered in ("review", "test", "quiz"):
        label = source
        assessment = lowered in ("test", "quiz")
        return _unit_result(source, [f"{unit_name} {label}"], unit_name, True, [],
                            kind=lowered, assessment=assessment)

    # Unrecognized but non-empty: preserve verbatim, mark unresolved.
    return _unit_result(source, [source], unit_name, False, [source], kind="unknown")


# --------------------------------------------------------------------------- #
# Per-week translation
# --------------------------------------------------------------------------- #

_TRANSLATABLE_SUBJECTS = ("language_arts", "science", "history")


def translate_subject_week(
    week: dict[str, Any],
    subject: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Translate one subject's whole week deterministically.

    Returns a report with per-weekday ``days``, a list of ``assignments``
    (Classroom Practice / Chapter Test previews), and an ``unresolved`` list.
    Subjects without canonical rules (math/reading/spelling) return raw values
    with ``deterministic=False`` so callers fall back to their own engines.
    """
    config = config or load_config()
    week_code = week.get("week", {}).get("code", "")
    unit_context = week.get("unitContext", {}) if isinstance(week.get("unitContext"), dict) else {}

    if subject not in _TRANSLATABLE_SUBJECTS:
        raw_days: dict[str, dict[str, Any]] = {}
        for wd, day in (week.get("days") or {}).items():
            raw = day.get("subjects", {}).get(subject, {}).get("raw", "")
            raw_days[wd] = {"source": raw, "lines": [], "resolved": False, "unresolved": []}
        return {
            "subject": subject,
            "deterministic": False,
            "authority": "MODEL_INFERENCE",
            "days": raw_days,
            "assignments": [],
            "unresolved": [],
        }

    # History redirect-only in Q2/Q4 (inactive rotating subject).
    if subject == "history":
        quarter = week_code[1] if len(week_code) >= 2 else ""
        if quarter in ("2", "4"):
            redirect = config["subjects"]["history"].get("redirectMessage")
            return {
                "subject": subject,
                "deterministic": True,
                "authority": "OWNER_POLICY",
                "mode": "inactive-redirect",
                "redirectMessage": redirect,
                "days": {},
                "assignments": [],
                "announcements": [],
                "unresolved": [],
                "note": "History is inactive this quarter; redirect-only, no normal instructional generation.",
            }

    days: dict[str, dict[str, Any]] = {}
    assignments: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []
    chapter_context: int | None = None

    for wd in C.WEEKDAYS:
        day = (week.get("days") or {}).get(wd, {})
        raw = day.get("subjects", {}).get(subject, {}).get("raw", "")
        date = day.get("date", "")

        if subject == "language_arts":
            res = translate_shurley_cell(raw)
            # Update chapter context from any explicit chapter in the cell.
            for item in res["items"]:
                if item.get("chapter"):
                    chapter_context = item["chapter"]
            # Resolve bare Review/Checkup/Test chapter context.
            for item in res["items"]:
                if item.get("kind") in ("review", "checkup") and item.get("chapter") is None and chapter_context is not None:
                    item["chapter"] = chapter_context
                    item["translation"] = f"Chapter {chapter_context} {item['translation'].split()[-1]}"
                elif item.get("kind") == "chapter_test" and item.get("chapter") is None and chapter_context is not None:
                    item["chapter"] = chapter_context
            # Assignments: only Classroom Practice and Chapter Test.
            for cp in res["cp_numbers"]:
                assignments.append(classroom_practice_assignment(cp, date, config))
            for n in res["test_numbers"]:
                assignments.append(chapter_test_assignment(n, date, config))
            # Rebuild lines from items (to reflect context resolution).
            lines = [it["translation"] for it in res["items"]]
            res["lines"] = lines
        elif subject == "science":
            unit = resolve_science_unit_name(config, unit_context.get("science"))
            res = translate_science_cell(raw, unit)
            # No assignment intent for Q2W1 science (chapter/check/review only).
            res["assignmentIntent"] = "NONE"
        else:  # history (active quarter)
            unit = resolve_history_unit_name(config, unit_context.get("history"))
            res = translate_history_cell(raw, unit)

        days[wd] = {
            "source": res["source"],
            "lines": res["lines"],
            "resolved": res["resolved"],
            "unresolved": res["unresolved"],
        }
        for token in res["unresolved"]:
            if token:
                unresolved.append({"weekday": wd, "token": token, "subject": subject})

    return {
        "subject": subject,
        "deterministic": True,
        "authority": "OWNER_POLICY",
        "week_code": week_code,
        "unit_context": unit_context,
        "days": days,
        "assignments": assignments,
        "unresolved": unresolved,
        "local_model": {
            "status": "SKIPPED",
            "reason": "all tokens resolved deterministically (OWNER_POLICY)",
        },
    }


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #


def command_self_test() -> int:
    config = load_config()

    # Shurley lesson expansion.
    r = translate_shurley_cell("5.1")
    assert r["lines"] == ["Chapter 5, Lesson 1"], r
    assert r["resolved"] is True and r["cp_numbers"] == []

    r = translate_shurley_cell("5.2, CP19")
    assert r["lines"] == ["Chapter 5, Lesson 2", "Classroom Practice 19"], r
    assert r["cp_numbers"] == [19], r
    assert r["resolved"] is True

    # Shurley token vocabulary: checkup / test / review / Ch N L M.
    assert translate_shurley_cell("CH5 Checkup")["lines"] == ["Chapter 5 Checkup"]
    assert translate_shurley_cell("Ch. 5 Checkup")["lines"] == ["Chapter 5 Checkup"]
    assert translate_shurley_cell("Chapter 5 Checkup")["lines"] == ["Chapter 5 Checkup"]
    assert translate_shurley_cell("CH5 Test")["lines"] == ["Chapter 5 Test"]
    assert translate_shurley_cell("Chapter 5 Test")["lines"] == ["Chapter 5 Test"]
    assert translate_shurley_cell("CH5 Review")["lines"] == ["Chapter 5 Review"]
    assert translate_shurley_cell("Ch.1 L6")["lines"] == ["Chapter 1, Lesson 6"]
    assert translate_shurley_cell("Review")["lines"] == ["Review"]
    assert translate_shurley_cell("CP20")["lines"] == ["Classroom Practice 20"]

    # Unknown Shurley token fails closed.
    unk = translate_shurley_cell("HG3")
    assert unk["resolved"] is False and unk["unresolved"] == ["HG3"], unk

    # Chapter Test assignment.
    ct = chapter_test_assignment(5, "2026-10-20", config)
    assert ct["title"] == "ELA4: Chapter 5 Test"
    assert ct["assignment_group"] == "Assessments"
    assert ct["points_possible"] == 100 and ct["grading_type"] == "percent" and ct["submission_types"] == "on_paper"

    # Classroom Practice assignment preview.
    a = classroom_practice_assignment(19, "2026-10-15", config)
    assert a["title"] == "Classroom Practice 19", a
    assert a["assignment_group"] == "Classwork"

    # Science translation with canonical unit name.
    unit = resolve_science_unit_name(config, None)
    assert unit == "Force and Motion", unit
    assert translate_science_cell("Ch. 1", unit)["lines"] == ["Force and Motion Chapter 1"]
    assert translate_science_cell("Ch. 2 Check", unit)["lines"] == ["Force and Motion Chapter 2 Check"]
    assert translate_science_cell("Ch. 1-2 Review", unit)["lines"] == ["Force and Motion Chapters 1-2 Review"]
    assert translate_science_cell("Ramp Lab", unit)["lines"] == ["Force and Motion Ramp Lab"]
    assert translate_science_cell("F&M: CH1", unit)["lines"] == ["Force and Motion Chapter 1"]

    # Science unknown component ("/30cm") preserved + unresolved.
    s = translate_science_cell("Ch. 3 / 30cm", unit)
    assert "Force and Motion Chapter 3" in s["lines"], s
    assert s["unresolved"] == ["30cm"], s
    assert s["resolved"] is False

    # Science Check is not a quiz (assignmentIntent NONE).
    assert translate_science_cell("Ch. 2 Check", unit)["assignmentIntent"] == "NONE"

    # Science fails closed without a unit name.
    r = translate_science_cell("Ch. 1", None)
    assert r["resolved"] is False and r["unresolved"] == ["Ch. 1"], r

    # History translation.
    assert translate_history_cell("Ch 3", "Maps")["lines"] == ["Maps Chapter 3"]
    assert translate_history_cell("Ch 4 Worksheet", "Maps")["lines"] == ["Maps Chapter 4 Worksheet"]
    assert translate_history_cell("Review", "Maps")["lines"] == ["Maps Review"]
    assert translate_history_cell("Test", "Maps")["lines"] == ["Maps Test"]
    assert translate_history_cell("Test", "Maps")["assessment"] is True
    assert translate_history_cell("Ch 3", None)["resolved"] is False

    # Whole-week translation (synthetic Q2W1-like week).
    week = {
        "week": {"code": "Q2W1", "startDate": "2026-10-12", "endDate": "2026-10-16"},
        "unitContext": {"science": "Force and Motion"},
        "days": {
            "Monday": {"date": "2026-10-12", "subjects": {"language_arts": {"raw": "5.1"}, "science": {"raw": "Ch. 1"}, "history": {"raw": ""}}},
            "Tuesday": {"date": "2026-10-13", "subjects": {"language_arts": {"raw": "5.1"}, "science": {"raw": "Ch. 1"}, "history": {"raw": ""}}},
            "Wednesday": {"date": "2026-10-14", "subjects": {"language_arts": {"raw": "5.2"}, "science": {"raw": "Ch. 2"}, "history": {"raw": ""}}},
            "Thursday": {"date": "2026-10-15", "subjects": {"language_arts": {"raw": "5.2, CP19"}, "science": {"raw": "Ch. 2 Check"}, "history": {"raw": ""}}},
            "Friday": {"date": "2026-10-16", "subjects": {"language_arts": {"raw": "5.3"}, "science": {"raw": "Ch. 1-2 Review"}, "history": {"raw": ""}}},
        },
    }

    la = translate_subject_week(week, "language_arts", config)
    assert la["deterministic"] is True
    assert la["days"]["Thursday"]["lines"] == ["Chapter 5, Lesson 2", "Classroom Practice 19"]
    assert len(la["assignments"]) == 1, la["assignments"]
    assert la["assignments"][0]["title"] == "Classroom Practice 19"
    assert la["assignments"][0]["due_date"] == "2026-10-15"
    assert la["unresolved"] == []

    sci = translate_subject_week(week, "science", config)
    assert sci["days"]["Monday"]["lines"] == ["Force and Motion Chapter 1"]
    assert sci["days"]["Friday"]["lines"] == ["Force and Motion Chapters 1-2 Review"]
    assert sci["unresolved"] == []
    assert sci["assignments"] == []  # no speculative Science assignments

    hist = translate_subject_week(week, "history", config)
    assert hist["mode"] == "inactive-redirect", hist
    assert hist["assignments"] == [] and hist["days"] == {}
    assert "Science" in hist["redirectMessage"]

    # Non-translatable subject returns deterministic=False.
    math = translate_subject_week(week, "math", config)
    assert math["deterministic"] is False

    print("PASS pacing translation self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
