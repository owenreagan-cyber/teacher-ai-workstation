# Core Teacher Workstation Planning Cleanup

## Purpose

This document returns to core Teacher Workstation planning cleanup after prompt pack stack completion marker. It tightens planning and status references for teacher workflows, current safe commands, completed support infrastructure, parked work, and next build priorities without changing behavior.

This PR returns to core Teacher Workstation planning cleanup. This PR tightens planning/status references only. This PR marks the prompt pack documentation stack complete for now. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: core Teacher Workstation planning cleanup complete.
```

Teacher Planning command detail polish tightens safe Teacher Planning command references. See `docs/teacher-planning-command-detail-polish.md`.

## Why This Cleanup Exists

After prompt pack stack completion marker, the reusable prompt pack documentation stack was complete for now but core Teacher Workstation planning references still needed a focused cleanup pass. This cleanup makes teacher workflow priorities, safe commands, and next build priorities easy to find without weakening lifecycle gates or final local-main proof.

## Core Teacher Workstation Focus

```text
The current focus is core Teacher Workstation planning clarity.
Teacher workflow docs and safe command references should be easy to find.
Completed prompt pack support work should be visible but not treated as active work.
Future-only work should remain parked or explicitly labeled.
Next build priorities should stay safe, local, and documentation/status-first unless explicitly approved.
```

## Completed Support Infrastructure

```text
Reusable prompt pack documentation stack: complete for now
Workflow docs navigation and cross-link stack: complete for now
PR lifecycle guardrails: complete for now
Branch hygiene and local-main proof docs: complete for now
Dashboard section summary and command map polish: complete for now
Appearance & Vibe wallpaper/photo foundation stack: complete for now
```

## Current Safe Teacher Workflow Commands

```bash
bin/chief-of-staff --teacher-planning-command-status
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --local-document-indexing-follow-up-status
bin/chief-of-staff --dashboard
```

```text
These commands are safe status/view/planning commands.
They must not generate real lesson content.
They must not create real review notes.
They must not use student data.
They must not scan or index documents.
```

## Current Teacher Workflow Docs

```text
Teacher planning command organization: docs/teacher-planning-command-organization.md
Lesson review workflow polish: docs/lesson-review-workflow-polish.md
Review notes workflow polish: docs/review-notes-workflow-polish.md
Local document indexing follow-up: docs/local-document-indexing-follow-up.md
Chief of Staff workflow quick-start guide: docs/chief-of-staff-workflow-quick-start-guide.md
```

## Prompt Pack Stack Status

```text
Prompt pack stack completion marker: docs/prompt-pack-stack-completion-marker.md
Prompt pack handoff summary: docs/prompt-pack-handoff-summary.md
Prompt pack freshness report polish: docs/prompt-pack-freshness-report-polish.md
Prompt pack stale-reference audit: docs/prompt-pack-stale-reference-audit.md
Prompt pack reference index: docs/prompt-pack-reference-index.md
Prompt pack maintenance checklist: docs/prompt-pack-maintenance-checklist.md
```

The prompt pack documentation stack is complete for now. See `docs/prompt-pack-stack-completion-marker.md`.

## Parked and Future-Only Work

```text
Live wallpaper/photo curator implementation is not started.
Reddit and Devvit remain future-only.
3D Design Factory Agent remains parked.
Document scanning and file indexing are not implemented.
Lesson generation changes are not implemented.
Student data handling is not implemented.
Live integrations, network calls, and automation are not implemented.
```

## Next Safe Build Priority

```text
Next recommended PR: Teacher workflow quick-reference polish

Scope: Add a compact quick-reference for safe Teacher Workstation workflow commands and docs. Preserve every existing command and status check. No checks removed, no command behavior changes, no lesson generation changes, no document scanning/indexing implementation, no student data, no live integrations, no network calls, and no automation.
```

## Planning Cleanup Rules

```text
completed support stacks should be summarized, not treated as active
current teacher workflow priorities should be easy to find
next recommended PR should match build queue and memory
parked work should remain clearly labeled
future-only work should remain clearly labeled
safety boundaries should remain visible
```

## Lifecycle Guardrails Still Required

```text
PR-specific checks remain required
no-commit review remains required
PR open/unmerged verification remains required
mergedAt null before merge remains required
mergedAt non-null after merge remains required
branch deletion verification remains required when available
local main sync after merge remains required
dashboard proof on local main remains required
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

This PR does not implement document scanning. This PR does not implement file indexing. This PR does not generate lesson content. This PR does not create real review notes. This PR does not use student data. This PR does not add external integrations. This PR does not add network calls. This PR does not add automation.

## Commands Reference

```bash
bin/chief-of-staff --core-teacher-workstation-planning-cleanup-status
bin/chief-of-staff --teacher-planning-command-status
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --prompt-pack-stack-completion-status
bin/chief-of-staff --dashboard
bash scripts/core-teacher-workstation-planning-cleanup-status.sh
```
