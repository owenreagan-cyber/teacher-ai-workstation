"""Deterministic Class 4-A birthday service (private roster; no AI, no network).

The legacy Apps Script engine stored birthdays in source, used fixed
millisecond offsets, filtered adjacent-weekend birthdays by the current month
only, and called Gemini for shoutouts. This module replaces that with:

* a private, gitignored owner-approved roster under ``.local/``;
* calendar-date arithmetic for week/month/year boundaries and DST;
* deterministic, warm shoutouts without any external AI service;
* HTML escaping at the rendering boundary.

No function here prints birthday values. Tests use synthetic rosters only.
"""
from __future__ import annotations

import hashlib
import html
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION_PATH = (
    REPO_ROOT / "config" / "curriculum" / "canvas"
    / "homeroom-birthday-authorization-2026-2027.json"
)

MONTH_NAMES = (
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


class BirthdayRosterError(RuntimeError):
    """Raised when the private roster is missing, unauthorized, or invalid."""


@dataclass(frozen=True)
class Birthday:
    name: str
    month: int
    day: int


@dataclass(frozen=True)
class BirthdayOnDate:
    birthday: Birthday
    date: date

    @property
    def is_weekend(self) -> bool:
        return self.date.weekday() >= 5

    @property
    def display_date(self) -> str:
        return f"{MONTH_NAMES[self.birthday.month]} {self.birthday.day}"


def load_authorization(path: Path | None = None) -> dict[str, Any]:
    p = Path(path) if path is not None else AUTHORIZATION_PATH
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("status") != "OWNER_APPROVED":
        raise BirthdayRosterError("birthday roster is not owner-approved")
    if data.get("classLabel") != "4-A":
        raise BirthdayRosterError("birthday authorization is not for Class 4-A")
    if not data.get("privateRosterPath"):
        raise BirthdayRosterError("birthday authorization is missing privateRosterPath")
    return data


def resolve_roster_path(authorization: dict[str, Any] | None = None) -> Path:
    auth = authorization or load_authorization()
    path = Path(auth["privateRosterPath"])
    return path if path.is_absolute() else REPO_ROOT / path


def parse_roster(data: dict[str, Any], *, authorization: dict[str, Any] | None = None) -> list[Birthday]:
    auth = authorization or {}
    if data.get("authorized") is not True:
        raise BirthdayRosterError("private roster is not authorized")
    if data.get("classLabel") != (auth.get("classLabel") or "4-A"):
        raise BirthdayRosterError("private roster class label mismatch")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise BirthdayRosterError("private roster has no entries")
    out: list[Birthday] = []
    seen: set[tuple[str, int, int]] = set()
    for item in entries:
        if not isinstance(item, dict):
            raise BirthdayRosterError("invalid birthday entry")
        name = str(item.get("name") or "").strip()
        try:
            month = int(item.get("month"))
            day = int(item.get("day"))
        except (TypeError, ValueError):
            raise BirthdayRosterError("invalid birthday month/day") from None
        if not name or not 1 <= month <= 12 or not 1 <= day <= 31:
            raise BirthdayRosterError("invalid birthday entry values")
        # Validate the day against a leap year so February 29 is representable.
        try:
            date(2024, month, day)
        except ValueError:
            raise BirthdayRosterError("invalid calendar day") from None
        key = (name.lower(), month, day)
        if key in seen:
            raise BirthdayRosterError("duplicate birthday entry")
        seen.add(key)
        out.append(Birthday(name=name, month=month, day=day))
    return out


def load_roster(
    path: Path | None = None, authorization: dict[str, Any] | None = None,
) -> list[Birthday]:
    auth = authorization or load_authorization()
    roster_path = Path(path) if path is not None else resolve_roster_path(auth)
    try:
        data = json.loads(roster_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BirthdayRosterError("private birthday roster unavailable") from exc
    return parse_roster(data, authorization=auth)


def roster_version(roster: list[Birthday]) -> str:
    """Stable non-reversible version hash of private roster values."""
    normalized = sorted((b.month, b.day, b.name.lower()) for b in roster)
    payload = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def birthdays_in_month(month: int, *, roster: list[Birthday]) -> list[Birthday]:
    if not 1 <= int(month) <= 12:
        raise ValueError("month must be 1-12")
    return sorted(
        (b for b in roster if b.month == int(month)),
        key=lambda b: (b.day, b.name.lower()),
    )


def birthdays_in_week(
    week_start: date, week_end: date, *, roster: list[Birthday],
) -> list[BirthdayOnDate]:
    """Birthdays in the instructional week plus adjacent weekends.

    Calendar-date arithmetic is used; no fixed millisecond offsets. A birthday
    in the previous/next month is included when it falls inside the adjacent
    weekend window. Recurring dates are evaluated across year transitions.
    """
    if week_end < week_start:
        raise ValueError("week_end must not precede week_start")
    window_start = week_start - timedelta(days=2)  # previous Saturday
    window_end = week_end + timedelta(days=2)      # following Sunday
    years = range(window_start.year - 1, window_end.year + 2)
    found: list[BirthdayOnDate] = []
    seen: set[tuple[str, date]] = set()
    for birthday in roster:
        for year in years:
            try:
                occurrence = date(year, birthday.month, birthday.day)
            except ValueError:
                continue  # Feb 29 in a non-leap year
            if window_start <= occurrence <= window_end:
                key = (birthday.name.lower(), occurrence)
                if key in seen:
                    continue
                seen.add(key)
                found.append(BirthdayOnDate(birthday=birthday, date=occurrence))
    return sorted(found, key=lambda item: (item.date, item.birthday.name.lower()))


def months_in_week(week_start: date, week_end: date) -> list[int]:
    """Unique calendar months covered by the instructional week."""
    months: list[int] = []
    cursor = week_start
    while cursor <= week_end:
        if cursor.month not in months:
            months.append(cursor.month)
        cursor += timedelta(days=1)
    return months


def monthly_birthdays(
    week_start: date, week_end: date, *, roster: list[Birthday],
) -> list[tuple[int, list[Birthday]]]:
    """Month-ordered birthday lists for each month covered by the week."""
    return [(month, birthdays_in_month(month, roster=roster)) for month in months_in_week(week_start, week_end)]


def weekly_shoutout(
    week_start: date, week_end: date, *, roster: list[Birthday],
) -> str:
    """Deterministic, warm, parent-facing birthday shoutout (plain text)."""
    items = birthdays_in_week(week_start, week_end, roster=roster)
    if not items:
        return ""
    if len(items) == 1:
        item = items[0]
        when = item.display_date
        if item.is_weekend:
            return f"Happy birthday to {item.birthday.name} on {when}! 🎉"
        return f"Happy birthday to {item.birthday.name} on {when}! 🎉"
    pieces = [f"{item.birthday.name} on {item.display_date}" for item in items]
    if len(pieces) == 2:
        joined = f"{pieces[0]} and {pieces[1]}"
    else:
        joined = ", ".join(pieces[:-1]) + ", and " + pieces[-1]
    return f"Happy birthday to {joined}! 🎉"


def escape_name(value: str) -> str:
    return html.escape(str(value), quote=True)


def month_label(month: int) -> str:
    return MONTH_NAMES[int(month)]


def command_self_test() -> int:
    # Synthetic roster only. Never place real roster values in tests.
    roster = [
        Birthday("Student One", 1, 1),
        Birthday("Student Two", 2, 2),
        Birthday("Student Three", 3, 3),
        Birthday("Student Four", 4, 4),
        Birthday("Student Five", 5, 5),
        Birthday("Student Six", 6, 6),
        Birthday("Student Seven", 7, 7),
        Birthday("Student Eight", 8, 8),
        Birthday("Student Nine", 9, 9),
        Birthday("Student Ten", 10, 10),
        Birthday("Student Eleven", 11, 11),
        Birthday("Student Twelve", 12, 12),
    ]
    for month in range(1, 13):
        assert len(birthdays_in_month(month, roster=roster)) == 1
    assert birthdays_in_month(6, roster=[] ) == []

    # Monday and Friday birthdays.
    mon = birthdays_in_week(date(2026, 11, 2), date(2026, 11, 6), roster=[Birthday("Monday Kid", 11, 2)])
    assert len(mon) == 1 and mon[0].date == date(2026, 11, 2)
    fri = birthdays_in_week(date(2026, 11, 2), date(2026, 11, 6), roster=[Birthday("Friday Kid", 11, 6)])
    assert len(fri) == 1 and fri[0].date == date(2026, 11, 6)

    # Adjacent weekend birthdays (previous Sunday and following Saturday).
    prev_sun = birthdays_in_week(date(2026, 11, 2), date(2026, 11, 6), roster=[Birthday("Prev Weekend", 11, 1)])
    next_sat = birthdays_in_week(date(2026, 11, 2), date(2026, 11, 6), roster=[Birthday("Next Weekend", 11, 7)])
    assert prev_sun and prev_sun[0].date == date(2026, 11, 1)
    assert next_sat and next_sat[0].date == date(2026, 11, 7)

    # Month boundary: an adjacent-weekend birthday in the next month must be found.
    boundary = birthdays_in_week(date(2026, 10, 26), date(2026, 10, 30), roster=[Birthday("Next Month", 11, 1)])
    assert boundary and boundary[0].date == date(2026, 11, 1), boundary

    # December/January transition.
    dec_jan = birthdays_in_week(date(2026, 12, 28), date(2027, 1, 1), roster=[Birthday("New Year", 1, 2)])
    assert dec_jan and dec_jan[0].date == date(2027, 1, 2), dec_jan
    assert months_in_week(date(2026, 12, 28), date(2027, 1, 1)) == [12, 1]

    # DST transition weeks remain calendar-correct.
    spring = birthdays_in_week(date(2026, 3, 2), date(2026, 3, 6), roster=[Birthday("Spring", 3, 8)])
    fall = birthdays_in_week(date(2026, 10, 26), date(2026, 10, 30), roster=[Birthday("Fall", 11, 1)])
    assert spring and spring[0].date == date(2026, 3, 8)
    assert fall and fall[0].date == date(2026, 11, 1)

    # Empty month and empty week.
    assert birthdays_in_month(6, roster=[]) == []
    assert birthdays_in_week(date(2026, 11, 2), date(2026, 11, 6), roster=[]) == []
    assert weekly_shoutout(date(2026, 11, 2), date(2026, 11, 6), roster=[]) == ""

    # Deterministic shoutout and HTML escaping.
    shout = weekly_shoutout(date(2026, 11, 2), date(2026, 11, 6), roster=[Birthday("A & B <Kid>", 11, 3)])
    assert "A & B <Kid>" in shout
    assert escape_name('A & B <Kid>') == "A &amp; B &lt;Kid&gt;"
    assert weekly_shoutout(date(2026, 11, 2), date(2026, 11, 6), roster=[Birthday("Same", 11, 3)]) == \
        weekly_shoutout(date(2026, 11, 2), date(2026, 11, 6), roster=[Birthday("Same", 11, 3)])

    # Duplicate roster entries fail closed.
    try:
        parse_roster({"authorized": True, "classLabel": "4-A", "entries": [
            {"name": "Dup", "month": 11, "day": 3},
            {"name": "Dup", "month": 11, "day": 3},
        ]}, authorization={"classLabel": "4-A"})
        raise AssertionError("expected BirthdayRosterError")
    except BirthdayRosterError:
        pass

    # Roster version is stable and non-empty.
    assert len(roster_version(roster)) == 64

    print("PASS Class 4-A birthday engine self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
