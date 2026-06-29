# Cursor PR Review Checklist

Use this checklist before approving a Cursor PR. ChatGPT and Owen may both use it.

## 1. PR Metadata

- [ ] PR title matches intended scope
- [ ] PR body lists adds, updates, safety boundaries, and tests
- [ ] PR is workflow/process only unless explicitly scoped otherwise

## 2. Branch and Commit

- [ ] Feature branch name matches the prompt
- [ ] No commits directly on `main`
- [ ] Commit message matches approved message
- [ ] Commit contains only intended files

## 3. Scope Match

- [ ] Changes match stated GOAL and SCOPE
- [ ] No lesson-generation behavior changes unless explicitly requested
- [ ] No unrelated refactors or drive-by edits

## 4. Safety Boundaries

- [ ] No student-sensitive data
- [ ] No real student names
- [ ] No Gmail, Drive, Calendar, APIs, OAuth, secrets, or school-system integrations
- [ ] No unauthorized network calls
- [ ] No LLM lesson drafting or automatic lesson generation added

## 5. Required Files

- [ ] All required add files present
- [ ] All required update files present
- [ ] No required file skipped

## 6. Unexpected Files

- [ ] `git diff --name-only` matches intended file list
- [ ] Any unexpected file is explained and approved

## 7. Existing Behavior Impact

- [ ] Each updated existing file has a clear impact summary
- [ ] Existing CLI commands still work
- [ ] Dashboard and phase checks still behave as expected

## 8. Status Script Behavior

- [ ] New or updated status scripts use `set -euo pipefail`
- [ ] Status scripts print parseable `PASS:` / `WARN:` / `FAIL:` summary
- [ ] Exit nonzero only when `FAIL > 0` (unless script documents otherwise)

## 9. Dashboard Behavior

- [ ] Dashboard captures subprocess output safely
- [ ] New dashboard section parses summary correctly
- [ ] Expected dashboard health achieved locally on the feature branch

## 10. Generated Files

- [ ] No generated lesson brief files committed unintentionally
- [ ] No generated lesson draft files committed unintentionally
- [ ] Local gitignored lesson artifacts remain local only

## 11. GitHub Merge State

- [ ] PR is open and reviewable
- [ ] CI/check expectations documented if applicable
- [ ] Merge state verified with `gh pr view`:

```text
mergedAt: null means not merged
non-null mergedAt means merged
```

## 12. Local Main Verification

After merge (not before), use the **Post-Merge Verification Bundle** from `docs/testing-checklist-consolidation.md`:

```bash
git switch main
git pull --ff-only
git log --oneline -5
git status --short
bin/chief-of-staff --dashboard
```

- [ ] Local `main` fast-forwarded from origin
- [ ] `bin/chief-of-staff --dashboard` passes on local `main`
- [ ] Phase checks pass on local `main`

## 13. Reusable Verification Bundles

Use `docs/workflow-docs-cross-link-polish.md` as the map for workflow docs.
Use `docs/workflow-docs-navigation-status-summary.md` to verify the workflow doc map remains intact.
Use `docs/prompt-pack-reference-index.md` to find reusable prompt pack references.
Use `docs/prompt-pack-maintenance-checklist.md` before reusing or updating prompt packs.

Prompt packs must be checked after roadmap changes.
Prompt packs must be checked after dashboard count changes.
Prompt packs must be checked after new status commands are added.
Prompt pack references do not replace PR-specific checks.
Prompt pack references do not replace no-commit review.
Prompt pack references do not replace PR open/unmerged verification.
Prompt pack references do not replace mergedAt non-null verification.
Prompt pack references do not replace branch deletion verification.
Prompt pack references do not replace final local-main dashboard proof.

Use `docs/prompt-pack-handoff-summary.md` to understand the current reusable prompt pack stack.
The handoff summary points to maintenance, freshness, stale-reference audit, reference index, workflow navigation, verification bundles, and lifecycle guardrails.
Use `docs/prompt-pack-reference-index.md` to find reusable prompt pack references.
Use `docs/prompt-pack-maintenance-checklist.md` before reusing or updating prompt packs.
Use `docs/prompt-pack-stale-reference-audit.md` to review reusable prompt docs for stale roadmap labels, dashboard counts, status commands, branch examples, and next recommended PR references.
Use `docs/prompt-pack-freshness-report-polish.md` to summarize whether reusable prompt docs are current.

Handoff summaries do not replace PR-specific checks.
Handoff summaries do not replace no-commit review.
Handoff summaries do not replace PR open/unmerged verification.
Handoff summaries do not replace mergedAt non-null verification.
Handoff summaries do not replace branch deletion verification.
Handoff summaries do not replace final local-main dashboard proof.

Stale-reference audits do not replace PR-specific checks.
Stale-reference audits do not replace no-commit review.
Stale-reference audits do not replace PR open/unmerged verification.
Stale-reference audits do not replace mergedAt non-null verification.
Stale-reference audits do not replace branch deletion verification.
Stale-reference audits do not replace final local-main dashboard proof.

Freshness reports should cover roadmap labels, dashboard counts, status commands, verification bundles, lifecycle guardrails, and safety boundaries.
Freshness reports do not replace PR-specific checks.
Freshness reports do not replace no-commit review.
Freshness reports do not replace PR open/unmerged verification.
Freshness reports do not replace mergedAt non-null verification.
Freshness reports do not replace branch deletion verification.
Freshness reports do not replace final local-main dashboard proof.

Lifecycle guardrails: `docs/pr-lifecycle-guardrail-consolidation.md`

Branch hygiene: `docs/branch-hygiene-cleanup-reference.md`

Local main proof: `docs/local-main-proof-report-polish.md`

Template tightening: `docs/checklist-driven-prompt-template-tightening.md`

Compact picker: `docs/command-check-bundle-reference-polish.md`

Full commands: `docs/testing-checklist-consolidation.md`

Named bundles:

- Core Verification Bundle (every PR)
- Documentation/Status PR Bundle
- Teacher Planning and Review Bundle
- Document Indexing Safety Bundle
- Appearance & Vibe Safety Bundle
- Pre-Commit Review Bundle
- Post-Merge Verification Bundle

```bash
bin/chief-of-staff --local-main-proof-report-status
bin/chief-of-staff --branch-hygiene-cleanup-status
bin/chief-of-staff --pr-lifecycle-guardrail-status
bin/chief-of-staff --checklist-driven-prompt-template-status
bin/chief-of-staff --command-check-bundle-reference-status
bin/chief-of-staff --testing-checklist-status
```

Every PR completion must prove local main.
Every PR completion must report the local main commit.
Every PR completion must report dashboard PASS/WARN/FAIL and health count.
Every PR completion must report next recommended PR.
Every PR completion must report branch deletion status.
Every PR completion must end with final status: on main, clean working tree, dashboard passing.
Final report polish does not replace merge verification or branch hygiene checks.

Navigation summaries help people find the right process doc.
Navigation summaries do not replace PR-specific checks.
Navigation summaries do not replace no-commit review.
Navigation summaries do not replace PR open/unmerged verification.
Navigation summaries do not replace mergedAt non-null verification.
Navigation summaries do not replace branch deletion verification.
Navigation summaries do not replace final local-main dashboard proof.

Cross-links help navigation but do not replace PR-specific checks.
Cross-links do not replace no-commit review.
Cross-links do not replace PR open/unmerged verification.
Cross-links do not replace mergedAt non-null verification.
Cross-links do not replace branch deletion verification.
Cross-links do not replace final local-main dashboard proof.

Every PR prompt must name the expected branch.
Every PR prompt must verify the current branch before work and before commit.
Every PR prompt must verify PR headRefName and baseRefName before merge.
Every PR prompt must verify remote branch deletion after merge when available.
Every PR prompt must return to local main after merge.
Every PR prompt must end with clean working tree and dashboard passing.
Branch cleanup guidance does not replace no-commit review or merge verification.

Every PR prompt must verify preflight on main.
Every PR prompt must verify the feature branch.
Every PR prompt must include no-commit review.
Every PR prompt must verify PR state is OPEN and mergedAt is null before merge.
Every PR prompt must verify merged state is MERGED and mergedAt is non-null after merge.
Every PR prompt must verify local main is synced after merge.
Every PR prompt must end with clean working tree and dashboard passing.
Reusable bundles do not replace these lifecycle guardrails.

Reusable verification bundles may shorten future prompts.

Reusable verification bundles do **not** replace PR-specific checks.

Reusable verification bundles do **not** replace no-commit review.

Reusable verification bundles do **not** replace PR open/unmerged verification.

Reusable verification bundles do **not** replace mergedAt non-null verification.

Reusable verification bundles do **not** replace final local-main dashboard proof.

Every PR must still end on local `main`, clean working tree, and dashboard passing.

## 14. Approval Decision

Choose one outcome:

```text
APPROVE TO COMMIT
APPROVE TO PUSH/PR
APPROVE TO MERGE
REQUEST CHANGES
BLOCKED
```

Notes:

- Use **APPROVE TO COMMIT** when no-commit review passed but commit is not yet made.
- Use **APPROVE TO PUSH/PR** after commit when push/PR is the next gate.
- Use **APPROVE TO MERGE** only after PR review and Owen approval.
- Use **REQUEST CHANGES** when fixes are needed but work can continue.
- Use **BLOCKED** for safety, scope, or verification failures that must stop work.
