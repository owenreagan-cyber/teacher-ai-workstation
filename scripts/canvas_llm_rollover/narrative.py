"""Subject-isolated Week-in-Review + Next-Week-Overview narrative generation.

Produces the two narrative paragraphs that sit between the greeting and the
transition in each weekly-update announcement (§6 contract):

    Good afternoon,
    [WEEK IN REVIEW]
    [NEXT-WEEK OVERVIEW]
    The Canvas {subject} page has been updated...
    [FULL EXACT UPCOMING AGENDA]
    Have a great weekend!
    Mr. Reagan

Hard rules enforced here:

- Each subject's narrative reads ONLY that subject's raw pacing cells. There is
  no cross-subject access (course isolation, §9).
- Text is derived strictly from the source cells; nothing is invented (no
  scores, no mastery, no behavior claims, no fabricated resources).
- Output is deterministic for identical input.

The normalized week structure is the Phase 3 ``extract_week`` output:

    week_norm["days"][weekday]["subjects"][subject_key]["raw"]

``reading`` and ``spelling`` are separate keys that map to the single
Reading/Spelling course.
"""
from __future__ import annotations

import re
from typing import Iterable

from scripts.canvas_llm_phase3 import pacing_extractor as _pe
from scripts.canvas_llm_phase3 import pacing_translation as _pt

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

SUBJECT_LABELS = {
    "math": "Math",
    "reading_spelling": "Reading/Spelling",
    "language_arts": "Language Arts",
    "science": "Science",
    "history": "History",
}

# Normalized-week subject keys per course key.
_KEYS = {
    "math": ("math",),
    "reading_spelling": ("reading", "spelling"),
    "language_arts": ("language_arts",),
    "science": ("science",),
    "history": ("history",),
}


def _cells(week_norm: dict, subject: str) -> list[str]:
    keys = _KEYS.get(subject, (subject,))
    out: list[str] = []
    for wd in WEEKDAYS:
        day = (week_norm or {}).get("days", {}).get(wd, {})
        subs = day.get("subjects", {}) if isinstance(day, dict) else {}
        for key in keys:
            cell = subs.get(key, {}) if isinstance(subs, dict) else {}
            raw = (cell.get("raw") if isinstance(cell, dict) else "") or ""
            raw = str(raw).strip()
            if raw:
                out.append(raw)
    return out


def _cells_by_day(week_norm: dict, subject: str) -> dict[str, dict[str, str]]:
    """Return ``{weekday: {subject_key: raw}}`` for a subject's week.

    Preserves the weekday -> raw-cell mapping (unlike ``_cells``, which flattens
    across weekdays), so assessment dates can be derived from the day a major
    assessment actually occurs on.
    """
    keys = _KEYS.get(subject, (subject,))
    out: dict[str, dict[str, str]] = {}
    for wd in WEEKDAYS:
        day = (week_norm or {}).get("days", {}).get(wd, {})
        subs = day.get("subjects", {}) if isinstance(day, dict) else {}
        for key in keys:
            cell = subs.get(key, {}) if isinstance(subs, dict) else {}
            raw = (cell.get("raw") if isinstance(cell, dict) else "") or ""
            raw = str(raw).strip()
            if raw:
                out.setdefault(wd, {})[key] = raw
    return out


def _weekday_dates(week_norm: dict) -> dict[str, str]:
    """Return ``{weekday: 'Thursday, October 29'}`` for days with a known date."""
    out: dict[str, str] = {}
    for wd in WEEKDAYS:
        day = (week_norm or {}).get("days", {}).get(wd, {})
        iso = (day.get("date") if isinstance(day, dict) else "") or ""
        if iso:
            out[wd] = _pe.format_weekday_date_iso(iso)
    return out


def _major_assessments(subject: str, week_norm: dict) -> list[tuple[str, str]]:
    """Return ``[(weekday, label)]`` for major assessments in the upcoming week.

    Only items the source/policy classifies as major assessments get a date:
    Math Written/ Fact Assessment; Spelling Test; Reading Mastery Test/Checkout;
    Language Arts Chapter Test. Science ``Check (MC)``, labs, investigations,
    classroom practice, workbook, and ordinary lessons are NOT assessments
    (no date is added for them).
    """
    by_day = _cells_by_day(week_norm, subject)
    out: list[tuple[str, str]] = []
    for wd in WEEKDAYS:
        day = by_day.get(wd, {})
        if not day:
            continue
        labels: list[str] = []
        if subject == "math":
            raw = day.get("math", "")
            wa = _ints([raw], r"\bWA\s*(\d+)")
            fa = _ints([raw], r"\bFA\s*(\d+)")
            if wa:
                labels.append(f"Written Assessment {' and '.join(str(n) for n in wa)}")
            if fa:
                labels.append(f"Fact Assessment {' and '.join(str(n) for n in fa)}")
        elif subject == "reading_spelling":
            st = _ints([day.get("spelling", "")], r"\bTest\s*(\d+)")
            rt = _ints([day.get("reading", "")], r"\b(?:RMT|Mastery Test|Checkout|MT)\s*(\d+)")
            if st:
                labels.append(f"Spelling Test {' and '.join(str(n) for n in st)}")
            if rt:
                labels.append(f"Reading Test {' and '.join(str(n) for n in rt)}")
        elif subject == "language_arts":
            m = re.search(r"\b(?:CH|Ch|Chapter)\.?\s*(\d+)\s*Test\b",
                          day.get("language_arts", ""), re.IGNORECASE)
            if m:
                labels.append(f"Chapter {m.group(1)} Test")
        # science / history: no automatic major assessment
        if labels:
            out.append((wd, _join_and(labels)))
    return out


def _ints(cells: list[str], pattern: str) -> list[int]:
    seen: list[int] = []
    for c in cells:
        for m in re.findall(pattern, c, flags=re.IGNORECASE):
            try:
                n = int(m)
            except ValueError:
                continue
            if n not in seen:
                seen.append(n)
    return sorted(seen)


def _lesson_range(nums: list[int], singular: str = "Lesson") -> str:
    if not nums:
        return ""
    if len(nums) == 1:
        return f"{singular} {nums[0]}"
    # Collapse contiguous runs into ranges (e.g. 36,37,38 -> 36-38).
    runs: list[tuple[int, int]] = []
    for n in nums:
        if runs and n == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], n)
        else:
            runs.append((n, n))
    parts = []
    for a, b in runs:
        if a == b:
            parts.append(str(a))
        else:
            parts.append(f"{a}-{b}")
    noun = singular + "s" if len(nums) > 1 else singular
    return f"{noun} {', '.join(parts)}"


def _join_and(parts: Iterable[str]) -> str:
    parts = [p for p in parts if p]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


# --------------------------------------------------------------------------- #
# Math (Saxon Math 5)
# --------------------------------------------------------------------------- #

def _math_parts(cells: list[str]) -> dict:
    lessons = _ints(cells, r"\bL\s*(\d+)")
    wa = _ints(cells, r"\bWA\s*(\d+)")
    fa = _ints(cells, r"\bFA\s*(\d+)")
    inv = _ints(cells, r"\bINV\s*(\d+)")
    review = any(re.search(r"\breview\b", c, re.IGNORECASE) for c in cells)
    return {"lessons": lessons, "wa": wa, "fa": fa, "inv": inv, "review": review}


def _math_summary(parts: dict, *, future: bool) -> str:
    verb = "will complete" if future else "completed"
    fin = "finish" if future else "finished"
    items: list[str] = []
    if parts["lessons"]:
        items.append(_lesson_range(parts["lessons"]))
    if parts["review"]:
        items.append("the weekly review")
    if parts["inv"]:
        inv_noun = "Investigation" if len(parts["inv"]) == 1 else "Investigations"
        items.append(f"{inv_noun} {', '.join(str(n) for n in parts['inv'])}")
    assess = []
    if parts["wa"]:
        assess.append(f"Written Assessment {', '.join(str(n) for n in parts['wa'])}")
    if parts["fa"]:
        assess.append(f"Fact Assessment {', '.join(str(n) for n in parts['fa'])}")
    completed = _join_and(items)
    finished = _join_and(assess)
    if completed and finished:
        return f"{verb} {completed}, and {fin} {finished}"
    if completed:
        return f"{verb} {completed}"
    if finished:
        return f"{fin} {finished}"
    return "this week's lessons" if not future else "the upcoming lessons"


# --------------------------------------------------------------------------- #
# Reading/Spelling (Reading Mastery 4 + Spelling 4)
# --------------------------------------------------------------------------- #

def _rs_parts(cells_by_key: dict) -> dict:
    reading_cells = cells_by_key.get("reading", [])
    spelling_cells = cells_by_key.get("spelling", [])
    # Spelling tests appear as "Test <n>" under the spelling key.
    spell_tests = _ints(spelling_cells, r"\bTest\s*(\d+)")
    # Reading test/checkout tokens.
    reading_tests = _ints(reading_cells, r"\b(?:RMT|Test|Checkout)\s*(\d+)")
    # Lesson numbers exclude test numbers.
    reading = [n for n in _ints(reading_cells, r"\b(\d{1,2})\b") if n not in reading_tests]
    spelling = [n for n in _ints(spelling_cells, r"\b(\d{1,2})\b") if n not in spell_tests]
    return {
        "reading": reading, "spelling": spelling,
        "spell_tests": spell_tests, "reading_tests": reading_tests,
    }


# --------------------------------------------------------------------------- #
# Language Arts (Shurley English 4)
# --------------------------------------------------------------------------- #

def _la_parts(cells: list[str]) -> dict:
    chapters = _ints(cells, r"\b(?:CH|Ch|ch)\.?\s*(\d+)")
    lessons = _ints(cells, r"\bL\s*(\d+)")
    cp = _ints(cells, r"\bCP\s*(\d+)")
    checkup = any(re.search(r"checkup", c, re.IGNORECASE) for c in cells)
    test = any(re.search(r"\btest\b", c, re.IGNORECASE) for c in cells)
    compound = any(re.search(r"compound", c, re.IGNORECASE) for c in cells)
    review = any(re.search(r"\breview\b", c, re.IGNORECASE) for c in cells)
    return {
        "chapters": chapters, "lessons": lessons, "cp": cp,
        "checkup": checkup, "test": test, "compound": compound, "review": review,
    }


# --------------------------------------------------------------------------- #
# Science (Science 4)
# --------------------------------------------------------------------------- #

def _science_parts(cells: list[str]) -> dict:
    """Extract only Science unit number(s) and chapter number(s).

    Named activities (Reading / Slides / Notes / Finish / Quiz / Labs / Checks)
    are deliberately NOT extracted here: the family-facing narrative must stay
    chapter-level and never leak raw pacing activity names. Raw pacing cells are
    preserved verbatim upstream in the normalized week (source of truth).
    """
    units = _ints(cells, r"\bU\s*(\d+)")
    chapters = _ints(cells, r"\bCh\.?\s*(\d+)")
    return {"units": units, "chapters": chapters}


def _science_unit_name(week_norm: dict | None) -> str | None:
    """Resolve the Science unit display name (e.g. 'Force and Motion').

    Authority order: normalized-week ``unitContext``, then the canonical
    pacing-translation config. The config name is only authoritative for the
    configured unit (Unit 1), so it is not applied to weeks that reference a
    different unit number. Never models general knowledge.
    """
    ctx = (week_norm or {}).get("unitContext") or {}
    if isinstance(ctx, dict):
        name = (ctx.get("science") or "").strip()
        if name:
            return name
    cells = _cells(week_norm or {}, "science")
    units = _ints(cells, r"\bU\s*(\d+)")
    if units and units != [1]:
        return None
    try:
        return _pt.resolve_science_unit_name(_pt.load_config(), None)
    except Exception:  # noqa: BLE001 - unit name is advisory
        return None


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def week_in_review(subject: str, prior_norm: dict | None) -> str:
    """One deterministic, source-derived recap sentence for the prior week."""
    cells = _cells(prior_norm or {}, subject)
    if subject == "math":
        parts = _math_parts(cells)
        return f"We had another great week in Math! Students {_math_summary(parts, future=False)}."
    if subject == "reading_spelling":
        rk = {k: _cells(prior_norm or {}, k) for k in ("reading", "spelling")}
        parts = _rs_parts(rk)
        seg = []
        if parts["reading"]:
            seg.append(f"completed Reading {_lesson_range(parts['reading'])}")
        if parts["spelling"]:
            seg.append(f"completed Spelling {_lesson_range(parts['spelling'])}")
        tests = []
        if parts["spell_tests"]:
            tests.append(f"Spelling Test {', '.join(str(n) for n in parts['spell_tests'])}")
        if parts["reading_tests"]:
            tests.append(f"Reading Test {', '.join(str(n) for n in parts['reading_tests'])}")
        if tests:
            seg.append(f"finished {_join_and(tests)}")
        body = _join_and(seg) or "continued their reading and spelling work"
        return f"We had another great week in Reading/Spelling! Students {body}."
    if subject == "language_arts":
        parts = _la_parts(cells)
        seg = []
        if parts["chapters"]:
            seg.append(f"worked through {_lesson_range(parts['chapters'], 'Chapter')}")
        if parts["lessons"]:
            seg.append(f"completed {_lesson_range(parts['lessons'])}")
        if parts["cp"]:
            seg.append(f"practiced Classroom {_lesson_range(parts['cp'], 'Practice')}")
        if parts["checkup"]:
            seg.append("completed the chapter checkup")
        if parts["test"]:
            seg.append("took the chapter test")
        if parts["review"] and not seg:
            seg.append("reviewed the chapter")
        body = _join_and(seg) or "continued their Shurley grammar work"
        return f"We had another great week in Language Arts! Students {body}."
    if subject == "science":
        parts = _science_parts(cells)
        unit_name = _science_unit_name(prior_norm)
        seg = []
        if unit_name:
            seg.append(f"continued our {unit_name} unit")
        elif parts["units"]:
            seg.append(f"continued Unit {', '.join(str(n) for n in parts['units'])}")
        if parts["chapters"]:
            seg.append(f"worked through {_lesson_range(parts['chapters'], 'Chapter')}")
        body = _join_and(seg) or "continued their science investigations"
        return f"We had another great week in Science! Students {body}."
    # history is inactive during the Science rotation; no narrative.
    return ""


def next_week_overview(subject: str, next_norm: dict | None) -> str:
    """One deterministic, source-derived preview sentence for the upcoming week.

    Major assessments with a known, source-supported date include that date in
    the prose (canonical ``Day of the week, Month day`` form), per the
    weekly-update communication contract.
    """
    cells = _cells(next_norm or {}, subject)
    dates = _weekday_dates(next_norm or {})
    assess_days = _major_assessments(subject, next_norm or {})
    assess_clauses = [
        f"{label} on {dates[wd]}" if wd in dates else label
        for wd, label in assess_days
    ]
    assess = _join_and(assess_clauses) if assess_clauses else ""

    if subject == "math":
        parts = _math_parts(cells)
        items = []
        if parts["lessons"]:
            items.append(_lesson_range(parts["lessons"]))
        if parts["review"]:
            items.append("the weekly review")
        if parts["inv"]:
            inv_noun = "Investigation" if len(parts["inv"]) == 1 else "Investigations"
            items.append(f"{inv_noun} {', '.join(str(n) for n in parts['inv'])}")
        completed = _join_and(items)
        if completed and assess:
            body = f"will complete {completed}, and finish {assess}"
        elif completed:
            body = f"will complete {completed}"
        elif assess:
            body = f"will finish {assess}"
        else:
            body = "will continue the upcoming lessons"
        return f"Next week, students {body}."
    if subject == "reading_spelling":
        rk = {k: _cells(next_norm or {}, k) for k in ("reading", "spelling")}
        parts = _rs_parts(rk)
        seg = []
        if parts["reading"]:
            seg.append(f"complete Reading {_lesson_range(parts['reading'])}")
        if parts["spelling"]:
            seg.append(f"complete Spelling {_lesson_range(parts['spelling'])}")
        if assess:
            seg.append(f"finish {assess}")
        body = _join_and(seg) or "continue their reading and spelling work"
        return f"Next week, students will {body}."
    if subject == "language_arts":
        parts = _la_parts(cells)
        seg = []
        if parts["checkup"]:
            seg.append("take the chapter checkup")
        if parts["lessons"]:
            seg.append(f"begin {_lesson_range(parts['lessons'])}")
        if parts["cp"]:
            seg.append(f"practice Classroom {_lesson_range(parts['cp'], 'Practice')}")
        if parts["compound"]:
            seg.append("work on the compound sentence bridge")
        if assess:
            seg.append(f"take the {assess}")
        body = _join_and(seg) or "continue their Shurley grammar work"
        return f"Next week, students will {body}."
    if subject == "science":
        parts = _science_parts(cells)
        unit_name = _science_unit_name(next_norm)
        if unit_name and parts["chapters"]:
            return (f"Next week, students will continue our {unit_name} unit "
                    f"as we work through {_lesson_range(parts['chapters'], 'Chapter')}.")
        if unit_name:
            return f"Next week, students will continue our {unit_name} unit."
        if parts["chapters"]:
            return (f"Next week, students will work through "
                    f"{_lesson_range(parts['chapters'], 'Chapter')}.")
        # Science has no auto major assessment (Check (MC) / lab are not
        # tests/quizzes), so no assessment date is ever injected here.
        return "Next week, students will continue their science investigations."
    return ""


def command_self_test() -> int:
    # Deterministic Q2W2 (prior) and Q2W3 (upcoming) fixtures from the real
    # normalized-week cells (including per-day dates for assessment-date tests).
    prior = {
        "days": {
            "Monday": {"date": "2026-10-19",
                       "subjects": {"math": {"raw": "inv 3"}, "reading": {"raw": "41"},
                                    "spelling": {"raw": "36"}, "language_arts": {"raw": "5.3, CP20"},
                                    "science": {"raw": "Ch. 3"}}},
            "Tuesday": {"date": "2026-10-20",
                        "subjects": {"math": {"raw": "WA6/ FA6*"}, "reading": {"raw": "42"},
                                     "spelling": {"raw": "37"}, "language_arts": {"raw": "5.4, CP21"},
                                     "science": {"raw": "Ramp Lab"}}},
            "Wednesday": {"date": "2026-10-21",
                          "subjects": {"math": {"raw": "L36"}, "reading": {"raw": "43"},
                                       "spelling": {"raw": "38"}, "language_arts": {"raw": "5.5"},
                                       "science": {"raw": "Ramp Lab"}}},
            "Thursday": {"date": "2026-10-22",
                         "subjects": {"math": {"raw": "L37"}, "reading": {"raw": "44"},
                                      "spelling": {"raw": "39"}, "language_arts": {"raw": "5.6"},
                                      "science": {"raw": "Ch. 3"}}},
            "Friday": {"date": "2026-10-23",
                       "subjects": {"math": {"raw": "L38"}, "reading": {"raw": "45"},
                                    "spelling": {"raw": "Test 40"}, "language_arts": {"raw": "Review / CP23"},
                                    "science": {"raw": "Ch. 3 Check"}}},
        }
    }
    upcoming = {
        "days": {
            "Monday": {"date": "2026-10-26",
                       "subjects": {"math": {"raw": "L39"}, "reading": {"raw": "46"},
                                    "spelling": {"raw": "41"}, "language_arts": {"raw": "CH 5 Checkup"},
                                    "science": {"raw": "U1 Ch4 Electricity Transfer"}}},
            "Tuesday": {"date": "2026-10-27",
                        "subjects": {"math": {"raw": "L40"}, "reading": {"raw": "47"},
                                     "spelling": {"raw": "42"}, "language_arts": {"raw": "CH 5 Test"},
                                     "science": {"raw": "U1 Ch4 Electricity Detective"}}},
            "Wednesday": {"date": "2026-10-28",
                          "subjects": {"math": {"raw": "Review"}, "reading": {"raw": "48"},
                                       "spelling": {"raw": "43"}, "language_arts": {"raw": "Ch 7 L1 + CP25"},
                                       "science": {"raw": "U1 Ch4 Check (MC)"}}},
            "Thursday": {"date": "2026-10-29",
                         "subjects": {"math": {"raw": "WA7/ FA7*"}, "reading": {"raw": "49"},
                                      "spelling": {"raw": "44"}, "language_arts": {"raw": "Ch 7 L2 + CP26"},
                                      "science": {"raw": "U1 Ch5 Collisions / Crash Lab"}}},
            "Friday": {"date": "2026-10-30",
                       "subjects": {"math": {"raw": "INV 4"}, "reading": {"raw": "50"},
                                    "spelling": {"raw": "Test 45"}, "language_arts": {"raw": "Ch 7 Compound + CP27 bridge"},
                                    "science": {"raw": "U1 Ch5 Check (MC)"}}},
        }
    }

    math_review = week_in_review("math", prior)
    math_overview = next_week_overview("math", upcoming)
    assert "Math" in math_review and "36-38" in math_review, math_review
    assert "Written Assessment 6" in math_review and "Fact Assessment 6" in math_review, math_review
    assert "39-40" in math_overview and "Written Assessment 7" in math_overview, math_overview

    # CASE A — Math same-day dual assessment gets a dated phrase.
    assert "Written Assessment 7 and Fact Assessment 7 on Thursday, October 29" in math_overview, math_overview
    # CASE G — canonical date form; no ISO/slashed dates in prose.
    for bad in ("2026-10-29", "10/29", "Thu 10/29"):
        assert bad not in math_overview, (bad, math_overview)

    rs_review = week_in_review("reading_spelling", prior)
    assert "Reading" in rs_review and "41-45" in rs_review and "Spelling Test 40" in rs_review, rs_review
    rs_overview = next_week_overview("reading_spelling", upcoming)
    # CASE B — Spelling Test 45 carries its date.
    assert "Spelling Test 45 on Friday, October 30" in rs_overview, rs_overview

    la_overview = next_week_overview("language_arts", upcoming)
    assert "checkup" in la_overview, la_overview
    # CASE C — Chapter 5 Test carries its date.
    assert "Chapter 5 Test on Tuesday, October 27" in la_overview, la_overview

    sci_overview = next_week_overview("science", upcoming)
    assert "Force and Motion" in sci_overview, sci_overview
    assert "Chapters 4-5" in sci_overview, sci_overview
    # No raw activity-name leakage (Reading / Slides / Notes / Finish / Lab).
    assert "Electricity" not in sci_overview, sci_overview
    # CASE D — Science non-assessment items never get a fake assessment date.
    assert "on Thursday" not in sci_overview and "on Friday" not in sci_overview, sci_overview
    for bad in ("Test", "Quiz", "Assessment", "Reading", "Slides", "Notes", "Finish", "Lab"):
        assert bad not in sci_overview, (bad, sci_overview)

    # Course isolation: each subject's narrative must never leak another
    # subject's distinctive markers (§9 hard rule).
    forbidden = {
        "math": ["Reading Lesson", "Spelling Test", "Shurley", "Electricity",
                 "Crash Lab", "chapter checkup", "chapter test"],
        "reading_spelling": ["Written Assessment", "Fact Assessment", "Shurley",
                             "Electricity", "Crash Lab", "chapter checkup"],
        "language_arts": ["Written Assessment", "Fact Assessment", "Reading Lesson",
                          "Spelling Test", "Electricity", "Crash Lab"],
        "science": ["Written Assessment", "Fact Assessment", "Reading Lesson",
                    "Spelling Test", "Shurley", "chapter checkup"],
    }
    outputs = {
        "math": [math_review, math_overview],
        "reading_spelling": [rs_review, rs_overview],
        "language_arts": [week_in_review("language_arts", prior), la_overview],
        "science": [week_in_review("science", prior), sci_overview],
    }
    for s, texts in outputs.items():
        for text in texts:
            for tok in forbidden[s]:
                assert tok not in text, (s, tok, text)

    print("PASS canvas-rollover narrative self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
