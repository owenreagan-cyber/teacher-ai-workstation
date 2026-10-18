# PROMPT — REL-2: Canvas correctness

## Where you are

- **Worktree and branch:** `~/Projects/taw-rel2`, branch `feature/rel-2`, from `main` at
  `b1f22dc` (PR #386, REL-1).
- **Read first:**
  - `AGENTS.md`
  - `CHIEF-OF-STAFF.md`
  - `docs/DECISIONS.md` (D-018, D-022)
  - `docs/rel-1-baseline.md`
  - `docs/prompts/PROMPT-REL-1.md` and its report findings
- **Git limits:** don't push, merge, rebase, or force anything. Owen pushes and opens the PR.
- **Sandbox:** the D-022 light profile is active. localhost/Ollama and github.com fetch work;
  push, credential folders, and destructive commands outside the project are blocked. Writes
  are allowed only in the worktree and temp folders, so keep using the REL-1 `mktemp` shim.
- **Packages:** Owen installed PyMuPDF, PyYAML, Pillow, python-docx, and python-pptx for both
  `python3` (3.14) and `python3.12` before this session.
- **Commits:** one commit per section, in order.

## 0. Baseline

Rerun the REL-1 167-command set (10-minute cap each, with the shim). Record the results in
`docs/rel-2-baseline.md`. Note every change from REL-1's final 151/16 and its cause. The new
packages should fix the artifact-quality and python3-based failures.

## 1. Week parser: ranges that cross a month or a year (highest priority)

- **The bug:** week ranges that cross a month ("August 31–September 4", "November 30 –
  December 4") parse with no start date, so Q1W7, Q2W7, and Q4W9 have `startsOn`/`endsOn`
  `None`. Q2W7 (starting Nov 30) is treated as a break.
- **Find every parser** of the instructional-weeks config:
  - the phase-22 `load_instructional_weeks` / `instructional_week_for_date`
  - `scripts/canvas_llm_intake/week_resolution.py` (`_week_start` and related)
  - grade-check quarter ranges
  - anything else that reads the same config
- **Make them share one parser** if practical; otherwise fix each one.
- **Handle:**
  - same-month ranges
  - cross-month ranges
  - cross-year ranges ("December 28 – January 1")
  - en dash, em dash, and hyphen, with or without spaces
  - an abbreviated month ("Nov 30 – Dec 4")
- **Tests:**
  - every week in `config/curriculum/canvas/instructional-weeks-2026-2027.json` parses to
    non-null `startsOn`/`endsOn`
  - `startsOn <= endsOn`, and consecutive weeks don't overlap
  - Q1W7, Q2W7, and Q4W9 get the exact expected dates
  - with `TAW_TODAY=2026-12-01`, the startup week is Q2W7 (not a break)
- **Report:** a table of the weeks whose dates changed (before → after). This is an intended
  behavior change approved by Owen.

## 2. Homeroom course ID = 26429 (Owen confirmed on 2026-10-18 in Canvas)

- Find every occurrence of `26427` and `26429` across `config/`, `scripts/`, `docs/`,
  `tests/`, `fixtures/`, and `apps/`.
- **Change only the places where `26427` means the homeroom course.** If `26427` is a
  different course anywhere (another subject or section), leave it alone and list it in the
  report.
- Make the intake test that expects 26429 pass because of correct data, not by weakening it.
- **Report:** every file and line changed, plus any `26427` left in place and why.
- No Canvas writes, and no live Canvas calls in this section.

## 3. "At Home" wording

The config uses "At Home" (Owen's current term) where the phase-22 canonical-knowledge
validator expects "Homework". Update the validator and its fixtures to the owner's term
"At Home". Accept "Homework" only as a documented legacy alias if older data still uses it.
Keep the test strict otherwise.

## 4. One shared write guard for every local server

- **Extract** REL-1's route-protection checks from `scripts/teacher_workstation/server.py`
  into a shared module, `scripts/local_http_guard.py`:
  - loopback Host
  - same-origin
  - per-start token
  - JSON content type
  - 1 MB limit
  - Transfer-Encoding refusal
  - token injection into served pages
- **Use it in the Teacher Workstation server** (no behavior change; its 15 tests still pass)
  **and in the older phase-22, phase-23, and phase-26 servers** that accept local-planning
  POSTs on their own ports. Update their front ends to send the token and JSON headers.
- **If one of those older servers is clearly superseded** by the Teacher Workstation (no
  launcher, docs, or tests use it), don't guard it. Instead make it refuse to start, with a
  one-line message pointing to `bin/teacher-workstation`. Keep the code.
- **Tests:** for each guarded server, a foreign Origin, a missing token, and a wrong content
  type are refused, while valid same-origin requests work. Use the socket-pair fallback if
  binding is still blocked.

## 5. Phase-23 demo absolute paths

Replace the absolute `~/Projects/teacher-ai-workstation` paths in the committed phase-23 demo
data and fixtures with repo-relative paths, so the phase-23 test passes from any worktree.

## 6. Real-model Chief check

Ollama is reachable now. After the last commit, on a clean tree, run
`python3.12 evals/harness/run.py --model real`. Report `certification`, each suite's
pass/fail counts, and timing. Then unload any model it loaded: `ollama stop <model>` for each
model in `ollama ps`.

## Validation

- the 167-command set: no new failures vs `docs/rel-2-baseline.md`, plus the fail→pass list
- `python3.12 -m unittest discover -s tests/cos -p 'test_*.py'`
- `python3.12 -m unittest discover -s tests/evals -p 'test_*.py'`
- `python3.12 -m unittest discover -s tests -p 'test_dev_guard*.py'`
- `python3.12 tools/dev_safety/dev_safety_probe.py --synthetic`
- the REL-1 unit test folders: `tests/teacher_workstation`, `tests/canvas_dates`,
  `tests/python_deps`
- `python3.12 evals/harness/run.py --model fake` (`certification: true` on the clean tree)
- `cd apps/chief-desktop && npm ci && npm test && npm run typecheck && npm run build`
- `git diff --check`

## Report

- SHAs per section
- baseline vs final counts, plus the fail→pass list
- the week-date change table
- every homeroom ID change, and any `26427` left in place
- the guarded servers vs retired servers
- real-model harness results
- anything not fixed, and why
- Owen's exact next commands:
  1. `git push -u origin feature/rel-2`
  2. PR click steps, using a merge commit
- `git status -sb`
