# Teacher Planning Command Organization

## Purpose

This document defines a teacher planning command organization pass after dashboard section summary polish. It improves how lesson-planning, review, and document commands are grouped in help text and `--list-workflows` while preserving every existing command and its behavior.

This PR improves teacher planning command organization only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals and no command renames.

## Current Status

```text
Current status: teacher planning command organization complete.
```

Lesson review workflow polish improves safe local review guidance. See `docs/lesson-review-workflow-polish.md`.

Teacher planning commands are grouped for easier discovery. Safe sample slugs and review-only boundaries are documented clearly.

## Why This Organization Pass Exists

After dashboard section summary polish, lesson-planning commands were spread across help sections. A clearer organization helps teachers find safe status and review commands without implying real lesson generation or student data handling exists.

## Teacher Planning Command Goals

```text
make teacher planning commands easier to find
make safe sample commands easy to identify
make review-only commands clear
make planning/status commands clear
keep fractions-review as the default safe sample slug
avoid implying real lesson generation exists
avoid implying student data is used
preserve every existing command
preserve existing command behavior
```

## Command Groups

```text
Lesson Review
Review Notes
Document Indexing
Command Launcher
Cursor / Developer Verification
Dashboard and Health
```

## Safe Sample Slug Rules

```text
fractions-review is the default safe sample slug
sample slugs must not contain real student data
sample slugs must not generate new lesson content in this PR
lesson review commands are local review/status commands
real classroom content requires separate explicit approval
```

## Lesson Review Commands

Review-only local commands use safe sample slugs. Default example:

```bash
bin/chief-of-staff --lesson-review-view fractions-review
bin/chief-of-staff --lesson-review-checklist-status
```

These commands show local review/status views only. They do not generate lesson content and do not use student data.

## Review Notes Commands

```bash
bin/chief-of-staff --review-notes-template-status
```

Review notes template status is planning/status only. No generated review notes are created by this organization pass.

## Document and Indexing Commands

```bash
bin/chief-of-staff --document-indexing-plan-status
```

Document indexing remains future-only until explicitly approved. This command is planning/status only.

## Developer / Cursor Verification Commands

When verifying lesson-planning workflows alongside developer work:

```bash
bin/chief-of-staff --cursor-workflow-status
bin/chief-of-staff --developer-status
bin/chief-of-staff --command-launcher-status
```

## Backward Compatibility Rules

```text
do not remove existing commands
do not rename existing commands
do not change command behavior
do not change dashboard summary format
do not change PASS/WARN/FAIL semantics
do not remove existing lesson planning checks
```

## Safety Boundaries

```text
no lesson generation changes
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

- This PR improves teacher planning command organization only.
- This PR does not generate lesson content.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Commands Reference

```bash
bin/chief-of-staff --teacher-planning-command-status
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --lesson-review-view fractions-review
bin/chief-of-staff --review-notes-template-status
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --dashboard
bash scripts/teacher-planning-command-organization-status.sh
bash scripts/lesson-review-workflow-polish-status.sh
```
