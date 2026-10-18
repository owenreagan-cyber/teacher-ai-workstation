#!/usr/bin/env python3
"""Grade Check health check (read-only operational readiness + freshness).

Answers one question: "Is Grade Check healthy and actually running?"

Safety contract (enforced, not merely intended):
- No Canvas access at all, so CANVAS WRITES PERFORMED is 0 by construction.
- No email transport is invoked and no send path is reachable.
- The state file is opened read-only and never rewritten (STATE MUTATIONS: 0).
- No token, client secret, SMTP password, auth code, or student grade data is
  ever printed. Only presence/absence and PASS/FAIL/YES/NO verdicts.

Exit codes: 0 = PASS, 1 = WARN, 2 = FAIL.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_grade_check import emailer  # noqa: E402
from scripts.instructional_weeks import parse_week_range  # noqa: E402
from scripts.canvas_llm_grade_check import gmail_transport  # noqa: E402
from scripts.canvas_llm_grade_check import scheduler  # noqa: E402

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"

EXIT_PASS = 0
EXIT_WARN = 1
EXIT_FAIL = 2

# Warn when the scheduler has not completed successfully for this many school
# days (weekend days are never counted).
STALE_AFTER_SCHOOL_DAYS = 2

# Expected repo files for a complete Grade Check installation.
EXPECTED_FILES = (
    "bin/grade-check",
    "bin/grade-check-schedule",
    "bin/grade-check-health",
    "scripts/canvas_llm_grade_check/config.py",
    "scripts/canvas_llm_grade_check/engine.py",
    "scripts/canvas_llm_grade_check/reader.py",
    "scripts/canvas_llm_grade_check/report.py",
    "scripts/canvas_llm_grade_check/emailer.py",
    "scripts/canvas_llm_grade_check/gmail_transport.py",
    "scripts/canvas_llm_grade_check/scheduler.py",
    "scripts/canvas_llm_grade_check/state.py",
    "scripts/canvas_llm_grade_check/templates.py",
    "config/canvas-llm/grade-check-config.json",
)

INSTRUCTIONAL_WEEKS_REL = "config/curriculum/canvas/instructional-weeks-2026-2027.json"


# Synthetic/test identities that must never appear in production state.
# Real Canvas student ids in this district are 5-digit; the deterministic test
# fixtures use student_id 1/2 with course 26404.
_SYNTHETIC_COURSE = "26404"
_SYNTHETIC_STUDENT_IDS = {"1", "2"}


@dataclass
class Section:
    title: str
    lines: list[str] = field(default_factory=list)
    status: str = PASS

    def add(self, text: str, status: str = PASS) -> None:
        self.lines.append(text)
        self.status = _worst(self.status, status)


@dataclass
class HealthReport:
    sections: list[Section] = field(default_factory=list)
    overall: str = PASS
    scheduler_status: str = PASS
    freshness_status: str = PASS
    school_days_since: int | None = None

    @property
    def exit_code(self) -> int:
        return {PASS: EXIT_PASS, WARN: EXIT_WARN, FAIL: EXIT_FAIL}[self.overall]


def _worst(a: str, b: str) -> str:
    order = {PASS: 0, WARN: 1, FAIL: 2}
    return a if order[a] >= order[b] else b


def _yn(flag: bool | None) -> str:
    if flag is None:
        return "UNKNOWN"
    return "YES" if flag else "NO"


# ---------------------------------------------------------------------------
# School-day calendar
# ---------------------------------------------------------------------------
def school_days(now: dt.datetime | None = None) -> tuple[set[dt.date], str]:
    """Return the set of known school days and the label describing the source.

    Prefers the canonical instructional-week export: it enumerates each
    instructional week, so weekdays NOT covered by any week (fall/spring breaks,
    track-out) are correctly excluded. Falls back to weekday-only logic with an
    explicit label when that export is missing or unparseable.
    """
    path = REPO_ROOT / INSTRUCTIONAL_WEEKS_REL
    if not path.exists():
        return set(), "weekday-only (instructional-week calendar unavailable)"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set(), "weekday-only (instructional-week calendar unreadable)"

    days: set[dt.date] = set()
    for week in raw.get("weeks", []):
        bounds = parse_week_range(week.get("pageTitle") or "")
        if bounds is None:
            continue
        start, end = bounds
        cur = start
        while cur <= end:
            if cur.weekday() < 5:
                days.add(cur)
            cur += dt.timedelta(days=1)

    if not days:
        return set(), "weekday-only (instructional-week calendar had no parsable weeks)"
    return days, "instructional-week calendar (weekends and breaks excluded)"


def is_school_day(day: dt.date, days: set[dt.date], source: str) -> bool:
    if day.weekday() >= 5:      # weekends are never school days
        return False
    if source.startswith("weekday-only"):
        return True
    return day in days


def school_days_between(
    earlier: dt.date, later: dt.date, days: set[dt.date], source: str
) -> int:
    """Count school days in (earlier, later].

    The earlier day itself is not counted (a successful run that day satisfies
    that day), so an immediate next-school-day success yields 0.
    """
    count = 0
    cur = earlier + dt.timedelta(days=1)
    while cur <= later:
        if is_school_day(cur, days, source):
            count += 1
        cur += dt.timedelta(days=1)
    return count


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def check_repo() -> Section:
    sec = Section("REPO")
    sec.add(f"repo exists: {_yn(REPO_ROOT.is_dir())}",
            PASS if REPO_ROOT.is_dir() else FAIL)
    missing = [rel for rel in EXPECTED_FILES if not (REPO_ROOT / rel).exists()]
    sec.add(f"expected Grade Check files present: {_yn(not missing)}",
            PASS if not missing else FAIL)
    if missing:
        for rel in missing:
            sec.add(f"  missing: {rel}", FAIL)
    return sec


def _iter_state_keys(state: dict) -> list[str]:
    keys: list[str] = []
    keys.extend(state.get("active_flags", {}) or {})
    keys.extend(state.get("resolved_flags", {}) or {})
    keys.extend(state.get("one_time_issued", {}) or {})
    return keys


def synthetic_keys(state: dict) -> list[str]:
    """Keys bearing test-fixture identity (course 26404 + student id 1/2)."""
    hits = []
    for key in _iter_state_keys(state):
        parts = str(key).split(":")
        if len(parts) >= 3 and parts[0] == _SYNTHETIC_COURSE and parts[1] in _SYNTHETIC_STUDENT_IDS:
            hits.append(key)
    return hits


def check_state(state_path: Path | None = None) -> tuple[Section, dict | None]:
    sec = Section("STATE")
    path = state_path or (REPO_ROOT / ".local" / "canvas-llm" / "grade-check" / "state.json")
    if not path.exists():
        sec.add("state file exists: NO", FAIL)
        return sec, None
    sec.add("state file exists: YES")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        sec.add("state JSON parses cleanly: FAIL", FAIL)
        sec.add(f"  state file is corrupt or unreadable: {type(exc).__name__}", FAIL)
        return sec, None

    sec.add("state JSON parses cleanly: PASS")
    active = state.get("active_flags", {}) or {}
    issued = state.get("one_time_issued", {}) or {}
    last_send = state.get("last_send")
    sec.add(f"active flag count: {len(active)}")
    sec.add(f"one-time issued count: {len(issued)}")
    sec.add(f"last-send metadata present: {_yn(bool(last_send))}",
            PASS if last_send else WARN)

    synth = synthetic_keys(state)
    sec.add(f"no synthetic/test keys detected: {_yn(not synth)}",
            PASS if not synth else FAIL)
    for key in synth:
        sec.add(f"  synthetic key present: {key}", FAIL)
    return sec, state


def check_oauth() -> Section:
    sec = Section("OAUTH")
    status = gmail_transport.oauth_status()
    sec.add(f"client credential present: {_yn(status['client_credential_present'])}",
            PASS if status["client_credential_present"] else FAIL)
    sec.add(f"token present: {_yn(status['token_present'])}",
            PASS if status["token_present"] else FAIL)
    sec.add(f"token permissions safe: {PASS if status['token_permissions_safe'] else FAIL}",
            PASS if status["token_permissions_safe"] else FAIL)
    ident = status["authorized_sender_identity"]
    sec.add(f"authorized sender identity: {PASS if ident is True else FAIL}",
            PASS if ident is True else FAIL)
    scope = status["gmail_send_scope_present"]
    sec.add(f"gmail.send scope present: {PASS if scope is True else FAIL}",
            PASS if scope is True else FAIL)
    ready = status["gmail_transport_ready"]
    sec.add(f"Gmail transport ready: {_yn(ready)}", PASS if ready else FAIL)
    if status.get("blocker"):
        # gmail_transport returns a fail-closed reason string; it never contains
        # secret values. Surface it so the operator knows what to fix.
        sec.add(f"  blocker: {status['blocker']}", FAIL)
    return sec


def check_recipient_safety() -> Section:
    sec = Section("RECIPIENT SAFETY")
    cfg = None
    try:
        from scripts.canvas_llm_grade_check import config as config_mod

        cfg = config_mod.load_config()
    except Exception:  # noqa: BLE001
        pass

    sender_ok = emailer._sender_allowed(emailer.ALLOWED_SENDER)
    sec.add(f"sender allowlist: {PASS if sender_ok else FAIL}",
            PASS if sender_ok else FAIL)

    recipient = cfg.recipient_email if cfg else emailer.ALLOWED_RECIPIENT
    recipient_ok = emailer.check_recipient_safety(recipient) is None
    sec.add(f"recipient allowlist: {PASS if recipient_ok else FAIL}",
            PASS if recipient_ok else FAIL)

    cc_blocked = (emailer.check_recipient_safety(recipient, cc="parent@example.com") or "").startswith("RECIPIENT SAFETY BLOCK")
    bcc_blocked = (emailer.check_recipient_safety(recipient, bcc="parent@example.com") or "").startswith("RECIPIENT SAFETY BLOCK")
    sec.add(f"CC/BCC prohibition: {PASS if (cc_blocked and bcc_blocked) else FAIL}",
            PASS if (cc_blocked and bcc_blocked) else FAIL)

    # No parent/guardian/student recipient may ever be accepted, and no send
    # path to one may exist anywhere in the emailer.
    parent_blocked = (emailer.check_recipient_safety("parent@example.com") or "").startswith("RECIPIENT SAFETY BLOCK")
    student_blocked = (emailer.check_recipient_safety("student@thalesacademy.org") or "").startswith("RECIPIENT SAFETY BLOCK")
    no_parent_path = emailer.emailer_has_no_parent_recipients()
    prohib_ok = parent_blocked and student_blocked and no_parent_path
    sec.add(f"parent/student send prohibition: {PASS if prohib_ok else FAIL}",
            PASS if prohib_ok else FAIL)
    return sec


def trigger_safety(plist: dict) -> tuple[bool, list[str]]:
    """Detect launchd triggers that can start the job outside its calendar.

    Delegates to the scheduler's audit so there is one source of truth for the
    forbidden-trigger list. The Grade Check job must run ONLY on its Mon-Fri
    calendar schedule: ``KeepAlive`` (e.g. ``{"SuccessfulExit": False}``) makes
    launchd re-run the job as soon as it is loaded/reloaded, which can send an
    email without an explicit scheduled trigger. ``RunAtLoad`` and the other
    watch/path/interval triggers carry the same hazard.
    """
    problems, _notes = scheduler.audit_plist_triggers(plist)
    return (not problems), problems


def _read_plist(path: Path) -> dict | None:
    try:
        import plistlib

        return plistlib.loads(path.read_bytes())
    except Exception:  # noqa: BLE001
        return None


def check_scheduler(cfg) -> tuple[Section, str, str | None, str | None]:
    """Return (section, scheduler_status, last_run_iso, expected_command)."""
    sec = Section("SCHEDULER")
    installed = scheduler.plist_path().exists()
    loaded = scheduler.is_loaded() if installed else False
    expected = scheduler.scheduled_shell_command()

    sec.add(f"installed: {_yn(installed)}", PASS if installed else FAIL)
    sec.add(f"loaded: {_yn(loaded)}", PASS if loaded else FAIL)
    try:
        sec.add(f"schedule: {scheduler._schedule_label(cfg.schedule)}")
    except Exception:  # noqa: BLE001
        sec.add("schedule: unknown", WARN)
    sec.add(f"expected command: {expected}")

    last_exit = scheduler._last_exit_status() if loaded else None
    # launchd prints "last exit code = (never exited)" for a job that has not
    # run yet. A freshly installed calendar job legitimately has no run until
    # its first trigger, so this is not a failure. Only a real numeric non-zero
    # exit code is a defect. Freshness (below) is the authoritative staleness
    # signal.
    exit_is_numeric = (
        last_exit is not None and last_exit.strip().lstrip("-").isdigit()
    )
    exit_failed = exit_is_numeric and last_exit.strip() != "0"
    if exit_failed:
        sec.add(f"last exit status: {last_exit}", FAIL)
    elif exit_is_numeric:
        sec.add(f"last exit status: {last_exit}")
    else:
        sec.add("last exit status: no scheduled run recorded yet")

    last_run = scheduler._last_run_timestamp()
    sec.add(f"last run timestamp: {last_run if last_run else 'unavailable'}",
            PASS if last_run else WARN)

    # Trigger safety: the job must only fire on its calendar schedule.
    trigger_ok = False
    trigger_problems: list[str] = []
    if installed:
        plist = _read_plist(scheduler.plist_path())
        if plist is None:
            sec.add("trigger safety: FAIL (plist unreadable)", FAIL)
        else:
            trigger_ok, trigger_problems = trigger_safety(plist)
            sec.add(f"trigger safety: {PASS if trigger_ok else FAIL}",
                    PASS if trigger_ok else FAIL)
            for problem in trigger_problems:
                sec.add(f"  UNSAFE TRIGGER: {problem}", FAIL)
            if not trigger_ok:
                sec.add(
                    "  Unsafe triggers can send a Grade Check email immediately "
                    "on install/reload, outside the Mon-Fri 4:15 PM schedule.",
                    FAIL,
                )

    status = PASS
    if not installed:
        status = FAIL
    elif not loaded:
        status = FAIL
    elif exit_failed:
        status = FAIL
    elif trigger_problems:
        status = FAIL
    return sec, status, last_run, expected


def last_successful_run_iso(log_path: Path) -> str | None:
    """Timestamp of the most recent run that completed without a blocker.

    A run with a blocker (failed send, missing credentials) is not a successful
    completion, so it must not refresh scheduler freshness.
    """
    last_ok: str | None = None
    try:
        for raw in log_path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if rec.get("blocker"):
                continue
            ts = rec.get("timestamp")
            if ts:
                last_ok = ts
    except OSError:
        return None
    return last_ok


def check_logs() -> tuple[Section, dict | None]:
    sec = Section("LOGS")
    log_dir = scheduler.log_dir()
    exists = log_dir.is_dir()
    sec.add(f"log directory exists: {_yn(exists)}", PASS if exists else WARN)
    if not exists:
        return sec, None

    runs = log_dir / "grade-check.runs.jsonl"
    if not runs.exists():
        sec.add("most recent run-log timestamp: unavailable", WARN)
        sec.add("most recent run result: unavailable", WARN)
        return sec, None

    last: dict | None = None
    try:
        for raw in runs.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                last = json.loads(raw)
            except json.JSONDecodeError:
                continue
    except OSError:
        sec.add("run log unreadable: WARN", WARN)
        return sec, None

    if not last:
        sec.add("most recent run-log timestamp: unavailable", WARN)
        sec.add("most recent run result: unavailable", WARN)
        return sec, None

    sec.add(f"most recent run-log timestamp: {last.get('timestamp') or 'unavailable'}")
    counts = last.get("counts") or {}
    result = (
        f"email_sent={_yn(bool(last.get('email_sent')))} "
        f"quarter={last.get('quarter')} "
        f"missing_new={counts.get('missing_new', '?')} "
        f"missing_still_active={counts.get('missing_still_active', '?')} "
        f"unresolved={counts.get('unresolved', '?')}"
    )
    sec.add(f"most recent run result: {result}")
    return sec, last


def check_freshness(last_run_iso: str | None, now: dt.datetime | None = None) -> tuple[Section, str, int | None, str]:
    """Scheduler freshness: WARN when no successful completion in >2 school days."""
    sec = Section("SCHEDULER FRESHNESS")
    now = now or dt.datetime.now()
    days, source = school_days(now)
    sec.add(f"school-day source: {source}")

    if not last_run_iso:
        sec.add("Last successful run: unavailable", WARN)
        sec.add("School days since successful run: unknown", WARN)
        sec.add("WARNING: no recorded Grade Check run, so freshness cannot be verified.", WARN)
        sec.add("Scheduler freshness: WARN", WARN)
        return sec, WARN, None, source

    try:
        stamp = dt.datetime.fromisoformat(last_run_iso)
    except ValueError:
        sec.add(f"Last successful run: {last_run_iso} (unparsable)", WARN)
        sec.add("School days since successful run: unknown", WARN)
        sec.add("Scheduler freshness: WARN", WARN)
        return sec, WARN, None, source

    days_since = school_days_between(stamp.date(), now.date(), days, source)
    # Run timestamps are recorded in UTC; display in local (school) time.
    if stamp.tzinfo is not None:
        local = stamp.astimezone()
        tz = local.strftime("%Z") or "local"
        shown = f"{local.strftime('%Y-%m-%d %H:%M')} {tz}"
    else:
        shown = stamp.strftime("%Y-%m-%d %H:%M")
    sec.add(f"Last successful run: {shown}")
    sec.add(f"School days since successful run: {days_since}")

    if days_since > STALE_AFTER_SCHOOL_DAYS:
        sec.add(f"WARNING: Grade Check has not completed successfully in more than "
                f"{STALE_AFTER_SCHOOL_DAYS} school days.", WARN)
        sec.add("Scheduler freshness: WARN", WARN)
        return sec, WARN, days_since, source

    sec.add("Scheduler freshness: PASS", PASS)
    return sec, PASS, days_since, source


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def build_report(now: dt.datetime | None = None) -> HealthReport:
    rep = HealthReport()
    try:
        from scripts.canvas_llm_grade_check import config as config_mod

        cfg = config_mod.load_config()
    except Exception:  # noqa: BLE001
        cfg = None

    repo_sec = check_repo()
    state_sec, _state = check_state()
    oauth_sec = check_oauth()
    recip_sec = check_recipient_safety()

    # Scheduler: if config is unavailable, still report what we can.
    if cfg is not None:
        sched_sec, sched_status, last_run, _cmd = check_scheduler(cfg)
    else:
        sched_sec, sched_status, last_run = Section("SCHEDULER"), FAIL, None
        sched_sec.add("scheduler check unavailable: config could not be loaded", FAIL)

    logs_sec, last_log = check_logs()

    # Freshness: prefer the most recent run that actually completed without a
    # blocker; fall back to the scheduler's own recorded run timestamp.
    runs_path = scheduler.log_dir() / "grade-check.runs.jsonl"
    last_ok = last_successful_run_iso(runs_path) if runs_path.exists() else None
    freshness_ts = last_ok or last_run
    fresh_sec, fresh_status, days_since, _src = check_freshness(freshness_ts, now)

    rep.sections = [repo_sec, state_sec, oauth_sec, recip_sec, sched_sec, logs_sec, fresh_sec]
    rep.scheduler_status = sched_status
    rep.freshness_status = fresh_status
    rep.school_days_since = days_since

    overall = PASS
    for sec in (repo_sec, state_sec, oauth_sec, recip_sec, sched_sec, logs_sec, fresh_sec):
        overall = _worst(overall, sec.status)
    rep.overall = overall
    return rep


def render(rep: HealthReport) -> str:
    out: list[str] = []
    out.append("=== GRADE CHECK HEALTH ===")
    out.append("")
    for sec in rep.sections:
        out.append(f"--- {sec.title} ---")
        out.extend(sec.lines)
        out.append("")
    out.append("CANVAS WRITES PERFORMED: 0")
    out.append("EMAILS SENT: 0")
    out.append("STATE MUTATIONS: 0")
    out.append("")
    out.append(f"GRADE CHECK HEALTH: {rep.overall}")
    return "\n".join(out)


def command_health() -> int:
    rep = build_report()
    print(render(rep))
    return rep.exit_code


def command_self_test() -> int:
    """Deterministic health-check tests. Sends nothing, writes nothing."""
    import tempfile

    now_school = dt.datetime(2026, 9, 10, 16, 15)   # Thursday
    days, source = school_days(now_school)
    assert source.startswith("instructional-week calendar"), source
    # Weekends are never school days.
    assert is_school_day(dt.date(2026, 9, 12), days, source) is False  # Saturday
    assert is_school_day(dt.date(2026, 9, 13), days, source) is False  # Sunday
    # A known instructional day.
    assert is_school_day(dt.date(2026, 9, 10), days, source) is True
    # Fall break weekdays are excluded by the canonical calendar.
    assert is_school_day(dt.date(2026, 9, 22), days, source) is False

    # School-day counting excludes weekends.
    # Thu 2026-09-10 -> Mon 2026-09-14 crosses Fri + Mon = 2 (Sat/Sun excluded).
    assert school_days_between(dt.date(2026, 9, 10), dt.date(2026, 9, 14), days, source) == 2
    # Thu -> Fri = 1.
    assert school_days_between(dt.date(2026, 9, 10), dt.date(2026, 9, 11), days, source) == 1
    # Same day = 0.
    assert school_days_between(dt.date(2026, 9, 10), dt.date(2026, 9, 10), days, source) == 0
    # Fri -> Mon counts only Monday (weekend ignored).
    assert school_days_between(dt.date(2026, 9, 11), dt.date(2026, 9, 14), days, source) == 1
    # A long weekend gap is still 0/1, never inflated by Sat/Sun.
    assert school_days_between(dt.date(2026, 9, 11), dt.date(2026, 9, 13), days, source) == 0

    # Freshness: same-day success is PASS.
    _sec, st, n, _s = check_freshness("2026-09-10T16:15:00", now_school)
    assert st == PASS and n == 0, (st, n)
    # One school day later is still PASS (threshold is >2).
    _sec, st, n, _s = check_freshness("2026-09-09T16:15:00", now_school)
    assert st == PASS and n == 1, (st, n)
    # Exactly 2 school days is still PASS (strictly greater than 2 warns).
    _sec, st, n, _s = check_freshness("2026-09-08T16:15:00", now_school)
    assert st == PASS and n == 2, (st, n)
    # 3 school days is stale -> WARN.
    _sec, st, n, _s = check_freshness("2026-09-07T16:15:00", now_school)
    assert st == WARN and n == 3, (st, n)
    # A Friday run viewed on Monday is only 1 school day -> PASS.
    monday = dt.datetime(2026, 9, 14, 16, 15)
    _sec, st, n, _s = check_freshness("2026-09-11T16:15:00", monday)
    assert st == PASS and n == 1, (st, n)
    # No recorded run -> WARN, not FAIL.
    _sec, st, n, _s = check_freshness(None, now_school)
    assert st == WARN and n is None

    # A blocked run must not refresh freshness.
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "runs.jsonl"
        p.write_text(
            '{"timestamp": "2026-09-01T20:00:00+00:00", "blocker": null}\n'
            '{"timestamp": "2026-09-10T20:00:00+00:00", "blocker": "RECIPIENT SAFETY BLOCK"}\n',
            encoding="utf-8",
        )
        assert last_successful_run_iso(p) == "2026-09-01T20:00:00+00:00"
        # A log with only blocked runs yields no successful run at all.
        p.write_text('{"timestamp": "2026-09-10T20:00:00+00:00", "blocker": "boom"}\n',
                     encoding="utf-8")
        assert last_successful_run_iso(p) is None

    # Synthetic key detection.
    assert synthetic_keys({"active_flags": {"26404:1:10:MISSING_ASSIGNMENT": {}}}) == [
        "26404:1:10:MISSING_ASSIGNMENT"
    ]
    assert synthetic_keys({"one_time_issued": {"26442:22140:1020031:LOW_ASSESSMENT_SCORE": True}}) == []
    assert synthetic_keys({"active_flags": {"26404:31353:1:MISSING_ASSIGNMENT": {}}}) == []

    # Exit-code mapping.
    assert (EXIT_PASS, EXIT_WARN, EXIT_FAIL) == (0, 1, 2)

    # Trigger safety: only StartCalendarInterval is allowed.
    _cal = {"StartCalendarInterval": [{"Weekday": 1, "Hour": 16, "Minute": 15}]}
    _ok, _probs = trigger_safety(dict(_cal))
    assert _ok and _probs == [], (_ok, _probs)
    # The exact form that caused the unapproved 2026-09-10 20:24 EDT send.
    _ok, _probs = trigger_safety({**_cal, "KeepAlive": {"SuccessfulExit": False}})
    assert not _ok and _probs, "KeepAlive{SuccessfulExit:false} must be FAIL"
    # A null/false KeepAlive is still a key that must never be installed.
    for _null in (None, False):
        _ok, _probs = trigger_safety({**_cal, "KeepAlive": _null})
        assert not _ok and _probs, f"KeepAlive={_null!r} must be rejected"
    # RunAtLoad must never be set; explicit false is only a note.
    _ok, _probs = trigger_safety({**_cal, "RunAtLoad": True})
    assert not _ok and _probs
    _ok, _probs = trigger_safety({**_cal, "RunAtLoad": False})
    assert _ok and _probs == [], _probs
    # Every other off-schedule trigger key is rejected.
    for _key in scheduler.FORBIDDEN_TRIGGER_KEYS:
        if _key in ("KeepAlive", "RunAtLoad"):
            continue
        _ok, _probs = trigger_safety({**_cal, _key: True})
        assert not _ok and _probs, f"{_key} must be rejected"
    # Missing calendar trigger is rejected.
    _ok, _probs = trigger_safety({"Label": "x"})
    assert not _ok and _probs

    # The health command must not touch Canvas or email: assert the production
    # code (everything before this self-test) has no writer/transport call sites.
    src = Path(__file__).read_text(encoding="utf-8")
    marker = "def command_self_test"
    prod = src[: src.find(marker)] if marker in src else src
    for forbidden in ("urlopen", "smtplib", "send_via_gmail_api", "send_teacher_report",
                      "_paginate", "requests.", "smtplib.SMTP"):
        assert forbidden not in prod, f"health module must not reference {forbidden!r}"
    # And it must never write the state file or the run log.
    for writer in ("write_state", "os.replace", "store.save", "Path.write_text"):
        assert writer not in prod, f"health module must not reference {writer!r}"

    print("PASS grade-check health self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "self-test":
        return command_self_test()
    if args and args[0] not in ("--health", "--status"):
        print("usage: bin/grade-check-health [--status|self-test]")
        return EXIT_FAIL
    return command_health()


if __name__ == "__main__":
    raise SystemExit(main())
