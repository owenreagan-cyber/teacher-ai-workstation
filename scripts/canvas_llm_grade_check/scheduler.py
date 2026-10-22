#!/usr/bin/env python3
"""Grade Check scheduled automation (macOS launchd LaunchAgent).

Runs the stable Grade Check send workflow on a predictable schedule (Mon-Fri
04:15 PM local time by default) and emails Owen ONLY when something meaningfully
changes (NEW or RESOLVED flags). Unchanged STILL ACTIVE flags are suppressed.

Safety invariants (inherited, unchanged, not re-ordered):
- Recipient safety: only owen.reagan@thalesacademy.org. Never parents,
  guardians, students, other staff, CC, BCC, or second recipients.
- Parent messages remain copy/paste templates only.
- Canvas remains GET-only (CANVAS WRITES PERFORMED: 0).
- Gmail OAuth credentials stay in the existing gitignored config dir; this
  module never duplicates, relocates, reads, or prints any token or secret.
- Quarter/course scope comes from config, never duplicated here.
- Scheduled runs never use --baseline.

This module only generates/inspects/loads a LaunchAgent plist. It performs no
network calls and sends no email.
"""
from __future__ import annotations

import json
import os
import plistlib
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# launchd LaunchAgent identity (single, deduplicated).
LAUNCH_AGENT_LABEL = "com.teacher-ai-workstation.grade-check"
PLIST_FILENAME = f"{LAUNCH_AGENT_LABEL}.plist"

# Repo-local, gitignored log/state paths.
LOG_DIR_REL = ".local/canvas-llm/grade-check/logs"
STDOUT_LOG_REL = LOG_DIR_REL + "/grade-check.out.log"
STDERR_LOG_REL = LOG_DIR_REL + "/grade-check.err.log"

# launchd: 0 and 7 are Sunday, 1 = Monday .. 5 = Friday, 6 = Saturday.
WEEKDAY_NUMBERS = (1, 2, 3, 4, 5)

# Environment whitelist for the scheduled job. Minimal and explicit; contains
# no secrets (OAuth client/refresh tokens are read from the gitignored config
# dir by the workflow itself, never from this plist).
SCHEDULE_ENV = {
    "CANVAS_LLM_GRADE_CHECK_SEND_APPROVED": "1",
    # SMTP fallback, enabled by Owen on 2026-10-21 in the installed agent;
    # kept here so a reinstall does not drop it.
    "CANVAS_LLM_GRADE_CHECK_SMTP_ENABLED": "1",
}

# The scheduled command never uses --baseline.
SCHEDULED_ARGS = ("--send",)

# Keys that can start the job OUTSIDE its calendar schedule. This job sends
# automated email, so an off-schedule start is a safety defect: reloading the
# agent (e.g. on install) must never send a Grade Check report. The plist is
# built calendar-only and any of these keys present is a validation failure.
FORBIDDEN_TRIGGER_KEYS = (
    "KeepAlive",
    "RunAtLoad",
    "StartInterval",
    "StartOnMount",
    "WatchPaths",
    "QueueDirectories",
    "PathState",
    "OtherJobEnabled",
    "NetworkState",
    "SuccessfulExit",
)

# The only allowed automatic trigger.
ALLOWED_TRIGGER_KEY = "StartCalendarInterval"


class ScheduleError(RuntimeError):
    """Raised when the LaunchAgent cannot be generated or managed."""


@dataclass
class InstalledSchedule:
    plist_path: Path
    label: str


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
def plist_path() -> Path:
    """Per-user LaunchAgent path (~/Library/LaunchAgents/<label>.plist)."""
    return Path.home() / "Library" / "LaunchAgents" / PLIST_FILENAME


def log_dir() -> Path:
    return REPO_ROOT / LOG_DIR_REL


def stdout_log_path() -> Path:
    return REPO_ROOT / STDOUT_LOG_REL


def stderr_log_path() -> Path:
    return REPO_ROOT / STDERR_LOG_REL


def python_executable() -> str:
    """Interpreter for the scheduled job.

    Prefers the interpreter running this module (so a venv/homebrew python is
    preserved) and falls back to the launchd-safe system python3.
    """
    exe = sys.executable
    if exe and Path(exe).exists():
        return exe
    return "/usr/bin/python3"


def scheduled_command() -> list[str]:
    """Exact argv for a scheduled run: non-baseline Grade Check send.

    ``bin/grade-check`` is a bash wrapper that execs the Python CLI. launchd
    runs with a minimal environment, so bash and the wrapper path are made
    explicit rather than relying on ``#!/usr/bin/env bash`` PATH resolution.
    """
    return [
        "/bin/bash",
        str(REPO_ROOT / "bin" / "grade-check"),
        *SCHEDULED_ARGS,
    ]


def scheduled_shell_command() -> str:
    """Human-readable one-line equivalent of the scheduled command."""
    return (
        f"cd {REPO_ROOT} && "
        "CANVAS_LLM_GRADE_CHECK_SEND_APPROVED=1 bin/grade-check --send"
    )


# ---------------------------------------------------------------------------
# Plist generation
# ---------------------------------------------------------------------------
def build_plist(cfg=None) -> dict:
    """Build the LaunchAgent plist as a dict.

    Schedule comes from canonical config (never hard-coded here). Contains no
    secrets: only the approval flag, PATH, HOME, log paths, and the repo command.
    """
    if cfg is None:
        from scripts.canvas_llm_grade_check import config as config_mod

        cfg = config_mod.load_config()
    sched = cfg.schedule

    intervals: list[dict[str, int]] = []
    if sched.weekdays_only:
        # One interval per weekday (Mon-Fri) at the configured local time.
        for wd in WEEKDAY_NUMBERS:
            intervals.append({
                "Weekday": wd,
                "Hour": sched.hour_local,
                "Minute": sched.minute_local,
            })
    else:
        intervals.append({"Hour": sched.hour_local, "Minute": sched.minute_local})

    # Minimal explicit environment. PATH is included so the interpreter and
    # git-adjacent tooling resolve; HOME so ~/.config lookup works.
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
        "HOME": str(Path.home()),
    }
    env.update(SCHEDULE_ENV)

    # Calendar-only: StartCalendarInterval is the sole automatic trigger.
    # KeepAlive/RunAtLoad are deliberately ABSENT — see FORBIDDEN_TRIGGER_KEYS.
    plist = {
        "Label": LAUNCH_AGENT_LABEL,
        "ProgramArguments": scheduled_command(),
        "WorkingDirectory": str(REPO_ROOT),
        "EnvironmentVariables": env,
        "StartCalendarInterval": intervals,
        "StandardOutPath": str(stdout_log_path()),
        "StandardErrorPath": str(stderr_log_path()),
        "ProcessType": "Background",
    }
    validate_plist_triggers(plist)
    return plist


def validate_plist_triggers(plist: dict) -> None:
    """Fail closed if the plist can start outside its calendar schedule.

    Raises ScheduleError so a bad definition can never be written or bootstrapped.
    """
    present = [key for key in FORBIDDEN_TRIGGER_KEYS if key in plist]
    if present:
        raise ScheduleError(
            "refusing to install a plist with off-schedule trigger(s): "
            + ", ".join(present)
        )
    intervals = plist.get(ALLOWED_TRIGGER_KEY)
    if not intervals:
        raise ScheduleError(
            f"refusing to install a plist without {ALLOWED_TRIGGER_KEY}"
        )


def audit_plist_triggers(plist: dict) -> tuple[list[str], list[str]]:
    """Inspect an existing plist for off-schedule triggers.

    Returns (problems, notes). Never raises — used for read-only auditing of an
    installed plist that may already be unsafe.
    """
    problems: list[str] = []
    notes: list[str] = []
    for key in FORBIDDEN_TRIGGER_KEYS:
        if key not in plist:
            continue
        value = plist[key]
        if key == "RunAtLoad" and value is False:
            # Explicit false is inert, but the key is still removed from the
            # generated plist; report it as a note rather than a defect.
            notes.append(f"{key} present but set to false")
            continue
        problems.append(f"{key} present ({value!r})")
    if not plist.get(ALLOWED_TRIGGER_KEY):
        problems.append(f"{ALLOWED_TRIGGER_KEY} missing")
    return problems, notes


def render_plist_xml(cfg=None) -> str:
    """Render the LaunchAgent plist as XML text."""
    try:
        return plistlib.dumps(build_plist(cfg)).decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        raise ScheduleError(f"could not render LaunchAgent plist: {exc}") from exc


def command_preview(cfg=None) -> int:
    """Print the plist that would be installed. Installs nothing."""
    sys.stdout.write(render_plist_xml(cfg))
    return 0


# ---------------------------------------------------------------------------
# launchctl interaction (install / status / uninstall)
# ---------------------------------------------------------------------------
def _user_domain() -> str:
    return f"gui/{os.getuid()}"


def _run_launchctl(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["launchctl", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def is_loaded(label: str = LAUNCH_AGENT_LABEL) -> bool:
    """True when launchd currently knows about the agent."""
    res = _run_launchctl(["print", f"{_user_domain()}/{label}"])
    return res.returncode == 0


def install() -> int:
    """Install + load the LaunchAgent for the current user (idempotent).

    Duplicate protection: the plist is written to a single canonical path and
    bootstrapped under one label, so re-running replaces rather than duplicates.
    """
    try:
        cfg = _load_cfg()
    except Exception as exc:  # noqa: BLE001
        print(f"BLOCKER: {exc}")
        return 1

    path = plist_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    log_dir().mkdir(parents=True, exist_ok=True)

    path = plist_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    log_dir().mkdir(parents=True, exist_ok=True)

    # Unload FIRST, while the old definition is still the one on disk. This
    # closes the window where launchd could act on a stale trigger definition
    # against a freshly written file, and guarantees the new definition is what
    # launchd reads when we bootstrap. Only this label is touched.
    if is_loaded():
        _run_launchctl(["bootout", f"{_user_domain()}/{LAUNCH_AGENT_LABEL}"])
        if is_loaded():
            print("BLOCKER: launchctl could not unload the existing agent")
            return 1

    xml = render_plist_xml(cfg)
    # Write atomically so a partial file can never be bootstrapped.
    tmp = path.with_suffix(".plist.tmp")
    tmp.write_text(xml, encoding="utf-8")
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)

    # Re-read the file we just wrote and refuse to load it if it carries any
    # off-schedule trigger. This guards against partial writes and regressions.
    installed = plistlib.loads(path.read_bytes())
    problems, _notes = audit_plist_triggers(installed)
    if problems:
        print("BLOCKER: refusing to load an unsafe LaunchAgent:")
        for problem in problems:
            print(f"  {problem}")
        return 1

    # Validate the on-disk plist with the platform's own linter before loading.
    lint = subprocess.run(
        ["plutil", "-lint", str(path)], capture_output=True, text=True, timeout=30
    )
    if lint.returncode != 0:
        print(f"BLOCKER: plutil -lint rejected the plist: "
              f"{(lint.stderr or lint.stdout or '').strip()}")
        return 1

    res = _run_launchctl(["bootstrap", _user_domain(), str(path)])
    if res.returncode != 0:
        # Some macOS versions prefer the legacy load path.
        legacy = _run_launchctl(["load", "-w", str(path)])
        if legacy.returncode != 0:
            print(f"BLOCKER: launchctl could not load the agent: "
                  f"{(res.stderr or legacy.stderr or '').strip()}")
            return 1

    sched = cfg.schedule
    print("INSTALLED LAUNCH AGENT")
    print(f"  label: {LAUNCH_AGENT_LABEL}")
    print(f"  plist: {path}")
    print(f"  schedule: {_schedule_label(sched)}")
    print(f"  command: {scheduled_shell_command()}")
    print(f"  logs: {log_dir()}")
    print("  loaded: " + ("YES" if is_loaded() else "NO"))
    print(f"  trigger safety: {'PASS' if not problems else 'FAIL'} (calendar-only)")
    print("CANVAS WRITES PERFORMED: 0")
    print("EMAILS SENT: 0")
    return 0


def uninstall() -> int:
    """Remove ONLY the Grade Check scheduler (plist + launchd registration)."""
    path = plist_path()
    removed_plist = False
    removed_agent = False

    if is_loaded():
        res = _run_launchctl(["bootout", f"{_user_domain()}/{LAUNCH_AGENT_LABEL}"])
        if res.returncode != 0:
            legacy = _run_launchctl(["unload", "-w", str(path)])
            removed_agent = legacy.returncode == 0
        else:
            removed_agent = True

    if path.exists():
        path.unlink()
        removed_plist = True

    print("UNINSTALLED GRADE CHECK SCHEDULER")
    print(f"  label: {LAUNCH_AGENT_LABEL}")
    print(f"  launchd registration removed: {'YES' if removed_agent else 'NO'}")
    print(f"  plist removed: {'YES' if removed_plist else 'NO'}")
    print("  other LaunchAgents untouched: YES")
    print("CANVAS WRITES PERFORMED: 0")
    print("EMAILS SENT: 0")
    return 0


def _load_cfg():
    from scripts.canvas_llm_grade_check import config as config_mod

    return config_mod.load_config()


def _schedule_label(sched) -> str:
    days = "Mon–Fri" if sched.weekdays_only else "Every day"
    hour12 = sched.hour_local % 12 or 12
    ampm = "AM" if sched.hour_local < 12 else "PM"
    return f"{days} {hour12}:{sched.minute_local:02d} {ampm} ET"


def _last_exit_status(label: str = LAUNCH_AGENT_LABEL) -> str | None:
    """Parse ``launchctl print`` for the last exit status (never raises)."""
    res = _run_launchctl(["print", f"{_user_domain()}/{label}"])
    if res.returncode != 0:
        return None
    for raw in res.stdout.splitlines():
        line = raw.strip()
        if line.startswith("last exit code"):
            return line.split("=", 1)[-1].strip()
    return None


def _last_run_timestamp() -> str | None:
    """Safest available last-run signal: the newest log file mtime.

    Uses only repo-local gitignored log metadata; never parses log contents and
    never touches grade data.
    """
    candidates = [p for p in (stdout_log_path(), stderr_log_path()) if p.exists()]
    if not candidates:
        return None
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    return datetime.fromtimestamp(newest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def status() -> int:
    """Read-only scheduler + transport readiness report. Sends nothing."""
    from scripts.canvas_llm_grade_check import gmail_transport

    try:
        cfg = _load_cfg()
        sched = cfg.schedule
        sched_label = _schedule_label(sched)
    except Exception as exc:  # noqa: BLE001
        sched_label = f"unknown ({exc})"

    path = plist_path()
    installed = path.exists()
    loaded = is_loaded() if installed else False
    last_exit = _last_exit_status() if loaded else None
    last_run = _last_run_timestamp()
    gmail_ready = bool(gmail_transport.oauth_ready())

    print("GRADE CHECK SCHEDULER")
    print(f"installed: {'YES' if installed else 'NO'}")
    print(f"loaded: {'YES' if loaded else 'NO'}")
    print(f"schedule: {sched_label}")
    print(f"plist: {path}")
    print(f"command: {scheduled_shell_command()}")
    print(f"last exit status: {last_exit if last_exit is not None else 'unavailable'}")
    print(f"last run timestamp: {last_run if last_run else 'unavailable'}")
    print(f"Gmail transport ready: {'YES' if gmail_ready else 'NO'}")
    print("CANVAS WRITES PERFORMED: 0")
    print("EMAILS SENT: 0")
    return 0


def run_now() -> int:
    """Trigger one scheduled-equivalent run through the same safety gates.

    Executes the exact non-baseline ``bin/grade-check --send`` command with the
    approval flag set, so all recipient/sender/transactional gates still apply.
    """
    env = dict(os.environ)
    env.update(SCHEDULE_ENV)
    log_dir().mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        scheduled_command(),
        cwd=str(REPO_ROOT),
        env=env,
        timeout=1800,
    )
    return res.returncode


def command_self_test() -> int:
    """Deterministic scheduler tests. Installs nothing, sends nothing."""
    cfg = _load_cfg()
    sched = cfg.schedule

    # Schedule comes from config and is the expected weekday 4:15 PM.
    assert sched.weekdays_only is True
    assert sched.hour_local == 16 and sched.minute_local == 15
    assert _schedule_label(sched) == "Mon–Fri 4:15 PM ET"

    plist = build_plist(cfg)
    assert plist["Label"] == LAUNCH_AGENT_LABEL

    # Mon-Fri only: exactly five intervals, weekdays 1-5, never weekend.
    intervals = plist["StartCalendarInterval"]
    assert isinstance(intervals, list) and len(intervals) == 5
    weekdays = sorted(i["Weekday"] for i in intervals)
    assert weekdays == [1, 2, 3, 4, 5], weekdays
    assert 0 not in weekdays and 6 not in weekdays and 7 not in weekdays
    for i in intervals:
        assert i["Hour"] == 16 and i["Minute"] == 15

    # Calendar-only: NO off-schedule trigger key may be emitted. This is the
    # guard for the defect that let a reload fire an unapproved email send.
    for key in FORBIDDEN_TRIGGER_KEYS:
        assert key not in plist, f"plist must not emit off-schedule trigger {key!r}"

    # validate_plist_triggers fails closed on each forbidden key.
    for key in FORBIDDEN_TRIGGER_KEYS:
        bad = dict(plist)
        bad[key] = {"SuccessfulExit": False} if key == "KeepAlive" else True
        try:
            validate_plist_triggers(bad)
            raise AssertionError(f"validator must reject {key}")
        except ScheduleError:
            pass
    # ...and on a missing calendar trigger.
    try:
        validate_plist_triggers({"Label": LAUNCH_AGENT_LABEL})
        raise AssertionError("validator must reject a missing calendar trigger")
    except ScheduleError:
        pass
    # The real plist passes.
    validate_plist_triggers(plist)

    # audit_plist_triggers flags the exact historical defect...
    _probs, _notes = audit_plist_triggers(
        {"StartCalendarInterval": intervals, "KeepAlive": {"SuccessfulExit": False}})
    assert any("KeepAlive" in p for p in _probs), _probs
    # ...and treats explicit RunAtLoad:false as a note, not a defect.
    _probs, _notes = audit_plist_triggers(
        {"StartCalendarInterval": intervals, "RunAtLoad": False})
    assert _probs == [] and any("RunAtLoad" in n for n in _notes), (_probs, _notes)
    # A clean calendar-only plist audits clean.
    _probs, _notes = audit_plist_triggers(plist)
    assert _probs == [] and _notes == [], (_probs, _notes)

    # Scheduled command invokes the bash wrapper directly, never via python.
    args = plist["ProgramArguments"]
    assert args[0] in ("/bin/bash", "/bin/sh"), args[0]
    assert args[1].endswith("bin/grade-check")
    assert "--send" in args
    assert "--baseline" not in args
    assert "--preview" not in args
    assert "--baseline" not in scheduled_shell_command()
    # The Python interpreter must never be used to run the bash wrapper.
    assert "python" not in args[0].lower()

    # Approval flag present; no secrets anywhere in the plist.
    env = plist["EnvironmentVariables"]
    assert env["CANVAS_LLM_GRADE_CHECK_SEND_APPROVED"] == "1"
    # SMTP fallback enabled 2026-10-21; a reinstall must keep it.
    assert env["CANVAS_LLM_GRADE_CHECK_SMTP_ENABLED"] == "1"
    xml = render_plist_xml(cfg)
    lowered = xml.lower()
    for forbidden in (
        "refresh_token", "access_token", "client_secret", "client_id",
        "password", "smtp_password", "secret",
    ):
        assert forbidden not in lowered, f"plist must not contain {forbidden!r}"

    # OAuth credential paths are unchanged (not duplicated or relocated).
    assert str(gmail_oauth_dir()) == str(
        Path.home() / ".config" / "teacher-ai-workstation" / "grade-check-oauth"
    )
    assert "grade-check-oauth" not in xml
    # The real transport module must agree with that path.
    from scripts.canvas_llm_grade_check import gmail_transport as _gt_real

    assert _gt_real.CONFIG_DIR == gmail_oauth_dir()
    assert _gt_real.TOKEN_FILE.parent == gmail_oauth_dir()

    # Logs are repo-local and gitignored.
    assert ".local/canvas-llm/grade-check/logs" in str(plist["StandardOutPath"])
    assert plist["StandardOutPath"] == str(stdout_log_path())

    # Single canonical plist path => duplicate install protection.
    assert plist_path().name == PLIST_FILENAME
    assert plist_path().parent == Path.home() / "Library" / "LaunchAgents"

    # Uninstall targets only the Grade Check label/path.
    assert LAUNCH_AGENT_LABEL == "com.teacher-ai-workstation.grade-check"
    assert SCHEDULED_ARGS == ("--send",)

    print("PASS grade-check scheduler self-test")
    return 0


def gmail_oauth_dir() -> Path:
    """The existing (unchanged) OAuth config dir.

    Declared as a literal so the regression assertion cannot be made vacuous by a
    test-injected mock in ``sys.modules``.
    """
    return Path.home() / ".config" / "teacher-ai-workstation" / "grade-check-oauth"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    usage = (
        "usage: bin/grade-check-schedule "
        "{install|status|run-now|uninstall|preview|self-test}"
    )
    if not args:
        print(usage)
        return 2
    cmd = args[0]
    if cmd == "install":
        return install()
    if cmd == "status":
        return status()
    if cmd == "run-now":
        return run_now()
    if cmd == "uninstall":
        return uninstall()
    if cmd == "preview":
        return command_preview()
    if cmd == "self-test":
        return command_self_test()
    print(usage)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
