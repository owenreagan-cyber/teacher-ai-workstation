#!/usr/bin/env python3
"""Grade-check configuration loading and quarter resolution.

The quarter -> course applicability, assessment classification, threshold, and
email settings all live in ``config/canvas-llm/grade-check-config.json`` so the
scanner never hard-codes which subjects are active in which quarter.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "canvas-llm" / "grade-check-config.json"
INSTRUCTIONAL_WEEKS_PATH = (
    REPO_ROOT / "config" / "curriculum" / "canvas" / "instructional-weeks-2026-2027.json"
)

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}


class ConfigError(RuntimeError):
    """Raised when the grade-check configuration is missing or malformed."""


@dataclass(frozen=True)
class SubjectConfig:
    key: str
    display_name: str
    course_id: int
    assessment_groups: tuple[str, ...] = ()
    non_assessment_groups: tuple[str, ...] = ()
    manual_only: bool = False


@dataclass
class ScheduleConfig:
    """Scheduled-run settings (launchd LaunchAgent). No secrets live here."""
    weekdays_only: bool
    hour_local: int
    minute_local: int
    timezone: str


@dataclass
class GradeCheckConfig:
    recipient_email: str
    recipient_name: str
    report_subject: str
    send_requires_approval: bool
    suppress_empty_report: bool
    suppress_unchanged_report: bool
    threshold: float
    quarter_subjects: dict[int, tuple[str, ...]]
    subjects: dict[str, SubjectConfig]
    test_title_keywords: tuple[str, ...]
    missing_grade_markers: tuple[str, ...]
    state_directory: str
    state_file: str
    enrollment_overrides_file: str
    schedule: ScheduleConfig
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


def load_config(path: Path | None = None) -> GradeCheckConfig:
    cfg_path = path or CONFIG_PATH
    if not cfg_path.exists():
        raise ConfigError(f"grade-check config not found: {cfg_path}")
    raw = json.loads(cfg_path.read_text(encoding="utf-8"))

    subjects_raw = raw.get("subjects", {})
    subjects: dict[str, SubjectConfig] = {}
    for key, s in subjects_raw.items():
        subjects[key] = SubjectConfig(
            key=key,
            display_name=s.get("displayName", key),
            course_id=int(s["courseId"]),
            assessment_groups=tuple(s.get("assessmentGroups", [])),
            non_assessment_groups=tuple(s.get("nonAssessmentGroups", [])),
            manual_only=bool(s.get("manualOnly", False)),
        )

    quarter_subjects: dict[int, tuple[str, ...]] = {}
    for q, subj_keys in raw.get("quarters", {}).items():
        quarter = int(q)
        quarter_subjects[quarter] = tuple(subj_keys)
        for sk in subj_keys:
            if sk not in subjects:
                raise ConfigError(f"quarter {quarter} references unknown subject {sk!r}")

    recipient = raw.get("recipient", {})
    state = raw.get("state", {})
    sched_raw = raw.get("scheduling", {})
    return GradeCheckConfig(
        recipient_email=recipient.get("email", "owen.reagan@thalesacademy.org"),
        recipient_name=recipient.get("displayName", "Owen Reagan — Teacher"),
        report_subject=recipient.get("reportSubject", "4A Grade Check - Student Flags"),
        send_requires_approval=bool(recipient.get("sendRequiresApproval", True)),
        suppress_empty_report=bool(recipient.get("suppressEmptyReport", True)),
        suppress_unchanged_report=bool(recipient.get("suppressUnchangedReport", True)),
        threshold=float(raw.get("threshold", {}).get("atOrBelow", 85)),
        quarter_subjects=quarter_subjects,
        subjects=subjects,
        test_title_keywords=tuple(
            raw.get("classification", {}).get("testTitleKeywords", [])
        ),
        missing_grade_markers=tuple(
            raw.get("missing", {}).get("gradeMarkers", ["MI", "MISSING"])
        ),
        state_directory=state.get("directory", ".local/canvas-llm/grade-check"),
        state_file=state.get("stateFile", "state.json"),
        enrollment_overrides_file=state.get("enrollmentOverridesFile", "enrollment-overrides.json"),
        schedule=ScheduleConfig(
            weekdays_only=bool(sched_raw.get("weekdaysOnly", True)),
            hour_local=int(sched_raw.get("hourLocal", 16)),
            minute_local=int(sched_raw.get("minuteLocal", 15)),
            timezone=str(sched_raw.get("timezone", "America/New_York")),
        ),
        raw=raw,
    )


def active_subjects(cfg: GradeCheckConfig, quarter: int) -> list[SubjectConfig]:
    """Subjects scanned in the given quarter, resolved through configuration."""
    keys = cfg.quarter_subjects.get(quarter, ())
    return [cfg.subjects[k] for k in keys if k in cfg.subjects]


def active_course_ids(cfg: GradeCheckConfig, quarter: int) -> set[int]:
    """Course IDs currently in scope for grade-check scanning this quarter."""
    return {s.course_id for s in active_subjects(cfg, quarter)}


def all_subject_course_ids(cfg: GradeCheckConfig) -> set[int]:
    """Every grade-check subject course ID (used to distinguish out-of-scope)."""
    return {s.course_id for s in cfg.subjects.values()}


# ---------------------------------------------------------------------------
# Quarter resolution (uses the authoritative instructional-weeks export)
# ---------------------------------------------------------------------------

_WEEK_TITLE_RE = re.compile(
    r"\-\s*(?P<sm>[A-Za-z]+)\s+(?P<sd>\d{1,2})\s*[-–]\s*"
    r"(?:(?P<em>[A-Za-z]+)\s+)?(?P<ed>\d{1,2}),\s*(?P<yr>\d{4})"
)


def _parse_week_dates(page_title: str) -> tuple[dt.date, dt.date] | None:
    match = _WEEK_TITLE_RE.search(page_title)
    if not match:
        return None
    year = int(match.group("yr"))
    start_month = _MONTHS.get(match.group("sm").lower())
    if start_month is None:
        return None
    end_month = start_month
    if match.group("em"):
        end_month = _MONTHS.get(match.group("em").lower()) or start_month
    start = dt.date(year, start_month, int(match.group("sd")))
    end = dt.date(year, end_month, int(match.group("ed")))
    return start, end


def quarter_date_ranges(
    path: Path | None = None,
) -> dict[int, tuple[dt.date, dt.date]]:
    """Derive each quarter's first-week start and last-week end dates."""
    weeks_path = path or INSTRUCTIONAL_WEEKS_PATH
    if not weeks_path.exists():
        return {}
    raw = json.loads(weeks_path.read_text(encoding="utf-8"))
    per_quarter: dict[int, list[tuple[dt.date, dt.date]]] = {}
    for week in raw.get("weeks", []):
        quarter = int(week.get("quarter"))
        dates = _parse_week_dates(week.get("pageTitle", ""))
        if dates is not None:
            per_quarter.setdefault(quarter, []).append(dates)

    ranges: dict[int, tuple[dt.date, dt.date]] = {}
    for quarter, spans in per_quarter.items():
        starts = [s for s, _e in spans]
        ends = [e for _s, e in spans]
        ranges[quarter] = (min(starts), max(ends))
    return ranges


def resolve_quarter(
    today: dt.date | None = None,
    *,
    explicit_quarter: int | None = None,
    weeks_path: Path | None = None,
) -> int:
    """Resolve the quarter to scan.

    An explicit ``--quarter`` wins. Otherwise today's date is matched against
    the instructional-weeks quarter boundaries; gaps (breaks) resolve to the
    next upcoming quarter, before/after the year resolve to Q1/Q4.
    """
    if explicit_quarter is not None:
        if explicit_quarter not in (1, 2, 3, 4):
            raise ConfigError(f"invalid quarter {explicit_quarter!r}; expected 1-4")
        return explicit_quarter

    today = today or dt.date.today()
    ranges = quarter_date_ranges(path=weeks_path)
    if not ranges:
        raise ConfigError(
            "cannot auto-detect quarter: instructional-weeks export missing; pass --quarter"
        )

    ordered = sorted(ranges.items())
    first_start = ordered[0][1][0]
    last_end = ordered[-1][1][1]
    for quarter, (start, end) in ordered:
        if start <= today <= end:
            return quarter
    if today < first_start:
        return ordered[0][0]
    if today > last_end:
        return ordered[-1][0]
    for quarter, (start, _end) in ordered:
        if start > today:
            return quarter
    return ordered[-1][0]


def command_self_test() -> int:
    cfg = load_config()
    assert cfg.threshold == 85
    assert cfg.recipient_email == "owen.reagan@thalesacademy.org"
    assert cfg.quarter_subjects[1] == ("reading-spelling", "math", "language-arts", "history")
    assert cfg.quarter_subjects[2] == ("reading-spelling", "math", "language-arts", "science")
    assert cfg.quarter_subjects[3] == ("reading-spelling", "math", "language-arts", "history")
    assert cfg.quarter_subjects[4] == ("reading-spelling", "math", "language-arts", "science")
    assert cfg.subjects["math"].course_id == 26404
    assert cfg.subjects["reading-spelling"].course_id == 26442
    assert cfg.subjects["language-arts"].course_id == 28171
    assert cfg.subjects["history"].course_id == 28165
    assert cfg.subjects["science"].course_id == 28166
    assert "Written Assessments" in cfg.subjects["math"].assessment_groups
    assert "Homework" in cfg.subjects["reading-spelling"].non_assessment_groups

    # Q2 academic scope includes the three core subjects + Science (rotating).
    assert [s.key for s in active_subjects(cfg, 2)] == [
        "reading-spelling", "math", "language-arts", "science",
    ]
    assert active_course_ids(cfg, 2) == {26404, 26442, 28171, 28166}
    assert 28165 not in active_course_ids(cfg, 2)  # History rotated out in Q2
    assert 26429 not in all_subject_course_ids(cfg)  # Homeroom never grade-checked

    # Q1/Q3 use History (rotating), Q2/Q4 use Science (rotating).
    assert active_course_ids(cfg, 1) == {26404, 26442, 28171, 28165}
    assert active_course_ids(cfg, 3) == {26404, 26442, 28171, 28165}
    assert active_course_ids(cfg, 4) == {26404, 26442, 28171, 28166}

    # Quarter resolution against the authoritative instructional-weeks export.
    assert resolve_quarter(dt.date(2026, 9, 8)) == 1  # Q1W8
    assert resolve_quarter(dt.date(2026, 10, 20)) == 2  # Q2W2
    assert resolve_quarter(dt.date(2027, 1, 15)) == 3  # Q3W1
    assert resolve_quarter(dt.date(2027, 5, 1)) == 4  # Q4W4
    assert resolve_quarter(dt.date(2026, 9, 8), explicit_quarter=4) == 4
    assert resolve_quarter(dt.date(2026, 9, 29)) == 2  # fall break -> next quarter

    active = active_subjects(cfg, 1)
    assert [s.key for s in active] == ["reading-spelling", "math", "language-arts", "history"]
    assert [s.key for s in active_subjects(cfg, 2)] == ["reading-spelling", "math", "language-arts", "science"]
    print("PASS grade-check config self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
