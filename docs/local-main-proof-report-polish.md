# Local Main Proof Report Polish

## Purpose

This document defines a local-main proof and final report polish pass after branch hygiene and cleanup reference. It polishes completion report expectations so every PR finish clearly shows branch state, clean working tree, dashboard count, next recommended PR, merge commit, local main commit, and branch deletion status without changing Git behavior.

This PR adds local-main proof and final report polish only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

See also `docs/branch-hygiene-cleanup-reference.md` and `docs/pr-lifecycle-guardrail-consolidation.md`.

## Current Status

```text
Current status: local main proof report polish complete.
```

Workflow docs cross-link polish and navigation status summary continue workflow documentation navigation. See `docs/workflow-docs-cross-link-polish.md` and `docs/workflow-docs-navigation-status-summary.md`.

## Why Local Main Proof Exists

After branch hygiene and cleanup reference, branch naming and deletion checks were explicit but completion reports still varied. This polish makes final reports consistent so local-main proof is easy to verify without weakening merge verification or branch hygiene checks.

## Final Report Goals

```text
make completion reports consistent
make local-main proof easy to verify
show dashboard count clearly
show next recommended PR clearly
show merge commit clearly
show local main commit clearly
show branch deletion status clearly
show final branch and clean working tree status clearly
preserve every existing command
preserve every existing check
```

## Required Local Main Proof

```text
final proof must run on local main
local main must be synced after merge
working tree must be clean
dashboard must pass on local main
dashboard health must match expected count
local main commit must be reported
final status must say on main, clean working tree, dashboard passing
```

## Required Final Report Fields

```text
PR number
merged timestamp
merge commit
local main commit
dashboard summary
next recommended PR
branch deleted status
final status
what shipped summary
constraints honored summary
```

## Dashboard Count Rules

```text
dashboard summary must include PASS count
dashboard summary must include WARN count
dashboard summary must include FAIL count
dashboard summary must include health count
dashboard count must match expected post-PR count
warnings and failures must not be hidden
PASS/WARN/FAIL semantics must not change
```

## Branch Deletion Reporting Rules

```text
branch deleted status must be explicit
remote branch deletion should be verified when available
branch deletion should name the deleted branch
if branch deletion cannot be verified, report that honestly
branch deletion status must not be guessed
```

## Next Recommended PR Rules

```text
next recommended PR should match build queue
next recommended PR should match dashboard recommendation when displayed
if next recommended PR is missing or inconsistent, stop and report
```

## Clean Working Tree Rules

```text
working tree must be clean before final report
git status --short must show no unstaged or untracked intended files
final status must confirm clean working tree on local main
do not claim complete with a dirty working tree
```

## Completion Report Template

Every PR completion should end with this template:

```text
COMPLETE

PR:
Merged:
Merge commit:
Local main commit:
Dashboard:
Next recommended PR:
Branch deleted:
Final status:

What shipped:
- ...

Constraints honored:
- ...
```

## Future Prompt Reuse Rules

```text
future prompts may reference this final report guide
future prompts must still include expected dashboard count
future prompts must still verify branch deletion
future prompts must still verify local main
future prompts must still verify clean working tree
future prompts must still run dashboard on local main
future prompts must still include final report format
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
do not weaken branch deletion proof
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
no skipped branch deletion verification
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

- This PR adds local-main proof and final report polish only.
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
- PR lifecycle: `docs/pr-lifecycle-guardrail-consolidation.md`
- Workflow doc map: `docs/workflow-docs-cross-link-polish.md`
- Navigation status: `docs/workflow-docs-navigation-status-summary.md`

## Commands Reference

```bash
bin/chief-of-staff --local-main-proof-report-status
bin/chief-of-staff --branch-hygiene-cleanup-status
bin/chief-of-staff --pr-lifecycle-guardrail-status
bin/chief-of-staff --dashboard
bash scripts/local-main-proof-report-status.sh
```
