# Lesson Review Workflow Polish

## Purpose

This document defines a safe local lesson review workflow polish pass after teacher planning command organization. It improves review workflow guidance, review status visibility, and review notes boundaries without generating lesson content.

This PR improves safe local lesson review workflow guidance only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals and no command renames.

## Current Status

```text
Current status: lesson review workflow polish complete.
```

Review notes workflow polish improves safe local review notes guidance. See `docs/review-notes-workflow-polish.md`.

Safe lesson review workflow steps, sample slug rules, and review notes guidance are documented for local status commands only.

## Why This Polish Exists

After teacher planning command organization, lesson review commands were easier to find but the safe review workflow still needed clearer step-by-step guidance. This polish makes review readiness visible without implying lesson generation or student data handling exists.

## Safe Lesson Review Workflow

```text
Start with dashboard:
bin/chief-of-staff --dashboard

Check the safe sample review view:
bin/chief-of-staff --lesson-review-view fractions-review

Check review notes template status:
bin/chief-of-staff --review-notes-template-status

Check teacher planning command organization:
bin/chief-of-staff --teacher-planning-command-status
```

## First Command to Run

```text
Start here:
bin/chief-of-staff --dashboard
```

Then run the safe sample lesson review view with `fractions-review`.

## Safe Sample Slug Rules

```text
fractions-review is the default safe sample slug
sample slugs must not contain real student data
sample slugs must not identify real students
sample slugs must not generate new lesson content in this PR
lesson review commands are local review/status commands
real classroom content requires separate explicit approval
```

## Review Status Visibility

```text
review status should make the selected slug visible
review status should make missing files obvious
review status should make safety boundaries visible
review status should not imply student data is present
review status should not imply lesson generation occurred
review status should remain local-only
```

## Review Notes Guidance

```text
review notes should use templates or safe examples only
review notes should not include student names
review notes should not include student-sensitive data
review notes should not include private classroom information
review notes should not be generated automatically in this PR
review notes should clearly separate observations from actions
review notes should clearly mark anything requiring teacher approval
```

## Teacher Workflow

```text
1. Run dashboard.
2. Run the safe sample lesson review view.
3. Run review notes template status.
4. Read the output before making changes.
5. Do not add student-sensitive data.
6. Use real classroom content only after explicit separate approval.
```

## Cursor / Developer Verification Workflow

```text
1. Verify branch and clean working tree.
2. Run dashboard.
3. Run lesson review view using fractions-review.
4. Run review notes template status.
5. Run phase-1 status.
6. Verify no generated lesson files are present.
7. Verify no student data was added.
```

## Backward Compatibility Rules

```text
do not remove existing commands
do not rename existing commands
do not change command behavior
do not change dashboard summary format
do not change PASS/WARN/FAIL semantics
do not remove existing lesson review checks
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

- This PR improves safe local lesson review workflow guidance only.
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
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --lesson-review-view fractions-review
bin/chief-of-staff --review-notes-template-status
bin/chief-of-staff --teacher-planning-command-status
bin/chief-of-staff --dashboard
bash scripts/lesson-review-workflow-polish-status.sh
```
