# PROMPT — MERGE-1: Bring the Chief branch stack into `main`

## Where you are

- **Worktree:** `~/Projects/taw-integrate`, branch `integrate/cos-into-main`. Owen created it
  from `origin/main` at `0609599` (PR #383) before this session.
- **Source branch to merge:** `feature/cos-p1a5` (the stack `feature/cos-e1-harness` →
  `feature/cos-p1a` → `feature/cos-p1a5`, now at `8fc3ac3`). Merge base with main: `31cb330`.
  Count the commits on each side with
  `git rev-list --left-right --count HEAD...feature/cos-p1a5`.
- **Do not touch:**
  - the other worktrees
  - `~/Projects/teacher-ai-workstation` (the main checkout)
  - the branch `wip/canvas-live-q1w9`, which holds Owen's uncommitted Canvas and workspace
    work and gets its own PR later. It is not part of this merge.
- **Git limits:** do not push, merge into `main`, rebase, or force anything. Owen pushes and
  opens the PR.
- **Sandbox:** you're running under the D1.1 sandbox, so Ollama and github.com are
  unreachable. Run fake-model checks only, and list the real-model commands for Owen.

## Goal

One branch that contains everything from `main` **and** the Chief work: the `cos/` core,
`apps/chief-desktop`, `evals/`, `tools/dev_safety/`, `docs/DECISIONS.md` (D-001..D-026),
`docs/NEXT-PHASES.md`, the prompts, and `CHIEF-OF-STAFF.md`. Every test suite must pass at
least as well as it did on `main` before the merge.

## Steps

1. **Commit this prompt first:** `docs/prompts/PROMPT-MERGE-1.md`.
2. **Baseline before merging,** on the current HEAD, which equals `origin/main`.
   - Find main's own test and validation commands. Check `AGENTS.md`, `README.md`,
     `scripts/chief-of-staff-validate-all.sh`, and `tests/`.
   - Run them with a 10-minute cap per command.
   - Save the pass/fail list to `docs/merge-1-baseline.md`. Failures that already exist on
     main are recorded, not fixed.
3. **Inventory:**
   - `git diff --stat 31cb330..HEAD` and `git diff --stat 31cb330..feature/cos-p1a5`
   - the list of files changed on **both** sides, which are the likely conflicts
   - put all three in the report
4. **Merge:** `git merge --no-ff feature/cos-p1a5 -m "Merge Chief of Staff stack (cos core, Chief.app, evals, D1.1) into main"`.
5. **Conflict rules:**
   - Keep both sides wherever possible.
   - `.gitignore`: take the union, and keep the rule that tracks only `.claude/settings.json`.
   - Docs: merge the content. Never drop main's Canvas, Teacher Workstation, or dashboard
     material.
   - **Never delete or weaken main's Canvas, approval, deployment, or dashboard-timeout code**
     (PRs #374–#383).
   - If both sides changed the same script, keep main's behavior and add the branch's
     changes on top. If that's impossible, stop and describe both versions in the report;
     don't choose.
   - Record every conflict and how it was resolved in `docs/merge-1-report.md`.
6. **Verify after the merge:**
   - main's baseline commands again, with no new failures compared to the baseline
   - `python3.12 -m unittest discover -s tests/cos -p 'test_*.py'`
   - `python3.12 -m unittest discover -s tests/evals -p 'test_*.py'`
   - `python3.12 -m unittest discover -s tests -p 'test_dev_guard*.py'`
   - `python3.12 tools/dev_safety/dev_safety_probe.py --synthetic`
   - `python3.12 evals/harness/run.py --model fake` (must print `certification: true`)
   - `cd apps/chief-desktop && npm ci && npm test && npm run typecheck && npm run build`
   - `git diff --check`

   Fix only failures the merge caused, in small, separate commits.
7. **Docs:**
   - `CHIEF-OF-STAFF.md` gets a short "What lives where" section:
     - **Teacher Workstation, Canvas, and dashboard:** existing `main` paths
     - **Chief core:** `cos/`, `bin/cos`
     - **Chief desktop:** `apps/chief-desktop/`
     - **Evals:** `evals/`
     - **Developer safety:** `tools/dev_safety/`
     - **Decisions:** `docs/DECISIONS.md`
     - **Plan:** `docs/NEXT-PHASES.md`
     - **Earlier workspace architecture** (`assistant/chief-of-staff/workspace/`): on
       `wip/canvas-live-q1w9`, reference only, not yet merged
   - Add one line to `AGENTS.md` pointing coding agents to `CHIEF-OF-STAFF.md` and
     `docs/DECISIONS.md`.
   - Fix any doc on either side that now says something false, for example "read-only, no
     Canvas writes."

## Report

- commit SHAs
- the inventory, including files changed on both sides
- each conflict and its resolution
- baseline vs after-merge results for every suite, as counts
- the harness result
- desktop build result
- anything you couldn't resolve and stopped on
- the exact commands Owen runs next, in a plain Terminal:
  1. the real-model harness run
  2. `git push -u origin integrate/cos-into-main`
  3. how to open the PR on GitHub, as click steps
- `git status -sb`
