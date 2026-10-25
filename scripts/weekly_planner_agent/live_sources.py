"""Live read-only source adapters for the Weekly Planner Agent.

This module is the ONLY place the Weekly Planner Agent touches the real world:

* Google pacing — the authoritative public ``gviz`` CSV export (GET only),
  fresh-read through the existing ``scripts.canvas_llm_phase3.pacing_extractor``.
* Canvas — the credential-gated ``CanvasReadOnly`` client (GET only), wrapped by
  a hard read-only guard that FAILS (``NonGetVerbError``) if any non-GET verb is
  ever attempted through the live reconciliation path.

Nothing here writes to Canvas, sends email, or mutates the pacing sheet. Fetched
state is persisted only under ``.local/`` by the snapshot layer in the caller.
The Canvas token is never printed, logged, or returned.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from scripts.canvas_llm_intake import constants as intake_constants
from scripts.canvas_llm_phase3 import constants as pacing_constants
from scripts.canvas_llm_phase3 import pacing_extractor
from scripts.canvas_llm_phase3 import pacing_math
from scripts.canvas_llm_phase3 import pacing_reading
from scripts.canvas_llm_phase3 import pacing_translation

from . import snapshot as snap
from .canvas_observation import observe_canvas

WEEKDAYS = pacing_constants.WEEKDAYS

# Non-GET verbs are forbidden through the live reconciliation path.
WRITE_VERBS = ("post", "put", "patch", "delete")

# Subject key (intake/agent) -> pacing normalized subject key.
_SUBJECT_TO_PACING = {
    "math": "math",
    "reading_spelling": "reading",  # reading + spelling share one pacing group
    "language_arts": "language_arts",
    "science": "science",
    "history": "history",
}

_ASSESSMENT_TOKEN_KINDS = {"written_assessment", "fact_assessment", "rmt_fco", "test"}


class NonGetVerbError(RuntimeError):
    """Raised when a non-GET verb is attempted through the live reconciliation path.

    This is the enforcement proof: the observation workflow cannot issue
    POST/PUT/PATCH/DELETE. The caller treats this as a hard FAIL.
    """


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReadOnlyCanvasClient:
    """GET-only facade over the credential-gated ``CanvasReadOnly`` client.

    Exposes ONLY read methods. Any attribute that is not a whitelisted read
    method — and especially any write verb — raises ``NonGetVerbError``, so a
    live reconciliation path that reaches for a write operation fails closed
    instead of mutating Canvas. A mutation audit records every attempted verb.
    """

    def __init__(self, client: Any = None) -> None:
        from scripts.canvas_llm_intake.canvas_readonly import CanvasReadOnly
        self._client = client if client is not None else CanvasReadOnly.from_env()
        self.mutation_audit = {"GET": 0, "POST": 0, "PUT": 0, "PATCH": 0, "DELETE": 0}

    # ---- whitelisted GET-only reads ----
    def get_course(self, course_id: int) -> dict[str, Any]:
        self.mutation_audit["GET"] += 1
        return self._client.get_course(course_id)

    def find_page(self, course_id: int, slug: str) -> dict[str, Any] | None:
        self.mutation_audit["GET"] += 1
        return self._client.find_page(course_id, slug)

    def list_pages(self, course_id: int) -> list[dict[str, Any]]:
        self.mutation_audit["GET"] += 1
        pages = self._client.list_pages(course_id)
        # Live Canvas keys pages by ``url`` (slug), not a numeric id; expose the
        # slug as the stable page_id so observation identities are deterministic.
        return [{**p, "page_id": p.get("page_id") or p.get("url")} for p in pages]

    def list_assignments(self, course_id: int) -> list[dict[str, Any]]:
        self.mutation_audit["GET"] += 1
        return self._client.list_assignments(course_id)

    def list_assignment_groups(self, course_id: int) -> list[dict[str, Any]]:
        self.mutation_audit["GET"] += 1
        return self._client.list_assignment_groups(course_id)

    def list_announcements(self, course_id: int) -> list[dict[str, Any]]:
        self.mutation_audit["GET"] += 1
        return self._client.list_announcements(course_id)

    def list_active_announcements(self, context_codes: list[str] | None = None) -> list[dict[str, Any]]:
        self.mutation_audit["GET"] += 1
        return self._client.list_active_announcements(context_codes)

    def __getattr__(self, name: str) -> Any:
        # Normal attribute lookup failed: any other method is out of scope and
        # is treated as a forbidden write. Map method-name prefixes to their
        # HTTP verb so the mutation audit proves exactly what was attempted.
        low = name.lower()
        for verb in WRITE_VERBS:
            if verb in low:
                self.mutation_audit[verb.upper()] += 1
                raise NonGetVerbError(
                    f"non-GET verb forbidden in live reconciliation: {name!r}"
                )
        for prefix, verb in (
            ("create", "POST"), ("add", "POST"),
            ("update", "PUT"), ("set_", "PUT"),
            ("delete", "DELETE"), ("remove", "DELETE"),
        ):
            if low.startswith(prefix):
                self.mutation_audit[verb] += 1
                raise NonGetVerbError(
                    f"non-GET verb ({verb}) forbidden in live reconciliation: {name!r}"
                )
        raise NonGetVerbError(
            f"unknown/forbidden method in live reconciliation: {name!r}"
        )


# Agent subject key -> Canvas course-mappings subjectId (canonical, reused from
# scripts/canvas_llm_intake.intake._course_id).
_CANVAS_SUBJECT_ID = {
    "math": "math",
    "reading_spelling": "reading",  # reading/spelling share course 26442
    "language_arts": "language-arts",
    "science": "science",
    "history": "history",
}


def build_course_map(quarter: int) -> dict[str, int]:
    """Active academic subjects + homeroom -> production Canvas course id."""
    course_map: dict[str, int] = {}
    for subject in intake_constants.active_subject_keys_for_quarter(quarter):
        sid = _CANVAS_SUBJECT_ID.get(subject, subject)
        cid = intake_constants.course_id_for_subject(sid)
        if cid is not None:
            course_map[subject] = cid
    homeroom_id = intake_constants.course_id_for_subject("homeroom")
    if homeroom_id is not None:
        course_map["homeroom"] = homeroom_id
    return course_map


def read_live_canvas(quarter: int, *, client: Any = None) -> dict[str, Any]:
    """Observe real Canvas state (GET-only) for the quarter's active courses.

    Returns the normalized ``canvas`` snapshot section plus a mutation audit.
    A per-course read failure is recorded as ``read_error`` (never fabricated).
    """
    guard = client if client is not None else ReadOnlyCanvasClient()
    course_map = build_course_map(quarter)
    observation = observe_canvas(guard, course_map, observed_at=_now())
    observation["status"] = snap.SNAPSHOT_OK
    observation["read_only_enforced"] = True
    return observation


def _assessment_from_math(day_plan: dict[str, Any], date: str, day: str) -> dict[str, Any] | None:
    if day_plan.get("token_kind") in ("written_assessment", "fact_assessment"):
        return {"name": day_plan.get("translation") or day, "date": date, "day": day}
    return None


def _assessment_from_reading_spelling(
    reading: dict[str, Any], spelling: dict[str, Any], date: str, day: str
) -> dict[str, Any] | None:
    if reading.get("token_kind") == "rmt_fco":
        name = reading.get("translation") or f"Reading assessment on {day}"
        return {"name": name, "date": date, "day": day}
    if spelling.get("token_kind") == "test" and spelling.get("translation"):
        return {"name": spelling.get("translation"), "date": date, "day": day}
    return None


def _chapter_from_lines(lines: list[str]) -> str | None:
    for line in lines:
        low = line.lower()
        if "chapter" in low or low.startswith("ch"):
            return line
    return None


def _assessment_from_lines(lines: list[str], date: str, day: str) -> dict[str, Any] | None:
    joined = " ".join(lines)
    low = joined.lower()
    if "test" in low or "quiz" in low or "assessment" in low:
        return {"name": joined, "date": date, "day": day}
    return None


def normalize_pacing_cells(
    week: dict[str, Any], *, active_subjects: list[str]
) -> dict[str, Any]:
    """Normalize one extracted pacing week into reconciliation cells.

    Reuses the existing deterministic translators (math / reading+spelling /
    language arts / science / history) so no duplicate translation logic is
    introduced. Each cell carries the five fields change detection compares:
    lesson, chapter, classwork, homework, assessment.
    """
    days = week.get("days") or {}
    cells: dict[str, Any] = {}

    math_report = None
    rs_report = None
    trans_config = None
    if "math" in active_subjects:
        math_report = pacing_math.translate_math_week(week)
    if "reading_spelling" in active_subjects:
        rs_report = pacing_reading.translate_reading_spelling_week(week)
    if any(s in active_subjects for s in ("language_arts", "science", "history")):
        trans_config = pacing_translation.load_config()

    for wd in WEEKDAYS:
        day = days.get(wd, {})
        date = day.get("date", "")
        for subject in active_subjects:
            if subject == "math" and math_report is not None:
                mp = math_report.get("days", {}).get(wd, {}) or {}
                cells[f"math|{wd}"] = {
                    "lesson": mp.get("translation") or None,
                    "chapter": None,
                    "classwork": list(mp.get("in_class") or []),
                    "homework": [mp["at_home"]] if mp.get("at_home") else [],
                    "assessment": _assessment_from_math(mp, date, wd),
                }
            elif subject == "reading_spelling" and rs_report is not None:
                rd = rs_report.get("reading", {}).get("days", {}).get(wd, {}) or {}
                sp = rs_report.get("spelling", {}).get("days", {}).get(wd, {}) or {}
                lesson_parts = [
                    f"Reading {rd['translation']}" if rd.get("translation") else "",
                    f"Spelling {sp['translation']}" if sp.get("translation") else "",
                ]
                lesson = " · ".join(p for p in lesson_parts if p) or None
                in_class = list(rd.get("in_class") or []) + list(sp.get("in_class") or [])
                cells[f"reading_spelling|{wd}"] = {
                    "lesson": lesson,
                    "chapter": None,
                    "classwork": in_class,
                    "homework": [rd["at_home"]] if rd.get("at_home") else [],
                    "assessment": _assessment_from_reading_spelling(rd, sp, date, wd),
                }
            else:
                subject_report = pacing_translation.translate_subject_week(
                    week, subject, trans_config
                )
                day_report = subject_report.get("days", {}).get(wd, {}) or {}
                lines = list(day_report.get("lines") or [])
                cells[f"{subject}|{wd}"] = {
                    "lesson": ", ".join(lines) or None,
                    "chapter": _chapter_from_lines(lines),
                    "classwork": lines,
                    "homework": [],
                    "assessment": _assessment_from_lines(lines, date, wd),
                }
    return cells


def read_live_pacing(quarter: int, week: int) -> dict[str, Any]:
    """Fresh-read the real Google pacing sheet and normalize it into cells.

    Returns ``{status, observed_at, identity, source_timestamp, cells}``.
    If the live source cannot be read, ``status`` is STALE/UNAVAILABLE and no
    stale cache is silently substituted as "live".
    """
    week_code = f"Q{quarter}W{week}"
    rows, meta = pacing_extractor.fetch_pacing(fresh=True)
    identity = {
        "name": meta.get("workbook") or "2026-2027 FPK Pacing Guides",
        "tab": meta.get("sheet") or pacing_constants.SHEET_NAME,
        "spreadsheet_id": meta.get("spreadsheet_id") or pacing_constants.SPREADSHEET_ID,
        "week_code": week_code,
    }
    source_timestamp = meta.get("readTimestampUtc") or _now()

    if meta.get("status") != "FRESH_READ_OK":
        # Never substitute stale cache and call it live.
        return {
            "status": snap.SNAPSHOT_UNAVAILABLE,
            "observed_at": _now(),
            "identity": identity,
            "source_timestamp": source_timestamp,
            "cells": {},
            "read_error": meta.get("status"),
        }

    week = pacing_extractor.extract_week(rows, week_code, meta)
    if week.get("error"):
        return {
            "status": snap.SNAPSHOT_UNAVAILABLE,
            "observed_at": _now(),
            "identity": identity,
            "source_timestamp": source_timestamp,
            "cells": {},
            "read_error": week.get("error"),
        }

    active = intake_constants.active_subject_keys_for_quarter(quarter)
    cells = normalize_pacing_cells(week, active_subjects=active)
    return {
        "status": snap.SNAPSHOT_OK,
        "observed_at": _now(),
        "identity": identity,
        "source_timestamp": source_timestamp,
        "cells": cells,
    }


def live_sync_sources(quarter: int, week: int) -> dict[str, Any]:
    """Read both live sources (GET-only) and return a normalized observation pair.

    Never writes Canvas, never modifies the pacing sheet, never prints the
    Canvas token. The pacing/canvas dicts are shaped for ``sync_and_detect``.
    """
    pacing = read_live_pacing(quarter, week)
    canvas = read_live_canvas(quarter)
    return {"pacing": pacing, "canvas": canvas}


def command_self_test() -> int:
    # 1. Structural proof: this module's source never contains a write verb.
    from pathlib import Path
    source = Path(__file__).read_text(encoding="utf-8")
    tokens = [f".{v}(" for v in WRITE_VERBS]
    tokens += [f'method="{v.upper()}"' for v in WRITE_VERBS]
    for tok in tokens:
        assert tok not in source, f"write token {tok!r} present in live_sources"

    # 2. Read-only guard: a fake client with a write method must fail closed.
    class _FakeCanvas:
        def list_pages(self, course_id):
            return [{"url": "q2w3", "title": "Q2W3", "body": "<p>x</p>",
                     "published": True, "front_page": True}]

        def list_assignments(self, course_id):
            return []

        def list_announcements(self, course_id):
            return []

        def list_assignment_groups(self, course_id):
            return []

        def get_course(self, course_id):
            return {"id": course_id, "name": "Math"}

        def create_assignment(self, *a, **k):
            raise AssertionError("must not be reached")

    guard = ReadOnlyCanvasClient(client=_FakeCanvas())
    obs = read_live_canvas(2, client=guard)
    assert obs["status"] == snap.SNAPSHOT_OK, obs
    assert obs["read_only_enforced"] is True
    assert obs["courses"]["math"]["front_page"]["page_id"] == "q2w3"
    # Non-GET verb attempt through the live path -> NonGetVerbError (FAIL).
    try:
        guard.create_assignment(26404)
        raise AssertionError("write verb must be blocked")
    except NonGetVerbError:
        pass
    assert guard.mutation_audit["POST"] >= 1

    # 3. Pacing normalization reuses deterministic translators.
    week = {
        "week": {"code": "Q2W3"},
        "days": {
            "Monday": {"date": "2026-10-26", "subjects": {"math": {"raw": "L31"}}},
            "Tuesday": {"date": "2026-10-27", "subjects": {"math": {"raw": "WA8"}}},
        },
        "unitContext": {},
    }
    cells = normalize_pacing_cells(week, active_subjects=["math"])
    assert cells["math|Monday"]["lesson"] == "Lesson 31", cells
    assert cells["math|Tuesday"]["assessment"]["name"] == "Written Assessment 8", cells
    assert cells["math|Tuesday"]["assessment"]["date"] == "2026-10-27"

    print("PASS weekly-planner-agent live-sources self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
