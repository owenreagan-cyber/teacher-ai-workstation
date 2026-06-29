# Checklist-Driven Prompt Template Tightening

## Purpose

This document defines a checklist-driven prompt template tightening pass after command/check bundle reference polish. It tightens Cursor prompt template guidance so future prompts can reference reusable verification bundles while preserving full PR lifecycle guardrails.

This PR tightens Cursor prompt template guidance only. This pass points to `docs/testing-checklist-consolidation.md` and `docs/command-check-bundle-reference-polish.md`. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: checklist-driven prompt template tightening in progress.
```

Prompt template rules for bundle references, mandatory lifecycle sections, and safety boundaries are documented for local status commands only.

## Why This Tightening Exists

After command/check bundle reference polish, named bundles were easier to find but future prompts still risked skipping PR-specific checks or lifecycle gates. This tightening makes bundle use shorter and safer without weakening no-commit review, merge verification, or final local-main dashboard proof.

## Prompt Template Goals

```text
make future prompts shorter
make future prompts safer
allow named reusable verification bundles
keep PR-specific checks explicit
keep no-commit review mandatory
keep merge verification mandatory
keep final local-main dashboard proof mandatory
keep safety boundaries explicit
preserve every existing command
preserve every existing check
```

## Allowed Bundle References

```text
Core Verification Bundle
Documentation/Status PR Bundle
Teacher Planning and Review Bundle
Document Indexing Safety Bundle
Appearance & Vibe Safety Bundle
Pre-Commit Review Bundle
Post-Merge Verification Bundle
```

Each allowed bundle reference should point to:

```text
Primary source: docs/testing-checklist-consolidation.md
Compact reference: docs/command-check-bundle-reference-polish.md
```

## Required Explicit Prompt Sections

```text
Goal
Safety boundaries
Full lifecycle workflow
Preflight
Branch creation
Required files to add
Required files to update
PR-specific implementation details
Required checks
No-commit review
Commit
Push and PR
PR open/unmerged verification
Merge
Merged-state verification
Local main final proof
Final report format
```

## PR-Specific Checks Rule

```text
Reusable bundles may reduce repeated check blocks.
Reusable bundles must not replace PR-specific checks.
Every PR prompt must still list the new command/status script expected for that PR.
Every PR prompt must still list dashboard expected count.
Every PR prompt must still check intended changed files.
Every PR prompt must still check safety boundaries specific to that PR.
```

## No-Commit Review Rule

```text
No-commit review remains mandatory.
It must happen after checks and before commit.
It must include changed files review.
It must include unexpected files review.
It must include command compatibility review.
It must include dashboard count review.
It must include safety review.
It must include generated files review when relevant.
It must include final git status.
```

## Merge Verification Rule

```text
Before merge, verify the PR is open and mergedAt is null.
After merge, verify state is MERGED and mergedAt is non-null.
Do not treat an open PR as merged.
Do not merge if branch checks fail.
Do not skip local main update after merge.
```

## Final Local Main Proof Rule

```text
Every lifecycle prompt must end on local main.
The working tree must be clean.
The dashboard must pass.
The final dashboard health must match the expected check count.
The final report must include PR number, merged time, merge commit, local main commit, dashboard, next recommended PR, branch deletion, and final status.
```

This rule is the final local-main dashboard proof requirement for every lifecycle prompt.

## Safety Boundary Rule

```text
Safety boundaries must remain explicit in each PR prompt.
Bundle references do not replace safety boundaries.
Future prompts must still state what is not implemented.
Future prompts must still block live integrations, network calls, automation, student data, lesson generation, document indexing/scanning, and wallpaper/photo implementation unless explicitly approved in a future phase.
```

## Prompt Tightening Examples

```text
Instead of pasting every repeated check every time, a future prompt may say:
Run the Core Verification Bundle, Documentation/Status PR Bundle, this PR's new status command directly and through bin/chief-of-staff, the PR-specific safety checks below, and the required no-commit review.

But it must still explicitly list:
- the new files expected in this PR
- the existing files expected to change
- the dashboard count expected after this PR
- the PR-specific safety boundaries
- the final local-main proof
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
no skipped merge verification
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

- This PR tightens Cursor prompt template guidance only.
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
bin/chief-of-staff --checklist-driven-prompt-template-status
bin/chief-of-staff --command-check-bundle-reference-status
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --dashboard
bash scripts/checklist-driven-prompt-template-status.sh
```
