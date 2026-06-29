# Prompt Pack Stale-Reference Audit

## Purpose

This document defines a read-only stale-reference audit pass after prompt pack reference index. It adds guidance for verifying prompt pack docs still point to the current roadmap, dashboard counts, status command names, branch naming examples, and next recommended PR references without changing behavior.

This PR adds prompt pack stale-reference audit guidance only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: prompt pack stale-reference audit complete.
```

Prompt pack stack completion marker marks the reusable prompt pack stack complete for now. See `docs/prompt-pack-stack-completion-marker.md`.

## Why Stale-Reference Audits Exist

After prompt pack reference index, reusable prompt references were easy to find but could still go stale when roadmap labels, dashboard counts, status commands, branch examples, or next recommended PR references changed. This audit catches stale prompt pack references without weakening lifecycle gates or final local-main proof.

## Stale-Reference Audit Goals

```text
catch stale roadmap labels
catch stale dashboard count expectations
catch stale status command names
catch stale branch naming examples
catch stale next recommended PR references
catch stale prompt pack cross-links
keep reusable prompt docs current
preserve every existing command
preserve every existing check
```

## Roadmap Label Audit

```text
active-priorities.md should match current PR
projects.md should match current project state
docs/build-queue.md should show current and next PR
README should not contradict the build queue
prompt pack docs should not point to completed work as active
parked work should remain clearly labeled
```

## Dashboard Count Audit

```text
preflight dashboard count should match latest main
expected post-PR dashboard count should match the new dashboard total
dashboard count references should be easy to update
dashboard health should include PASS/WARN/FAIL and total health
warnings and failures must not be hidden
PASS/WARN/FAIL semantics must remain unchanged
```

## Status Command Name Audit

```text
new status command names should match bin/chief-of-staff help
new status script names should match the command behavior
dashboard section names should match the new doc/status area
phase-1 should validate new docs and scripts
README should mention the new status command
```

## Branch Naming Example Audit

```text
branch examples should use kebab-case
branch names should match the current PR scope
branch names should not reuse merged branches
branch examples should not contradict lifecycle docs
```

## Next Recommended PR Audit

```text
next recommended PR should match docs/build-queue.md
next recommended PR should match memory files
next recommended PR should match dashboard recommendation when displayed
stale next recommended PR references should be updated during each PR
```

## Prompt Pack Cross-Link Audit

```text
prompt pack reference index should point to maintenance guidance
prompt pack maintenance checklist should point to the reference index
workflow navigation docs should point to prompt pack references
cursor prompt template should point to prompt pack references
cursor PR review checklist should point to prompt pack references
```

Reference docs:

- `docs/prompt-pack-reference-index.md`
- `docs/prompt-pack-maintenance-checklist.md`

## Lifecycle Guardrail Audit

```text
prompt pack references do not replace PR-specific checks
prompt pack references do not replace no-commit review
prompt pack references do not replace PR open/unmerged verification
prompt pack references do not replace mergedAt non-null verification
prompt pack references do not replace branch deletion verification
prompt pack references do not replace final local-main dashboard proof
```

## Safety Boundary Audit

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

- This PR adds prompt pack stale-reference audit guidance only.
- This PR preserves all existing commands.
- This PR does not rename commands.
- This PR does not remove commands.
- This PR does not remove checks.
- This PR does not change command behavior.
- This PR preserves dashboard checks.
- This PR preserves PASS/WARN/FAIL semantics.
- This PR does not implement document scanning.
- This PR does not implement file indexing.
- This PR does not generate lesson content.
- This PR does not create real review notes.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Related prompt docs

- Prompt pack freshness report: `docs/prompt-pack-freshness-report-polish.md`
- Prompt pack handoff summary: `docs/prompt-pack-handoff-summary.md`
- Prompt pack stack completion marker: `docs/prompt-pack-stack-completion-marker.md`

## Commands Reference

```bash
bin/chief-of-staff --prompt-pack-stale-reference-audit-status
bin/chief-of-staff --prompt-pack-reference-index-status
bin/chief-of-staff --prompt-pack-maintenance-status
bin/chief-of-staff --workflow-docs-navigation-status
bin/chief-of-staff --dashboard
bash scripts/prompt-pack-stale-reference-audit-status.sh
```
