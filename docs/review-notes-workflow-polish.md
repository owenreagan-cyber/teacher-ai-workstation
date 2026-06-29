# Review Notes Workflow Polish

## Purpose

This document defines a safe local review notes workflow polish pass after lesson review workflow polish. It improves review notes template guidance, status visibility, and safe review-note workflow boundaries without creating real review notes.

This PR improves safe local review notes workflow guidance only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals and no command renames.

## Current Status

```text
Current status: review notes workflow polish complete.
```

Core Teacher Workstation planning cleanup tightens teacher workflow planning references. See `docs/core-teacher-workstation-planning-cleanup.md`.

Local document indexing follow-up improves safe local document indexing plan/status visibility. See `docs/local-document-indexing-follow-up.md`.

Project memory cleanup improves active priorities and project memory clarity. See `docs/project-memory-cleanup.md`.

Review notes template guidance, safe sample slug rules, and teacher/Cursor workflows are documented for local status commands only.

## Why This Polish Exists

After lesson review workflow polish, review notes commands were easier to find but safe review-note workflow guidance still needed clearer boundaries. This polish makes template-guided review notes visible without implying lesson generation or student data handling exists.

## Safe Review Notes Workflow

```text
Start with dashboard:
bin/chief-of-staff --dashboard

Check review notes template status:
bin/chief-of-staff --review-notes-template-status

Check safe lesson review workflow:
bin/chief-of-staff --lesson-review-workflow-status

Check safe sample review view:
bin/chief-of-staff --lesson-review-view fractions-review
```

## First Command to Run

```text
Start here:
bin/chief-of-staff --dashboard
```

Then run review notes template status before any manual review-note work.

## Review Notes Template Guidance

```text
review notes should start from the tracked template
review notes should separate observations from action items
review notes should mark anything requiring teacher approval
review notes should avoid private classroom information
review notes should avoid student names
review notes should avoid student-sensitive data
review notes should not be generated automatically in this PR
```

## Safe Sample Slug Rules

```text
fractions-review is the default safe sample slug
sample slugs must not contain real student data
sample slugs must not identify real students
sample slugs must not generate new lesson content in this PR
review notes must remain local-only and template-guided
real classroom content requires separate explicit approval
```

## What Belongs in Review Notes

```text
safe local observations
teacher-approved next steps
checklist outcomes
questions for teacher review
template-based sections
manual action items
```

## What Does Not Belong in Review Notes

```text
student names
student-sensitive data
private classroom details
medical or behavior records
grades tied to real students
automatically generated lesson content
network-fetched content
unapproved AI-generated classroom content
```

## Teacher Workflow

```text
1. Run dashboard.
2. Run review notes template status.
3. Run lesson review workflow status.
4. Use fractions-review for safe sample checks.
5. Read the template before making changes.
6. Do not add student-sensitive data.
7. Use real classroom content only after explicit separate approval.
```

## Cursor / Developer Verification Workflow

```text
1. Verify branch and clean working tree.
2. Run dashboard.
3. Run review notes template status.
4. Run lesson review workflow status.
5. Run lesson review view using fractions-review.
6. Run phase-1 status.
7. Verify no generated lesson files are present.
8. Verify no generated review notes are present.
9. Verify no student data was added.
```

## Backward Compatibility Rules

```text
do not remove existing commands
do not rename existing commands
do not change command behavior
do not change dashboard summary format
do not change PASS/WARN/FAIL semantics
do not remove existing review notes checks
do not change fractions-review as the default safe sample slug
```

## Safety Boundaries

```text
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

- This PR improves safe local review notes workflow guidance only.
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
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --review-notes-template-status
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --lesson-review-view fractions-review
bin/chief-of-staff --dashboard
bash scripts/review-notes-workflow-polish-status.sh
```
