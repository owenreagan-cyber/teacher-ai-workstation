# Command/Check Bundle Reference Polish

## Purpose

This document defines a command/check bundle reference polish pass after testing/checklist consolidation. It adds a compact reference layer so README, help, workflow docs, and Cursor prompts can point to the same named verification bundles.

This PR adds command/check bundle reference polish only. This pass points to the consolidated bundles in `docs/testing-checklist-consolidation.md`. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: command/check bundle reference polish complete.
```

Checklist-driven prompt template tightening adds lifecycle guardrail rules for bundle references. See `docs/checklist-driven-prompt-template-tightening.md`.

Compact bundle picker and per-bundle references are documented for quick lookup without duplicating full check lists.

## Why This Reference Exists

After testing/checklist consolidation, named verification bundles existed in one doc but README, help, and Cursor workflow docs still required users to hunt for the right bundle. This reference makes bundle selection faster without weakening checks.

## Bundle Reference Goals

```text
make the consolidated bundles easier to find
make future prompts shorter without weakening checks
make README point to the right bundle doc
make Chief of Staff help point to the right bundle doc
make Cursor workflow docs point to the right bundle doc
preserve every existing command
preserve every existing check
keep PR-specific checks required
keep no-commit review required
keep post-merge verification required
```

## Quick Bundle Picker

```text
Daily sanity check: Core Verification Bundle
Docs/status-only PR: Documentation/Status PR Bundle
Teacher planning or review PR: Teacher Planning and Review Bundle
Document/indexing safety PR: Document Indexing Safety Bundle
Appearance & Vibe PR: Appearance & Vibe Safety Bundle
Before commit: Pre-Commit Review Bundle plus PR-specific checks
After merge: Post-Merge Verification Bundle
```

Primary source for full command lists: `docs/testing-checklist-consolidation.md`

Status command:

```bash
bin/chief-of-staff --testing-checklist-status
```

## Core Verification Bundle Reference

Primary source: `docs/testing-checklist-consolidation.md`

Use for every PR. Includes dashboard, phase checks, and git diff review.

```bash
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --dashboard
```

## Documentation/Status PR Bundle Reference

Primary source: `docs/testing-checklist-consolidation.md`

Use for documentation, status, workflow-polish, and memory-cleanup PRs. Includes bash syntax checks and dashboard validation.

## Teacher Planning and Review Bundle Reference

Primary source: `docs/testing-checklist-consolidation.md`

Use for lesson review, review notes, and teacher planning workflow PRs. Includes `fractions-review` sample checks and empty lesson-planning `find` results.

## Document Indexing Safety Bundle Reference

Primary source: `docs/testing-checklist-consolidation.md`

Use for document indexing plan and follow-up PRs. Includes plan status commands and safety-boundary grep review (wording only, not implementation).

## Appearance & Vibe Safety Bundle Reference

Primary source: `docs/testing-checklist-consolidation.md`

Use when Appearance & Vibe foundation or safety docs change. Foundation remains complete for now; live curator implementation is not started.

## Pre-Commit Review Bundle Reference

Primary source: `docs/testing-checklist-consolidation.md`

Use before every commit. Run in addition to PR-specific checks; bundle references must not be used to skip safety checks.

## Post-Merge Verification Bundle Reference

Primary source: `docs/testing-checklist-consolidation.md`

Use after merge on local `main`. Final state must be clean working tree and dashboard passing.

## Cursor Prompt Reuse Rules

Cursor prompt reuse rules for future prompts:

```text
future Cursor prompts may reference named bundles
future Cursor prompts must still include PR-specific checks
future Cursor prompts must still include no-commit review
future Cursor prompts must still verify PR open/unmerged before merge
future Cursor prompts must still verify mergedAt is non-null after merge
future Cursor prompts must still end on local main with clean working tree and dashboard passing
bundle references must not be used to skip safety checks
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
```

## Safety Boundaries

```text
no check removals
no command removals
no command renames
no behavior changes
no dashboard count regression
no PASS/WARN/FAIL semantic changes
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

- This PR adds command/check bundle reference polish only.
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
bin/chief-of-staff --command-check-bundle-reference-status
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --dashboard
bash scripts/command-check-bundle-reference-status.sh
```
