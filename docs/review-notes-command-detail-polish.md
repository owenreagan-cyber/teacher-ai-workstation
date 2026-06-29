# Review Notes Command Detail Polish

## Purpose

This document tightens the safe Review Notes command reference after lesson review command detail polish. It adds clearer command descriptions, output expectations, and planning-only boundaries without changing behavior.

This PR adds Review Notes command detail polish only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: review notes command detail polish complete.
```

Document Indexing command detail polish tightens safe Document Indexing planning command references. See `docs/document-indexing-command-detail-polish.md`.

Teacher Workflow command detail summary links all command detail docs. See `docs/teacher-workflow-command-detail-summary.md`.

Teacher Workflow safe-output examples document expected output shapes. See `docs/teacher-workflow-safe-output-examples.md`.

## Why Command Detail Matters

After lesson review command detail polish, safe Review Notes commands were listed but command purpose, expected output, and planning-only boundaries still needed clearer detail. This polish makes the Review Notes status command easier to understand without implying real review notes, real lesson review, lesson generation, document indexing, or student data handling exists.

## Review Notes Command

```bash
bin/chief-of-staff --review-notes-workflow-status
```

```text
This command is a safe status/planning command.
It verifies Review Notes workflow organization and references.
It must not review real lessons.
It must not generate lesson content.
It must not create lesson briefs.
It must not create lesson drafts.
It must not create real review notes.
It must not use student data.
It must not scan folders.
It must not index documents.
It must not call network services.
It must not start automation.
```

## Expected Output

```text
The command should print a readable status header.
The command should report PASS/WARN/FAIL counts.
The command should make planning-only status clear.
The command should preserve existing PASS/WARN/FAIL semantics.
The command should exit nonzero only when FAIL is greater than zero.
The command should not create, modify, or delete teacher content.
The command should not create, modify, or delete review notes.
```

## Planning-Only Boundaries

```text
Review Notes command detail remains documentation/status only.
Review Notes references do not review real lessons.
Review Notes references do not create lesson content.
Review Notes references do not create lesson briefs.
Review Notes references do not create lesson drafts.
Review Notes references do not create review notes.
Review Notes references do not read or write student data.
Review Notes references do not scan folders.
Review Notes references do not index documents.
Review Notes references do not call external services.
```

## Related Safe Commands

```bash
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --lesson-review-command-detail-status
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --teacher-planning-command-detail-status
bin/chief-of-staff --teacher-workflow-status-summary
bin/chief-of-staff --teacher-workflow-quick-reference-status
bin/chief-of-staff --core-teacher-workstation-planning-cleanup-status
bin/chief-of-staff --dashboard
```

## Related Teacher Workflow Docs

```text
Review notes workflow polish: docs/review-notes-workflow-polish.md
Lesson Review command detail polish: docs/lesson-review-command-detail-polish.md
Teacher Planning command detail polish: docs/teacher-planning-command-detail-polish.md
Teacher workflow status summary: docs/teacher-workflow-status-summary.md
Teacher workflow quick-reference polish: docs/teacher-workflow-quick-reference-polish.md
Core Teacher Workstation planning cleanup: docs/core-teacher-workstation-planning-cleanup.md
Chief of Staff workflow quick-start guide: docs/chief-of-staff-workflow-quick-start-guide.md
```

## Not Implemented

```text
Real review notes are not implemented.
Real lesson review is not implemented.
Real lesson generation is not implemented.
Lesson brief generation is not implemented.
Lesson draft generation is not implemented.
Student data handling is not implemented.
Document scanning is not implemented.
File indexing is not implemented.
Network calls are not implemented.
Automation is not implemented.
```

## Dashboard Status Summary

```text
Review Notes command detail should remain documentation/status only.
Dashboard checks should remain additive and parseable.
Dashboard health should show PASS/WARN/FAIL and total health.
Warnings and failures must not be hidden.
PASS/WARN/FAIL semantics must remain unchanged.
```

## Next Safe Build Priority

```text
Next recommended PR: Document indexing command detail polish

Scope: Tighten the safe Document Indexing planning command reference with clearer command descriptions, output expectations, and planning-only boundaries. Preserve every existing command and status check. No checks removed, no command behavior changes, no lesson generation changes, no document scanning/indexing implementation, no student data, no live integrations, no network calls, and no automation.
```

## Command Detail Rules

```text
keep command purpose clear
keep expected output clear
keep planning-only boundaries clear
keep related docs easy to find
do not imply real review-note generation exists
do not imply real lesson review exists
do not imply real lesson generation exists
do not imply document indexing exists
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
bin/chief-of-staff --review-notes-command-detail-status
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --lesson-review-command-detail-status
bin/chief-of-staff --teacher-planning-command-detail-status
bin/chief-of-staff --teacher-workflow-status-summary
bin/chief-of-staff --teacher-workflow-quick-reference-status
bin/chief-of-staff --core-teacher-workstation-planning-cleanup-status
bin/chief-of-staff --dashboard
bash scripts/review-notes-command-detail-status.sh
```
