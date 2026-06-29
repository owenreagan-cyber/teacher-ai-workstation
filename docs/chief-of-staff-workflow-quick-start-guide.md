# Chief of Staff Workflow Quick-Start Guide

## Purpose

This document is a plain-English quick-start guide for common Chief of Staff / Teacher Workstation workflows after the help examples polish. It tells you what to run daily, before a PR, before committing, after a merge, and for safe status checks.

This PR adds a quick-start guide only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals and no command renames.

## Current Status

```text
Current status: workflow quick-start guide complete.
```

Core Teacher Workstation planning cleanup tightens teacher workflow planning references. See `docs/core-teacher-workstation-planning-cleanup.md`.

Lesson Review command detail polish tightens safe Lesson Review command references. See `docs/lesson-review-command-detail-polish.md`.

Dashboard section summary polish adds high-level section summaries. See `docs/dashboard-section-summary-polish.md`.

Teacher planning command organization improves lesson-planning command discoverability. See `docs/teacher-planning-command-organization.md`.

Lesson review workflow polish improves safe local review guidance. See `docs/lesson-review-workflow-polish.md`.

Review notes workflow polish improves safe local review notes guidance. See `docs/review-notes-workflow-polish.md`.

Local document indexing follow-up improves safe local document indexing plan/status visibility. See `docs/local-document-indexing-follow-up.md`.

Project memory cleanup improves active priorities and project memory clarity. See `docs/project-memory-cleanup.md`.

Testing/checklist consolidation documents reusable verification bundles. See `docs/testing-checklist-consolidation.md`.

Command/check bundle reference polish adds a compact bundle picker. See `docs/command-check-bundle-reference-polish.md`.

See also `docs/chief-of-staff-help-examples-polish.md` and `docs/chief-of-staff-command-map-cleanup.md` for example blocks and command grouping.

## First Command to Run

```text
Start here:
bin/chief-of-staff --dashboard
```

The dashboard is the fastest way to see local health, grouped status checks, and the next recommended PR.

## Daily Health Check

Run once per day or whenever you return to the repo:

```bash
bin/chief-of-staff --dashboard
```

Optional follow-ups:

```bash
bin/chief-of-staff --return-to-core-status
bin/chief-of-staff --workflow-quick-start-status
```

## Before Starting a PR

```bash
git switch main
git pull --ff-only
bin/chief-of-staff --dashboard
bin/chief-of-staff --list-workflows
bin/chief-of-staff --command-map-status
bin/chief-of-staff --help-examples-status
bash scripts/phase-1-status.sh
```

Confirm dashboard health is passing and the working tree is clean before creating a feature branch.

## Before Committing

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --help-examples-status
bin/chief-of-staff --workflow-quick-start-status
git diff --check
git status --short
```

Review changed files, run required status checks for your PR scope, and confirm no generated lesson files or student-sensitive data are included.

## After Merging a PR

```bash
git switch main
git pull --ff-only
bin/chief-of-staff --dashboard
bin/chief-of-staff --dashboard-readability-status
```

Confirm local `main` matches remote and dashboard health still passes.

## Lesson Review Workflow

```text
Use safe local sample slugs.
Use fractions-review as the default safe sample slug.
Do not include student-sensitive data.
Do not generate real student content in this PR.
```

```bash
bin/chief-of-staff --lesson-review-view fractions-review
bin/chief-of-staff --review-notes-template-status
```

## Document and Review Workflow

```bash
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --local-document-indexing-follow-up-status
bin/chief-of-staff --review-notes-template-status
bin/chief-of-staff --return-to-core-status
```

Document indexing remains future-only until explicitly approved. These commands are planning/status only.

## Developer / Cursor Workflow

```bash
bin/chief-of-staff --cursor-workflow-status
bin/chief-of-staff --developer-status
bin/chief-of-staff --help
```

Use these before Cursor-heavy work or Developer Mode template checks.

## Appearance & Vibe Safe Checks

```text
Appearance & Vibe wallpaper/photo foundation commands are status/planning/dry-run only.
Live wallpaper/photo curator implementation is not started.
No fetcher exists.
No image processor exists.
No scheduler exists.
No notifications exist.
No macOS wallpaper or Photos automation exists.
Reddit and Devvit remain future-only.
```

```bash
bin/chief-of-staff --wallpaper-photo-folder-creation-status
bin/chief-of-staff --wallpaper-photo-create-folders --dry-run
bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status
```

## Dry-Run and Validator Commands

```text
Dry-run commands report intended behavior only.
Validator commands inspect sample/config files only.
Dry-run and validator examples must not imply live automation.
Dry-run and validator examples must not imply network calls.
Dry-run and validator examples must not imply image processing.
```

Use dry-run and validator commands for planning and safety review only. They do not perform live file writes, network calls, or image processing unless a command is already explicitly documented as a safe helper with human approval.

## Parked and Future-Only Work

```text
3D Design Factory Agent remains parked.
Reddit remains a possible future source only.
Devvit remains a possible future Reddit-native companion only.
Live wallpaper/photo curator implementation is not started.
```

Check `docs/build-queue.md` and `assistant/memory/active-priorities.md` for the current next recommended PR.

## Safety Boundaries

```text
no command removals
no command renames
no behavior changes
no dashboard count regression
no PASS/WARN/FAIL semantic changes
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
no lesson generation changes
no student data
```

## Commands Reference

```bash
bin/chief-of-staff --workflow-quick-start-status
bin/chief-of-staff --dashboard-section-summary-status
bin/chief-of-staff --teacher-planning-command-status
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --local-document-indexing-follow-up-status
bin/chief-of-staff --project-memory-cleanup-status
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --command-check-bundle-reference-status
bin/chief-of-staff --dashboard
bin/chief-of-staff --help
bin/chief-of-staff --list-workflows
bash scripts/chief-of-staff-workflow-quick-start-status.sh
bash scripts/dashboard-section-summary-status.sh
bash scripts/teacher-planning-command-organization-status.sh
bash scripts/lesson-review-workflow-polish-status.sh
bash scripts/review-notes-workflow-polish-status.sh
bash scripts/local-document-indexing-follow-up-status.sh
bash scripts/project-memory-cleanup-status.sh
bash scripts/testing-checklist-consolidation-status.sh
bash scripts/command-check-bundle-reference-status.sh
```
