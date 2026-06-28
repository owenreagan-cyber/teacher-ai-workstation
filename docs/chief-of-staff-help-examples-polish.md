# Chief of Staff Help Examples Polish

## Purpose

This document defines a help-examples and common-workflow polish pass for the local `bin/chief-of-staff` CLI after the command map cleanup. It improves copy-paste examples in help text and README docs while preserving every existing command and its behavior.

This PR improves help examples and workflow examples only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals and no command renames.

## Current Status

```text
Current status: help examples polish complete.
```

Workflow quick-start guide adds plain-English daily/PR/merge workflows. See `docs/chief-of-staff-workflow-quick-start-guide.md`.

Help text and README include clearer common-workflow example blocks for daily health checks, teacher review, developer/Cursor verification, and safe Appearance & Vibe status/dry-run commands.

## Why This Polish Exists

After the command map cleanup, commands were easier to find but common-user workflows still required scanning long example lists. This pass adds grouped, copy-paste-friendly examples without changing command behavior.

## Help Example Goals

```text
make common workflows easier to copy
show first-run commands clearly
show daily health-check commands clearly
show teacher review commands clearly
show developer/Cursor verification commands clearly
label dry-run commands clearly
label validator commands clearly
avoid implying live wallpaper/photo curator implementation exists
preserve every existing command
preserve existing command behavior
```

## Common User Workflows

### Daily health check

```bash
bin/chief-of-staff --dashboard
```

### Pre-PR verification

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --command-map-status
bin/chief-of-staff --help-examples-status
bash scripts/phase-1-status.sh
```

### Post-merge verification

```bash
git switch main
git pull --ff-only
bin/chief-of-staff --dashboard
```

### Lesson review check

```bash
bin/chief-of-staff --lesson-review-view fractions-review
bin/chief-of-staff --review-notes-template-status
```

### Document/review workflow check

```bash
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --review-notes-template-status
```

### Appearance & Vibe foundation check

```bash
bin/chief-of-staff --wallpaper-photo-folder-creation-status
bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status
```

### Safe dry-run folder check

```bash
bin/chief-of-staff --wallpaper-photo-create-folders --dry-run
```

### Command discovery check

```bash
bin/chief-of-staff --list-workflows
bin/chief-of-staff --command-map-status
bin/chief-of-staff --help
```

## Teacher Planning Examples

```text
Use lesson review commands only with safe local sample slugs.
Do not generate real student content.
Do not include student-sensitive data.
Use fractions-review as the safe example slug unless the repo already documents another safe sample.
```

Example:

```bash
bin/chief-of-staff --lesson-review-view fractions-review
```

## Review and Document Examples

```bash
bin/chief-of-staff --review-notes-template-status
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --return-to-core-status
```

## Developer / Cursor Examples

```bash
bin/chief-of-staff --cursor-workflow-status
bin/chief-of-staff --developer-status
bin/chief-of-staff --dashboard-readability-status
```

## Appearance & Vibe Safe Examples

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

Examples:

```bash
bin/chief-of-staff --wallpaper-photo-folder-creation-status
bin/chief-of-staff --wallpaper-photo-create-folders --dry-run
bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status
```

## Validator and Dry-Run Example Rules

```text
validators inspect sample/config files only
dry-run helpers must clearly say dry-run
examples must not imply real file writes unless command is already explicitly a safe helper
examples must not imply network calls
examples must not imply image processing
examples must not imply live automation
```

Validator commands and dry-run helpers remain planning/safety only. Examples label them clearly in help text.

## Backward Compatibility Rules

```text
do not remove existing help examples unless replacing with clearer equivalent examples
do not remove existing commands
do not rename existing commands
do not change command behavior
do not change dashboard summary format
do not change PASS/WARN/FAIL semantics
```

## Blocked Changes

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

## What This PR Does Not Implement

- This PR improves help examples and workflow examples only.
- This PR does not implement new live features.
- This PR does not implement the wallpaper/photo curator.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.
- This PR does not generate lesson content.
- This PR does not use student data.

## Commands Reference

```bash
bin/chief-of-staff --help-examples-status
bin/chief-of-staff --workflow-quick-start-status
bin/chief-of-staff --help
bin/chief-of-staff --list-workflows
bin/chief-of-staff --dashboard
bash scripts/chief-of-staff-help-examples-status.sh
bash scripts/chief-of-staff-workflow-quick-start-status.sh
```
