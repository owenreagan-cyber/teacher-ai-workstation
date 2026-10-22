#!/usr/bin/env python3
"""GC-1: Grade Check quarter scope (fake Canvas reader only, synthetic data).

Covers the quarter filter, quarter boundaries (including the November DST
change), the two course-average paths and their labels, courses not active this
quarter, state across quarters and scope switches, and the --scope CLI default.
No Canvas access, no email, no real student data. State lives in a temp dir.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_grade_check import cli, config, engine, report  # noqa: E402
from scripts.canvas_llm_grade_check import state as state_mod  # noqa: E402
from scripts.canvas_llm_grade_check.reader import (  # noqa: E402
    Assignment,
    AssignmentGroup,
    GradingPeriod,
    Student,
    Submission,
)
from scripts.canvas_llm_grade_check.state import StateStore  # noqa: E402

PASSED = 0


def check(name: str, cond: bool, detail: object = "") -> None:
    global PASSED
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        raise SystemExit(f"FAILED: {name} {detail}")
    PASSED += 1


MATH = 26404
HISTORY = 28165
# "Now" for every scan: Thursday of Q2 week 2, 4 PM New York (EDT).
NOW = dt.datetime(2026, 10, 22, 20, 0, tzinfo=dt.timezone.utc)

# Canvas's real Q1/Q2 grading-period shape (UTC instants for NY midnights).
PERIODS = [
    GradingPeriod(id=374, title="Q1", start_date="2026-07-20T04:00:00Z",
                  end_date="2026-09-19T03:59:59Z"),
    GradingPeriod(id=375, title="Q2", start_date="2026-10-12T04:00:00Z",
                  end_date="2026-12-19T04:59:59Z"),
]

GROUPS = [
    AssignmentGroup(id=1, name="Written Assessments", group_weight=60.0),
    AssignmentGroup(id=2, name="Homework/Class Work", group_weight=20.0),
]

Q1_DUE = "2026-09-10T03:59:59Z"   # Sept 9, Q1
Q2_DUE = "2026-10-16T03:59:59Z"   # Oct 15, Q2, already past
Q2_FUTURE = "2026-12-02T04:59:59Z"  # Dec 1, Q2, not yet due

ASSIGNMENTS = [
    Assignment(id=101, name="SM5: Lesson 10 Homework", due_at=Q1_DUE,
               assignment_group_id=2, points_possible=10),
    Assignment(id=102, name="SM5: Written Assessment 2", due_at=Q1_DUE,
               assignment_group_id=1, points_possible=100),
    Assignment(id=201, name="SM5: Lesson 40 Homework", due_at=Q2_DUE,
               assignment_group_id=2, points_possible=10),
    Assignment(id=202, name="SM5: Written Assessment 5", due_at=Q2_DUE,
               assignment_group_id=1, points_possible=100),
    Assignment(id=203, name="SM5: Lesson 41 Homework", due_at=Q2_DUE,
               assignment_group_id=2, points_possible=10),
    Assignment(id=301, name="SM5: Lesson 70 Homework", due_at=Q2_FUTURE,
               assignment_group_id=2, points_possible=10),
    Assignment(id=401, name="SM5: Reading Log", due_at=None,
               assignment_group_id=2, points_possible=10),
]

# Student 1: missing Q1 homework, low Q1 test, missing one Q2 homework, low Q2
# test, perfect other Q2 homework, blank future homework, blank no-due-date item.
SUBMISSIONS = [
    Submission(id=1, user_id=1, assignment_id=101, grade=None),
    Submission(id=2, user_id=1, assignment_id=102, score=60.0, grade="60"),
    Submission(id=3, user_id=1, assignment_id=201, grade=None),
    Submission(id=4, user_id=1, assignment_id=202, score=70.0, grade="70"),
    Submission(id=5, user_id=1, assignment_id=203, score=10.0, grade="10"),
    Submission(id=6, user_id=1, assignment_id=301, grade=None),
    Submission(id=7, user_id=1, assignment_id=401, grade=None),
]


class FakeCanvas:
    """GET-shaped fake reader. Records calls; has no write methods."""

    def __init__(self, *, periods=None, weighted=False, year_score=95.0,
                 period_scores=None, assignments=None, submissions=None,
                 with_period_api=True):
        self.periods = PERIODS if periods is None else periods
        self.weighted = weighted
        self.year_score = year_score
        self.period_scores = period_scores or {}
        self.assignments = ASSIGNMENTS if assignments is None else assignments
        self.submissions = SUBMISSIONS if submissions is None else submissions
        self.calls: list[tuple] = []
        if not with_period_api:
            self.list_grading_periods = None  # type: ignore[assignment]

    def list_students(self, course_id, grading_period_id=None):
        self.calls.append(("students", course_id, grading_period_id))
        score = (self.period_scores.get(grading_period_id)
                 if grading_period_id is not None else self.year_score)
        return [Student(user_id=1, name="Student Alpha", current_score=score)]

    def list_assignments(self, course_id):
        return list(self.assignments)

    def list_assignment_groups(self, course_id):
        return list(GROUPS)

    def list_submissions(self, course_id):
        return list(self.submissions)

    def list_grading_periods(self, course_id):  # noqa: F811 - may be nulled above
        self.calls.append(("periods", course_id))
        return list(self.periods)

    def course_applies_group_weights(self, course_id):
        return self.weighted


def make_cfg(tmp: str, quarter_subjects=None, subject_keys=("math",)):
    cfg = config.load_config()
    cfg.subjects = {k: v for k, v in cfg.subjects.items() if k in subject_keys}
    cfg.quarter_subjects = quarter_subjects or {1: ("math",), 2: ("math",)}
    cfg.state_directory = tmp
    cfg.state_file = "state.json"
    return cfg


def scan(reader, cfg, quarter, scope, tmp):
    return cli.run_scan(reader, cfg, quarter, StateStore(Path(tmp), "state.json"),
                        scope=scope, now=NOW)


def persist(scan_report, tmp):
    state_mod.write_state(
        StateStore(Path(tmp), "state.json"),
        active_persistent=scan_report.active_persistent,
        resolved_flags=scan_report.merged_resolved,
        one_time_issued=scan_report.merged_issued,
        out_of_scope_flags=scan_report.out_of_scope_persistent,
        not_eligible_flags=scan_report.merged_not_eligible,
    )


def missing_titles(outcome):
    return sorted(e.flag.assignment_title for e in outcome.missing)


def assessment_titles(outcome):
    return sorted(e.flag.assignment_title for e in outcome.low_assessment)


def main() -> int:
    q2 = config.quarter_window(2)

    # --- Quarter filter -----------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        cfg = make_cfg(tmp)
        out_q = scan(FakeCanvas(), cfg, 2, config.SCOPE_QUARTER, tmp).outcome
        out_y = scan(FakeCanvas(), cfg, 2, config.SCOPE_YEAR, tmp).outcome
    check("Q1 homework excluded from missing in Q2 scope",
          "SM5: Lesson 10 Homework" not in missing_titles(out_q))
    check("Q1 homework included in year scope",
          "SM5: Lesson 10 Homework" in missing_titles(out_y))
    check("Q2 past-due homework is missing in Q2 scope",
          missing_titles(out_q) == ["SM5: Lesson 40 Homework"], missing_titles(out_q))
    check("Q1 low test excluded in Q2 scope",
          assessment_titles(out_q) == ["SM5: Written Assessment 5"], assessment_titles(out_q))
    check("Q1 low test included in year scope",
          "SM5: Written Assessment 2" in assessment_titles(out_y))
    check("future assignment never missing (quarter)",
          "SM5: Lesson 70 Homework" not in missing_titles(out_q))
    check("future assignment never missing (year)",
          "SM5: Lesson 70 Homework" not in missing_titles(out_y))
    check("no-due-date assignment left out of quarter scope",
          "SM5: Reading Log" not in missing_titles(out_q))
    check("no-due-date note counts it", out_q.no_due_date == 1, out_q.no_due_date)
    check("out-of-quarter assignments counted", out_q.skipped_assignments == 2,
          out_q.skipped_assignments)
    preview_q = report.render_preview(out_q)
    check("preview has the no-due-date note (count only)",
          "No due date: 1 assignments left out of quarter scope." in preview_q)
    check("no-due-date note names no assignment", "Reading Log" not in preview_q)

    # --- Quarter boundaries -------------------------------------------------
    def in_q2(iso):
        return q2.contains(engine.parse_due_at(iso))

    check("Q2 window is Oct 12 – Dec 18 from instructional weeks",
          (q2.first_day, q2.last_day) == (dt.date(2026, 10, 12), dt.date(2026, 12, 18)))
    check("11:59:59 PM Oct 11 (EDT) is outside Q2", not in_q2("2026-10-12T03:59:59Z"))
    check("midnight Oct 12 (EDT) is inside Q2", in_q2("2026-10-12T04:00:00Z"))
    check("11:59:59 PM Dec 18 (EST, after DST) is inside Q2", in_q2("2026-12-19T04:59:59Z"))
    check("midnight Dec 19 (EST) is outside Q2", not in_q2("2026-12-19T05:00:00Z"))
    check("11:30 PM Dec 18 EST is inside Q2 (a fixed EDT offset would drop it)",
          in_q2("2026-12-19T04:30:00Z"))
    check("Q2 start is EDT, end is EST",
          (q2.start.utcoffset(), q2.end.utcoffset())
          == (dt.timedelta(hours=-4), dt.timedelta(hours=-5)))
    # Windows that start or end on the Nov 1 DST change itself.
    ends_oct31 = config.QuarterWindow(9, dt.date(2026, 10, 26), dt.date(2026, 10, 31))
    starts_nov1 = config.QuarterWindow(9, dt.date(2026, 11, 1), dt.date(2026, 11, 6))
    check("window ending Oct 31 ends at Nov 1 00:00 EDT (04:00Z)",
          ends_oct31.end == dt.datetime(2026, 11, 1, 4, 0, tzinfo=dt.timezone.utc))
    check("Oct 31 11:59:59 PM EDT is inside the Oct window",
          ends_oct31.contains(engine.parse_due_at("2026-11-01T03:59:59Z")))
    check("Nov 1 1:30 AM (first, EDT) is inside the Nov window",
          starts_nov1.contains(engine.parse_due_at("2026-11-01T05:30:00Z")))
    check("Nov 1 00:00 EDT starts the Nov window",
          starts_nov1.start == dt.datetime(2026, 11, 1, 4, 0, tzinfo=dt.timezone.utc))
    check("Oct 31 11:59:59 PM is outside the Nov window",
          not starts_nov1.contains(engine.parse_due_at("2026-11-01T03:59:59Z")))
    part = engine.partition_assignments(ASSIGNMENTS, q2, now=NOW)
    check("partition: in-window / flaggable / no-due / out-of-window",
          ([a.id for a in part.in_window], [a.id for a in part.flaggable],
           [a.id for a in part.no_due_date], [a.id for a in part.out_of_window])
          == ([201, 202, 203, 301], [201, 202, 203], [401], [101, 102]))
    check("header label", q2.label == "Quarter 2 · October 12 – December 18, 2026")
    cross_year = config.QuarterWindow(3, dt.date(2026, 12, 28), dt.date(2027, 1, 8))
    check("cross-year label names both years",
          cross_year.label == "Quarter 3 · December 28, 2026 – January 8, 2027")

    # --- Averages -----------------------------------------------------------
    check("Canvas Q2 grading period matches the instructional-weeks quarter",
          engine.match_grading_period(PERIODS, q2).id == 375)
    check("Q1 period does not match Q2",
          engine.match_grading_period(PERIODS[:1], q2) is None)
    shifted = [GradingPeriod(id=9, title="Q2", start_date="2026-10-05T04:00:00Z",
                             end_date="2026-12-19T04:59:59Z")]
    check("a period with different dates does not match",
          engine.match_grading_period(shifted, q2) is None)

    with tempfile.TemporaryDirectory() as tmp:
        cfg = make_cfg(tmp)
        reader = FakeCanvas(period_scores={375: 80.0}, year_score=95.0)
        out = scan(reader, cfg, 2, config.SCOPE_QUARTER, tmp).outcome
    check("grading-period path asks Canvas for the Q2 period's scores",
          ("students", MATH, 375) in reader.calls, reader.calls)
    check("grading-period path never asks for the full-year score",
          ("students", MATH, None) not in reader.calls, reader.calls)
    check("grading-period average flagged (80, not the year's 95)",
          [e.flag.average for e in out.low_average] == [80.0])
    check("grading-period label on the flag",
          out.low_average[0].flag.average_source == "Canvas grading period Q2")
    check("grading-period label on the course",
          out.courses[0].average_source == "Canvas grading period Q2")
    preview = report.render_preview(out)
    check("preview header names the average source",
          "Course averages: Math — Canvas grading period Q2" in preview)
    check("preview average line names the source",
          "| 80 | Canvas grading period Q2" in preview)

    # Computed, unweighted: Q2 graded = 70/100 + 10/10 = 80/110 = 72.73.
    # (Q1's 60/100 and the ungraded items are left out.)
    with tempfile.TemporaryDirectory() as tmp:
        cfg = make_cfg(tmp)
        out = scan(FakeCanvas(periods=[], weighted=False), cfg, 2,
                   config.SCOPE_QUARTER, tmp).outcome
    check("computed unweighted average", [e.flag.average for e in out.low_average] == [72.73],
          [e.flag.average for e in out.low_average])
    check("computed unweighted label", out.courses[0].average_source == "computed")

    # Computed, weighted: (60 * 0.70 + 20 * 1.00) / 80 = 77.5.
    with tempfile.TemporaryDirectory() as tmp:
        cfg = make_cfg(tmp)
        out = scan(FakeCanvas(periods=shifted, weighted=True), cfg, 2,
                   config.SCOPE_QUARTER, tmp).outcome
    check("computed weighted average", [e.flag.average for e in out.low_average] == [77.5],
          [e.flag.average for e in out.low_average])
    check("computed weighted label",
          out.courses[0].average_source == "computed (weighted groups)")

    # A reader without the grading-period API falls back to computed.
    with tempfile.TemporaryDirectory() as tmp:
        cfg = make_cfg(tmp)
        out = scan(FakeCanvas(with_period_api=False), cfg, 2,
                   config.SCOPE_QUARTER, tmp).outcome
    check("reader without period API -> computed",
          out.courses[0].average_source == "computed")

    check("weighted average ignores zero-weight and ungraded groups",
          engine.computed_average(
              1, ASSIGNMENTS[2:5],
              [AssignmentGroup(id=1, name="A", group_weight=100.0),
               AssignmentGroup(id=2, name="H", group_weight=0.0)],
              SUBMISSIONS, weighted=True) == 70.0)
    check("excused work is not averaged",
          engine.computed_average(
              1, ASSIGNMENTS[3:4], GROUPS,
              [Submission(id=1, user_id=1, assignment_id=202, score=0.0, excused=True)],
              weighted=False) is None)

    # Year scope keeps Canvas's full-year score.
    with tempfile.TemporaryDirectory() as tmp:
        cfg = make_cfg(tmp)
        out = scan(FakeCanvas(year_score=84.0), cfg, 2, config.SCOPE_YEAR, tmp).outcome
    check("year scope uses the full-year current score",
          [e.flag.average for e in out.low_average] == [84.0])
    check("year scope label",
          out.low_average[0].flag.average_source == "Canvas current score (full year)")

    # --- Courses not active this quarter ----------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        cfg = make_cfg(tmp, quarter_subjects={1: ("math", "history"), 2: ("math",)},
                       subject_keys=("math", "history"))
        out_q = scan(FakeCanvas(), cfg, 2, config.SCOPE_QUARTER, tmp).outcome
        out_y = scan(FakeCanvas(), cfg, 2, config.SCOPE_YEAR, tmp).outcome
    check("History left out in Q2 quarter scope",
          [c.course_id for c in out_q.courses] == [MATH])
    check("History included in year scope",
          sorted(c.course_id for c in out_y.courses) == sorted([MATH, HISTORY]))
    check("quarter footer counts the inactive course", out_q.inactive_courses == 1)
    pq = report.render_preview(out_q)
    check("quarter preview body never mentions History", "History" not in pq)
    check("quarter preview has no out-of-scope section",
          "--- OUT OF SCOPE" not in pq)
    check("quarter preview ends with one out-of-scope line",
          sum(1 for ln in pq.splitlines() if ln.startswith("Skipped as out of scope:")) == 1)
    check("quarter header states the scope",
          "Scope: Quarter 2 · October 12 – December 18, 2026" in pq)
    py = report.render_preview(out_y)
    check("year header states the scope", "Scope: Full year" in py)
    check("year preview has no quarter footer", "Skipped as out of scope" not in py)
    body = report.render_email_body(out_q)
    check("email body states the scope",
          "Scope: Quarter 2 · October 12 – December 18, 2026" in body)
    check("email body has the out-of-scope line", "Skipped as out of scope:" in body)

    # --- State --------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        cfg = make_cfg(tmp)
        # Q1 history: a year-style (pre-GC-1) run issued the Q1 flags.
        q1 = scan(FakeCanvas(), cfg, 1, None, tmp)
        persist(q1, tmp)
        q1_missing_key = engine.missing_key(MATH, 1, 101)
        q1_test_key = engine.low_assessment_key(MATH, 1, 102)
        seeded = json.loads((Path(tmp) / "state.json").read_text())
        check("seed: Q1 missing flag active", q1_missing_key in seeded["active_flags"])
        check("seed: Q1 low test issued", q1_test_key in seeded["one_time_issued"])
        # A pre-GC-1 flag has no average_source; strip it to mimic old files.
        for bucket in ("active_flags", "out_of_scope_flags", "resolved_flags"):
            for f in seeded[bucket].values():
                f.pop("average_source", None)
        (Path(tmp) / "state.json").write_text(json.dumps(seeded))
        before = (Path(tmp) / "state.json").read_text()

        # Q2 quarter scope: Q1 flags do not come back as new.
        q2_scan = scan(FakeCanvas(), cfg, 2, config.SCOPE_QUARTER, tmp)
        o = q2_scan.outcome
        new_keys = {e.flag.key for e in o.missing if e.status == report.NEW}
        check("earlier-quarter missing flag not NEW in Q2", q1_missing_key not in new_keys)
        check("earlier-quarter test not re-alerted in Q2",
              q1_test_key not in {e.flag.key for e in o.low_assessment})
        check("earlier-quarter missing flag held out of scope, not resolved",
              q1_missing_key in {f.key for f in o.out_of_scope}
              and q1_missing_key not in {f.key for f in o.resolved})
        check("preview leaves state untouched",
              (Path(tmp) / "state.json").read_text() == before)
        persist(q2_scan, tmp)
        after_q = json.loads((Path(tmp) / "state.json").read_text())
        check("state keeps format version 2", after_q["version"] == state_mod.STATE_VERSION == 2)
        check("Q1 missing flag kept in out_of_scope_flags",
              q1_missing_key in after_q["out_of_scope_flags"])
        check("Q1 issued test kept", q1_test_key in after_q["one_time_issued"])

        # Same quarter again: nothing re-alerts.
        again = scan(FakeCanvas(), cfg, 2, config.SCOPE_QUARTER, tmp).outcome
        check("second Q2 run: no NEW missing",
              all(e.status == report.STILL_ACTIVE for e in again.missing))
        check("second Q2 run: low test not re-alerted", again.low_assessment == [])

        # Switch to year scope: Q1 flag returns as STILL ACTIVE, never NEW.
        yr = scan(FakeCanvas(), cfg, 2, config.SCOPE_YEAR, tmp)
        status = {e.flag.key: e.status for e in yr.outcome.missing}
        check("year after quarter: Q1 missing flag STILL ACTIVE",
              status.get(q1_missing_key) == report.STILL_ACTIVE, status)
        check("year after quarter: Q1 test not re-alerted",
              q1_test_key not in {e.flag.key for e in yr.outcome.low_assessment})
        persist(yr, tmp)
        # And back to quarter scope: state loads, nothing lost or reset.
        back = scan(FakeCanvas(), cfg, 2, config.SCOPE_QUARTER, tmp)
        persist(back, tmp)
        final = json.loads((Path(tmp) / "state.json").read_text())
        check("scope round-trip keeps the Q1 flag",
              q1_missing_key in final["out_of_scope_flags"])
        check("scope round-trip keeps every issued one-time key",
              set(after_q["one_time_issued"]) <= set(final["one_time_issued"]))
        check("loaded flags round-trip",
              StateStore(Path(tmp), "state.json").out_of_scope_flags()[q1_missing_key].key
              == q1_missing_key)

    # --- CLI ----------------------------------------------------------------
    seen: list[str | None] = []
    orig_preview = cli.command_preview
    cli.command_preview = lambda cfg, quarter, **k: seen.append(k.get("scope")) or 0
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            cli.main(["--preview", "--quarter", "2"])
            cli.main(["--preview", "--quarter", "2", "--scope", "year"])
            cli.main(["--preview", "--quarter", "2", "--scope", "quarter"])
    finally:
        cli.command_preview = orig_preview
    check("CLI default scope is quarter", seen[0] == config.SCOPE_QUARTER, seen)
    check("CLI --scope year", seen[1] == config.SCOPE_YEAR, seen)
    check("CLI --scope quarter", seen[2] == config.SCOPE_QUARTER, seen)
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            cli.main(["--preview", "--scope", "semester"])
        rejected = False
    except SystemExit as exc:
        rejected = exc.code == 2
    check("CLI rejects an unknown scope", rejected)
    check("config default scope is quarter", config.load_config().scope == "quarter")

    print(f"PASS GC-1 grade-check scope tests: {PASSED} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
