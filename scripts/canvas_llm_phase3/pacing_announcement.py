"""Phase 3.2 — assessment + announcement intelligence (deterministic facts + dry-run writer).

Deterministic layer only: resolves assessment facts from pacing, plans the
two-notice communication (FIRST_NOTICE ~5 days, REMINDER ~1-2 days), computes
duplicate identities, and drives a bounded style-only local-Qwen announcement
writer. Reads canonical maps; never invents facts, never selects resources, and
never writes to Canvas.

Rules promoted here (OWNER_POLICY, approved by Owen Reagan):

* Math cumulative assessment + Fact Test on the same day -> TWO gradebook
  assignments (Written Assessments + Fact Assessments) -> ONE combined
  announcement for family communication.
* Reading Mastery Test + Fluency Checkout on the same day -> TWO assignments
  (Assessments + Check Out) -> ONE combined announcement.
* Fact Test -> Power Up letter (deterministic map) -> verified Canvas file
  (currently UNRESOLVED -> FAIL CLOSED).
* Reading Test -> Checkout (1-13); Test 14 has no Checkout.
* Local Qwen: style only. It receives the already-resolved fact packet and must
  not alter any deterministic field.

Read-only: no Canvas I/O, no network.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, datetime, timedelta
from typing import Any

from . import constants as C
from . import pacing_translation as pt

# --------------------------------------------------------------------------- #
# Canonical config + maps
# --------------------------------------------------------------------------- #


def load_config() -> dict[str, Any]:
    return json.loads(C.ASSESSMENT_ANNOUNCEMENT_POLICY_PATH.read_text(encoding="utf-8"))


def _load_json(path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_fact_test_map() -> dict[str, Any]:
    return _load_json(C.REPO_ROOT / "config" / "curriculum" / "math" / "saxon-math-5" / "fact-test-practice-map.json")


def load_checkout_map() -> dict[str, Any]:
    return _load_json(C.REPO_ROOT / "config" / "curriculum" / "reading" / "reading-mastery-4" / "checkout-passage-map.json")


# Fluency targets confirmed for Checkouts 1-7; 8-13 unresolved.
_CONFIRMED_FLUENCY = {str(n): {"wpm": 100, "maxErrors": 2} for n in range(1, 8)}


# --------------------------------------------------------------------------- #
# Assessment token parsing (reuse math token shapes where applicable)
# --------------------------------------------------------------------------- #

_WA_RE = re.compile(r"^(?:WA|Written\s+Assessment)\s*(\d+)\s*$", re.IGNORECASE)
_FA_RE = re.compile(r"^(?:FA|Fact\s+Assessment)\s*(\d+)\s*$", re.IGNORECASE)
_RMT_RE = re.compile(r"^(?:MT|Mastery\s+Test)\s*(\d+)\s*$", re.IGNORECASE)
_SPELLING_TEST_RE = re.compile(r"^(?:Test|Spelling\s+Test)\s*(\d+)\s*$", re.IGNORECASE)


def math_assessment_numbers(raw: str) -> dict[str, int | None]:
    """Return {'written': n, 'fact': n} parsed from a Math pacing cell."""
    out: dict[str, int | None] = {"written": None, "fact": None}
    for seg in re.split(r"[/,]", (raw or "").strip()):
        seg = seg.strip().rstrip("*").strip()
        m = _WA_RE.match(seg)
        if m:
            out["written"] = int(m.group(1))
            continue
        m = _FA_RE.match(seg)
        if m:
            out["fact"] = int(m.group(1))
    return out


def resolve_fact_test(n: int) -> dict[str, Any] | None:
    """Resolve Fact Test N -> {powerUp, skill, resource}. Resource is UNRESOLVED."""
    m = load_fact_test_map().get("tests", {}).get(str(n))
    if not m:
        return None
    return {
        "factTestNumber": n,
        "powerUp": m.get("powerUpCode"),
        "skill": m.get("practiceDescription"),
        "resource": None,
        "resourceStatus": "UNRESOLVED",
        "resourceReason": "no verified Canvas Power Up PDF file ID in repo config; requires future GET-only Files sweep",
    }


def resolve_checkout(n: int) -> dict[str, Any] | None:
    """Resolve Checkout N -> passage/fluency metadata. Test 14 -> None."""
    if not 1 <= n <= 13:
        return None
    m = load_checkout_map().get("checkouts", {}).get(str(n))
    if not m:
        return None
    flu = _CONFIRMED_FLUENCY.get(str(n), {"wpm": None, "maxErrors": None})
    return {
        "checkoutNumber": n,
        "readingTestNumber": n,
        "passage": m.get("passage"),
        "bookVolume": m.get("bookVolume"),
        "page": m.get("page"),
        "fluency": flu,
        "fluencyResolved": str(n) in _CONFIRMED_FLUENCY,
    }


# --------------------------------------------------------------------------- #
# Fact packet resolution
# --------------------------------------------------------------------------- #


def resolve_assessment_facts(week: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve deterministic assessment fact packets from a normalized week.

    Returns a list of assessment events (math pair, reading pair, spelling),
    each carrying deterministic facts. No model inference.
    """
    from . import pacing_reading as prd

    # Latest Reading lesson (for RMT+FCO test-number resolution).
    latest_reading_lesson = 0
    for wd in C.WEEKDAYS:
        day = (week.get("days") or {}).get(wd, {})
        raw = day.get("subjects", {}).get("reading", {}).get("raw", "")
        tok = prd.parse_reading_token(raw)
        if tok["kind"] == "lesson" and tok["number"]:
            latest_reading_lesson = max(latest_reading_lesson, tok["number"])

    events: list[dict[str, Any]] = []
    for wd in C.WEEKDAYS:
        day = (week.get("days") or {}).get(wd, {})
        date = day.get("date", "")
        subjects = day.get("subjects", {})
        math_raw = subjects.get("math", {}).get("raw", "")
        reading_raw = subjects.get("reading", {}).get("raw", "")
        spelling_raw = subjects.get("spelling", {}).get("raw", "")

        ma = math_assessment_numbers(math_raw)
        if ma["written"] is not None or ma["fact"] is not None:
            fact = resolve_fact_test(ma["fact"]) if ma["fact"] is not None else None
            events.append({
                "family": "math_assessment",
                "course": "Math",
                "courseId": 26404,
                "assessmentDate": date,
                "weekday": wd,
                "assessments": [
                    f"Math Test {ma['written']}" if ma["written"] is not None else None,
                    f"Fact Test {ma['fact']}" if ma["fact"] is not None else None,
                ],
                "assignments": [
                    {"kind": "written_assessment", "group": "Written Assessments", "title": f"SM5: Written Assessment {ma['written']}", "number": ma["written"]},
                    {"kind": "fact_assessment", "group": "Fact Assessments", "title": f"SM5: Fact Assessment {ma['fact']}", "number": ma["fact"]},
                ],
                "preparation": {
                    "cumulativeAssessment": "prepare for the cumulative Math assessment",
                    "factSkill": fact["skill"] if fact else None,
                    "powerUp": fact["powerUp"] if fact else None,
                    "resource": None,
                    "resourceStatus": "UNRESOLVED" if fact else None,
                },
                "facts": {
                    "assessmentDate": date,
                    "assessments": [f"Math Test {ma['written']}", f"Fact Test {ma['fact']}"],
                },
            })

        rtok = prd.parse_reading_token(reading_raw)
        if rtok["kind"] == "rmt_fco" and latest_reading_lesson:
            res = prd.resolve_reading_test_checkout(latest_reading_lesson)
            n = res["readingTestNumber"]
            checkout = res["checkoutExists"]
            events.append({
                "family": "reading_assessment",
                "course": "Reading/Spelling",
                "courseId": 26442,
                "assessmentDate": date,
                "weekday": wd,
                "assessments": [f"Reading Mastery Test {n}", f"Fluency Checkout {n}" if checkout else None],
                "assignments": [
                    {"kind": "mastery_test", "group": "Assessments", "title": f"RM4: Mastery Test {n}", "number": n},
                    {"kind": "fluency_checkout", "group": "Check Out", "title": f"RM4: Fluency Checkout {n}", "number": n} if checkout else None,
                ],
                "preparation": {
                    "masteryTest": "prepare for the Reading Mastery Test",
                    "fluency": res["fluencyResolved"],
                    "fluencyWpm": res["fluency"]["wpm"] if res["fluency"] else None,
                    "fluencyMaxErrors": res["fluency"]["maxErrors"] if res["fluency"] else None,
                },
                "facts": {
                    "assessmentDate": date,
                    "assessments": [f"Reading Mastery Test {n}"] + ([f"Fluency Checkout {n}"] if checkout else []),
                    "checkoutExists": checkout,
                },
            })
        else:
            rmt = _RMT_RE.match(reading_raw.strip())
            if rmt:
                n = int(rmt.group(1))
                checkout = resolve_checkout(n)
                events.append({
                    "family": "reading_assessment",
                    "course": "Reading/Spelling",
                    "courseId": 26442,
                    "assessmentDate": date,
                    "weekday": wd,
                    "assessments": [f"Reading Mastery Test {n}", f"Fluency Checkout {n}" if checkout else None],
                    "assignments": [
                        {"kind": "mastery_test", "group": "Assessments", "title": f"RM4: Mastery Test {n}", "number": n},
                        {"kind": "fluency_checkout", "group": "Check Out", "title": f"RM4: Fluency Checkout {n}", "number": n} if checkout else None,
                    ],
                    "preparation": {
                        "masteryTest": "prepare for the Reading Mastery Test",
                        "fluency": checkout and checkout["fluency"]["wpm"] is not None,
                        "fluencyWpm": checkout and checkout["fluency"]["wpm"],
                        "fluencyMaxErrors": checkout and checkout["fluency"]["maxErrors"],
                    },
                    "facts": {
                        "assessmentDate": date,
                        "assessments": [f"Reading Mastery Test {n}"] + ([f"Fluency Checkout {n}"] if checkout else []),
                        "checkoutExists": checkout is not None,
                    },
                })

        st = _SPELLING_TEST_RE.match(spelling_raw.strip())
        # A bare "Test" token resolves the Spelling test number from the week's
        # numbered lessons (tests every fifth lesson).
        if not st and spelling_raw.strip().lower() in ("test", "test "):
            spelling_test_number = prd.resolve_spelling_test_number(week)
            if spelling_test_number:
                st = re.match(r"^(\d+)$", str(spelling_test_number))
        if st:
            n = int(st.group(1))
            practice_start = max(1, n - 4)
            practice_end = n - 1
            events.append({
                "family": "spelling_assessment",
                "course": "Reading/Spelling",
                "courseId": 26442,
                "assessmentDate": date,
                "weekday": wd,
                "assessments": [f"Spelling Test {n}"],
                "assignments": [{"kind": "spelling_test", "group": "Assessments", "title": f"RM4: Spelling Test {n}", "number": n}],
                "preparation": {
                    "practiceRange": f"Lessons {practice_start} through {practice_end}",
                },
                "facts": {
                    "assessmentDate": date,
                    "assessments": [f"Spelling Test {n}"],
                },
            })

        # Language Arts / Shurley Chapter Test (auto-create + announcement).
        la_raw = subjects.get("language_arts", {}).get("raw", "")
        if la_raw:
            la_cell = pt.translate_shurley_cell(la_raw)
            for chapter in la_cell["test_numbers"]:
                events.append({
                    "family": "language_arts_assessment",
                    "course": "Language Arts",
                    "courseId": 28171,
                    "assessmentDate": date,
                    "weekday": wd,
                    "assessments": [f"Chapter {chapter} Test"],
                    "assignments": [{"kind": "chapter_test", "group": "Assessments", "title": f"ELA4: Chapter {chapter} Test", "number": chapter}],
                    "preparation": {"prepare": "prepare for the Shurley Chapter Test"},
                    "facts": {"assessmentDate": date, "assessments": [f"Chapter {chapter} Test"]},
                })

        # Science / History: only explicit test/quiz tokens trigger announcements.
        science_raw = subjects.get("science", {}).get("raw", "")
        if science_raw:
            sci_unit = pt.resolve_science_unit_name(pt.load_config(), (week.get("unitContext") or {}).get("science"))
            sci_cell = pt.translate_science_cell(science_raw, sci_unit)
            if sci_cell.get("assessment"):
                events.append({
                    "family": "science_assessment",
                    "course": "Science",
                    "courseId": 28166,
                    "assessmentDate": date,
                    "weekday": wd,
                    "assessments": sci_cell["lines"],
                    "assignments": [],
                    "preparation": {},
                    "facts": {"assessmentDate": date, "assessments": sci_cell["lines"]},
                })

        history_raw = subjects.get("history", {}).get("raw", "")
        if history_raw:
            hist_unit = pt.resolve_history_unit_name(pt.load_config(), (week.get("unitContext") or {}).get("history"))
            hist_cell = pt.translate_history_cell(history_raw, hist_unit)
            if hist_cell.get("assessment"):
                events.append({
                    "family": "history_assessment",
                    "course": "History",
                    "courseId": 28165,
                    "assessmentDate": date,
                    "weekday": wd,
                    "assessments": hist_cell["lines"],
                    "assignments": [],
                    "preparation": {},
                    "facts": {"assessmentDate": date, "assessments": hist_cell["lines"]},
                })

    return events


# --------------------------------------------------------------------------- #
# Scheduling
# --------------------------------------------------------------------------- #


def _prior_instructional_day(d: date) -> date:
    """Move back to the most recent weekday (Mon-Fri)."""
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def schedule_notices(assessment_date: str, config: dict[str, Any]) -> dict[str, Any]:
    """Compute FIRST_NOTICE and REMINDER planned dates from policy lead days.

    Weekend/break-aware: a computed weekend date moves to the prior weekday,
    and a warning is emitted when the move pushes the notice outside its
    intended lead window (rather than silently choosing a bad date).
    Returns {'firstNotice': iso, 'reminder': iso, 'warnings': [...]}.
    """
    a = date.fromisoformat(assessment_date)
    first_lead = config["twoNoticePolicy"]["firstNotice"]["targetLeadDays"]
    rem_lead = config["twoNoticePolicy"]["reminder"]["defaultLeadDays"]
    warnings: list[str] = []

    first = a - timedelta(days=first_lead)
    if first.weekday() >= 5:
        first = _prior_instructional_day(first)
        warnings.append("FIRST_NOTICE moved earlier due to weekend; lead is now under 5 days")

    reminder = a - timedelta(days=rem_lead)
    if reminder.weekday() >= 5:
        reminder = _prior_instructional_day(reminder)
        warnings.append("REMINDER moved earlier due to weekend; reminder lead now exceeds 2 days")

    if first >= a:
        warnings.append("FIRST_NOTICE date is not before the assessment date; teacher review required")
    if reminder >= a:
        warnings.append("REMINDER date is not before the assessment date; teacher review required")
    return {"firstNotice": first.isoformat(), "reminder": reminder.isoformat(), "warnings": warnings}


# --------------------------------------------------------------------------- #
# Duplicate identity
# --------------------------------------------------------------------------- #


def announcement_identity(course: str, family: str, source_event: str, assessment_date: str, notice_type: str) -> str:
    key = "|".join([course, family, source_event, assessment_date, notice_type])
    return "ann-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def source_event_label(event: dict[str, Any]) -> str:
    return "+".join(a for a in (event.get("assessments") or []) if a)


# --------------------------------------------------------------------------- #
# Announcement state machine
# --------------------------------------------------------------------------- #

_ANNOUNCEMENT_STATES = (
    "SOURCE_TRIGGER",
    "FACTS_RESOLVED",
    "DRAFTED",
    "TEACHER_APPROVED",
    "SCHEDULED_INTENT",
    "PUBLISHED_VERIFIED",
)
_PHASE32_BLOCKED = {"PUBLISHED_VERIFIED"}
_VALID_TRANSITIONS = {
    "SOURCE_TRIGGER": {"FACTS_RESOLVED"},
    "FACTS_RESOLVED": {"DRAFTED"},
    "DRAFTED": {"TEACHER_APPROVED", "FACTS_RESOLVED"},
    "TEACHER_APPROVED": {"SCHEDULED_INTENT", "DRAFTED"},
    "SCHEDULED_INTENT": {"TEACHER_APPROVED"},
    "PUBLISHED_VERIFIED": set(),
}


class AnnouncementStateError(RuntimeError):
    pass


def transition_announcement(item: dict[str, Any], target: str, *, reason: str) -> dict[str, Any]:
    current = item.get("state", "SOURCE_TRIGGER")
    if target in _PHASE32_BLOCKED:
        raise AnnouncementStateError("PUBLISHED_VERIFIED cannot be entered in Phase 3.2")
    if current not in _ANNOUNCEMENT_STATES or target not in _ANNOUNCEMENT_STATES:
        raise AnnouncementStateError(f"unknown state {current!r} -> {target!r}")
    if target not in _VALID_TRANSITIONS[current]:
        raise AnnouncementStateError(f"invalid transition {current} -> {target}")
    item["state"] = target
    item.setdefault("history", []).append({"from": current, "to": target, "reason": reason})
    return item


# --------------------------------------------------------------------------- #
# Local-Qwen style-only dry-run writer
# --------------------------------------------------------------------------- #


def draft_announcement(fact_packet: dict[str, Any], notice_type: str, *, use_llm: bool = False) -> dict[str, Any]:
    """Produce a draft for one notice type.

    ``use_llm=False`` (default) returns a deterministic template draft without
    invoking the local model. ``use_llm=True`` invokes Qwen style-only and
    verifies the facts block is preserved.
    """
    if notice_type not in ("FIRST_NOTICE", "REMINDER"):
        raise ValueError("notice_type must be FIRST_NOTICE or REMINDER")

    wording = _template_wording(fact_packet, notice_type)
    model_status = "SKIPPED"

    if use_llm:
        from . import local_llm as llm
        if llm.model_available():
            try:
                styled = llm.run_model(_writer_prompt(fact_packet, notice_type))
                candidate = styled.get("message") or styled.get("body_text") or ""
                if candidate and _facts_preserved(fact_packet, candidate):
                    wording = candidate
                    model_status = "OK"
                else:
                    model_status = "REJECTED_FACTS_CHANGED"
            except Exception as exc:  # noqa: BLE001
                model_status = f"UNAVAILABLE:{type(exc).__name__}"
        else:
            model_status = "UNAVAILABLE"

    return {
        "notice_type": notice_type,
        "course": fact_packet.get("course"),
        "assessment_date": fact_packet.get("assessmentDate"),
        "facts": dict(fact_packet.get("facts", {})),
        "wording": wording,
        "facts_preserved": True,
        "model_status": model_status,
        "authority": "OWNER_POLICY (facts) + MODEL_INFERENCE (style)" if model_status == "OK" else "OWNER_POLICY",
    }


def _template_wording(fp: dict[str, Any], notice_type: str) -> str:
    course = fp.get("course", "")
    date_disp = _display_date(fp.get("assessmentDate"))
    assessments = fp.get("assessments") or []
    joined = " and ".join(assessments)
    lead = "This week" if notice_type == "FIRST_NOTICE" else "Reminder"
    lines = [f"Good afternoon,", f"{lead}, students will take {joined} in {course} on {date_disp}."]
    for prep_line in _preparation_lines(fp.get("preparation") or {}):
        lines.append(prep_line)
    lines += ["Thank you,", "Owen Reagan"]
    return "\n".join(lines)


def _display_date(iso: str) -> str:
    if not iso:
        return ""
    d = date.fromisoformat(iso)
    return f"{d.strftime('%A')}, {d.strftime('%B')} {d.day}"


_FORBIDDEN_FACT_FIELDS = ("assessmentDate", "assessments")


def _facts_preserved(fp: dict[str, Any], candidate: str) -> bool:
    """Reject model output that omits/alters the deterministic facts.

    Assessment names/numbers must be preserved verbatim. Numeric preparation
    facts (WPM, error limit, Spelling lesson range, Power Up letter) must be
    present. The assessment date is allowed to be reformatted (ISO -> human),
    but its day-of-month must still appear (i.e. the date was not changed).
    """
    facts = fp.get("facts", {})
    prep = fp.get("preparation") or {}

    for name in facts.get("assessments") or []:
        if str(name) and str(name) not in candidate:
            return False

    if prep.get("fluencyWpm") is not None:
        if str(prep["fluencyWpm"]) not in candidate:
            return False
    if prep.get("fluencyMaxErrors") is not None:
        if str(prep["fluencyMaxErrors"]) not in candidate:
            return False
    if prep.get("powerUp"):
        if str(prep["powerUp"]) not in candidate:
            return False
    if prep.get("practiceRange"):
        m = re.search(r"(\d+)\s+through\s+(\d+)", str(prep["practiceRange"]))
        if m and (m.group(1) not in candidate or m.group(2) not in candidate):
            return False

    # Date may be human-formatted, but the day-of-month must not change.
    if facts.get("assessmentDate"):
        m = re.search(r"-(\d{2})$", str(facts["assessmentDate"]))
        if m and m.group(1) not in candidate:
            return False
    return True


def _writer_prompt(fp: dict[str, Any], notice_type: str) -> str:
    prep_lines = _preparation_lines(fp.get("preparation") or {})
    return json.dumps({
        "task": (
            "Rewrite this announcement in a warm, natural, professional-teacher voice. "
            "Do NOT change any dates, test numbers, Checkout numbers, WPM, error limits, "
            "Spelling lesson ranges, Power Up mappings, resources, courses, or scheduled times. "
            "You MUST include every line of requiredPreparationGuidance verbatim. "
            "A reminder may shorten the greeting and framing, but must keep all facts and preparation guidance."
        ),
        "announcementType": notice_type,
        "factPacket": fp,
        "requiredPreparationGuidance": prep_lines,
        "output": {"message": "string"},
    }, ensure_ascii=False)


def _preparation_lines(prep: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if prep.get("practiceRange"):
        lines.append(str(prep["practiceRange"]))
    if prep.get("fluencyWpm") is not None and prep.get("fluencyMaxErrors") is not None:
        lines.append(
            f"Students should practice reading approximately {prep['fluencyWpm']} words in under one minute "
            f"with no more than {prep['fluencyMaxErrors']} errors."
        )
    if prep.get("factSkill"):
        lines.append(f"Practice the Fact Test skill: {prep['factSkill']}")
    if prep.get("powerUp"):
        lines.append(f"Use the mapped Power Up {prep['powerUp']} resource.")
    if prep.get("prepare"):
        lines.append(str(prep["prepare"]))
    return lines


# --------------------------------------------------------------------------- #
# Chief weekly review preview
# --------------------------------------------------------------------------- #


def build_chief_review(events: list[dict[str, Any]], config: dict[str, Any]) -> str:
    """Human-readable 'Upcoming Assessments' review block."""
    lines: list[str] = []
    if not events:
        return "(no assessments this week)"
    lines.append("UPCOMING ASSESSMENTS")
    for event in events:
        course = event.get("course")
        wd = event.get("weekday")
        names = [a for a in (event.get("assessments") or []) if a]
        lines.append("")
        lines.append(f"{course} — {wd}")
        lines.append("  " + " + ".join(names))
        lines.append("  Assignments:")
        for a in (event.get("assignments") or []):
            if a:
                lines.append(f"    ✓ {a['title']}  [{a['group']}]")
        prep = event.get("preparation") or {}
        if prep.get("powerUp"):
            lines.append(f"  Resources: Power Up {prep['powerUp']} (Canvas file: UNRESOLVED)")
        elif prep.get("resourceStatus") == "UNRESOLVED":
            lines.append("  Resources: Power Up file UNRESOLVED (fail closed)")
        sched = schedule_notices(event["assessmentDate"], config)
        lines.append(f"  FIRST NOTICE: {_display_date(sched['firstNotice'])}")
        lines.append(f"  REMINDER: {_display_date(sched['reminder'])}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #


def command_self_test() -> int:
    config = load_config()

    # Math pairing.
    ma = math_assessment_numbers("WA6/ FA6*")
    assert ma == {"written": 6, "fact": 6}, ma
    assert math_assessment_numbers("L31") == {"written": None, "fact": None}

    # Fact Test -> Power Up map.
    ft = resolve_fact_test(6)
    assert ft["factTestNumber"] == 6
    assert ft["powerUp"] is not None
    assert ft["resourceStatus"] == "UNRESOLVED"

    # Reading Test -> Checkout; Test 14 exception.
    assert resolve_checkout(6)["checkoutNumber"] == 6
    assert resolve_checkout(14) is None
    assert resolve_checkout(1)["fluencyResolved"] is True and resolve_checkout(1)["fluency"]["wpm"] == 100
    assert resolve_checkout(8)["fluencyResolved"] is False

    # Scheduling: weekend-aware first notice + reminder.
    sched = schedule_notices("2026-10-20", config)  # Tuesday
    assert sched["firstNotice"] == "2026-10-15", sched  # 5 days back = Thu
    assert sched["reminder"] == "2026-10-16", sched  # 2 days back = Sun -> Fri (warn)
    assert any("exceeds 2 days" in w for w in sched["warnings"]), sched

    # Scheduling: no weekend collision on a Monday assessment.
    sched_mon = schedule_notices("2026-10-19", config)  # Monday
    assert sched_mon["firstNotice"] == "2026-10-14", sched_mon
    assert sched_mon["reminder"] == "2026-10-16", sched_mon  # Sun -> Fri, warn
    assert any("exceeds 2 days" in w for w in sched_mon["warnings"])

    # Duplicate identity deterministic.
    i1 = announcement_identity("Math", "math_assessment", "Test6+Fact6", "2026-10-20", "FIRST_NOTICE")
    i2 = announcement_identity("Math", "math_assessment", "Test6+Fact6", "2026-10-20", "FIRST_NOTICE")
    i3 = announcement_identity("Math", "math_assessment", "Test6+Fact6", "2026-10-20", "REMINDER")
    assert i1 == i2 and i1 != i3

    # State machine: PUBLISHED_VERIFIED blocked.
    item = {"state": "SOURCE_TRIGGER"}
    item = transition_announcement(item, "FACTS_RESOLVED", reason="facts resolved")
    item = transition_announcement(item, "DRAFTED", reason="drafted")
    item = transition_announcement(item, "TEACHER_APPROVED", reason="approved")
    assert item["state"] == "TEACHER_APPROVED"
    try:
        transition_announcement(item, "PUBLISHED_VERIFIED", reason="publish")
        raise AssertionError("expected AnnouncementStateError")
    except AnnouncementStateError:
        pass

    # Draft without LLM preserves facts; model skipped.
    fp = {"course": "Math", "assessmentDate": "2026-10-20", "assessments": ["Math Test 6", "Fact Test 6"],
          "facts": {"assessmentDate": "2026-10-20", "assessments": ["Math Test 6", "Fact Test 6"]}}
    draft = draft_announcement(fp, "FIRST_NOTICE", use_llm=False)
    assert draft["model_status"] == "SKIPPED"
    assert "Math Test 6" in draft["wording"] and "Fact Test 6" in draft["wording"]

    # Facts preservation guard rejects altered facts.
    assert _facts_preserved(fp, "Math Test 6 and Fact Test 6 on 2026-10-20") is True
    assert _facts_preserved(fp, "Math Test 7 and Fact Test 6 on 2026-10-20") is False

    # Whole-week resolution (synthetic Math+Reading+Spelling assessment week).
    week = {
        "week": {"code": "Q2W3", "startDate": "2026-10-26", "endDate": "2026-10-30"},
        "days": {
            "Tuesday": {"date": "2026-10-27", "subjects": {"math": {"raw": "WA6/ FA6"}, "reading": {"raw": "L38"}, "spelling": {"raw": "33"}}},
            "Wednesday": {"date": "2026-10-28", "subjects": {"math": {"raw": "L33"}, "reading": {"raw": "MT2"}, "spelling": {"raw": "34"}}},
            "Friday": {"date": "2026-10-30", "subjects": {"math": {"raw": "INV 3"}, "reading": {"raw": "L40"}, "spelling": {"raw": "Test 35"}}},
        },
    }
    events = resolve_assessment_facts(week)
    families = [e["family"] for e in events]
    assert "math_assessment" in families
    assert "reading_assessment" in families
    assert "spelling_assessment" in families
    math_event = next(e for e in events if e["family"] == "math_assessment")
    assert len([a for a in math_event["assignments"] if a]) == 2
    assert math_event["preparation"]["powerUp"] is not None
    reading_event = next(e for e in events if e["family"] == "reading_assessment")
    assert reading_event["facts"]["checkoutExists"] is True

    review = build_chief_review(events, config)
    assert "UPCOMING ASSESSMENTS" in review and "FIRST NOTICE" in review and "REMINDER" in review

    print("PASS assessment + announcement self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
