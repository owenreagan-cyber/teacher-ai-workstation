# MERGE-1 Report — Chief of Staff stack into `main`

```text
Branch: integrate/cos-into-main (worktree ~/Projects/taw-integrate)
Prompt: docs/prompts/PROMPT-MERGE-1.md
Date: 2026-10-18
Pushed: no (Owen pushes and opens the PR)
```

## Commits

| SHA | What |
| --- | --- |
| `8279bcb` | Add MERGE-1 prompt |
| `2d84b23` | Record baseline test results on `main` (`docs/merge-1-baseline.md`) |
| `1ec8e2f` | Correct one baseline failure cause (missing `yaml`) |
| `578ce24` | **Merge `feature/cos-p1a5` (`8fc3ac3`)**, made by Owen in a plain Terminal (see "Sandbox block" below) |
| `1daacf8` | Merge `origin/main` (`140eb77`, PR #384), which moved 2 commits after this worktree was created |
| `ca8e297` | Remove the duplicated `.claude` block from `.gitignore` |
| `c4de912` | Docs: "What lives where", AGENTS.md pointer, stale-claim fixes |
| (this file) | MERGE-1 report |

## Inventory

Merge base of `main` and `feature/cos-p1a5`: `31cb330` (PR #360). Before the merge,
`git rev-list --left-right --count HEAD...feature/cos-p1a5` gave `49 56`.

- `git diff --stat 31cb330..HEAD` (main side, at `1ec8e2f`): **183 files, +32,860 / −116**.
  Main's work is Canvas LLM (phase 3, intake, grade check, phase 22/23, deploy, mastery),
  Teacher Workstation UI and apps, `config/curriculum`, `config/fpk`, `docs/programs`, the
  Canvas planner launcher, and their tests (PRs #361–#383).
- `git diff --stat 31cb330..feature/cos-p1a5` (Chief side): **163 files, +26,364 / −0**.
  162 files are added; only `.gitignore` is modified. Areas: `apps/chief-desktop` (34),
  `tests/cos` (24), `evals/` (41), `cos/` (19), `tools/dev_safety` (8),
  `apps/raycast-chief-of-staff` (8), docs (`DECISIONS.md`, `NEXT-PHASES.md`, review bundles,
  guides, 3 prompts), `CHIEF-OF-STAFF.md`, `bin/cos`, `.claude/settings.json`,
  `scripts/cos-build-eventkit-helper.sh`, `tests/test_dev_guard.py`.
- **Files changed on both sides: none.** (`comm -12` of the two name lists is empty.)
- `origin/main` follow-up (`0609599..140eb77`): 4 files, +219 / −5:
  `scripts/canvas_llm_deploy/plan.py`, `scripts/canvas_llm_deploy/preflight.py`,
  `scripts/canvas_llm_intake/intake.py`, new `tests/q2w3-corrective-pass-regression-test.sh`.
  None overlap the Chief files.

## Conflicts and resolutions

| Item | Result |
| --- | --- |
| Merge of `feature/cos-p1a5` | **No conflicts.** `578ce24`'s tree (`de7ea93`) is identical to `git merge-tree --write-tree 1ec8e2f 8fc3ac3`, so nothing was hand-edited. |
| Merge of `origin/main` | **No conflicts.** Auto-merged, 4 files from PR #384. |
| `.gitignore` | Only the Chief side changed it, so it merged cleanly as the union (main's rules plus Chief build/output rules). The Chief side carried the `.claude/*` / `!.claude/settings.json` block **twice**; `ca8e297` removes the second copy. Checked: `.claude/settings.json` is not ignored and stays tracked; `.claude/settings.local.json` and `.claude/.cc-writes/` are ignored. |
| Docs | No doc changed on both sides. No Canvas, Teacher Workstation, or dashboard material dropped. |
| Main's Canvas / approval / deployment / dashboard-timeout code (PRs #374–#384) | Untouched. No script changed on both sides. |

### Sandbox block during the first merge attempt

The first `git merge` run inside the Claude Code sandbox failed with
`unable to create file .claude/settings.json: Operation not permitted`: that path is on the
sandbox's write-deny list for this worktree. Git left no merge state, only the 161 other
Chief files as untracked files (each checked byte-identical to `feature/cos-p1a5`). Owen ran
`git clean -fd` and the merge in a plain Terminal, which produced `578ce24`.

## Test results: baseline vs after merge

Same 167 commands, same order, one at a time, 10-minute cap each, python3.12, with the same
`mktemp` → `$TMPDIR` shim on `PATH` (see `docs/merge-1-baseline.md`). The "after" column is
the final tree (`c4de912`); the run straight after `ca8e297` gave the same results.

| Suite | Baseline (`main`) | After merge |
| --- | --- | --- |
| AGENTS.md proof commands (10) | 8 pass / 2 fail | 8 pass / 2 fail |
| `validate-all` default | FAIL (76 / 0 / 3) | FAIL (76 / 0 / 3) |
| `validate-all` smoke + phase 1 | FAIL (76 / 0 / 3) | FAIL (76 / 0 / 3) |
| `tests/*.sh` (143) | 115 pass / 28 fail | 115 pass / 28 fail |
| `tests/*.py` (9) | 9 pass | 9 pass |
| unittest `artifact_quality`, `curriculum_production`, `lesson_blueprint` | 0 / 3 pass | 0 / 3 pass |
| **Total** | **132 pass / 35 fail** | **132 pass / 35 fail** |

The same 35 commands fail before and after, for the causes recorded in the baseline. There is
no new failing command.

**One merge-caused difference inside already-failing checks.** The app-runtime approval gate
(`scripts/app-runtime-approval-gate-status.sh`) and the timer runtime gate
(`scripts/classroom-timer-stopwatch-runtime-status.sh`) allow only
`apps/classroom-timer-stopwatch/` and already fail on `main` for 5 other app folders. After the
merge they also flag `apps/chief-desktop/` and `apps/raycast-chief-of-staff/` (FAIL lines
5 → 7 in each; the same lines show up in `bin/chief-of-staff --dashboard`). **Not changed:**
adding the Chief apps to those gates would weaken an approval gate, which is Owen's call. The
same decision is already open for main's own 5 apps.

**New test from PR #384:** `tests/q2w3-corrective-pass-regression-test.sh` fails here
(`AssertionError: Science reminder must be non-empty`). It fails the same way on a clean
`git archive` export of `origin/main`, so the merge didn't cause it (most likely the date or
sandbox, like the other Q2W3 tests).

### Chief suites (after merge)

| Command | Result |
| --- | --- |
| `python3.12 -m unittest discover -s tests/cos -p 'test_*.py'` | 276 tests, OK |
| `python3.12 -m unittest discover -s tests/evals -p 'test_*.py'` | 38 tests, OK |
| `python3.12 -m unittest discover -s tests -p 'test_dev_guard*.py'` | 38 tests, OK |
| `python3.12 tools/dev_safety/dev_safety_probe.py --synthetic` | 586/586 probes (552 deny, 34 allow) |
| `python3.12 evals/harness/run.py --model fake` | **`certification: true`**: all 9 suites pass (honesty 16, injection 21, kill_switch 10, local_only 5, personality 6, robustness 18, sessions 18, tool_choice 25, web_search 26) |
| `apps/chief-desktop`: `npm ci` | OK (npm reports 11 audit advisories and 2 unapproved install scripts: `electron-winstaller`, `fsevents`) |
| `npm test` | 31/31 node tests, 272/272 static checks |
| `npm run typecheck` | OK |
| `npm run build` | OK (renderer 232.7 kB JS, 15.2 kB CSS) |
| `git diff --check` (worktree and `origin/main..HEAD`) | clean |

No merge-caused failures needed a fix.

## Docs

- `CHIEF-OF-STAFF.md`: new **What lives where** section. §3 no longer calls the repo a
  "product home candidate" and now says that `main` has approved live Canvas deployment tooling
  (PRs #374–#384).
- `AGENTS.md`: one line pointing coding agents to `CHIEF-OF-STAFF.md` and `docs/DECISIONS.md`.
- `docs/NEXT-PHASES.md`: "Merge gate and Stage 0 consolidation" notes MERGE-1 as the first step.
- **Checked and left alone:** main's Canvas docs that say "no Canvas writes" each describe one
  phase and stay true. The Chief review bundles that say "not merged" are dated snapshots.
- **Left alone, flagged for Owen:** `CHIEF-OF-STAFF.md` §3 "Works today / Missing" was already
  stale on the Chief branch before the merge (it still lists chat, tools, time/weather, brief, and
  a desktop window as missing). The merge didn't cause this, and it needs Owen's view of what
  counts as done.

## Not resolved / stopped on

- Whether the app-runtime and timer gates should allow `apps/chief-desktop/` and
  `apps/raycast-chief-of-staff/` (and main's 5 apps). This is a gate decision for Owen.
- Writing `.claude/settings.json` in this worktree is sandbox-blocked, so any future merge that
  touches it has to run outside the sandbox.

## Commands for Owen (plain Terminal)

1. Real-model harness (needs Ollama running):

   ```bash
   cd ~/Projects/taw-integrate
   python3.12 evals/harness/run.py --model real
   ```

   Expect `certification: true` on the last lines.

2. Push:

   ```bash
   git push -u origin integrate/cos-into-main
   ```

3. Open the PR on GitHub:
   1. Go to https://github.com/owenreagan-cyber/teacher-ai-workstation.
   2. Click the yellow **Compare & pull request** banner for `integrate/cos-into-main`. If it's
      gone, click **Pull requests** → **New pull request**.
   3. Set **base:** `main` and **compare:** `integrate/cos-into-main`.
   4. Title: `Merge Chief of Staff stack (cos core, Chief.app, evals, D1.1) into main`.
      Body: link `docs/merge-1-report.md` and `docs/merge-1-baseline.md`.
   5. Click **Create pull request**. Choose a merge commit (not squash or rebase) when merging,
      so the Chief history is kept.
