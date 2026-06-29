# Teacher Workflow Quick-Reference Polish

## Purpose

This document adds a compact quick-reference for safe Teacher Workstation workflow commands and docs after core Teacher Workstation planning cleanup. It makes teacher planning, lesson review, review notes, and document-indexing planning references easy to find without changing behavior.

This PR adds a Teacher Workflow quick-reference only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: teacher workflow quick-reference polish complete.
```

Lesson Review command detail polish tightens safe Lesson Review command references. See `docs/lesson-review-command-detail-polish.md`.

Review Notes command detail polish tightens safe Review Notes command references. See `docs/review-notes-command-detail-polish.md`.

Document Indexing command detail polish tightens safe Document Indexing planning command references. See `docs/document-indexing-command-detail-polish.md`.

Teacher Workflow command detail summary links all command detail docs. See `docs/teacher-workflow-command-detail-summary.md`.

Teacher Workflow safe-output checker verifies example docs remain safe. See `docs/teacher-workflow-safe-output-checker.md`.

## Why This Quick Reference Exists

After core Teacher Workstation planning cleanup, safe teacher workflow commands and docs were documented but still spread across multiple polish docs. This quick-reference collects the safe commands and doc links in one place without implying lesson generation, document indexing, or student data handling exists.

## Safe Teacher Workflow Commands

```bash
bin/chief-of-staff --teacher-planning-command-status
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --local-document-indexing-follow-up-status
bin/chief-of-staff --core-teacher-workstation-planning-cleanup-status
bin/chief-of-staff --dashboard
```

```text
These are safe status, planning, and reference commands.
They must not generate real lesson content.
They must not create real review notes.
They must not use student data.
They must not scan folders.
They must not index documents.
They must not call network services.
They must not start automation.
```

## Teacher Planning References

```text
Teacher planning command organization: docs/teacher-planning-command-organization.md
Core Teacher Workstation planning cleanup: docs/core-teacher-workstation-planning-cleanup.md
Chief of Staff workflow quick-start guide: docs/chief-of-staff-workflow-quick-start-guide.md
```

## Lesson Review References

```text
Lesson review workflow polish: docs/lesson-review-workflow-polish.md
Lesson review status command: bin/chief-of-staff --lesson-review-workflow-status
```

## Review Notes References

```text
Review notes workflow polish: docs/review-notes-workflow-polish.md
Review notes status command: bin/chief-of-staff --review-notes-workflow-status
```

## Document Indexing Planning References

```text
Document indexing plan status: bin/chief-of-staff --document-indexing-plan-status
Local document indexing follow-up: docs/local-document-indexing-follow-up.md
Local document indexing follow-up status: bin/chief-of-staff --local-document-indexing-follow-up-status
Document scanning and file indexing are not implemented.
```

## Dashboard and Status References

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --teacher-workflow-quick-reference-status
```

Use the dashboard for overall health. Use this quick-reference for safe Teacher Workstation command and doc discovery.

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

## Quick-Reference Rules

```text
keep safe commands easy to find
keep teacher workflow docs easy to find
keep completed support stacks summarized
keep future-only work clearly labeled
do not imply real lesson generation exists
do not imply document indexing exists
do not imply review-note generation exists
do not imply student data handling exists
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

This PR preserves all existing commands. This PR does not rename commands. This PR does not remove commands. This PR does not remove checks. This PR does not change command behavior. This PR preserves dashboard checks. This PR preserves PASS/WARN/FAIL semantics.

## Commands Reference

```bash
bin/chief-of-staff --teacher-workflow-quick-reference-status
bin/chief-of-staff --teacher-planning-command-status
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --local-document-indexing-follow-up-status
bin/chief-of-staff --core-teacher-workstation-planning-cleanup-status
bin/chief-of-staff --dashboard
bash scripts/teacher-workflow-quick-reference-status.sh
```
