"""Baseline cross-source consistency engine.

Compares the CURRENT normalized pacing state directly against the CURRENT
normalized Canvas state — independent of any previous snapshot. This detects
disagreement that exists *right now*:

    "Google pacing currently says Thursday, but Canvas currently says Friday."

It is distinct from temporal change detection (previous ↔ current). Both systems
coexist; this module never invents a before→after change.

Read-only and non-destructive: no Canvas writes, no Google writes, no sends.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from . import change_detection as cd
from . import snapshot as snap
from .models import Authority, SourceChangeEvent, WeeklyPlan

ET = ZoneInfo("America/New_York")

# Subjects whose assessment assignments are auto-created (Canvas assignment
# policy "enabled"). Science/History are manual-only and are never flagged for
# a missing assessment assignment.
ASSIGNMENT_ENABLED = {"math", "reading_spelling", "language_arts"}

# Artifact types (object_type) this engine can emit.
ASSESSMENT_DATE = "assessment_date"
ASSESSMENT_IDENTITY = "assessment_identity"
ASSESSMENT_ASSIGNMENT_MISSING = "assessment_assignment_missing"
FRONT_PAGE = "front_page"
FIRST_ANNOUNCEMENT = "first_announcement"
DAY_BEFORE_REMINDER = "day_before_reminder"
REMINDER_DUPLICATE = "reminder_duplicate"
REMINDER_OBSOLETE = "reminder_obsolete"
PACING_VS_OVERRIDE = "pacing_vs_override"

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

# A "reminder" is the day-before nudge (title says "reminder"/"tomorrow").
# An assessment announcement like "Written Assessment 7 … Thursday" is the FIRST
# announcement, not a reminder — it must not be misclassified.
_REMINDER_HINTS = ("reminder", "tomorrow")
_UPDATE_HINTS = ("weekly update", "agenda updated")


def _now() -> str:
    return datetime.now().isoformat()


def canvas_due_local_day(due_at: str | None) -> str | None:
    """Convert a Canvas ``due_at`` to the local instructional day (America/New_York).

    Canvas stores ``due_at`` in UTC; ``03:59:00Z`` is 11:59 PM ET the prior
    evening, so ``2026-10-30T03:59:00Z`` is Thursday 2026-10-29 locally. A naive
    UTC date comparison would fabricate a one-day conflict; this normalization
    is the bounded, correct comparison and keeps harmless Canvas-owned
    formatting differences out of the conflict stream.
    """
    if not due_at:
        return None
    text = str(due_at).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).astimezone(ET).date().isoformat()
    except (ValueError, TypeError):
        # Fall back to the raw date portion (still better than a false conflict).
        return text[:10] if len(text) >= 10 else None


# --------------------------------------------------------------------------- #
# Assessment identity parsing (bounded, canonical prefixes only)
# --------------------------------------------------------------------------- #

_KIND_PATTERNS = (
    ("written_assessment", r"written\s+assessment"),
    ("fact_assessment", r"fact\s+assessment"),
    ("spelling_test", r"spelling\s+test"),
    ("mastery_test", r"mastery\s+test|reading\s+mastery\s+test"),
    ("checkout", r"fluency\s+checkout|\bcheck\s*out\b|\bcheckout\b"),
    ("classroom_practice", r"classroom\s+practice"),
    ("chapter_test", r"chapter\s*\d+\s+(?:shurley\s+)?test|shurley.*?\btest\b"),
    ("quiz", r"quiz"),
    ("test", r"\btest\b"),
)


def _kind_of(name: str) -> str | None:
    low = name.lower()
    for kind, pattern in _KIND_PATTERNS:
        if re.search(pattern, low):
            return kind
    return None


def _num_of(name: str) -> int | None:
    nums = re.findall(r"\d+", name)
    return int(nums[-1]) if nums else None


def assessment_identities(name: str | None) -> list[tuple[str, int | None]]:
    """Split a (possibly combined) assessment name into (kind, num) identities.

    ``"Written Assessment 7, Fact Assessment 7"`` -> [("written_assessment", 7),
    ("fact_assessment", 7)]. Deterministic; unknown tokens produce
    (None, None) so the caller can choose to skip rather than guess.
    """
    if not name:
        return []
    parts = [p.strip() for p in re.split(r"[,/]|\s\+\s|\sand\s", name.strip()) if p.strip()]
    out: list[tuple[str, int | None]] = []
    for part in parts:
        kind = _kind_of(part)
        out.append((kind, _num_of(part)))
    return out


def _assignment_identities(assignments: list[dict[str, Any]]) -> dict[tuple[str, int], list[dict[str, Any]]]:
    """Index Canvas assignments by (kind, num)."""
    index: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for a in assignments:
        kind = _kind_of(a.get("name") or a.get("title") or "")
        num = _num_of(a.get("name") or a.get("title") or "")
        if kind is None or num is None:
            continue
        index.setdefault((kind, num), []).append(a)
    return index


# --------------------------------------------------------------------------- #
# Authoritative value resolution (owner override > pacing > canvas)
# --------------------------------------------------------------------------- #

def authoritative_assessment(
    plan: WeeklyPlan | None, subject: str, day: str, cell: dict[str, Any]
) -> dict[str, Any]:
    """Resolve the authoritative assessment (name, date) for a subject/day.

    An explicit owner override wins; otherwise the verified pacing cell wins.
    Returns ``{name, date, authority, override}``.
    """
    ass = cell.get("assessment") or {}
    pacing_name = ass.get("name")
    pacing_date = ass.get("date")
    dp = plan.day(subject, day) if plan is not None else None
    if dp is not None and dp.authority == Authority.OWNER_INSTRUCTION and dp.teacher_override:
        ov = dp.teacher_override
        name = ", ".join(ov.get("assessments") or []) or (dp.assessment.name if dp.assessment else pacing_name)
        date = ov.get("assessment_date") or (dp.assessment.date if dp.assessment else None) or pacing_date
        return {"name": name, "date": date, "authority": "OWNER_INSTRUCTION", "override": ov}
    return {"name": pacing_name, "date": pacing_date, "authority": "VERIFIED_PACING", "override": None}


# --------------------------------------------------------------------------- #
# Event construction
# --------------------------------------------------------------------------- #

def cross_source_event_id(
    *,
    week_id: str,
    subject: str,
    object_type: str,
    object_identity: str,
    authoritative: str | None,
    observed: str | None,
    authority_winner: str,
) -> str:
    body = "|".join([
        str(week_id), "cross_source", str(subject), object_type,
        str(object_identity), str(authoritative), str(observed), str(authority_winner),
    ])
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:20]


def _conflict(
    *,
    week_id: str,
    subject: str,
    object_type: str,
    object_identity: str,
    authoritative: str | None,
    observed: str | None,
    authority_winner: str,
    affected: list[str],
    pacing_value: str | None,
    canvas_value: str | None,
    teacher_override: dict[str, Any] | None,
    source_timestamps: dict[str, Any],
    source_freshness: dict[str, Any],
    family_comms: bool = False,
) -> SourceChangeEvent:
    return SourceChangeEvent(
        source="cross_source",
        subject=subject,
        object_type=object_type,
        old_value=authoritative,
        new_value=observed,
        classification=cd.CROSS_SOURCE_CONFLICT,
        object_identity=object_identity,
        severity="high",
        affected_artifacts=affected,
        requires_teacher_approval=True,
        family_comms_affected=family_comms,
        authority_winner=authority_winner,
        teacher_override=teacher_override,
        pacing_value=pacing_value,
        canvas_value=canvas_value,
        source_timestamps=source_timestamps,
        source_freshness=source_freshness,
        event_id=cross_source_event_id(
            week_id=week_id, subject=subject, object_type=object_type,
            object_identity=object_identity, authoritative=authoritative,
            observed=observed, authority_winner=authority_winner,
        ),
    )


def _assessment_artifacts(subject: str) -> list[str]:
    s = subject.title()
    return [
        f"{s} weekly page",
        f"{s} assessment assignment",
        f"{s} first parent announcement",
        f"{s} day-before reminder",
    ]


# --------------------------------------------------------------------------- #
# Scan
# --------------------------------------------------------------------------- #

def front_page_transition_state(snapshot: dict[str, Any]) -> tuple[bool, set[str]]:
    """Return (release_due, subjects in a verified expected transition).

    Before the target instructional week begins, its already-staged page
    need not be the current front page. Only the immediately preceding
    instructional week's front page qualifies as an expected transition.
    A verified rollover makes the new front page due immediately.
    Unknown calendar or ledger state is never silently classified as safe.
    """
    from scripts.canvas_llm_intake import week_resolution as wr
    from scripts.canvas_llm_rollover import ledger as rollover_ledger

    pacing = snapshot.get("pacing") or {}
    canvas = snapshot.get("canvas") or {}
    if pacing.get("status") != snap.SNAPSHOT_OK or canvas.get("status") != snap.SNAPSHOT_OK:
        return True, set()

    week_id = str(snapshot.get("week_id") or "")
    match = re.fullmatch(r"Q([0-9]+)W([0-9]+)", week_id)
    if match is None:
        return True, set()

    quarter, week = map(int, match.groups())
    weeks = sorted(
        (w for w in wr.load_weeks() if wr._week_start(w) is not None),
        key=wr._week_start,
    )
    index = next(
        (i for i, w in enumerate(weeks) if w.get("code") == week_id),
        None,
    )
    if index is None or index == 0:
        return True, set()

    start = wr._week_start(weeks[index])
    if start is None:
        return True, set()

    record = rollover_ledger.load_rollover_ledger(quarter, week)
    if record and record.get("lifecycle") == "PUBLISHED_VERIFIED":
        return True, set()

    if wr._now_local().date() >= start:
        return True, set()

    previous_code = str(weeks[index - 1].get("code") or "")
    expected = set()

    for subject, course in (canvas.get("courses") or {}).items():
        if subject == "homeroom":
            continue
        title = str((course.get("front_page") or {}).get("title") or "")
        candidates = [
            page for page in (course.get("pages") or [])
            if str(page.get("title") or "").startswith(week_id)
        ]
        if (
            previous_code
            and re.match(rf"^{re.escape(previous_code)}(?![A-Za-z0-9])", title)
            and len(candidates) == 1
        ):
            expected.add(subject)

    return False, expected


def scan(snapshot: dict[str, Any], plan: WeeklyPlan | None = None) -> list[SourceChangeEvent]:
    """Compare current pacing to current Canvas; return cross-source conflicts.

    Returns an empty list when either source is unavailable/stale (an outage
    must never fabricate a conflict). Deterministic only: ambiguous matches are
    skipped rather than guessed.
    """
    pacing = snapshot.get("pacing") or {}
    canvas = snapshot.get("canvas") or {}
    if pacing.get("status") not in (snap.SNAPSHOT_OK,) or canvas.get("status") not in (snap.SNAPSHOT_OK,):
        return []
    if (canvas.get("read_error") is not None) or canvas.get("status") != snap.SNAPSHOT_OK:
        return []

    week_id = snapshot.get("week_id") or ""
    release_due, expected_transitions = front_page_transition_state(snapshot)
    cells = pacing.get("cells") or {}
    courses = canvas.get("courses") or {}
    source_timestamps = {
        "pacing": pacing.get("source_timestamp") or pacing.get("observed_at"),
        "canvas": canvas.get("observed_at"),
    }
    source_freshness = {"pacing": pacing.get("status"), "canvas": canvas.get("status")}

    events: list[SourceChangeEvent] = []
    week_dates: dict[str, set[str]] = {}

    for key, cell in cells.items():
        subject, _, day = key.partition("|")
        week_dates.setdefault(subject, set())
        if cell.get("assessment") and cell["assessment"].get("date"):
            week_dates[subject].add(str(cell["assessment"]["date"]))

        course = courses.get(subject)
        if course is None:
            continue

        events.extend(_scan_assessment(
            week_id=week_id, subject=subject, day=day, cell=cell, course=course,
            plan=plan, source_timestamps=source_timestamps,
            source_freshness=source_freshness,
            week_dates=week_dates.get(subject) or set(),
        ))

    for subject, course in courses.items():
        # Homeroom front page is a monthly newsletter carried forward by the
        # Friday rollover; it has no "current week" page identity, so it is never
        # flagged as a wrong front page.
        if subject != "homeroom" and subject not in expected_transitions:
            events.extend(_scan_front_page(
                week_id, subject, course, week_dates.get(subject) or set(),
                post_release=release_due,
            ))
        events.extend(_scan_announcements_reminders(
            week_id=week_id, subject=subject, course=course, cells=cells, plan=plan,
            source_timestamps=source_timestamps, source_freshness=source_freshness,
        ))

    return events


def _scan_assessment(
    *, week_id: str, subject: str, day: str, cell: dict[str, Any], course: dict[str, Any],
    plan: WeeklyPlan | None, source_timestamps: dict[str, Any], source_freshness: dict[str, Any],
    week_dates: set[str],
) -> list[SourceChangeEvent]:
    events: list[SourceChangeEvent] = []
    ass = cell.get("assessment")
    if not ass:
        return events

    auth = authoritative_assessment(plan, subject, day, cell)
    auth_date = auth["date"]
    auth_name = auth["name"]
    authority_winner = auth["authority"]

    # Pacing-vs-override: an explicit owner override outranks pacing; if pacing
    # disagrees with the override, surface it (override preserved, not rewritten).
    if auth["override"] is not None and auth_date and ass.get("date") and auth_date != ass.get("date"):
        events.append(_conflict(
            week_id=week_id, subject=subject, object_type=PACING_VS_OVERRIDE,
            object_identity=f"{subject}|{day}|assessment",
            authoritative=auth_date, observed=ass.get("date"),
            authority_winner="OWNER_INSTRUCTION",
            affected=_assessment_artifacts(subject),
            pacing_value=ass.get("date"), canvas_value=None,
            teacher_override=auth["override"],
            source_timestamps=source_timestamps, source_freshness=source_freshness,
            family_comms=True,
        ))

    if subject not in ASSIGNMENT_ENABLED:
        return events

    identities = assessment_identities(auth_name)
    if not identities or any(kind is None or num is None for kind, num in identities):
        return events  # not deterministically comparable -> skip (no noise)

    index = _assignment_identities(course.get("assignments") or [])
    for kind, num in identities:
        matches = index.get((kind, num))
        if not matches:
            events.append(_conflict(
                week_id=week_id, subject=subject, object_type=ASSESSMENT_ASSIGNMENT_MISSING,
                object_identity=f"{subject}|{kind}|{num}",
                authoritative=f"{auth_name} ({auth_date})", observed=None,
                authority_winner=authority_winner,
                affected=_assessment_artifacts(subject),
                pacing_value=f"{kind}:{num}", canvas_value=None,
                teacher_override=auth["override"],
                source_timestamps=source_timestamps, source_freshness=source_freshness,
                family_comms=True,
            ))
            continue
        for a in matches:
            due_day = canvas_due_local_day(a.get("due_at"))
            if auth_date and due_day and due_day != auth_date:
                events.append(_conflict(
                    week_id=week_id, subject=subject, object_type=ASSESSMENT_DATE,
                    object_identity=f"{subject}|{kind}|{num}",
                    authoritative=auth_date, observed=due_day,
                    authority_winner=authority_winner,
                    affected=_assessment_artifacts(subject),
                    pacing_value=auth_date, canvas_value=due_day,
                    teacher_override=auth["override"],
                    source_timestamps=source_timestamps, source_freshness=source_freshness,
                    family_comms=True,
                ))

    # Assessment identity: same kind, different number, due within the active week.
    for (kind, num), assignments in index.items():
        if kind is None or num is None:
            continue
        expected = {n for k, n in identities if k == kind}
        if num in expected:
            continue
        for a in assignments:
            due_day = canvas_due_local_day(a.get("due_at"))
            if due_day in week_dates:
                events.append(_conflict(
                    week_id=week_id, subject=subject, object_type=ASSESSMENT_IDENTITY,
                    object_identity=f"{subject}|{kind}",
                    authoritative=f"{kind}:{sorted(expected) or ['?']}", observed=f"{kind}:{num}",
                    authority_winner=authority_winner,
                    affected=_assessment_artifacts(subject),
                    pacing_value=f"{kind}:{sorted(expected) or ['?']}",
                    canvas_value=f"{kind}:{num}",
                    teacher_override=auth["override"],
                    source_timestamps=source_timestamps, source_freshness=source_freshness,
                    family_comms=True,
                ))
    return events


def _scan_front_page(
    week_id: str, subject: str, course: dict[str, Any], week_dates: set[str],
    *, post_release: bool = False,
) -> list[SourceChangeEvent]:
    events: list[SourceChangeEvent] = []
    pages = course.get("pages") or []
    front = course.get("front_page") or {}
    week_pages = [p for p in pages if week_id and str(p.get("title") or "").startswith(week_id)]
    if not week_pages:
        return events  # current-week page may not exist yet -> UNKNOWN, not conflict

    # A current-week page exists; the active front page must be one of them.
    front_id = front.get("page_id") or front.get("title")
    current_is_front = any((p.get("page_id") or p.get("title")) == front_id for p in week_pages)
    if not current_is_front:
        observed = str(front.get("title") or front.get("page_id") or "")
        events.append(_conflict(
            week_id=week_id, subject=subject, object_type=FRONT_PAGE,
            # Post-release drift uses a distinct identity so an earlier
            # automatically superseded transition cannot hide a real failure.
            object_identity=(
                f"{subject}:front_page:post_release"
                if post_release else f"{subject}:front_page"
            ),
            authoritative=week_id, observed=observed,
            authority_winner="VERIFIED_PACING",
            affected=[f"{subject.title()} weekly page"],
            pacing_value=week_id, canvas_value=observed,
            teacher_override=None,
            source_timestamps={}, source_freshness={},
        ))
    return events


def _reminder_hint(title: str) -> bool:
    low = (title or "").lower()
    return any(h in low for h in _REMINDER_HINTS)


def _is_update(title: str) -> bool:
    low = (title or "").lower()
    return any(h in low for h in _UPDATE_HINTS)


def _scan_announcements_reminders(
    *, week_id: str, subject: str, course: dict[str, Any], cells: dict[str, Any],
    plan: WeeklyPlan | None, source_timestamps: dict[str, Any], source_freshness: dict[str, Any],
) -> list[SourceChangeEvent]:
    """First-announcement / day-before-reminder checks, scoped to avoid noise.

    Only runs for subjects with auto-assignment policy (science/history are
    manual-only) and only considers announcements/reminders relevant to the
    current week's assessments (scheduled/posted within a bounded window before
    each assessment). Historical reminders are ignored, not flagged.
    """
    events: list[SourceChangeEvent] = []
    if subject not in ASSIGNMENT_ENABLED:
        return events
    announcements = course.get("announcements") or []

    from datetime import timedelta

    # Authoritative assessment dates for this subject.
    assessment_dates: list[str] = []
    for key, cell in cells.items():
        s, _, day = key.partition("|")
        if s != subject or not cell.get("assessment"):
            continue
        auth = authoritative_assessment(plan, subject, day, cell)
        if auth["date"] and auth["date"] not in assessment_dates:
            assessment_dates.append(auth["date"])
    if not assessment_dates:
        return events

    def _relevant(a: dict[str, Any], before_days: int) -> bool:
        """True when the announcement is within ``before_days`` of a current assessment."""
        for stamp in (a.get("delayed_post_at"), a.get("posted_at")):
            day = canvas_due_local_day(stamp)
            if not day:
                continue
            try:
                stamp_date = datetime.fromisoformat(day).date()
            except ValueError:
                continue
            for ad in assessment_dates:
                try:
                    assess_date = datetime.fromisoformat(ad).date()
                except ValueError:
                    continue
                if assess_date - timedelta(days=before_days) <= stamp_date <= assess_date + timedelta(days=1):
                    return True
        return False

    firsts = [
        a for a in announcements
        if not _reminder_hint(a.get("title") or "") and not _is_update(a.get("title") or "")
        and _relevant(a, before_days=8)
    ]
    reminders = [a for a in announcements if _reminder_hint(a.get("title") or "") and _relevant(a, before_days=8)]

    # First parent announcement presence.
    if not firsts:
        events.append(_conflict(
            week_id=week_id, subject=subject, object_type=FIRST_ANNOUNCEMENT,
            object_identity=f"{subject}:first_announcement",
            authoritative="expected", observed=None,
            authority_winner="VERIFIED_PACING",
            affected=[f"{subject.title()} first parent announcement"],
            pacing_value="expected", canvas_value=None,
            teacher_override=None, source_timestamps=source_timestamps,
            source_freshness=source_freshness, family_comms=True,
        ))

    expected_reminder_days: set[str] = set()
    for date_str in assessment_dates:
        try:
            expected_reminder_days.add(
                (datetime.fromisoformat(date_str) - timedelta(days=1)).date().isoformat()
            )
        except ValueError:
            continue

    # Day-before reminder presence: only flag when a first announcement is
    # already posted (otherwise the reminder is simply "not yet created").
    first_posted = any(
        a.get("posted_at") and not a.get("delayed_post_at") for a in firsts
    )
    if firsts and first_posted and not reminders:
        events.append(_conflict(
            week_id=week_id, subject=subject, object_type=DAY_BEFORE_REMINDER,
            object_identity=f"{subject}:day_before_reminder",
            authoritative="expected", observed=None,
            authority_winner="VERIFIED_PACING",
            affected=[f"{subject.title()} day-before reminder"],
            pacing_value="expected", canvas_value=None,
            teacher_override=None, source_timestamps=source_timestamps,
            source_freshness=source_freshness, family_comms=True,
        ))

    seen_titles: dict[str, int] = {}
    for a in reminders:
        title = a.get("title") or ""
        seen_titles[title] = seen_titles.get(title, 0) + 1
        scheduled = a.get("delayed_post_at")
        if scheduled and expected_reminder_days:
            scheduled_day = canvas_due_local_day(scheduled)
            if scheduled_day and scheduled_day not in expected_reminder_days:
                events.append(_conflict(
                    week_id=week_id, subject=subject, object_type=REMINDER_OBSOLETE,
                    object_identity=f"{subject}:reminder:{title}",
                    authoritative=sorted(expected_reminder_days), observed=scheduled_day,
                    authority_winner="VERIFIED_PACING",
                    affected=[f"{subject.title()} day-before reminder"],
                    pacing_value=sorted(expected_reminder_days), canvas_value=scheduled_day,
                    teacher_override=None, source_timestamps=source_timestamps,
                    source_freshness=source_freshness, family_comms=True,
                ))
    for title, count in seen_titles.items():
        if count >= 2:
            events.append(_conflict(
                week_id=week_id, subject=subject, object_type=REMINDER_DUPLICATE,
                object_identity=f"{subject}:reminder_dup:{title}",
                authoritative="single", observed=f"{count}",
                authority_winner="VERIFIED_PACING",
                affected=[f"{subject.title()} day-before reminder"],
                pacing_value="single", canvas_value=str(count),
                teacher_override=None, source_timestamps=source_timestamps,
                source_freshness=source_freshness,
            ))

    return events


def unresolved_conflicts(store: Any) -> list[dict[str, Any]]:
    """Return unresolved cross-source conflicts from a durable event store."""
    return [
        e for e in store.unresolved()
        if e.get("classification") == cd.CROSS_SOURCE_CONFLICT
    ]


_ANN_REMINDER_TYPES = {
    FIRST_ANNOUNCEMENT, DAY_BEFORE_REMINDER, REMINDER_DUPLICATE, REMINDER_OBSOLETE,
}
_ASSESSMENT_TYPES = {
    ASSESSMENT_DATE, ASSESSMENT_IDENTITY, ASSESSMENT_ASSIGNMENT_MISSING, PACING_VS_OVERRIDE,
}


def scan_summary(snapshot: dict[str, Any], plan: WeeklyPlan | None = None) -> dict[str, Any]:
    """Human-readable breakdown of a baseline cross-source scan (read-only).

    Returns availability status plus per-category conflict lists. An outage is
    reported as SOURCE_UNAVAILABLE with no fabricated conflicts.
    """
    pacing = snapshot.get("pacing") or {}
    canvas = snapshot.get("canvas") or {}
    if pacing.get("status") != snap.SNAPSHOT_OK or canvas.get("status") != snap.SNAPSHOT_OK:
        return {
            "status": "SOURCE_UNAVAILABLE",
            "unknown_stale": True,
            "conflict_count": 0,
            "assessment_conflicts": [],
            "front_page_conflicts": [],
            "assignment_conflicts": [],
            "announcement_reminder_conflicts": [],
        }
    conflicts = scan(snapshot, plan=plan)
    return {
        "status": "SCANNED",
        "unknown_stale": False,
        "conflict_count": len(conflicts),
        "assessment_conflicts": [
            e.to_dict() for e in conflicts if e.object_type in _ASSESSMENT_TYPES
        ],
        "front_page_conflicts": [
            e.to_dict() for e in conflicts if e.object_type == FRONT_PAGE
        ],
        "assignment_conflicts": [
            e.to_dict() for e in conflicts
            if e.object_type in (ASSESSMENT_ASSIGNMENT_MISSING, ASSESSMENT_DATE, ASSESSMENT_IDENTITY)
        ],
        "announcement_reminder_conflicts": [
            e.to_dict() for e in conflicts if e.object_type in _ANN_REMINDER_TYPES
        ],
    }


def command_self_test() -> int:
    # 1. Due-date normalization (the critical Canvas-owned difference).
    assert canvas_due_local_day("2026-10-30T03:59:00Z") == "2026-10-29"
    assert canvas_due_local_day("2026-10-31T03:59:00Z") == "2026-10-30"
    assert canvas_due_local_day(None) is None

    # 2. Assessment identity parsing (combined + single).
    assert assessment_identities("Written Assessment 7, Fact Assessment 7") == [
        ("written_assessment", 7), ("fact_assessment", 7),
    ]
    assert assessment_identities("Spelling Test 45") == [("spelling_test", 45)]

    # 3. First-run cross-source conflict (no temporal event).
    plan = WeeklyPlan(week_id="Q2W3", quarter=2, week=3)
    sn = snap.blank_snapshot(2, 3, "Q2W3")
    sn["pacing"]["status"] = snap.SNAPSHOT_OK
    sn["pacing"]["cells"] = {
        "math|Thursday": {"lesson": "WA8", "chapter": None, "classwork": ["WA8"],
                          "homework": [],
                          "assessment": {"name": "Written Assessment 8", "date": "2026-11-05", "day": "Thursday"}},
    }
    sn["canvas"]["status"] = snap.SNAPSHOT_OK
    sn["canvas"]["courses"] = {
        "math": {
            "front_page": {"title": "Q2W3 Math", "page_id": "q2w3"},
            "pages": [{"title": "Q2W3 Math", "page_id": "q2w3", "front_page": True}],
            # due_at = Friday 11:59 PM ET -> Thursday vs Friday conflict.
            "assignments": [{"name": "SM5: Written Assessment 8", "due_at": "2026-11-07T03:59:00Z"}],
            "announcements": [
                {"title": "Math Weekly Update", "message": "", "delayed_post_at": None,
                 "posted_at": "2026-10-30T20:00:00Z"},
                {"title": "Math Assessment Reminder", "message": "",
                 "delayed_post_at": "2026-11-05T01:00:00Z", "posted_at": None},
            ],
        }
    }
    events = scan(sn, plan=plan)
    kinds = {e.object_type for e in events}
    assert ASSESSMENT_DATE in kinds, kinds
    date_ev = next(e for e in events if e.object_type == ASSESSMENT_DATE)
    assert date_ev.old_value == "2026-11-05" and date_ev.new_value == "2026-11-06"
    assert date_ev.classification == cd.CROSS_SOURCE_CONFLICT
    assert date_ev.authority_winner == "VERIFIED_PACING"

    # 4. Outage: canvas unavailable -> no conflict.
    sn2 = snap.blank_snapshot(2, 3, "Q2W3")
    sn2["pacing"]["status"] = snap.SNAPSHOT_OK
    sn2["pacing"]["cells"] = sn["pacing"]["cells"]
    sn2["canvas"]["status"] = snap.SNAPSHOT_UNAVAILABLE
    assert scan(sn2, plan=plan) == []

    print("PASS weekly-planner-agent cross-source self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(command_self_test())
