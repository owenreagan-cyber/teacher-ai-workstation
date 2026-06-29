# Branch Hygiene and Cleanup Reference

## Purpose

This document defines a branch hygiene and cleanup reference pass after PR lifecycle guardrail consolidation. It adds guidance for feature branches, remote deletion checks, local branch cleanup, and clean working tree proof after merges without changing Git behavior.

This PR adds branch hygiene and cleanup reference guidance only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

See also `docs/pr-lifecycle-guardrail-consolidation.md` for full PR lifecycle guardrails.

## Current Status

```text
Current status: branch hygiene and cleanup reference in progress.
```

Branch hygiene rules for starting state through final local-main proof are documented for local status commands only.

## Why Branch Hygiene Exists

After PR lifecycle guardrail consolidation, lifecycle gates were explicit but branch naming, remote deletion verification, and local cleanup guidance were still spread across prompts. This reference makes branch state easy to verify without weakening no-commit review, merge verification, or final local-main dashboard proof.

## Branch Hygiene Goals

```text
make branch state easy to verify
make feature branch naming explicit
make clean working tree proof explicit
make remote branch deletion checks explicit
make local branch cleanup guidance clear
make final local-main proof mandatory
preserve every existing command
preserve every existing check
```

## Starting State Rules

```text
start from local main
working tree must be clean
fetch origin before starting
pull main with --ff-only before branching
dashboard must pass before branch creation
previous PR must be verified merged with non-null mergedAt
stop and report if local state is dirty or out of sync
```

## Feature Branch Rules

```text
create one feature branch per PR
create the branch from updated main
use a descriptive kebab-case branch name
verify branch name immediately after creation
do not commit directly to main
do not reuse merged branches
do not continue if branch name does not match expected branch
```

## Pre-Commit Branch Rules

```text
verify current branch is the feature branch
verify changed files are intended
verify no unexpected files are present
run required checks before commit
print no-commit review before commit
do not commit if unresolved issues remain
```

## Pre-Merge Branch Rules

```text
verify PR state is OPEN
verify mergedAt is null before merge
verify headRefName matches feature branch
verify baseRefName is main
run final branch checks before merge
do not merge if branch checks fail
```

## Remote Branch Deletion Rules

```text
use gh pr merge with --delete-branch
after merge, verify state is MERGED
after merge, verify mergedAt is non-null
verify the remote feature branch is removed when available
do not treat branch deletion as complete until GitHub reports the branch removed or unavailable
```

After merge, confirm non-null mergedAt before treating branch deletion as complete.

## Local Branch Cleanup Rules

```text
switch back to main after merge
pull main with --ff-only
verify local main commit
verify working tree is clean
local merged branches may be pruned only after main is synced and merge is verified
local branch cleanup must not delete unmerged work
```

## Final Local Main Proof Rules

```text
final proof must happen on local main
working tree must be clean
dashboard must pass
dashboard health must match expected count
final report must include branch deletion status
final report must include final status
```

This section is the final local main proof requirement after branch cleanup.

## Future Prompt Reuse Rules

```text
future prompts may reference this branch hygiene guide
future prompts must still include the expected branch name
future prompts must still verify branch state
future prompts must still verify PR open/unmerged state
future prompts must still verify mergedAt after merge
future prompts must still verify final local main
future prompts must still include dashboard proof
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

- This PR adds branch hygiene and cleanup reference guidance only.
- This PR does not implement document scanning.
- This PR does not implement file indexing.
- This PR does not generate lesson content.
- This PR does not create real review notes.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Commands Reference

```bash
bin/chief-of-staff --branch-hygiene-cleanup-status
bin/chief-of-staff --pr-lifecycle-guardrail-status
bin/chief-of-staff --checklist-driven-prompt-template-status
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --dashboard
bash scripts/branch-hygiene-cleanup-status.sh
```
