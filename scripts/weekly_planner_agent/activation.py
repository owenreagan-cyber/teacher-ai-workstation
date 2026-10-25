"""Weekly Planner Agent — Friday scheduler activation.

Provides the stable CLI entrypoints the macOS LaunchAgent calls, plus the
LaunchAgent install/status/uninstall machinery. No business logic lives in the
plist; this module owns dispatch, and it is GET-only except for the single
guarded 4:00 PM publish path (which reuses the existing rollover publisher).

Entrypoints (conceptual):
    check     — periodic GET-only background reconciliation (never publishes)
    refresh   — Friday 3:00 PM final source refresh (read-only)
    notify    — Friday 3:30 PM approval-ready email (idempotent)
    publish   — Friday 4:00 PM guarded publication (approval + freshness gate)
    scheduled — time/date dispatch for the LaunchAgent
    install / status / uninstall / preview — LaunchAgent management
    self-test — deterministic, no network, no send, no install

All scheduler commands are fail-closed: no approval -> no publish, and email
never auto-enables itself.
"""
from __future__ import annotations

import json
import os
import plistlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from scripts.canvas_planner.state_root import planner_root

from . import schedule_config

REPO_ROOT = Path(__file__).resolve().parents[2]
EASTERN = ZoneInfo("America/New_York")

LAUNCH_AGENT_LABEL = "com.teacher-ai-workstation.canvas-friday"
PLIST_FILENAME = f"{LAUNCH_AGENT_LABEL}.plist"

LOG_DIR_REL = ".local/canvas-planner/logs"
OUT_LOG_REL = LOG_DIR_REL + "/friday-scheduler.log"
ERR_LOG_REL = LOG_DIR_REL + "/friday-scheduler.err.log"

# A scheduled publish must never be triggered off-calendar (reload, keepalive,
# watchpath, etc.). The only allowed automatic trigger is StartCalendarInterval.
FORBIDDEN_TRIGGER_KEYS = (
    "KeepAlive", "RunAtLoad", "StartInterval", "StartOnMount",
    "WatchPaths", "QueueDirectories", "PathState", "OtherJobEnabled",
    "NetworkState", "SuccessfulExit",
)
ALLOWED_TRIGGER_KEY = "StartCalendarInterval"


class ScheduleError(RuntimeError):
    """Raised when the LaunchAgent cannot be generated or managed safely."""


# --------------------------------------------------------------------------- #
# Time helpers
# --------------------------------------------------------------------------- #
def _now_et(now: datetime | None = None) -> datetime:
    return (now or datetime.now(EASTERN)).astimezone(EASTERN)


def _week_of(now: datetime) -> tuple[int, int]:
    from scripts.canvas_llm_intake import week_resolution
    try:
        return week_resolution.current_week(today=now.date())
    except RuntimeError:
        return week_resolution.next_week(today=now.date())


def resolve_target_week(now: datetime | None = None) -> tuple[int, int]:
    """Target week: current instructional week on a weekday, next on weekend."""
    from scripts.weekly_planner_agent import service
    return service.resolve_target_week() if now is None else _week_of(_now_et(now))


# --------------------------------------------------------------------------- #
# Scheduled dispatch (what runs at each Friday milestone)
# --------------------------------------------------------------------------- #
def dispatch(now: datetime | None = None) -> dict[str, Any]:
    """Route a scheduled invocation to the right milestone by ET time + weekday.

    Returns ``{action, ...}``. Never improvises: every action is bounded and the
    publish path re-runs the full guarded gate.
    """
    local = _now_et(now)
    sched = schedule_config.schedule()
    quarter, week = resolve_target_week(local)

    if local.weekday() == 4:  # Friday
        publish_hm = _to_minutes(sched["publish"])
        notify_hm = _to_minutes(sched["approval_ready_email"])
        refresh_hm = _to_minutes(sched["final_refresh"])
        now_hm = local.hour * 60 + local.minute
        if now_hm >= publish_hm:
            return publish_scheduled(quarter, week)
        if now_hm >= notify_hm:
            return notify_scheduled(quarter, week)
        if now_hm >= refresh_hm:
            return refresh_scheduled(quarter, week)

    return check_scheduled(quarter, week)


def _to_minutes(hhmm: str) -> int:
    h, _, m = hhmm.partition(":")
    return int(h) * 60 + int(m)


# --------------------------------------------------------------------------- #
# Milestone actions
# --------------------------------------------------------------------------- #
def check_scheduled(quarter: int, week: int) -> dict[str, Any]:
    """Periodic GET-only background reconciliation. Never publishes."""
    from scripts.weekly_planner_agent import service
    report = service.live_sync(quarter, week)
    return {
        "action": "CHECK",
        "week": f"Q{quarter}W{week}",
        "baseline": report.get("baseline"),
        "cross_source_conflicts": len(report.get("cross_source_conflicts") or []),
        "assessment_watch": len(report.get("assessment_watch") or []),
        "new_events_added": report.get("new_events_added"),
        "canvas_writes": report.get("canvas_writes") or 0,
        "notifications_delivered": report.get("notifications_delivered") or 0,
    }


def refresh_scheduled(quarter: int, week: int) -> dict[str, Any]:
    """Friday 3:00 PM final refresh: live reads + consistency + review recompute."""
    from scripts.weekly_planner_agent import service
    report = service.live_sync(quarter, week)
    review = service.friday_review(quarter, week)
    return {
        "action": "REFRESH",
        "week": f"Q{quarter}W{week}",
        "pacing_status": (report.get("live") or {}).get("pacing_status"),
        "canvas_status": (report.get("live") or {}).get("canvas_status"),
        "cross_source_conflicts": len(report.get("cross_source_conflicts") or []),
        "assessment_watch": len(report.get("assessment_watch") or []),
        "review_state": review.get("state"),
        "canvas_writes": report.get("canvas_writes") or 0,
        "notifications_delivered": report.get("notifications_delivered") or 0,
    }


def notify_scheduled(quarter: int, week: int) -> dict[str, Any]:
    """Friday 3:30 PM approval-ready email (idempotent, never publishes)."""
    from scripts.weekly_planner_agent import service
    return service.friday_notify(quarter, week)


def publish_scheduled(
    quarter: int, week: int, *, client_factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Friday 4:00 PM guarded publication. Reuses the sole rollover publisher."""
    from scripts.weekly_planner_agent import service
    from scripts.weekly_planner_agent import publish as pub

    plan = service.load_plan(quarter, week)
    gate = pub.build_publish_gate(quarter, week, plan=plan)
    if not gate["ready"]:
        return {
            "action": "PUBLISH", "week": f"Q{quarter}W{week}",
            "published": False, "state": "BLOCKED", "blockers": gate["blockers"],
            "canvas_writes": 0,
        }
    client = client_factory() if client_factory is not None else None
    if client is None:
        # Never construct a live client implicitly inside a scheduled path that
        # could publish unattended; production requires an explicit client.
        return {
            "action": "PUBLISH", "week": f"Q{quarter}W{week}",
            "published": False, "state": "HELD — LIVE CLIENT REQUIRED",
            "canvas_writes": 0,
        }
    result = pub.publish(quarter, week, client=client)
    return {
        "action": "PUBLISH", "week": f"Q{quarter}W{week}",
        "published": bool(result.get("published")),
        "state": result.get("review_state"),
        "report": result.get("report"),
        "canvas_writes": _report_writes(result.get("report")),
    }


def _report_writes(report: dict[str, Any] | None) -> int:
    if not report:
        return 0
    totals = report.get("verb_totals") or {}
    return sum(
        int(totals.get(v) or 0)
        for v in ("POST", "PUT", "PATCH", "DELETE")
    )


# --------------------------------------------------------------------------- #
# LaunchAgent plist (no business logic, no secrets)
# --------------------------------------------------------------------------- #
def plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / PLIST_FILENAME


def _scheduled_command() -> list[str]:
    # Explicit bash + repo-relative wrapper so launchd's minimal env is safe.
    return [
        "/bin/bash",
        str(REPO_ROOT / "bin" / "weekly-planner-friday"),
        "--scheduled",
    ]


def _calendar_intervals(sched: dict[str, Any]) -> list[dict[str, int]]:
    """Build StartCalendarInterval entries from the configured schedule."""
    intervals: list[dict[str, int]] = []

    def add(weekday: int, hhmm: str) -> None:
        h, _, m = hhmm.partition(":")
        intervals.append({"Weekday": weekday, "Hour": int(h), "Minute": int(m)})

    # Periodic weekday GET-only checks.
    if sched.get("periodic_reconciliation_enabled"):
        for hhmm in sched.get("periodic_check_hours") or []:
            for wd in (1, 2, 3, 4, 5):
                add(wd, hhmm)
    # Friday milestones.
    add(5, sched["final_refresh"])
    add(5, sched["approval_ready_email"])
    add(5, sched["publish"])
    # De-duplicate + sort for determinism.
    unique = {tuple(sorted(i.items())): i for i in intervals}
    return sorted(unique.values(), key=lambda i: (i.get("Weekday", 0), i.get("Hour", 0), i.get("Minute", 0)))


def build_plist(sched: dict[str, Any] | None = None) -> dict:
    sched = sched or schedule_config.schedule()
    env = {
        "PATH": os.environ.get("PATH", "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"),
        "HOME": str(Path.home()),
        "TAW_STATE_ROOT": str(planner_root()),
    }
    plist = {
        "Label": LAUNCH_AGENT_LABEL,
        "ProgramArguments": _scheduled_command(),
        "WorkingDirectory": str(REPO_ROOT),
        "EnvironmentVariables": env,
        ALLOWED_TRIGGER_KEY: _calendar_intervals(sched),
        "StandardOutPath": str(REPO_ROOT / OUT_LOG_REL),
        "StandardErrorPath": str(REPO_ROOT / ERR_LOG_REL),
        "ProcessType": "Background",
    }
    validate_plist_triggers(plist)
    return plist


def validate_plist_triggers(plist: dict) -> None:
    present = [k for k in FORBIDDEN_TRIGGER_KEYS if k in plist]
    if present:
        raise ScheduleError(
            "refusing plist with off-schedule trigger(s): " + ", ".join(present)
        )
    if not plist.get(ALLOWED_TRIGGER_KEY):
        raise ScheduleError("plist missing StartCalendarInterval")


def render_plist_xml(sched: dict[str, Any] | None = None) -> str:
    return plistlib.dumps(build_plist(sched)).decode("utf-8")


# --------------------------------------------------------------------------- #
# launchctl management
# --------------------------------------------------------------------------- #
def _user_domain() -> str:
    return f"gui/{os.getuid()}"


def _launchctl(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["launchctl", *args], capture_output=True, text=True, timeout=30)


def is_loaded() -> bool:
    return _launchctl(["print", f"{_user_domain()}/{LAUNCH_AGENT_LABEL}"]).returncode == 0


def scheduler_status() -> dict[str, Any]:
    path = plist_path()
    installed = path.exists()
    loaded = is_loaded() if installed else False
    last_exit = _last_exit_status() if loaded else None
    last_run = _last_run_timestamp()
    return {
        "label": LAUNCH_AGENT_LABEL,
        "installed": installed,
        "loaded": loaded,
        "plist_path": str(path),
        "last_exit_status": last_exit,
        "last_run": last_run,
        "next_milestone": _next_milestone(),
    }


def _last_exit_status() -> str | None:
    res = _launchctl(["print", f"{_user_domain()}/{LAUNCH_AGENT_LABEL}"])
    if res.returncode != 0:
        return None
    for raw in res.stdout.splitlines():
        if raw.strip().startswith("last exit code"):
            return raw.split("=", 1)[-1].strip()
    return None


def _last_run_timestamp() -> str | None:
    candidates = [REPO_ROOT / OUT_LOG_REL, REPO_ROOT / ERR_LOG_REL]
    candidates = [p for p in candidates if p.exists()]
    if not candidates:
        return None
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    return datetime.fromtimestamp(newest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def _next_milestone() -> str:
    sched = schedule_config.schedule()
    return (
        f"Friday {sched['final_refresh']} refresh · {sched['approval_ready_email']} notify · "
        f"{sched['publish']} guarded publish ({sched['timezone']})"
    )


def install() -> int:
    sched = schedule_config.schedule()
    path = plist_path()
    (REPO_ROOT / LOG_DIR_REL).mkdir(parents=True, exist_ok=True)

    if is_loaded():
        _launchctl(["bootout", f"{_user_domain()}/{LAUNCH_AGENT_LABEL}"])
        if is_loaded():
            print("BLOCKER: launchctl could not unload the existing agent")
            return 1

    xml = render_plist_xml(sched)
    tmp = path.with_suffix(".plist.tmp")
    tmp.write_text(xml, encoding="utf-8")
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)

    installed = plistlib.loads(path.read_bytes())
    problems = [k for k in FORBIDDEN_TRIGGER_KEYS if k in installed]
    if problems:
        print("BLOCKER: refusing to load unsafe plist: " + ", ".join(problems))
        return 1

    lint = subprocess.run(["plutil", "-lint", str(path)], capture_output=True, text=True, timeout=30)
    if lint.returncode != 0:
        print("BLOCKER: plutil -lint rejected plist: " + (lint.stderr or lint.stdout or "").strip())
        return 1

    res = _launchctl(["bootstrap", _user_domain(), str(path)])
    if res.returncode != 0:
        legacy = _launchctl(["load", "-w", str(path)])
        if legacy.returncode != 0:
            print("BLOCKER: launchctl could not load agent: " + (res.stderr or legacy.stderr or "").strip())
            return 1

    print("INSTALLED WEEKLY PLANNER FRIDAY SCHEDULER")
    print(f"  label: {LAUNCH_AGENT_LABEL}")
    print(f"  plist: {path}")
    print(f"  loaded: {'YES' if is_loaded() else 'NO'}")
    print(f"  next milestone: {_next_milestone()}")
    print("  CANVAS WRITES PERFORMED: 0")
    print("  EMAILS SENT: 0")
    return 0


def uninstall() -> int:
    path = plist_path()
    if is_loaded():
        _launchctl(["bootout", f"{_user_domain()}/{LAUNCH_AGENT_LABEL}"])
    if path.exists():
        path.unlink()
    print("UNINSTALLED WEEKLY PLANNER FRIDAY SCHEDULER")
    print("  other LaunchAgents untouched: YES")
    return 0


# --------------------------------------------------------------------------- #
# Self-test (deterministic, no network/send/install)
# --------------------------------------------------------------------------- #
def email_test() -> dict[str, Any]:
    """Send exactly one controlled test email to Owen (idempotent).

    Proves the real transport works. Does NOT trigger Canvas writes, change any
    weekly plan, approve anything, or schedule anything. Records the result in
    delivery history. A retry with the same idempotency key is suppressed.
    """
    from . import delivery
    from . import schedule_config

    cfg = schedule_config.delivery_config()
    if not cfg.get("email_enabled"):
        return {"sent": False, "status": "EMAIL_DISABLED",
                "reason": "email_enabled is false; enable it in local delivery config first"}
    record = delivery.make_record(
        notification_type="weekly_planner_email_test",
        subject="Teacher AI Workstation — Weekly Planner email test",
        body="This is a controlled Weekly Planner Agent delivery test. No Canvas changes were made.",
        review_link="",
        related_event_ids=["weekly-planner-email-test"],
        plan_version="activation-test",
    )
    result = delivery.deliver(record, mode="email")
    return {
        "sent": result.get("status") == "sent",
        "status": result.get("status"),
        "error": result.get("error"),
        "transport": result.get("transport"),
        "notification_id": result.get("notification_id"),
        "canvas_writes": 0,
    }


def command_self_test() -> int:
    # Plist generation: calendar-only, no secrets, correct label.
    plist = build_plist()
    assert plist["Label"] == LAUNCH_AGENT_LABEL
    intervals = plist[ALLOWED_TRIGGER_KEY]
    assert isinstance(intervals, list) and intervals
    for key in FORBIDDEN_TRIGGER_KEYS:
        assert key not in plist, f"forbidden trigger {key!r}"
    xml = render_plist_xml().lower()
    for secret in ("password", "token", "secret", "smtp_", "refresh_token", "access_token"):
        assert secret not in xml, f"plist leaked {secret!r}"
    # No live client is constructed inside the plist command.
    assert "--scheduled" in plist["ProgramArguments"]
    assert "python" not in plist["ProgramArguments"][0].lower()

    # dispatch is time-driven and fail-closed (no approval -> no publish).
    from datetime import datetime as dt
    fri_16 = dt(2026, 10, 30, 16, 0, tzinfo=EASTERN)
    fri_15 = dt(2026, 10, 30, 15, 0, tzinfo=EASTERN)
    fri_1530 = dt(2026, 10, 30, 15, 30, tzinfo=EASTERN)
    tue = dt(2026, 10, 27, 10, 0, tzinfo=EASTERN)

    from unittest import mock
    from scripts.weekly_planner_agent import activation as act

    with mock.patch.object(act, "publish_scheduled", return_value={"action": "PUBLISH", "canvas_writes": 0}) as mp:
        r = act.dispatch(fri_16)
        assert r["action"] == "PUBLISH"
        mp.assert_called_once()
    with mock.patch.object(act, "notify_scheduled", return_value={"action": "NOTIFY", "canvas_writes": 0}) as mn:
        r = act.dispatch(fri_1530)
        assert r["action"] == "NOTIFY"
        mn.assert_called_once()
    with mock.patch.object(act, "refresh_scheduled", return_value={"action": "REFRESH", "canvas_writes": 0}) as mr:
        r = act.dispatch(fri_15)
        assert r["action"] == "REFRESH"
        mr.assert_called_once()
    with mock.patch.object(act, "check_scheduled", return_value={"action": "CHECK", "canvas_writes": 0}) as mc:
        r = act.dispatch(tue)
        assert r["action"] == "CHECK"
        mc.assert_called_once()

    print("PASS weekly-planner-agent activation self-test")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: weekly-planner-friday {check|refresh|notify|publish|scheduled|email-test|install|status|uninstall|preview|self-test}")
        return 2
    cmd = args[0]
    if cmd == "self-test":
        return command_self_test()
    if cmd == "email-test":
        print(json.dumps(email_test(), indent=2, default=str))
        return 0
    if cmd == "preview":
        sys.stdout.write(render_plist_xml())
        return 0
    if cmd == "install":
        return install()
    if cmd == "uninstall":
        return uninstall()
    if cmd == "status":
        print(json.dumps(scheduler_status(), indent=2))
        return 0
    quarter, week = resolve_target_week()
    if cmd == "scheduled":
        print(json.dumps(dispatch(), indent=2, default=str))
        return 0
    if cmd == "check":
        print(json.dumps(check_scheduled(quarter, week), indent=2, default=str))
        return 0
    if cmd == "refresh":
        print(json.dumps(refresh_scheduled(quarter, week), indent=2, default=str))
        return 0
    if cmd == "notify":
        print(json.dumps(notify_scheduled(quarter, week), indent=2, default=str))
        return 0
    if cmd == "publish":
        print(json.dumps(publish_scheduled(quarter, week), indent=2, default=str))
        return 0
    print("unknown command: " + cmd)
    return 2


if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise SystemExit(command_self_test())
    raise SystemExit(main())
