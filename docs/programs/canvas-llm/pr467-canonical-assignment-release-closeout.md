# PR #467 Canonical Assignment Release Closeout

```text
Status: documentation and status record only
Scope: Canvas LLM weekly production — canonical Math and Reading assignment naming
Runtime activation: none
Implementation approval: not granted by this file
Canvas writes in this mission: none
Recorded: 2026-11-23
```

This is the canonical release record for PR #467. The workflow it validates is
documented in `docs/canvas-deployment-workflow.md`; the Canvas program handoff is
`docs/programs/canvas-llm/current-handoff.md`.

## 1. Verified release state

| Fact | Evidence |
| --- | --- |
| PR #467 — "Fix canonical Math and Reading Canvas assignment generation" | GitHub PR `#467`, base `main`, head `fix/canvas-reading-canonical-names-20261118` |
| State | **MERGED** at 2026-11-23T16:58:41Z (squash merge) |
| Merge commit | `708b73bb03610f5450c021cef49efcc23d01ab33` |
| CI validation | **PASS** — CI run #140 (`pull_request`, head `a93f060b`); job `Validate` succeeded with every step green, including `Whitespace and patch check`, `Q2W5 lifecycle and integration`, `Canvas intake and deployment`, and `Live authorization` |
| Post-merge CI | **PASS** — CI run #141 (`push` to `main`, commit `708b73b`) |
| Local `main` | `708b73b` |
| `origin/main` | `708b73b` — identical to local `main` |
| PR branch refs | No local branch and no `origin` branch for `fix/canvas-reading-canonical-names-20261118` remain |
| Live Canvas writes in this mission | None |

`main` and `origin/main` are the same commit. The release baseline is clean: the
merge commit is the tip of `origin/main`, so there is no later divergence to
reconcile.

## 2. Implemented corrections

### 2.1 Canonical Math and Reading assignment generation

- `scripts/canvas_llm_phase3/assignment_policy.py` classifies Reading titles by
  role in the canonical order: a title containing `Comprehension` is homework
  before a title containing `Workbook` is classwork. The same ordering now
  applies to semantic identity, so `RM4: Lesson <n> Workbook and Comprehension`
  resolves to the Reading homework family instead of the classwork family.
- `scripts/canvas_llm_phase3/pacing_reading.py` and
  `scripts/canvas_llm_phase3/pacing_routing.py` produce the canonical per-day
  Reading assignments from the pacing config. Math routing follows the same
  canonical resolution path.
- `scripts/canvas_llm_phase22/homework_rules.py` aligns homework rules with the
  canonical names.
- `scripts/canvas_llm_phase3/assignment_draft_generator.py` drafts assignments
  from the resolved canonical policy rather than a per-call convention.
- `config/curriculum/normalized/assignment-routing-contract-2026-2027.json`
  carries the matching routing contract entries.

### 2.2 Duplicate Reading homework removed

The duplicate came from one Reading lesson being classified twice under two
families. With the classification order fixed, the workbook-plus-comprehension
lesson is one homework assignment, and the legacy compatibility identities
(`RM4: Thursday Comprehension Questions — Lesson <n>`,
`RM4: Lesson <n> Workbook`) still resolve to the same semantic family they did
before. Historical titles remain compatible; they are not re-emitted.

### 2.3 Whole-week Reading regression coverage

`tests/canvas-llm-reading-canonical-policy-test.py` (new) asserts, for one full
week:

- Monday and Wednesday produce workbook-only Reading classwork.
- Tuesday and Thursday produce workbook-and-comprehension Reading homework.
- Friday produces no regular Reading assignment.
- The week contains exactly four canonical Reading assignments.
- No two assignment titles in the week are identical.

### 2.4 Q2W5 safety-test storage isolation

`tests/q2w5-canonical-assessment-integration-test.py` changed in two ways:

- The weekly release now expects ten assignments (four Math, four Reading, one
  Spelling, one Language Arts) and asserts the exact four Reading titles plus
  the absence of duplicate titles.
- The blocked-direct-execution scenarios run inside
  `scripts.canvas_llm_storage.isolated_storage()`. Each case starts with empty
  temporary ledgers and asserts no rollover ledger is loaded, so the safety
  tests never read or modify real Q2W5 publication history.

### 2.5 Production publication and deployment safeguards preserved

PR #467 changed no file under `scripts/canvas_llm_deploy/`,
`scripts/canvas_llm_rollover/`, or the live-authorization modules. The
fail-closed reconciliation, scoped preflight, week-scoped live authorization,
approval-phrase gates, and `UPDATE_REQUIRED` block described in
`docs/canvas-deployment-workflow.md` are unchanged. The mission performed no
live Canvas operation.

## 3. Local verification performed for this record

Run from the closeout worktree at `708b73b`, with `PYTHONPATH` set to the
repository root. Every command is local and read-only; none constructs a live
Canvas client.

| Command | Result |
| --- | --- |
| `python3 tests/canvas-llm-reading-canonical-policy-test.py` | PASS — whole-week Reading policy, duplicate protection, no Canvas calls |
| `python3 tests/q2w5-canonical-assessment-integration-test.py` | PASS — 10 passed, 0 failed |
| `bash tests/canvas-llm-homework-rules-test.sh` | PASS |
| `bash tests/canvas-llm-assignment-draft-generator-test.sh` | PASS |

## 4. Branch and worktree state

- The PR head branch is gone locally and on `origin`; the merge commit is the
  only remaining reference to this work.
- The unrelated `fix/q2w5-historical-reminder-noise` branch still exists locally
  and on `origin`. It is not part of PR #467 and was left alone.
- The protected development checkout `~/Projects/teacher-ai-workstation` was not
  modified, reset, stashed, cleaned, committed, or checked out. It remains on
  `feat/q2w6-restricted-release` at `4954070` with 53 modified and 13 untracked
  paths preserved.
- A prunable worktree registration for `docs/canvas-weekly-workflow-review`
  exists in the shared repository metadata. It is unrelated to PR #467 and was
  left untouched.

## 5. Roadmap reconciliation

Phase names, numbering, and hierarchy in `docs/master-build-roadmap.md` are
preserved. Nothing in this record marks a phase complete.

### 5.1 Completed and confirmed by PR #467

- Canonical Math assignment naming through the shared resolution path.
- Canonical Reading assignment naming, including workbook-and-comprehension
  homework.
- Duplicate Reading homework suppression.
- Whole-week Reading regression coverage.
- Q2W5 safety-test storage isolation, with the safety suites no longer touching
  real publication history.

### 5.2 In development

- **Q2W6 restricted (owner-scoped) release.** PR #465 added fail-closed
  assignment reconciliation and the scoped release path; PR #466 wired the
  restricted deployment safety tests into CI; PR #467 corrected the assignment
  names that path emits. The code path is merged. **Q2W6 is not complete**: no
  live Q2W6 restricted release is performed or verified by this record, and the
  scope record, preflight, and publication ledger live in gitignored local state.
- Uncommitted Q2W6 work remains in the protected checkout. It is preserved and
  is not part of this record.

### 5.3 Remaining unfinished Canvas production capabilities

1. **Owner-run Q2W6 restricted release.** Scope authorization, scoped preflight,
   and `restricted-release` execution have not been recorded as run for Q2W6.
2. **Full-week publication.** A restricted release is narrower than a full week
   by design: weekly announcements, assessment reminders, Homeroom, front-page
   switches, and deletes are absent, not blocked. Completing those artifacts
   remains future work.
3. **Assignment correction path.** An existing assignment whose reconciliation
   result is `UPDATE_REQUIRED` still blocks the release unless a separate
   explicit correction is approved. No correction path is implemented.
4. **Homeroom page identity and family announcement scheduling** remain separate
   gates with their own approval records.
5. **Phase 22–27 runtime limitations** recorded in the Canvas handoff still
   apply: fixture seeding, synthetic weekly generation input, and
   fixture-backed Phase 24/25 inputs in parts of Phase 26. Those paths are not
   the final production pipeline.

### 5.4 Dependencies between Canvas production and Chief of Staff

- Chief of Staff owns the owner-facing entry point:
  `bin/chief-of-staff --canvas-weekly-release` (status, prepare, review,
  approve, publish). It writes approvals and delegates publication to the single
  rollover engine; it is not a second publisher.
- Chief of Staff reads the rollover ledger back to report completion. Intake and
  publication ledgers must agree; a manifest status alone is not completion.
- `--canvas-deployment-status` and `--friday-rollover-status` are read-only
  health surfaces over the same records.
- The Canvas lane therefore depends on Chief of Staff for approval recording and
  readback, and Chief of Staff depends on the Canvas lane for the evidence it
  reports. Neither side may invent the other's state.

### 5.5 Contradictions and outdated statuses found

These were identified and deliberately **not** rewritten in this mission, because
correcting them requires phase-status decisions this record cannot verify:

| Document | Stale statement | Reality |
| --- | --- | --- |
| `docs/master-build-roadmap.md` §1 | Canvas LLM "Phase 27 readiness and safety diff in progress" | Canvas work continued well past that snapshot: weekly release manager, restricted release, and PRs #460–#467 are merged |
| `docs/master-build-roadmap.md` Program C | "Canvas Manual Restart (Frozen)" with a stop marker | Canvas publication paths are merged and exercised by CI; the frozen framing no longer describes the repository |
| `docs/whole-system-master-roadmap-build-state-report.md` §10 | "Canvas LLM frozen", "Canvas unfreeze" listed as blocked | Same as above |
| `docs/teacher-workstation-capability-map.md` | "Canvas LLM manual export — frozen/stopped" | Same as above |
| `docs/build-queue.md` | "Current Focus" text still lists Canvas Phase 5–11 as the frontier; "Current PR" section is empty | Merged work through #467 is not represented |
| `assistant/memory/active-priorities.md` | Canvas entries still say "complete/frozen/stopped"; the list stops in July | Same as above |
| `docs/programs/canvas-llm/current-handoff.md` | Production block named commit `8275c77` and PR #309 | Corrected in this mission to the verified `708b73b` / PR #467 baseline |

`docs/chief-of-staff/CURRENT_STATE.md` is a live-state snapshot last reviewed
2026-10-11 whose newest produced week is Q2W1. It is not evidence about Q2W5 or
Q2W6 and was not changed here; a fresh live read is required before it is
updated.

## 6. Recommended next phase

**Objective — Q2W6 restricted release, no-write readiness verification.**

Prove, without any Canvas mutation, that the corrected canonical assignment
policy produces exactly the scoped Q2W6 plan: the expected CREATE/SKIP set, one
Reading homework assignment per workbook-and-comprehension lesson, no duplicate
titles, and zero actions for every excluded subject and artifact type.

| Field | Value |
| --- | --- |
| Existing evidence | PR #465 (fail-closed reconciliation, scope record, scoped preflight), PR #466 (restricted safety tests in CI), PR #467 (canonical names, whole-week Reading regression, isolated safety storage) |
| Remaining gaps | No recorded Q2W6 scope/preflight verification; no documented expected-plan artifact in the repository; announcement and Homeroom artifacts intentionally absent from a restricted release; `UPDATE_REQUIRED` blocks |
| Dependencies | Owner approval phrase `SCOPE Q2W6`; owner-supplied GET-only Canvas credentials for the reconciliation step (never committed); Chief of Staff approval and readback surfaces |
| Proposed scope | Read-only GET reconciliation against the owner-scoped week, an expected-plan fixture or report committed as documentation of the verified plan, and a regression test asserting the plan matches the canonical policy. No writes, no approvals, no publication |
| Out of scope | Live restricted release, full-week publication, announcement or Homeroom scheduling, assignment correction path, roadmap phase changes |
| Complexity | **Small** — one verification path plus one regression test and one documentation record |
| Execution method | **Terminal-guided (Codex)** for the local work; the GET-only reconciliation is run by Owen in Terminal |
| Suggested model | Mid-tier coding model (Sonnet-class); the work is bounded verification, not architectural design |
| Acceptance criteria | Reconciliation report is GET-only and bound to the current source hash; the plan contains no duplicate assignment titles; Reading assignments match the four-per-week canonical set; every excluded subject and artifact type records zero actions; the new regression test fails if a duplicate Reading title reappears; `git diff --check` and the Canvas CI suites stay green |
| Validation | `python3 tests/canvas-llm-reading-canonical-policy-test.py`, `python3 tests/q2w5-canonical-assessment-integration-test.py`, `tests/canvas-llm-deploy-test.sh`, `tests/canvas-llm-intake-test.sh`, plus the CI `Validate` job on the pull request |

Completing existing work comes before starting any new Canvas capability. The
live restricted release remains a separate, owner-run, explicitly approved step
after this verification.

## 7. What this record does not claim

- Q2W6 is not complete, published, or verified.
- No live Canvas read or write was performed for this record.
- The Q2W5 suites are regression coverage with isolated storage; passing them is
  test-level evidence, not a live publication claim.
- No phase, program, or capability status outside the facts in §1–§3 is asserted.
