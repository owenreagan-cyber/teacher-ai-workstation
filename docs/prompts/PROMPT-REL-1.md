# PROMPT — REL-1: Reliability, Canvas route protection, and cleanup

## Where you are

- **Worktree and branch:** `~/Projects/taw-rel1`, branch `feature/rel-1`, from `main` at
  `92fb514` (PR #385, which merged the Chief stack).
- **Read first:**
  - `AGENTS.md`
  - `CHIEF-OF-STAFF.md`
  - `docs/DECISIONS.md` (especially D-018 and D-022..D-026)
  - `docs/merge-1-baseline.md`
  - `docs/merge-1-report.md`
- **Git limits:** don't push, merge, rebase, or force anything. Owen pushes and opens the PR.
- **Sandbox:** the D1.1 sandbox is active, so Ollama and github.com are unreachable. Run
  fake-model checks only. Use the same `mktemp` shim the MERGE-1 baseline used (see
  `docs/merge-1-baseline.md`).
- **Commits:** one commit per section, in the order below.

## 0. Baseline

Rerun the MERGE-1 command set (167 commands, 10-minute cap each, with the shim). Owen
installed PyYAML 6.0.3 and PyMuPDF 1.28.2 for python3.12 before this session. Record the
results in `docs/rel-1-baseline.md`.

## 1. Bounded execution: process-group containment

- **The problem:** `scripts/cos-run-bounded.sh` kills only its direct child.
- **The fix:** each bounded command starts in its own process group or session. On timeout
  or interrupt, send TERM to the **whole group**, wait a short grace period, then send KILL
  to the group. Clean up on EXIT, INT, and TERM as well.
- **Dashboard coverage:** route every potentially blocking check in
  `scripts/chief-of-staff-dashboard.sh` through the bounded helper (the review found 9 bounded
  calls against about 137 direct `bash scripts/...` substitutions). Keep the output text and
  the PASS/WARN/FAIL meaning the same.
- **Exit codes:** document them in the script header and in `docs/`: 0 = PASS, 1 = WARN,
  2 = FAIL, and 124 = timeout. Keep 124 distinct, and record it as timeout evidence.
- **Tests:**
  - a command that spawns a grandchild that ignores TERM; after the timeout, no process from
    the group survives
  - an interrupted run
  - a nested bounded call
  - timing stays close to the previous dashboard runtime, with no large slowdown

## 2. Canvas route protection on the local Teacher Workstation server (D-022: the one strict area)

Find the server that exposes approval, planning, preflight, and deployment POST routes (under
`apps/teacher-workstation/` or `scripts/`).

- **Bind and Host:** bind to 127.0.0.1 only. Reject requests whose `Host` isn't
  `127.0.0.1:<port>` or `localhost:<port>`.
- **Origin:** for every mutating route (POST, PUT, PATCH, DELETE), require `Origin` (or
  `Referer` when there's no Origin) to match the server's own origin. Reject cross-site
  requests.
- **Request token:** add a per-server-start random token. The UI receives it in the page and
  sends it as a header, and mutating routes reject requests without it.
- **Content type:** require `Content-Type: application/json` on mutating routes.
- **Size limit:** cap request bodies at 1 MB, returning 413 above that.
- **Don't change** the existing approval, write-gate, or deployment logic. These checks run
  before it.
- **Tests (HTTP integration, against a test instance on a free port):**
  - wrong Host
  - foreign Origin
  - missing token
  - wrong content type
  - oversized body
  - a valid same-origin request still works for each route
  - GET-only pages unaffected
- **Docs:** update the server and launcher docstrings, which still say "read-only, no Canvas
  writes." Describe read-only use and the guarded write workflow separately.

## 3. Date-independent Canvas tests and the `None > str` bug

- **The bug:** fix `select_startup_week` (and anything similar) so a missing week value can't
  be compared to a string.
- **Testable dates:** give the date-dependent code an injectable "today", through a parameter
  or an environment variable like `TAW_TODAY=YYYY-MM-DD`, used only by tests.
- **Tests:** pin the 19 date-dependent tests from the baseline to a fixed date inside their
  planned weeks. Real behavior must not change.
- Report which of the 19 now pass, and why any don't.

## 4. Clear dependency errors

- Where PyYAML or PyMuPDF is missing, fail with a one-line message naming the package and the
  install command, instead of `JSONDecodeError` or a traceback.
- Switch `import fitz` to `import pymupdf` where it appears. The `fitz` name is deprecated in
  PyMuPDF 1.28.
- Add a `requirements` note to `AGENTS.md`'s validation section listing both packages and the
  install command:
  `python3.12 -m pip install --user --break-system-packages pymupdf pyyaml`

## 5. App gates (D-022)

The app-runtime and timer gates allow only the timer app, while `apps/` holds the
Teacher Workstation apps plus `chief-desktop` and `raycast-chief-of-staff`. Update the gate
lists to the current, intended set of apps. Each entry needs a one-line reason. Keep the gate
itself, so an unknown new folder under `apps/` still fails. `validate-all` should pass where
the app gates were the only reason it failed.

## 6. Light D1 profile (D-022)

Owen installs this. You cannot write `.claude/` or `~/.claude/hooks/cos/`.

- **Edit `tools/dev_safety/render_settings.py`:**
  - Keep: the denied reads for credential folders, Claude Code state, and the ChiefOfStaff
    state folder; the hook's destructive-command and inline-code checks; git push and force
    denials.
  - Change: allow localhost (so Ollama works from sandboxed Bash) and github.com (fetch only;
    push stays denied by the hook and permission rules), and general web access for package
    and documentation lookups.
  - Remove: `~/.teacher-ai-workstation`, `~/Downloads`, and the student-data roots from the
    denied list. They're non-sensitive under D-022. Keep `student_data_roots.txt` as an
    empty, documented file in case Owen wants it later.
- **Regenerate** `settings.proposed.json` and `sandbox-lock.json`, and update the unit tests,
  the probe expectations, and `tools/dev_safety/README.md`.
- **Install steps:** write `docs/rel-1-owen-steps.md` with the exact commands:
  - render
  - copy to `.claude/settings.json`
  - run `install_dev_guard.py`
  - the synthetic probe against the installed hook
  - a 5-step live check in a fresh `cc` session: Ollama reachable from Bash; `git fetch`
    works; `git push` refused; `~/.ssh` unreadable; `rm -rf ~/Projects/x` refused

## 7. Desktop dependencies

In `apps/chief-desktop`:
- Review the `npm audit` advisories, and apply non-breaking fixes. Use
  `npm audit fix` only without `--force`.
- Explain any that remain.
- Report the 2 unapproved install scripts: which packages they belong to, and whether
  they're needed.
- Tests, typecheck, build, and static checks must still pass.

## 8. Docs refresh

- Rewrite the "Works today / Missing" lists in `CHIEF-OF-STAFF.md` to match reality (chat,
  sessions, daily brief, home card, desktop window, web search, weather, and start at login
  all work today).
- Mark D-001, D-004, D-011, and D-017 in `docs/DECISIONS.md` as "partly superseded by D-022"
  (in a note, not by deleting the text).

## Validation

- the 167-command set again: no new failures vs `docs/rel-1-baseline.md`, and list every
  command that went from fail to pass
- `python3.12 -m unittest discover -s tests/cos -p 'test_*.py'`
- `python3.12 -m unittest discover -s tests/evals -p 'test_*.py'`
- `python3.12 -m unittest discover -s tests -p 'test_dev_guard*.py'`
- `python3.12 tools/dev_safety/dev_safety_probe.py --synthetic`
- `python3.12 evals/harness/run.py --model fake` (`certification: true`)
- `cd apps/chief-desktop && npm ci && npm test && npm run typecheck && npm run build`
- `git diff --check`

## Report

- SHAs per section
- baseline vs final counts, plus the list of fail→pass commands
- for each section: what changed and its tests
- anything not fixed, and why
- Owen's exact next commands:
  1. the light-profile install from `docs/rel-1-owen-steps.md`
  2. `git push -u origin feature/rel-1`
  3. PR click steps, using a merge commit
- `git status -sb`
