"""Part A — deterministic pacing extractor.

Fresh-reads the live 2026-2027 FPK Pacing Guides (sheet ``4A - Reagan``) and
produces a normalized, token-free JSON week. This module translates nothing:
it preserves raw cell values verbatim, preserves blanks as blanks, and never
interprets curriculum meaning.

Read-only: the only network access is the authorized Google Sheets CSV export
(GET via the ``gviz`` endpoint). No Canvas calls, no writes.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.instructional_weeks import parse_week_range

from . import constants as C

REPO_ROOT = C.REPO_ROOT


def _pacing_url() -> str:
    return (
        "https://docs.google.com/spreadsheets/d/"
        f"{C.SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(C.SHEET_NAME)}"
    )


def fetch_pacing(fresh: bool = True, raw_csv_path: Path | None = None) -> tuple[list[list[str]], dict[str, Any]]:
    """Return (rows, source_meta). Fresh-reads the live sheet or falls back to the
    latest local snapshot when ``fresh`` is False or the network is unavailable."""
    raw_csv_path = raw_csv_path or (C.PACING_DIR / "raw" / "pacing-4A-reagan-fresh.csv")
    raw_csv_path.parent.mkdir(parents=True, exist_ok=True)
    meta: dict[str, Any] = {
        "workbook": "2026-2027 FPK Pacing Guides",
        "sheet": C.SHEET_NAME,
        "readTimestampUtc": datetime.now(timezone.utc).isoformat(),
    }
    if fresh:
        try:
            req = urllib.request.Request(_pacing_url(), headers={"Accept": "text/csv"})
            with urllib.request.urlopen(req, timeout=60) as response:
                text = response.read().decode("utf-8")
            raw_csv_path.write_text(text, encoding="utf-8")
            meta["freshRead"] = True
            meta["status"] = "FRESH_READ_OK"
            return list(csv.reader(text.splitlines())), meta
        except Exception as exc:  # noqa: BLE001 - fall back but do not fail hard
            meta["freshRead"] = False
            meta["status"] = "FRESH_READ_FAILED"
            meta["fallbackReason"] = type(exc).__name__
    else:
        meta["freshRead"] = False
    if raw_csv_path.exists():
        meta["status"] = meta.get("status", "STALE_CACHE")
        text = raw_csv_path.read_text(encoding="utf-8")
        return list(csv.reader(text.splitlines())), meta
    meta["status"] = "FAIL_NO_SOURCE"
    return [], meta


# --------------------------------------------------------------------------- #
# Week bound resolution from the instructional calendar
# --------------------------------------------------------------------------- #


def week_bounds_from_title(title: str) -> tuple[datetime, datetime] | None:
    """Parse a page title like 'Q2W1 - October 12–16, 2026' into (start, end).

    Uses the shared parser (scripts/instructional_weeks.py), which handles
    same-month, cross-month ('November 30–December 4, 2026') and cross-year
    ranges."""
    bounds = parse_week_range(title)
    if bounds is None:
        return None
    start, end = bounds
    return datetime(start.year, start.month, start.day), datetime(end.year, end.month, end.day)


def week_bounds(week_code: str) -> tuple[datetime, datetime] | None:
    weeks = json.loads(C.WEEKS_PATH.read_text(encoding="utf-8")).get("weeks", [])
    for w in weeks:
        if w.get("code") == week_code:
            return week_bounds_from_title(w.get("pageTitle", ""))
    return None


def instructional_status(week_code: str) -> str:
    """Return ACTIVE if the week is a real instructional week, else NON_INSTRUCTIONAL."""
    return "ACTIVE" if week_bounds(week_code) else "NON_INSTRUCTIONAL"


# --------------------------------------------------------------------------- #
# CSV column discovery
# --------------------------------------------------------------------------- #

_DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{2})$")


def _parse_mdy(value: str) -> datetime | None:
    m = _DATE_RE.match(value.strip())
    if not m:
        return None
    mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return datetime(2000 + yy, mm, dd)


def _header_rows(rows: list[list[str]]) -> list[int]:
    return [i for i, row in enumerate(rows) if row and row[0].strip() == "Subject:"]


def _find_week_header(rows: list[list[str]], monday: datetime) -> tuple[int, list[int]] | None:
    """Locate the month header row that contains ``monday`` and return
    (header_idx, [Mon..Fri column indices]).

    Generic fix: instead of assuming the five weekday columns are the five
    contiguous cells immediately after the Monday cell (absolute column
    indexing), verify that those cells actually parse as the consecutive
    Monday..Friday dates. A non-contiguous block (spacer/merged cells) is
    rejected rather than silently misaligned, which would otherwise collapse
    a subject to its Monday cell only.
    """
    for hi in _header_rows(rows):
        header = rows[hi]
        for ci, cell in enumerate(header):
            d = _parse_mdy(cell)
            if d is not None and d.date() == monday.date():
                cols = [ci]
                valid = True
                for i in range(1, 5):
                    nxt = ci + i
                    if nxt >= len(header):
                        valid = False
                        break
                    nd = _parse_mdy(header[nxt])
                    if nd is None or nd.date() != (monday + timedelta(days=i)).date():
                        valid = False
                        break
                    cols.append(nxt)
                if valid:
                    return hi, cols
    return None


# --------------------------------------------------------------------------- #
# Normalized week extraction
# --------------------------------------------------------------------------- #

_UNIT_CONTEXT_SCIENCE_RE = re.compile(r"^Science\s*[:–-]\s*(.+)$", re.IGNORECASE)
_UNIT_CONTEXT_HISTORY_RE = re.compile(r"^History\s+[A-Za-z0-9.]+\s*[-–]\s*(.+)$", re.IGNORECASE)


def _extract_unit_context(
    rows: list[list[str]], header_idx: int, next_header: int
) -> dict[str, str | None]:
    """Extract unit-name context rows (e.g. ``"Science: Force and Motion"``)
    that live inside a month block but outside the weekday subject rows.

    Returns ``{"science": unit|None, "history": unit|None}``. The first
    matching context cell per subject wins; non-matching cells are ignored.
    """
    science: str | None = None
    history: str | None = None
    for row in rows[header_idx + 1 : next_header]:
        for cell in row:
            c = (cell or "").strip()
            if not c:
                continue
            if science is None:
                m = _UNIT_CONTEXT_SCIENCE_RE.match(c)
                if m:
                    science = m.group(1).strip()
                    continue
            if history is None:
                m = _UNIT_CONTEXT_HISTORY_RE.match(c)
                if m:
                    history = m.group(1).strip()
                    continue
    return {"science": science, "history": history}


def extract_week(rows: list[list[str]], week_code: str, source: dict[str, Any]) -> dict[str, Any]:
    """Deterministic extraction of one week from the raw CSV rows."""
    bounds = week_bounds(week_code)
    if bounds is None:
        return {
            "schemaVersion": 1,
            "week": {"code": week_code, "instructionalStatus": "NON_INSTRUCTIONAL"},
            "source": source,
            "error": f"no instructional-week entry for {week_code}",
        }
    monday, friday = bounds

    located = _find_week_header(rows, monday)
    if located is None:
        return {
            "schemaVersion": 1,
            "week": {"code": week_code, "instructionalStatus": "NON_INSTRUCTIONAL"},
            "source": source,
            "error": f"date columns for {monday.strftime('%m/%d/%y')} not found",
        }
    header_idx, cols = located

    # Subject rows live after the header until the next month header.
    header_rows = _header_rows(rows)
    next_header = next((h for h in header_rows if h > header_idx), len(rows))

    subject_by_name: dict[str, dict[str, str]] = {}
    for row in rows[header_idx + 1 : next_header]:
        name = (row[0] if row else "").strip()
        key = C.SUBJECT_ROWS.get(name)
        if key is None:
            continue
        values: dict[str, str] = {}
        for wd, ci in zip(C.WEEKDAYS, cols):
            raw = (row[ci].strip() if ci < len(row) and row[ci] else "")
            values[wd] = raw
        subject_by_name[key] = values

    days: dict[str, Any] = {}
    for i, wd in enumerate(C.WEEKDAYS):
        date = monday + timedelta(days=i)
        subjects: dict[str, Any] = {}
        for key in C.SUBJECT_LABELS:
            raw = subject_by_name.get(key, {}).get(wd, "")
            subjects[key] = {"raw": raw, "blank": raw == ""}
        days[wd] = {"date": date.strftime("%Y-%m-%d"), "subjects": subjects}

    unit_context = _extract_unit_context(rows, header_idx, next_header)

    return {
        "schemaVersion": 1,
        "week": {
            "code": week_code,
            "startDate": monday.strftime("%Y-%m-%d"),
            "endDate": friday.strftime("%Y-%m-%d"),
            "instructionalStatus": instructional_status(week_code),
        },
        "source": source,
        "unitContext": unit_context,
        "days": days,
    }


def extract_week_json(week_code: str, fresh: bool = True) -> dict[str, Any]:
    """High-level entry: fetch + extract + return normalized week JSON."""
    rows, source = fetch_pacing(fresh=fresh)
    week = extract_week(rows, week_code, source)
    return week


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #


def command_self_test() -> int:
    # Authoritative Q2W1 structure: full Monday-Friday Shurley and Science,
    # blank History, a Science unit-context row, and a trailing week-2 fragment.
    rows = [
        ["Subject:", "", "", "10/12/26", "10/13/26", "10/14/26", "10/15/26", "10/16/26", "", "10/19/26", "10/20/26"],
        ["", "", "", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "", "Monday", "Tuesday"],
        ["Saxon Math", "5", "", "L31", "L32", "L33", "L34", "INV 3", "", "L35", "L36"],
        ["Reading Mastery", "4", "", "L37", "L38", "L39", "L40", "RMT+FCO", "", "41", "42"],
        ["Spelling", "4", "", "32", "33", "34", "Test", "review", "", "36", "37"],
        ["Shurley English", "4", "", "5.1", "5.1", "5.2", "5.2, CP19", "5.3", "", "", ""],
        ["History", "4", "", "", "", "", "", "", "", "", ""],
        ["Science", "4", "", "Ch. 1", "Ch. 1", "Ch. 2", "Ch. 2 Check", "Ch. 1-2 Review", "", "", ""],
        ["", "", "", "Science: Force and Motion", "", "", "", "", "", "", ""],
    ]
    source = {"workbook": "test", "sheet": "4A - Reagan", "freshRead": False, "status": "SYNTHETIC"}
    week = extract_week(rows, "Q2W1", source)

    assert week["week"]["startDate"] == "2026-10-12", week["week"]
    assert week["week"]["endDate"] == "2026-10-16", week["week"]
    assert week["week"]["instructionalStatus"] == "ACTIVE"

    days = week["days"]
    assert days["Monday"]["date"] == "2026-10-12"
    assert days["Friday"]["date"] == "2026-10-16"

    # Raw values preserved verbatim.
    assert days["Monday"]["subjects"]["math"]["raw"] == "L31"
    assert days["Friday"]["subjects"]["math"]["raw"] == "INV 3"
    assert days["Friday"]["subjects"]["reading"]["raw"] == "RMT+FCO"

    # Sparse rows + full Monday-Friday Language Arts and Science (regression).
    assert days["Monday"]["subjects"]["language_arts"]["raw"] == "5.1"
    assert days["Tuesday"]["subjects"]["language_arts"]["raw"] == "5.1"
    assert days["Wednesday"]["subjects"]["language_arts"]["raw"] == "5.2"
    assert days["Thursday"]["subjects"]["language_arts"]["raw"] == "5.2, CP19"
    assert days["Friday"]["subjects"]["language_arts"]["raw"] == "5.3"
    assert days["Monday"]["subjects"]["science"]["raw"] == "Ch. 1"
    assert days["Tuesday"]["subjects"]["science"]["raw"] == "Ch. 1"
    assert days["Wednesday"]["subjects"]["science"]["raw"] == "Ch. 2"
    assert days["Thursday"]["subjects"]["science"]["raw"] == "Ch. 2 Check"
    assert days["Friday"]["subjects"]["science"]["raw"] == "Ch. 1-2 Review"

    # Blank preservation.
    assert days["Monday"]["subjects"]["history"]["raw"] == ""
    assert days["Monday"]["subjects"]["history"]["blank"] is True
    assert days["Tuesday"]["subjects"]["history"]["raw"] == ""
    assert days["Tuesday"]["subjects"]["history"]["blank"] is True

    # Unit context is stored separately from weekday raw pacing.
    assert week["unitContext"]["science"] == "Force and Motion", week["unitContext"]
    assert week["unitContext"]["history"] is None

    # Subject row isolation: week 2 (10/19) must NOT leak into Q2W1 extraction.
    assert days["Monday"]["subjects"]["math"]["raw"] == "L31"  # not "L35"

    # Shortened / non-instructional week returns NON_INSTRUCTIONAL without dates.
    short = extract_week(rows, "Q9W9", source)
    assert short["week"]["instructionalStatus"] == "NON_INSTRUCTIONAL"

    # Week bounds from title.
    b = week_bounds_from_title("Q2W7 - November 30–December 4, 2026")
    assert b is not None and b[0].strftime("%Y-%m-%d") == "2026-11-30"
    assert b[1].strftime("%Y-%m-%d") == "2026-12-04"

    print("PASS pacing extractor self-test")
    return 0


if __name__ == "__main__":
    sys.exit(command_self_test())
