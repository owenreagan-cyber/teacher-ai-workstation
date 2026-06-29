# Prompt Pack Maintenance Checklist

## Purpose

This document defines a prompt pack maintenance checklist pass after workflow docs navigation status summary. It adds maintenance guidance for reusable Cursor prompt packs, including what must stay current after roadmap changes, dashboard count changes, and new status commands.

This PR adds prompt pack maintenance checklist guidance only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: prompt pack maintenance checklist complete.
```

Prompt pack reference index continues reusable prompt reference discovery. See `docs/prompt-pack-reference-index.md`.

## Why Prompt Pack Maintenance Exists

After workflow docs navigation status summary, navigation was verifiable but reusable Cursor prompts could still go stale when roadmap, dashboard count, or status commands changed. This checklist keeps reusable Cursor prompts accurate without weakening lifecycle gates or final local-main proof.

## Prompt Pack Maintenance Goals

```text
keep reusable Cursor prompts accurate
keep roadmap references current
keep dashboard count expectations current
keep new status commands discoverable
keep verification bundle references current
keep PR lifecycle guardrails explicit
keep branch hygiene and local-main proof explicit
avoid stale prompt instructions
preserve every existing command
preserve every existing check
```

## What Must Stay Current

```text
current PR name
next recommended PR
branch name
expected dashboard count
new status command
new status script
new doc path
required files to add
required files to update
verification bundles
safety boundaries
final report format
```

## Roadmap Update Checklist

```text
active-priorities.md matches current PR
projects.md matches current project state
docs/build-queue.md shows current and next PR
README links remain accurate
dashboard next recommendation remains accurate
completed work is marked complete
parked work remains clearly labeled
```

## Dashboard Count Update Checklist

```text
preflight dashboard count matches latest main
expected post-PR dashboard count adds exactly one new check when adding a new status section
dashboard section name is clear
dashboard line remains parseable
final health count matches expected count
PASS/WARN/FAIL semantics remain unchanged
```

## New Status Command Checklist

```text
new status script exists
new CLI command exists
CLI help mentions new command
list-workflows mentions new command or related group
dashboard runs new status script
phase-1 validates new doc and script
status script exits nonzero only on FAIL
status script is read-only
```

## Verification Bundle Reference Checklist

```text
reference docs/testing-checklist-consolidation.md when using bundles
reference docs/command-check-bundle-reference-polish.md when using compact bundle picker
bundles may shorten repeated check blocks
bundles must not replace PR-specific checks
bundles must not replace no-commit review
bundles must not replace merge verification
bundles must not replace final local-main proof
```

## Lifecycle Guardrail Checklist

```text
preflight on main
feature branch verification
no-commit review before commit
PR open/unmerged verification
mergedAt null before merge
mergedAt non-null after merge
remote branch deletion verification when available
local main sync after merge
clean working tree proof
dashboard proof on local main
final report with required fields
```

## Safety Boundary Checklist

```text
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

## Prompt Reuse Review Checklist

```text
confirm the prompt references the latest merged PR
confirm the prompt uses the correct next recommended PR
confirm the prompt uses the correct branch name
confirm the prompt uses the correct expected dashboard count
confirm required files match the PR scope
confirm required checks include PR-specific checks
confirm no-commit review is still explicit
confirm final local-main proof is still explicit
confirm safety boundaries are still explicit
```

Prompt packs do not replace PR-specific checks, no-commit review, or final local-main dashboard proof.

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

- This PR adds prompt pack maintenance checklist guidance only.
- This PR does not implement document scanning.
- This PR does not implement file indexing.
- This PR does not generate lesson content.
- This PR does not create real review notes.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Related prompt docs

- Prompt pack reference index: `docs/prompt-pack-reference-index.md`
- Prompt pack stale-reference audit: `docs/prompt-pack-stale-reference-audit.md`
- Prompt pack freshness report: `docs/prompt-pack-freshness-report-polish.md`

## Commands Reference

```bash
bin/chief-of-staff --prompt-pack-maintenance-status
bin/chief-of-staff --workflow-docs-navigation-status
bin/chief-of-staff --workflow-docs-cross-link-status
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --dashboard
bash scripts/prompt-pack-maintenance-status.sh
```
