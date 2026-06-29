# PR Lifecycle Guardrail Consolidation

## Purpose

This document defines a PR lifecycle guardrail consolidation pass after checklist-driven prompt template tightening. It consolidates preflight, branch, no-commit review, PR open/unmerged, merge, merged-state, and final local-main proof expectations so future prompts stay shorter but strict.

This PR consolidates PR lifecycle guardrails only. This pass points to `docs/testing-checklist-consolidation.md`, `docs/command-check-bundle-reference-polish.md`, and `docs/checklist-driven-prompt-template-tightening.md`. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: PR lifecycle guardrail consolidation complete.
```

Branch hygiene and cleanup reference is complete. See `docs/branch-hygiene-cleanup-reference.md`. Local main proof report polish adds final report and dashboard count rules. See `docs/local-main-proof-report-polish.md`. Workflow docs cross-link polish adds navigation map. See `docs/workflow-docs-cross-link-polish.md`.

## Why This Consolidation Exists

After checklist-driven prompt template tightening, bundle references were safer but lifecycle gates were still spread across multiple docs. This consolidation makes every PR lifecycle step explicit in one place without weakening checks.

## Lifecycle Guardrail Goals

```text
make PR lifecycle expectations easy to reuse
make preflight expectations explicit
make branch-state checks explicit
make no-commit review mandatory
make PR open/unmerged checks explicit
make merged-state verification explicit
make final local-main proof mandatory
make final report fields consistent
preserve every existing command
preserve every existing check
```

## Preflight Guardrails

```text
start from local main
working tree must be clean
fetch origin before starting
pull main with --ff-only
dashboard must pass before branch creation
previous PR must be verified merged with non-null mergedAt
next recommended PR should match build queue
stop and report if any preflight check fails
```

## Branch Guardrails

```text
create a feature branch from clean updated main
do not commit directly to main
verify branch name after creation
stop if branch name does not match expected branch
```

## No-Commit Review Guardrails

```text
no-commit review is mandatory
no-commit review happens after checks and before commit
review changed files
review unexpected files
review existing behavior impact
review command compatibility
review dashboard count
review safety boundaries
review generated files
review final git status
do not commit if review finds an unresolved issue
```

## Commit and Push Guardrails

```text
commit only intended files listed in the PR scope
use the approved commit message
push the feature branch before creating the PR
do not push directly to main
verify remote branch tracks the feature branch after push
```

## PR Open/Unmerged Guardrails

```text
after creating PR, verify state is OPEN
verify mergedAt is null before merge
verify headRefName matches feature branch
verify baseRefName is main
do not treat an open PR as merged
do not merge if branch checks fail
```

## Merge Guardrails

```text
merge only after clean final branch checks
use gh pr merge with branch deletion
after merge, verify state is MERGED
after merge, verify mergedAt is non-null
record merge commit
verify remote branch deletion when available
```

## Merged-State Verification Guardrails

```text
after merge, verify state is MERGED
after merge, verify mergedAt is non-null
record merge commit from gh pr view
do not treat mergedAt is null as merged
do not skip merged-state verification
```

## Local Main Final Proof Guardrails

```text
switch back to main after merge
pull main with --ff-only
verify local main commit
verify working tree is clean
run dashboard on local main
dashboard must pass
dashboard health must match expected count
final proof is not complete until local main is clean and dashboard passes
```

This section is the final local-main dashboard proof requirement.

## Final Report Rules

```text
final report must include PR number
final report must include merged timestamp
final report must include merge commit
final report must include local main commit
final report must include dashboard summary
final report must include next recommended PR
final report must include branch deleted status
final report must include final status
```

## Bundle Reuse Rules

```text
reusable bundles may shorten repeated check blocks
reusable bundles do not replace PR-specific checks
reusable bundles do not replace no-commit review
reusable bundles do not replace PR open/unmerged verification
reusable bundles do not replace mergedAt non-null verification
reusable bundles do not replace final local-main dashboard proof
```

Primary bundle sources:

```text
docs/testing-checklist-consolidation.md
docs/command-check-bundle-reference-polish.md
docs/checklist-driven-prompt-template-tightening.md
```

## Backward Compatibility Rules

```text
do not remove existing commands
do not rename existing commands
do not remove existing checks
do not change command behavior
do not change dashboard summary format
do not change PASS/WARN/FAIL semantics
do not change merge verification expectations
do not weaken no-commit review
do not weaken final local-main proof
```

## Safety Boundaries

```text
no check removals
no command removals
no command renames
no behavior changes
no dashboard count regression
no PASS/WARN/FAIL semantic changes
no weakened PR lifecycle
no skipped PR-specific checks
no skipped no-commit review
no skipped PR open/unmerged verification
no skipped merged-state verification
no skipped final local-main proof
no document scanning
no folder scanning
no file indexing
no content parsing
no OCR
no embeddings
no vector database
no lesson generation changes
no new lesson briefs
no new lesson drafts
no real review notes
no student data
no student-sensitive data
no live integrations
no network calls
no APIs
no OAuth
no secrets
no automation
no scheduler implementation
no notifications
no image processing
no wallpaper/photo curator implementation
```

## What This PR Does Not Implement

- This PR consolidates PR lifecycle guardrails only.
- This PR does not implement document scanning.
- This PR does not implement file indexing.
- This PR does not generate lesson content.
- This PR does not create real review notes.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Related workflow docs

- Branch hygiene: `docs/branch-hygiene-cleanup-reference.md`
- Local main proof: `docs/local-main-proof-report-polish.md`
- Verification bundles: `docs/testing-checklist-consolidation.md`
- Workflow doc map: `docs/workflow-docs-cross-link-polish.md`

## Commands Reference

```bash
bin/chief-of-staff --pr-lifecycle-guardrail-status
bin/chief-of-staff --checklist-driven-prompt-template-status
bin/chief-of-staff --command-check-bundle-reference-status
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --dashboard
bash scripts/pr-lifecycle-guardrail-status.sh
```
