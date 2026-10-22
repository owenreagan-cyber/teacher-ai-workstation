#!/usr/bin/env python3
"""bin/grade-check entry point.

Modes:
- --preview   live GET-only scan + teacher review report (never emails)
- --send      fresh scan, then send the consolidated report to Owen only
              (gated: requires explicit approval + SMTP config)
- --self-test deterministic tests using synthetic data only

The workflow is read-only against Canvas grades. It NEVER modifies grades,
assignments, submissions, or student records, and NEVER emails parents.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_grade_check import (  # noqa: E402
    config,
    emailer,
    engine,
    reader,
    report,
    state as state_mod,
)
from scripts.canvas_llm_grade_check.config import ConfigError  # noqa: E402
from scripts.canvas_llm_grade_check.reader import ReaderError  # noqa: E402
from scripts.canvas_llm_grade_check.state import StateStore  # noqa: E402

from dataclasses import dataclass, field  # noqa: E402


@dataclass
class ScanReport:
    """A completed scan plus the persistence payload to commit after send."""

    outcome: report.ScanOutcome
    active_persistent: dict[str, engine.Flag] = field(default_factory=dict)
    out_of_scope_persistent: dict[str, engine.Flag] = field(default_factory=dict)
    merged_resolved: dict[str, engine.Flag] = field(default_factory=dict)
    merged_not_eligible: dict[str, engine.Flag] = field(default_factory=dict)
    merged_issued: set[str] = field(default_factory=set)


def _load_eligibility_overrides(
    cfg: config.GradeCheckConfig, course_id: int
) -> dict[int, str]:
    """Load local late-enrollment eligibility overrides for one course.

    Reads ``.local/canvas-llm/grade-check/enrollment-overrides.json`` (gitignored).
    Returns a mapping of ``student_id -> eligible_from`` for the given course.
    Never raises on a missing/unreadable store; an absent override just means
    Canvas enrollment metadata governs.
    """
    from scripts.canvas_llm_grade_check import enrollment_overrides as eo

    return eo.eligible_from_map_for_course(cfg, course_id)


def _quarter_students(
    grade_reader: reader.GradeReader,
    subject: config.SubjectConfig,
    window: config.QuarterWindow,
    in_window: list[reader.Assignment],
    groups: list[reader.AssignmentGroup],
    submissions: list[reader.Submission],
) -> tuple[list[reader.Student], str]:
    """Students carrying quarter averages, plus where those averages came from.

    Preferred: Canvas's own score for the grading period that matches the
    quarter. Otherwise the average is computed from in-quarter graded scores.
    """
    list_periods = getattr(grade_reader, "list_grading_periods", None)
    periods = list_periods(subject.course_id) if list_periods is not None else []
    period = engine.match_grading_period(periods, window)
    if period is not None:
        students = grade_reader.list_students(subject.course_id, grading_period_id=period.id)
        return students, f"Canvas grading period {period.title or period.id}"

    students = grade_reader.list_students(subject.course_id)
    uses_weights = getattr(grade_reader, "course_applies_group_weights", None)
    weighted = bool(uses_weights(subject.course_id)) if uses_weights is not None else False
    computed = [
        replace(
            s,
            current_score=engine.computed_average(
                s.user_id, in_window, groups, submissions, weighted=weighted
            ),
            final_score=None,
        )
        for s in students
    ]
    return computed, "computed (weighted groups)" if weighted else "computed"


def run_scan(
    grade_reader: reader.GradeReader,
    cfg: config.GradeCheckConfig,
    quarter: int,
    store: StateStore,
    *,
    scope: str | None = None,
    now: dt.datetime | None = None,
) -> ScanReport:
    """Scan subjects and reconcile against state.

    ``scope`` (GC-1):
    - ``"quarter"``: only the quarter's active subjects; missing and low-score
      flags only on assignments due inside the quarter and already past; course
      averages for the quarter (Canvas grading period, else computed).
    - ``"year"``: every configured subject, every assignment, Canvas's
      full-year current score.
    - ``None``: the pre-GC-1 library behavior (quarter's active subjects, every
      assignment, full-year score), kept for older callers. The CLI always
      passes an explicit scope.

    This function is side-effect free: it never persists state. Persistence is
    the caller's decision — preview never persists, and send persists only after
    a confirmed successful email.
    """
    if scope is not None and scope not in config.SCOPES:
        raise ConfigError(f"invalid scope {scope!r}")
    window = config.quarter_window(quarter) if scope == config.SCOPE_QUARTER else None
    state = store.load()
    prev_active = {k: engine.flag_from_dict(v) for k, v in state["active_flags"].items()}
    prev_out_of_scope = {
        k: engine.flag_from_dict(v) for k, v in state.get("out_of_scope_flags", {}).items()
    }
    prev_resolved = {k: engine.flag_from_dict(v) for k, v in state["resolved_flags"].items()}
    prev_not_eligible = {
        k: engine.flag_from_dict(v) for k, v in state.get("not_eligible_flags", {}).items()
    }
    issued = set(state["one_time_issued"].keys())

    # A course returning to scope must re-evaluate its out-of-scope flags, so
    # previous persistent = active ∪ out_of_scope for reconciliation.
    previous_persistent = {**prev_out_of_scope, **prev_active}
    if scope == config.SCOPE_YEAR:
        subjects = config.all_subjects(cfg)
    else:
        subjects = config.active_subjects(cfg, quarter)
    active_ids = {s.course_id for s in subjects}

    course_summaries: list[report.CourseScanSummary] = []
    current_persistent: dict[str, engine.Flag] = {}
    current_one_time: list[engine.Flag] = []
    unresolved_all: list[engine.UnresolvedItem] = []
    ineligible_keys: set[str] = set()
    # Quarter scope bookkeeping: assignments left out, by (course, assignment).
    out_of_window: set[tuple[int, int]] = set()
    no_due_date_count = 0
    # Past-due assignments with no entered grade yet, by (course, assignment).
    not_graded: set[tuple[int, int]] = set()

    for subject in subjects:
        assignments = grade_reader.list_assignments(subject.course_id)
        groups = grade_reader.list_assignment_groups(subject.course_id)
        submissions = grade_reader.list_submissions(subject.course_id)
        average_source: str | None = None
        if window is not None:
            part = engine.partition_assignments(assignments, window, now=now)
            no_due_date_count += len(part.no_due_date)
            out_of_window |= {
                (subject.course_id, a.id) for a in (*part.out_of_window, *part.no_due_date)
            }
            in_window_ids = {a.id for a in part.in_window}
            submissions = [s for s in submissions if s.assignment_id in in_window_ids]
            students, average_source = _quarter_students(
                grade_reader, subject, window, part.in_window, groups, submissions
            )
            assignments = part.flaggable
        else:
            students = grade_reader.list_students(subject.course_id)
            if scope == config.SCOPE_YEAR:
                average_source = "Canvas current score (full year)"
        eligibility = _load_eligibility_overrides(cfg, subject.course_id)
        res = engine.scan_subject(
            subject, students, assignments, groups, submissions, cfg,
            now=now,
            eligibility_overrides=eligibility,
            average_source=average_source,
        )
        course_summaries.append(
            report.CourseScanSummary(
                subject.display_name, subject.course_id, res.students_scanned,
                average_source=average_source,
            )
        )
        for f in res.missing_flags:
            current_persistent[f.key] = f
        for f in res.low_average_flags:
            current_persistent[f.key] = f
        current_one_time.extend(res.low_assessment_flags)
        unresolved_all.extend(res.unresolved)
        ineligible_keys |= res.ineligible_missing_keys
        ineligible_keys |= res.ineligible_average_keys
        not_graded |= {(subject.course_id, aid) for aid in res.not_graded_assignment_ids}

    # A stored flag on an assignment that is not graded yet is held silently:
    # not reported, not resolved, kept in state so it returns as STILL ACTIVE
    # (not NEW) once grading starts.
    held_not_graded = {
        k: f for k, f in previous_persistent.items()
        if f.assignment_id is not None and (f.course_id, f.assignment_id) in not_graded
    }
    previous_persistent = {
        k: f for k, f in previous_persistent.items() if k not in held_not_graded
    }

    # Earlier-quarter flags on assignments outside this quarter are held as
    # out of scope, never resolved, so a later year view still sees them.
    out_of_scope_keys = {
        k for k, f in previous_persistent.items()
        if f.assignment_id is not None and (f.course_id, f.assignment_id) in out_of_window
    }
    rec = engine.reconcile(
        previous_persistent, current_persistent, current_one_time, issued,
        active_ids, ineligible_keys, out_of_scope_keys,
    )

    new_keys = {f.key for f in rec.new}
    missing_entries: list[report.ReportEntry] = []
    low_average_entries: list[report.ReportEntry] = []
    for f in rec.active_persistent:
        status = report.NEW if f.key in new_keys else report.STILL_ACTIVE
        entry = report.ReportEntry(f, status)
        if f.flag_type == engine.MISSING_ASSIGNMENT:
            missing_entries.append(entry)
        else:
            low_average_entries.append(entry)
    low_assessment_entries = [report.ReportEntry(f, report.NEW) for f in rec.new_one_time]

    def _sort_key(entry: report.ReportEntry) -> tuple[str, str, str]:
        return (
            entry.flag.student_name.lower(),
            entry.flag.course_name,
            entry.flag.assignment_title or "",
        )

    missing_entries.sort(key=_sort_key)
    low_average_entries.sort(key=_sort_key)
    low_assessment_entries.sort(key=_sort_key)

    outcome = report.ScanOutcome(
        quarter=quarter,
        courses=course_summaries,
        missing=missing_entries,
        low_assessment=low_assessment_entries,
        low_average=low_average_entries,
        resolved=rec.resolved,
        out_of_scope=rec.out_of_scope,
        not_eligible=rec.not_eligible,
        unresolved=unresolved_all,
        scope=scope or config.SCOPE_YEAR,
        scope_label=(
            config.scope_label(scope, window) if scope is not None else None
        ),
        skipped_assignments=len(out_of_window) - no_due_date_count,
        no_due_date=no_due_date_count,
        not_graded_skipped=(
            len(not_graded) if getattr(cfg, "missing_requires_graded", True) else None
        ),
        inactive_courses=(
            len(config.all_subject_course_ids(cfg) - active_ids)
            if scope == config.SCOPE_QUARTER else 0
        ),
    )

    active_persistent = {f.key: f for f in rec.active_persistent}
    out_of_scope_persistent = {f.key: f for f in rec.out_of_scope}
    out_of_scope_persistent.update(held_not_graded)
    merged_resolved = dict(prev_resolved)
    for f in rec.resolved:
        merged_resolved[f.key] = f
    merged_not_eligible = dict(prev_not_eligible)
    for f in rec.not_eligible:
        merged_not_eligible[f.key] = f
    merged_issued = issued | {f.key for f in rec.new_one_time}

    return ScanReport(
        outcome=outcome,
        active_persistent=active_persistent,
        out_of_scope_persistent=out_of_scope_persistent,
        merged_resolved=merged_resolved,
        merged_not_eligible=merged_not_eligible,
        merged_issued=merged_issued,
    )


def _build_reader() -> reader.LiveGradeReader:
    return reader.LiveGradeReader.from_env()


def command_preview(
    cfg: config.GradeCheckConfig,
    quarter: int,
    *,
    details: bool = False,
    parent_templates: bool = False,
    scope: str | None = None,
) -> int:
    grade_reader = _build_reader()
    store = StateStore(cfg.state_directory, cfg.state_file)
    # Review-only: never persists state, so a later --send still surfaces
    # every one-time low-assessment flag as NEW.
    scan = run_scan(grade_reader, cfg, quarter, store, scope=scope)
    if parent_templates:
        print(report.render_parent_templates(scan.outcome, writes=0, emails=0))
    else:
        print(report.render_preview(scan.outcome, writes=0, emails=0, details=details))
    return 0


def _log_run_summary(
    outcome: report.ScanOutcome,
    quarter: int,
    *,
    email_sent: bool,
    blocker: str | None,
    state_directory: str | None = None,
) -> None:
    """Append one safe operational line to the gitignored scheduler log.

    Logs only: timestamp, quarter, courses scanned, summary counts, whether an
    email was sent, and a blocker summary. Never logs tokens, client secrets,
    SMTP passwords, gradebook exports, or student IDs. Logging failures are
    non-fatal — a log write must never block or alter a send decision.

    The log path derives from the caller's state directory so an isolated
    (e.g. temporary test) state store also gets an isolated log; production
    defaults to ``.local/canvas-llm/grade-check/logs``.
    """
    try:
        base = Path(state_directory) if state_directory else (REPO_ROOT / ".local" / "canvas-llm" / "grade-check")
        if not base.is_absolute():
            base = REPO_ROOT / base
        log_dir = base / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": state_mod.utc_now(),
            "quarter": f"Q{quarter}",
            "scope": outcome.scope,
            "courses_scanned": [c.name for c in outcome.courses],
            "students_scanned": outcome.total_students,
            "counts": {
                "missing_new": sum(1 for e in outcome.missing if e.status == report.NEW),
                "missing_still_active": sum(
                    1 for e in outcome.missing if e.status == report.STILL_ACTIVE
                ),
                "missing_resolved": len([
                    f for f in outcome.resolved
                    if f.flag_type == engine.MISSING_ASSIGNMENT
                ]),
                "assessment_new": len(outcome.low_assessment),
                "average_still_active": sum(
                    1 for e in outcome.low_average if e.status == report.STILL_ACTIVE
                ),
                "average_resolved": len([
                    f for f in outcome.resolved
                    if f.flag_type == engine.LOW_COURSE_AVERAGE
                ]),
                "unresolved": len(outcome.unresolved),
            },
            "email_sent": email_sent,
            "blocker": blocker or None,
        }
        with (log_dir / "grade-check.runs.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    except Exception:  # noqa: BLE001
        # Logging must never break a run.
        pass


def command_send(
    cfg: config.GradeCheckConfig,
    quarter: int,
    *,
    baseline: bool = False,
    scope: str | None = None,
) -> int:
    """Fresh scan -> attempt email -> persist state ONLY on confirmed send.

    Transactional safeguard: if the email fails, nothing is persisted — one-time
    assessment flags are not consumed, persistent flags are not advanced, and
    last-send metadata is not written. The next run reproduces the same report.
    """
    grade_reader = _build_reader()
    store = StateStore(cfg.state_directory, cfg.state_file)

    # 1. Fresh live GET-only scan (no persistence yet).
    scan = run_scan(grade_reader, cfg, quarter, store, scope=scope)
    outcome = scan.outcome

    if not outcome.has_any_flag and cfg.suppress_empty_report:
        print("No active/new flags — clean-report email suppressed.")
        print("CANVAS WRITES PERFORMED: 0")
        print("EMAILS SENT: 0")
        return 0

    # Meaningful-change gate: when every active flag is unchanged STILL ACTIVE
    # and nothing is NEW or RESOLVED, there is nothing new to report. The
    # terminal preview still shows the persistent flags for context; no email is
    # sent. One-time assessment alerts are always NEW, so they always qualify.
    # The explicit --baseline run is a deliberate one-off and is not gated.
    if (not baseline and cfg.suppress_unchanged_report and not outcome.has_change):
        print("No NEW or RESOLVED flags — unchanged STILL ACTIVE only; email suppressed.")
        print(
            "STILL ACTIVE flags for context: "
            f"missing={sum(1 for e in outcome.missing if e.status == report.STILL_ACTIVE)}, "
            f"average={sum(1 for e in outcome.low_average if e.status == report.STILL_ACTIVE)}"
        )
        _log_run_summary(outcome, quarter, email_sent=False, blocker=None,
                         state_directory=cfg.state_directory)
        print("CANVAS WRITES PERFORMED: 0")
        print("EMAILS SENT: 0")
        return 0

    # 2. Compose the exact report.
    subject = report.BASELINE_SUBJECT if baseline else cfg.report_subject
    body = (
        report.render_baseline_email_body(outcome)
        if baseline
        else report.render_email_body(outcome)
    )

    # 3. Attempt email send.
    result = emailer.send_teacher_report(
        subject=subject,
        body=body,
        recipient=cfg.recipient_email,
    )

    print("CANVAS WRITES PERFORMED: 0")
    if not result.sent:
        # 4a. Send failed: do NOT consume flags or advance state.
        print("EMAILS SENT: 0")
        print(f"EMAIL BLOCKER: {result.reason}")
        print("STATE PERSISTED: 0 (transactional safeguard — state unchanged)")
        _log_run_summary(outcome, quarter, email_sent=False, blocker=result.reason,
                         state_directory=cfg.state_directory)
        return 1

    # 4b. Send succeeded: persist one-time issued + persistent active state +
    #     last-send metadata, atomically.
    last_send = {
        "sent_at": state_mod.utc_now(),
        "scope": outcome.scope,
        "subject": subject,
        "recipient": result.recipients,
        "missing_flags": len(outcome.missing),
        "assessment_flags": len(outcome.low_assessment),
        "average_flags": len(outcome.low_average),
    }
    state_mod.write_state(
        store,
        active_persistent=scan.active_persistent,
        resolved_flags=scan.merged_resolved,
        one_time_issued=scan.merged_issued,
        out_of_scope_flags=scan.out_of_scope_persistent,
        not_eligible_flags=scan.merged_not_eligible,
        last_send=last_send,
    )

    print("EMAILS SENT: 1")
    print(f"SENT to: {result.recipients}")
    print("STATE PERSISTED: 1 (one-time issued + active persistent + last-send metadata)")
    _log_run_summary(outcome, quarter, email_sent=True, blocker=None,
                     state_directory=cfg.state_directory)
    return 0


def command_self_test() -> int:
    from scripts.canvas_llm_grade_check import report as report_mod
    from scripts.canvas_llm_grade_check import templates
    from scripts.canvas_llm_grade_check import gmail_transport
    from scripts.canvas_llm_grade_check import scheduler
    from scripts.canvas_llm_grade_check import health as health_mod
    from scripts.canvas_llm_grade_check import enrollment_overrides

    config.command_self_test()
    reader.command_self_test()
    engine.command_self_test()
    state_mod.command_self_test()
    enrollment_overrides.command_self_test()
    templates.command_self_test()
    report_mod.command_self_test()
    emailer.command_self_test()
    gmail_transport.command_self_test()
    scheduler.command_self_test()
    health_mod.command_self_test()
    print("PASS grade-check CLI self-test")
    return 0


def command_transport_check(cfg: config.GradeCheckConfig) -> int:
    """Read-only transport/OAuth readiness check. Never sends an email."""
    from scripts.canvas_llm_grade_check import gmail_transport

    ready = gmail_transport.oauth_ready()
    smtp_on = emailer._smtp_enabled()
    selected = emailer._select_transport()
    print("GMAIL OAUTH/API TRANSPORT")
    print(f"  OAuth credentials configured (client_secret.json + token.json): "
          f"{'YES' if ready else 'NO'}")
    print(f"  Selected transport: {selected}")
    print(f"  SMTP fallback enabled: {'YES' if smtp_on else 'NO (disabled by default)'}")
    print(f"  Sender allowlist: {emailer.ALLOWED_SENDER}")
    print(f"  Recipient allowlist: {emailer.ALLOWED_RECIPIENT}")
    print("CANVAS WRITES PERFORMED: 0")
    print("EMAILS SENT: 0")
    if not ready and not smtp_on:
        print("BLOCKERS: no email transport ready (OAuth not configured; SMTP disabled)")
        return 1
    return 0


def command_oauth_status() -> int:
    """Read-only OAuth readiness report (never sends, never prints secrets)."""
    from scripts.canvas_llm_grade_check import gmail_transport

    for line in gmail_transport.oauth_status_lines():
        print(line)
    print("EMAILS SENT: 0")
    print("CANVAS WRITES PERFORMED: 0")
    status = gmail_transport.oauth_status()
    if status["gmail_transport_ready"]:
        return 0
    return 1


def command_oauth_setup() -> int:
    """One-time interactive OAuth authorization (never prints secrets)."""
    from scripts.canvas_llm_grade_check import gmail_transport

    rc = gmail_transport.run_oauth_setup()
    # Report accounts safety + email counts (no email is sent during setup).
    print("EMAILS SENT: 0")
    print("CANVAS WRITES PERFORMED: 0")
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canvas Grade Check / Teacher Alert (read-only)")
    parser.add_argument("--preview", action="store_true", help="live scan + review report, no email")
    parser.add_argument("--details", action="store_true",
                        help="with --preview: expanded metadata + parent templates + per-student detail")
    parser.add_argument("--parent-templates", action="store_true",
                        help="with --preview: print copy/paste parent drafts only (no send)")
    parser.add_argument("--send", action="store_true", help="scan then email the report to Owen only")
    parser.add_argument("--baseline", action="store_true", help="send the initial-baseline report")
    parser.add_argument("--transport-check", action="store_true",
                        help="report Gmail OAuth transport readiness (no email sent)")
    parser.add_argument("--oauth-status", action="store_true",
                        help="report OAuth credential/token readiness (no email sent)")
    parser.add_argument("--oauth-setup", action="store_true",
                        help="one-time OAuth authorization (no email sent)")
    parser.add_argument("--quarter", type=int, help="explicit quarter (1-4); auto-detected otherwise")
    parser.add_argument("--scope", choices=config.SCOPES, default=None,
                        help="quarter (default, from config) or year (full-year view)")
    parser.add_argument("--self-test", action="store_true", help="run deterministic self-tests")
    args = parser.parse_args(argv)

    if args.self_test:
        return command_self_test()
    if args.preview and args.send:
        print("BLOCKER: --preview and --send are mutually exclusive")
        return 2

    try:
        cfg = config.load_config()
        quarter = config.resolve_quarter(explicit_quarter=args.quarter)
        scope = args.scope or cfg.scope
    except ConfigError as exc:
        print(f"BLOCKER: {exc}")
        return 1

    try:
        if args.oauth_status:
            return command_oauth_status()
        if args.oauth_setup:
            return command_oauth_setup()
        if args.transport_check:
            return command_transport_check(cfg)
        if args.send:
            return command_send(cfg, quarter, baseline=args.baseline, scope=scope)
        return command_preview(cfg, quarter, details=args.details,
                               parent_templates=args.parent_templates, scope=scope)
    except (ReaderError, ConfigError) as exc:
        print(f"BLOCKER: {exc}")
        print("CANVAS WRITES PERFORMED: 0")
        print("EMAILS SENT: 0")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
