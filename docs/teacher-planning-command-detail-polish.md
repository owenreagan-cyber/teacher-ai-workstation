# Teacher Planning Command Detail Polish

## Purpose

This document tightens the safe Teacher Planning command reference after teacher workflow status summary. It adds clearer command descriptions, output expectations, and planning-only boundaries without changing behavior.

This PR adds Teacher Planning command detail polish only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: teacher planning command detail polish complete.
```

Lesson Review command detail polish tightens safe Lesson Review command references. See `docs/lesson-review-command-detail-polish.md`.

Review Notes command detail polish tightens safe Review Notes command references. See `docs/review-notes-command-detail-polish.md`.

Document Indexing command detail polish tightens safe Document Indexing planning command references. See `docs/document-indexing-command-detail-polish.md`.

Teacher Workflow command detail summary links all command detail docs. See `docs/teacher-workflow-command-detail-summary.md`.

Teacher Workflow safe-output examples document expected output shapes. See `docs/teacher-workflow-safe-output-examples.md`.

## Why Command Detail Matters

After teacher workflow status summary, safe Teacher Planning commands were listed but command purpose, expected output, and planning-only boundaries still needed clearer detail. This polish makes the Teacher Planning status command easier to understand without implying lesson generation, document indexing, or student data handling exists.

## Teacher Planning Command

```bash
bin/chief-of-staff --teacher-planning-command-status
```

```text
This command is a safe status/planning command.
It verifies Teacher Planning command organization and references.
It must not generate real lesson content.
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
```

## Planning-Only Boundaries

```text
Teacher Planning command detail remains documentation/status only.
Planning references do not create lesson content.
Planning references do not create lesson briefs.
Planning references do not create lesson drafts.
Planning references do not create review notes.
Planning references do not read or write student data.
Planning references do not scan folders.
Planning references do not index documents.
Planning references do not call external services.
```

## Related Safe Commands

```bash
bin/chief-of-staff --teacher-planning-command-status
bin/chief-of-staff --teacher-workflow-status-summary
bin/chief-of-staff --teacher-workflow-quick-reference-status
bin/chief-of-staff --core-teacher-workstation-planning-cleanup-status
bin/chief-of-staff --dashboard
```

## Related Teacher Workflow Docs

```text
Teacher planning command organization: docs/teacher-planning-command-organization.md
Teacher workflow status summary: docs/teacher-workflow-status-summary.md
Teacher workflow quick-reference polish: docs/teacher-workflow-quick-reference-polish.md
Core Teacher Workstation planning cleanup: docs/core-teacher-workstation-planning-cleanup.md
Chief of Staff workflow quick-start guide: docs/chief-of-staff-workflow-quick-start-guide.md
```

## Not Implemented

```text
Real lesson generation is not implemented.
Lesson brief generation is not implemented.
Lesson draft generation is not implemented.
Real review notes are not implemented.
Student data handling is not implemented.
Document scanning is not implemented.
File indexing is not implemented.
Network calls are not implemented.
Automation is not implemented.
```

## Dashboard Status Summary

```text
Teacher Planning command detail should remain documentation/status only.
Dashboard checks should remain additive and parseable.
Dashboard health should show PASS/WARN/FAIL and total health.
Warnings and failures must not be hidden.
PASS/WARN/FAIL semantics must remain unchanged.
```

## Next Safe Build Priority

```text
Next recommended PR: Lesson review command detail polish

Scope: Tighten the safe Lesson Review command reference with clearer command descriptions, output expectations, and planning-only boundaries. Preserve every existing command and status check. No checks removed, no command behavior changes, no lesson generation changes, no document scanning/indexing implementation, no student data, no live integrations, no network calls, and no automation.
```

## Command Detail Rules

```text
keep command purpose clear
keep expected output clear
keep planning-only boundaries clear
keep related docs easy to find
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
bin/chief-of-staff --teacher-planning-command-detail-status
bin/chief-of-staff --teacher-planning-command-status
bin/chief-of-staff --teacher-workflow-status-summary
bin/chief-of-staff --teacher-workflow-quick-reference-status
bin/chief-of-staff --core-teacher-workstation-planning-cleanup-status
bin/chief-of-staff --dashboard
bash scripts/teacher-planning-command-detail-status.sh
```
