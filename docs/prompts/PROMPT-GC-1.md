# PROMPT — GC-1: Grade Check reports scoped to the current quarter by default

## Where you are
- **Worktree and branch:** `~/Projects/taw-gc1`, branch `feature/gc-1`, from `origin/main`.
- **Read first:**
  - `AGENTS.md`
  - `docs/DECISIONS.md` (D-022: grades are the strictest area)
  - `scripts/canvas_llm_grade_check/`
  - `config/canvas-llm/grade-check-config.json`
  - `config/curriculum/canvas/instructional-weeks-2026-2027.json`
  - `scripts/instructional_weeks.py`
- **Git limits:** don't push or merge.
- **Canvas:** GET only, as today. No Canvas writes and no grade changes, ever. Email goes only
  to the allowlisted recipient, as today. Tests use the fake Canvas client only. Don't send
  email from tests.

## Owen's requirement
When reports run, missing assignments, missing homework, low scores, and course averages come
from the **current quarter only**, unless Owen explicitly asks for a year-long view.

## 1. Investigate first, then write it down
In `docs/gc-1-findings.md`, record what the tool does today for:
- which assignments are scanned (all year, or filtered by date or grading period)
- how missing and low-score flags are chosen
- where course averages come from (the enrollment `current_score`, and whether a
  `grading_period_id` is used)
- how out-of-quarter courses and late enrollments are handled
- how `state.json` tracks issued flags

Also check, read-only through the existing Canvas client, whether the Thales courses define
**grading periods**, and whether they match the instructional-week quarter dates.

## 2. Add a scope setting, quarter by default
- **CLI:** `--scope quarter|year`. Default `quarter`. Also a config key `scope` (default
  `"quarter"`) under the recipient/report settings.
- **Quarter boundaries:** come from the shared instructional-weeks parser
  (`scripts/instructional_weeks.py`): from the first day of the quarter's first week to the
  last day of its last week, in America/New_York. Keep the existing `--quarter N` to choose a
  quarter explicitly.
- **Missing assignments, homework, and low scores:** only assignments whose **due date falls
  inside the quarter** and is already past. Assignments with no due date are left out of
  quarter scope and listed in a short "no due date" note with a count only.
- **Course averages:**
  - If the course has a Canvas grading period matching the quarter, request enrollments with
    that `grading_period_id` and use Canvas's own score. This is the preferred source.
  - Otherwise, compute a quarter average from the in-quarter graded scores, respecting
    assignment-group weights when the course uses weighted groups, and label it "computed".
  - The report says which source each average came from.
- **Courses not active this quarter:** in quarter scope, leave them out of the report body
  entirely. One line at the end says how many items were skipped as out of scope.
- **Year scope:** today's behavior, with every course and assignment included.
- **Report header:** states the scope, for example "Quarter 2 · October 12 – December 18,
  2026", or "Full year".

## 3. State and history
- Flags already issued in earlier quarters must not reappear as "new" in quarter scope.
- Changing the scope must not corrupt or reset `state.json`. Keep its format compatible, or
  migrate it with a backup.

## 4. Scheduled job
The installed LaunchAgent stays as it is. It runs the quarter scope by default because that's
the CLI default. Also check whether the repo contains its own copy or template of the
grade-check plist. If it does, make sure it includes
`CANVAS_LLM_GRADE_CHECK_SMTP_ENABLED=1`, which Owen enabled on 2026-10-21, so a reinstall
doesn't drop it.

## Tests (fake Canvas only)
- **Quarter filter:** an assignment due in Q1 is excluded in Q2 scope and included in year
  scope; a future assignment is never "missing"; an assignment with no due date goes to the
  note.
- **Quarter boundaries:** edge days, including across the Nov 1 DST change.
- **Averages:** the grading-period path, plus the computed path with and without group weights.
  The labels are correct.
- **Out-of-quarter courses:** left out in quarter scope, included in year scope.
- **State:** earlier-quarter flags don't re-alert; switching scope leaves state intact.
- The existing grade-check self-tests and repo tests still pass:
  `bin/grade-check --self-test`, plus the grade-check shell tests.

## Report
- the findings, including whether Canvas grading periods exist and match
- SHAs
- test counts
- a sample preview header and summary counts for Q2. **No student names in the report.**
- Owen's exact next commands: a preview run, push, and the PR steps (merge commit)
- `git status -sb`
