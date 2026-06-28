# Chief of Staff Command Map Cleanup

## Purpose

This document defines a discoverability and organization pass for the local `bin/chief-of-staff` command map after the dashboard readability pass. It improves how commands are grouped in help text and `--list-workflows` while preserving every existing command and its behavior.

This PR improves command map discoverability only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals and no command renames.

## Current Status

```text
Current status: command map cleanup complete.
```

Help examples polish adds common-workflow example blocks. See `docs/chief-of-staff-help-examples-polish.md`.

Workflow quick-start guide adds plain-English daily/PR/merge workflows. See `docs/chief-of-staff-workflow-quick-start-guide.md`.

Help text and `--list-workflows` group related commands more clearly. Status commands, validators, and dry-run helpers are easier to distinguish.

## Why This Cleanup Exists

After the dashboard readability pass, the Chief of Staff CLI accumulated many status, validator, and dry-run commands across lesson planning, developer workflow, and Appearance & Vibe foundation work. A clearer command map makes discovery faster without changing behavior.

## Command Map Goals

```text
make commands easier to find
group related commands clearly
separate status commands from validators
separate dry-run helpers from live commands
make Appearance & Vibe foundation commands easier to scan
make lesson planning commands easier to scan
make developer/workflow commands easier to scan
preserve every existing command
preserve existing command behavior
avoid hiding safety checks
```

## Command Grouping Rules

Command map groups follow this scan order:

```text
Core Dashboard and Health
Return to Core / Roadmap
Lesson Planning
Document and Review Workflows
Developer and Cursor Workflow
Appearance & Vibe Foundation
Wallpaper/Photo Validators
Wallpaper/Photo Dry-Run Helpers
Future-Safety / Parked Work
Verification
```

Each group keeps individual command names visible. No command is hidden inside a group label.

## Help Text Rules

```text
help text should show stable command names
help text should group related commands
help text should avoid implying live wallpaper/photo curator implementation exists
help text should label dry-run commands clearly
help text should label validator commands clearly
help text should preserve existing examples
help text should include the new command map status command
```

## List Workflows Rules

```text
--list-workflows should remain backward-compatible
--list-workflows should group workflows clearly
--list-workflows should not hide any existing workflow
--list-workflows should keep Appearance & Vibe future-only boundaries visible
--list-workflows should keep verification commands visible
```

## Backward Compatibility Rules

```text
do not remove existing commands
do not rename existing commands
do not change command behavior
do not remove existing dashboard checks
do not change output summary format used by dashboard parsers
do not change build queue recommendation semantics
do not change dashboard health count semantics
```

## Command Categories

| Category | Command | Type |
| --- | --- | --- |
| Core Dashboard and Health | `--dashboard` | status |
| Core Dashboard and Health | `--dashboard-readability-status` | status |
| Core Dashboard and Health | `--command-map-status` | status |
| Return to Core / Roadmap | `--return-to-core-status` | status |
| Developer and Cursor Workflow | `--developer-status` | status |
| Developer and Cursor Workflow | `--cursor-workflow-status` | status |
| Lesson Planning | `--lesson-review-view` | view |
| Document and Review Workflows | `--review-notes-template-status` | status |
| Document and Review Workflows | `--document-indexing-plan-status` | status |
| Core Dashboard and Health | `--command-launcher-status` | status |
| Appearance & Vibe Foundation | `--wallpaper-photo-curator-plan-status` | status |
| Appearance & Vibe Foundation | `--wallpaper-photo-folder-design-status` | status |
| Wallpaper/Photo Dry-Run Helpers | `--wallpaper-photo-dry-run-folder-validator` | dry-run validator |
| Wallpaper/Photo Dry-Run Helpers | `--wallpaper-photo-create-folders --dry-run` | dry-run helper |
| Appearance & Vibe Foundation | `--wallpaper-photo-folder-creation-status` | status |
| Appearance & Vibe Foundation | `--wallpaper-photo-metadata-status` | status |
| Appearance & Vibe Foundation | `--wallpaper-photo-temp-queue-status` | status |
| Appearance & Vibe Foundation | `--wallpaper-photo-queue-file-status` | status |
| Wallpaper/Photo Validators | `--wallpaper-photo-queue-file-validator` | dry-run validator |
| Appearance & Vibe Foundation | `--wallpaper-photo-approve-dismiss-ui-status` | status |
| Appearance & Vibe Foundation | `--wallpaper-photo-image-processing-status` | status |
| Appearance & Vibe Foundation | `--wallpaper-photo-local-scheduler-status` | status |
| Appearance & Vibe Foundation | `--wallpaper-photo-source-fetcher-plan-status` | status |
| Appearance & Vibe Foundation | `--wallpaper-photo-source-allowlist-status` | status |
| Wallpaper/Photo Validators | `--wallpaper-photo-source-allowlist-validator` | dry-run validator |
| Appearance & Vibe Foundation | `--wallpaper-photo-simulated-discovery-status` | status |
| Wallpaper/Photo Validators | `--wallpaper-photo-simulated-discovery-validator` | dry-run validator |
| Appearance & Vibe Foundation | `--wallpaper-photo-review-ui-prototype-status` | status |
| Wallpaper/Photo Validators | `--wallpaper-photo-review-ui-state-validator` | dry-run validator |
| Appearance & Vibe Foundation | `--wallpaper-photo-image-processor-foundation-status` | status |
| Wallpaper/Photo Validators | `--wallpaper-photo-image-processing-plan-validator` | dry-run validator |
| Appearance & Vibe Foundation | `--wallpaper-photo-scheduler-foundation-status` | status |
| Wallpaper/Photo Validators | `--wallpaper-photo-scheduler-run-plan-validator` | dry-run validator |
| Appearance & Vibe Foundation | `--wallpaper-photo-notification-foundation-status` | status |
| Wallpaper/Photo Validators | `--wallpaper-photo-notification-plan-validator` | dry-run validator |
| Appearance & Vibe Foundation | `--wallpaper-photo-rotation-handoff-safety-status` | status |
| Wallpaper/Photo Validators | `--wallpaper-photo-rotation-handoff-validator` | dry-run validator |

Live wallpaper/photo curator implementation remains not started. Validators and dry-run helpers are planning/safety only.

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

- This PR improves command map discoverability only.
- This PR does not implement new live features.
- This PR does not implement the wallpaper/photo curator.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.
- This PR does not generate lesson content.
- This PR does not use student data.

## Commands Reference

```bash
bin/chief-of-staff --command-map-status
bin/chief-of-staff --help-examples-status
bin/chief-of-staff --workflow-quick-start-status
bin/chief-of-staff --help
bin/chief-of-staff --list-workflows
bin/chief-of-staff --dashboard
bash scripts/chief-of-staff-command-map-status.sh
bash scripts/chief-of-staff-help-examples-status.sh
bash scripts/chief-of-staff-workflow-quick-start-status.sh
```
