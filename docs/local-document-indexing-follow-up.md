# Local Document Indexing Follow-Up

## Purpose

This document defines a safe local document indexing follow-up pass after review notes workflow polish. It improves document indexing plan/status visibility and future approval boundaries without implementing indexing.

This PR improves safe local document indexing plan/status visibility only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals and no command renames.

## Current Status

```text
Current status: local document indexing follow-up in progress.
```

Document indexing remains planning/status only. Safe boundaries, future approval gates, and relationships to lesson review and review notes are documented for local status commands only.

## Why This Follow-Up Exists

After review notes workflow polish, document indexing plan commands existed but follow-up guidance for what is safe to say now versus what requires future approval still needed clearer visibility. This follow-up makes indexing boundaries visible without implying document scanning, file indexing, or student data handling exists.

## Safe Local Indexing Plan

```text
local document indexing remains a plan/status area only
future indexing would require explicit approval
future indexing would require a clear folder allowlist
future indexing would require a dry-run preview
future indexing would require privacy boundaries
future indexing would require student data safeguards
future indexing would require manual teacher control
future indexing would require a separate implementation PR
```

Start with dashboard and plan status:

```text
bin/chief-of-staff --dashboard
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --local-document-indexing-follow-up-status
```

## What Is Not Implemented

```text
no folder scanning
no document scanning
no file indexing
no file content parsing
no OCR
no embeddings
no vector database
no search index
no background watcher
no scheduler
no cloud sync
no network calls
no AI/LLM calls
no student data ingestion
```

## Privacy and Student Data Boundaries

```text
do not index student-sensitive data
do not read private classroom records
do not read grades tied to real students
do not read medical or behavior records
do not read parent communications
do not send documents to external services
do not create cloud indexes
do not run unattended
real classroom documents require separate explicit approval
```

## Relationship to Lesson Review

```text
lesson review remains local and sample-slug based
fractions-review remains the default safe sample slug
document indexing is not required for the current lesson review workflow
document indexing must not generate lesson content
document indexing must not add student data
```

## Relationship to Review Notes

```text
review notes remain template-guided and local-only
document indexing is not required for the current review notes workflow
document indexing must not create review notes
document indexing must not read private classroom information
document indexing must not generate classroom content
```

## Future Approval Gates

```text
1. Approve document indexing scope.
2. Approve folder allowlist.
3. Approve file type allowlist.
4. Approve dry-run preview output.
5. Approve privacy and student data boundaries.
6. Approve manual review workflow.
7. Approve no-network guarantee.
8. Approve indexing storage location.
9. Approve deletion/reset behavior.
10. Approve future implementation separately.
```

## Cursor / Developer Verification Workflow

```text
1. Verify branch and clean working tree.
2. Run dashboard.
3. Run local document indexing follow-up status.
4. Run document indexing plan status.
5. Run review notes workflow status.
6. Run lesson review workflow status.
7. Run phase-1 status.
8. Verify no generated lesson files are present.
9. Verify no generated review notes are present.
10. Verify no indexing, scanning, OCR, embeddings, vector DB, or network behavior was added.
```

## Backward Compatibility Rules

```text
do not remove existing commands
do not rename existing commands
do not change command behavior
do not change dashboard summary format
do not change PASS/WARN/FAIL semantics
do not remove existing document indexing plan checks
do not change lesson review or review notes behavior
```

## Safety Boundaries

```text
no document scanning
no folder scanning
no file indexing
no content parsing
no OCR
no embeddings
no vector database
no background watcher
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

- This PR improves safe local document indexing plan/status visibility only.
- This PR does not implement document scanning.
- This PR does not implement file indexing.
- This PR does not read user documents.
- This PR does not parse document contents.
- This PR does not generate lesson content.
- This PR does not create new lesson briefs.
- This PR does not create new lesson drafts.
- This PR does not create real review notes.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Commands Reference

```bash
bin/chief-of-staff --local-document-indexing-follow-up-status
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --dashboard
bash scripts/local-document-indexing-follow-up-status.sh
```
