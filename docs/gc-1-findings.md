# GC-1 Findings — Grade Check reports scoped to the current quarter

```text
Branch: feature/gc-1 (worktree ~/Projects/taw-gc1), from origin/main
Prompt: docs/prompts/PROMPT-GC-1.md
Date: 2026-10-22
Canvas: GET only. No Canvas writes, no grade changes, no email sent.
```

## 1. What the tool did before GC-1

### Which assignments were scanned

- Every assignment in every course the quarter's rotation marks active
  (`config.active_subjects`, from `quarters` in `grade-check-config.json`: the
  three core courses every quarter, History in Q1/Q3, Science in Q2/Q4).
- `reader.list_assignments` fetched all of a course's assignments with no date or
  grading-period filter, and `list_submissions` fetched every submission. Nothing
  was limited to the current quarter.

### How missing and low-score flags were chosen

- **Missing** (`engine.scan_subject`): the assignment's due date has passed
  (`due_at <= now`), and the student has no real grade (blank, or an `MI`/`MISSING`
  marker). A numeric 0 is a grade. Excused work is never missing. An assignment
  with no due date is never missing. This applied to assignments from any point in
  the year, so Q1 homework still showed as missing in Q2.
- **Low score**: any scored submission at or below 85 on an assignment classified
  as an assessment (assessment group, or a test keyword in the title when the
  group is unknown). There was **no due-date check**, so Q1 tests, future tests,
  and tests with no due date all counted. Low scores are one-time alerts keyed by
  course + student + assignment.

### Where course averages came from

- The enrollment's `grades.current_score` (falling back to `final_score`) from
  `GET /courses/:id/enrollments?include[]=grades`.
- **No `grading_period_id` was passed.** Per the Canvas API, the enrollment grades
  without `grading_period_id` are the course total across grading periods, so the
  "course average" was effectively the year-to-date average, not the quarter's.
  (I could not pull live enrollment scores to compare; see section 6.)
- A low average needs at least one real graded submission, so a student with no
  graded work is never flagged.

### Out-of-quarter courses and late enrollments

- A course not active this quarter (History in Q2) was not scanned. Its flags in
  `state.json` moved to the `out_of_scope_flags` bucket, marked "OUT OF SCOPE —
  NOT RESOLVED", and **listed by student name** in an "OUT OF SCOPE (QUARTER
  ROTATION)" section of the preview and email.
- Late enrollment: a student's eligibility date is the enrollment `start_at`, else
  `created_at`, or a local override in
  `.local/canvas-llm/grade-check/enrollment-overrides.json`. Work due before that
  date is never flagged, and a stale flag is retracted as `NOT_ELIGIBLE`, not
  resolved.

### How `state.json` tracks issued flags

- `.local/canvas-llm/grade-check/state.json` (gitignored), `version: 2`. Buckets:
  `active_flags`, `out_of_scope_flags`, `not_eligible_flags`, `resolved_flags`,
  `one_time_issued`, plus `last_scan_at` and `last_send`.
- Keys are IDs only: `course:student:assignment:TYPE` for missing and low-score
  flags, and `course:student:LOW_COURSE_AVERAGE` for averages.
- `one_time_issued` only grows, so a low score alerts once.
- `--preview` never writes state. `--send` writes state only after a confirmed
  successful email (atomic tmp file + rename).

## 2. Canvas grading periods: they exist and match

All five Grade Check courses (Reading/Spelling 26442, Math 26404, Language Arts
28171, History 28165, Science 28166) share grading-period group 328 (term 409).
Read with `GET /courses/:id/grading_periods` on 2026-10-22.

| Period | Canvas id | Canvas start (UTC) | Canvas end (UTC) | New York dates | Instructional weeks | Match |
| --- | --- | --- | --- | --- | --- | --- |
| Q1 | 374 | 2026-07-20T04:00Z | 2026-09-19T03:59:59Z | Jul 20 – Sep 18, 2026 | Jul 20 – Sep 18 | yes |
| Q2 | 375 | 2026-10-12T04:00Z | 2026-12-19T04:59:59Z | Oct 12 – Dec 18, 2026 | Oct 12 – Dec 18 | yes |
| Q3 | 376 | 2027-01-11T05:00Z | 2027-03-13T04:59:59Z | Jan 11 – Mar 12, 2027 | Jan 11 – Mar 12 | yes |
| Q4 | 377 | 2027-04-05T04:00Z | 2027-06-12T03:59:59Z | Apr 5 – Jun 11, 2027 | Apr 5 – Jun 11 | yes |

Every period starts at local midnight on the quarter's first day and ends at
11:59:59 PM local on its last day, matching the instructional-weeks quarters
exactly. Period weights are null (not weighted against each other). Q1 is closed.

Assignment-group weighting, from the same read:

| Course | Weighted groups | Groups (weight) |
| --- | --- | --- |
| Reading/Spelling | yes | Check Out 40, Assessments 40, Homework 20 |
| Math | yes | Written Assessments 60, Fact Assessments 20, Homework/Class Work 20 |
| Language Arts | yes | Assessments 70, Classwork 30 |
| History | no | Assignments 0 |
| Science | yes | Assignments 100 |

So in practice every course takes the preferred path: Canvas's own Q2 score.

## 3. What GC-1 changes

- **Scope setting.** `bin/grade-check --scope quarter|year`, default `quarter`.
  Config key `recipient.scope` (default `"quarter"`) in
  `config/canvas-llm/grade-check-config.json`. `--quarter N` still picks the
  quarter.
- **Quarter boundaries** (`config.quarter_window`): from the shared
  instructional-weeks parser, first day of the first week to last day of the last
  week, as local midnights in America/New_York. Each bound gets its own UTC
  offset, so Q2 starts at 04:00Z (EDT) and ends at 05:00Z (EST, after the Nov 1
  DST change).
- **Missing, homework, and low scores (quarter scope):** only assignments due
  inside the quarter and already past. Assignments with no due date are left out
  and counted in one note: "No due date: N assignments left out of quarter scope."
- **Course averages (quarter scope):**
  1. If a Canvas grading period's New York dates equal the quarter's, the scan
     requests enrollments with that `grading_period_id` and uses Canvas's score.
     Label: "Canvas grading period Q2".
  2. Otherwise it computes the average from in-quarter graded scores (excused,
     ungraded, zero-point, and omitted-from-final-grade work left out). If the
     course weights its groups, each group's percentage is weighted and
     renormalized over groups with graded work. Labels: "computed" or "computed
     (weighted groups)". Group drop rules are not applied.
  3. The header lists each course's source ("Course averages: Math — Canvas
     grading period Q2; …"), and each low-average line ends with its source.
- **Courses not active this quarter:** left out of the report body entirely. The
  "OUT OF SCOPE" section with names is gone in quarter scope. One line at the end:
  "Skipped as out of scope: N items (A assignments due outside the quarter, F
  earlier flags held — not resolved; C courses not active this quarter)."
- **Year scope:** every configured course (History and Science both), every
  assignment, Canvas's full-year score (labeled "Canvas current score (full
  year)").
- **Report header:** "Scope: Quarter 2 · October 12 – December 18, 2026" or
  "Scope: Full year", in the preview, the detailed preview, parent drafts, and the
  email bodies. The run log and `last_send` also record the scope.

## 4. State and history

- **No format change and no migration.** `state.json` stays `version: 2` with the
  same buckets. The only addition is an optional `average_source` field on
  flags; older flags without it load as before. Because nothing is migrated, no
  backup was needed.
- **Earlier-quarter flags don't come back as new.** In quarter scope, an existing
  flag on an assignment due outside the quarter (or with no due date) is moved to
  `out_of_scope_flags`, never `resolved_flags`. One-time keys in `one_time_issued`
  are never removed. Switching back to year scope finds those flags as STILL
  ACTIVE, not NEW.
- **Average flags keep the same key across scopes and quarters**
  (`course:student:LOW_COURSE_AVERAGE`), so a student who stays low from Q1 into
  Q2, or from year scope into quarter scope, is STILL ACTIVE, not NEW. Note: if
  Owen switches scope and the average under the new scope is above 85, that flag
  shows as RESOLVED for that run, which is accurate for the scope being viewed.
- The first quarter-scope `--send` will move today's Q1-era missing flags from
  `active_flags` to `out_of_scope_flags`. That is not a "change" for the
  email-suppression gate, so it alone does not trigger an email.

## 5. Scheduled job

- The installed LaunchAgent (`~/Library/LaunchAgents/com.teacher-ai-workstation.grade-check.plist`)
  was read, not changed. It runs `bin/grade-check --send` with no `--scope`, so it
  gets the quarter scope from the CLI default. It already has
  `CANVAS_LLM_GRADE_CHECK_SMTP_ENABLED=1`.
- The repo has no plist file. Its template is `scheduler.build_plist`, whose env
  comes from `SCHEDULE_ENV` in `scripts/canvas_llm_grade_check/scheduler.py`. That
  lacked the SMTP flag, so a reinstall would have dropped it. GC-1 adds
  `CANVAS_LLM_GRADE_CHECK_SMTP_ENABLED=1` there, with a scheduler self-test
  assertion. `bin/grade-check-schedule run-now` uses the same env, so it now
  matches the installed agent too.

## 6. Notes and things not changed

- **Live preview could not run from the agent sandbox.** The sandbox proxy
  truncated Canvas list responses (`http.client.IncompleteRead`, even at 25 items
  a page). The truncation hit the assignments and submissions list calls, which
  GC-1 does not change. The grading-period read above
  succeeded because those responses are small. Owen's preview run outside the
  sandbox is the live check.
- Pre-existing, not changed: an `IncompleteRead` is not wrapped as a
  `ReaderError`, so it prints a Python traceback instead of a `BLOCKER:` line.
- Pre-existing, not changed: the summary counts have no "NEW low averages" line
  (only STILL ACTIVE and RESOLVED).
- Pre-existing, not changed: `config.py` reads `scheduling` at the top level of the
  JSON, but the file nests it under `recipient`, so the code defaults are used.
  They are the same values (weekdays, 4:15 PM, America/New_York).
- Library default: `run_scan`, `command_preview`, and `command_send` called with
  no `scope` keep the pre-GC-1 behavior, so existing callers and tests are
  unchanged. `bin/grade-check` always passes a scope, defaulting to quarter.

## 7. Tests

- New: `tests/canvas-llm-grade-check-scope-test.py` (fake Canvas reader only, 78
  checks): quarter filter, boundaries (including Nov 1 DST), both average paths
  and their labels, inactive courses, state across quarters and scope switches,
  and the CLI default.
- `bin/grade-check --self-test` (all module self-tests, now with quarter-window
  and SMTP-env assertions).
- `tests/canvas-llm-grade-check-test.sh`, `tests/canvas-llm-mastery-fixtures-test.py`,
  `tests/canvas-llm-mastery-hardening-test.py`, and `tests/canvas_dates`.
