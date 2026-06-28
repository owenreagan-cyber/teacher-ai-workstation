# Chief of Staff Dashboard Readability Pass

## Purpose

This document defines a readability and grouping pass for the local Chief of Staff dashboard after the large Appearance & Vibe expansion. It improves scanability while preserving every existing check and command.

This PR improves dashboard readability only. This pass is about preserving all existing checks and preserving PASS/WARN/FAIL semantics while preserving existing commands.

## Current Status

```text
Current status: dashboard readability pass complete.
```

The dashboard groups core workstation, Chief of Staff workflow, lesson planning, developer/Cursor, Appearance & Vibe foundation, recommendation, and final health summary sections more clearly.

## Why This Pass Exists

The dashboard grew to 50 checks after the wallpaper/photo foundation stack. Long sequential sections made health scanning and next-step discovery harder. This pass reorganizes presentation without removing safety checks.

## Dashboard Readability Goals

```text
make the dashboard easier to scan
make high-level health obvious
group related checks into clear sections
keep long Appearance & Vibe checks readable
preserve every existing check
preserve parseable PASS/WARN/FAIL summaries
keep next recommended PR visible
avoid hiding failures
avoid reducing safety checks
```

## Grouping Rules

Dashboard groups follow this scan order:

```text
Core Workstation Status
Chief of Staff Workflow Status
Lesson Planning Status
Developer / Cursor Workflow Status
Appearance & Vibe Foundation Status
Future-Safety / Parked Work
Recommendation
Final Health Summary
```

Each group keeps individual PASS/WARN/FAIL status lines visible.

## Health Summary Rules

```text
top-level health should remain obvious
final PASS/WARN/FAIL summary must remain parseable
health count must still reflect all checks
failures must not be hidden inside groups
warnings must not be hidden inside groups
dashboard should still exit nonzero on failures if that is current behavior
```

## Appearance & Vibe Section Rules

```text
Appearance & Vibe foundation checks may be grouped together
wallpaper/photo foundation checks must remain visible
each status line must still show PASS/WARN/FAIL
live wallpaper/photo curator implementation remains not started
future Reddit and Devvit references remain future-only
```

## Backward Compatibility Rules

```text
do not remove existing status scripts
do not remove existing dashboard checks
do not rename existing commands
do not change output summary format used by dashboard parsers
do not change build queue recommendation semantics
do not change dashboard health count semantics
```

## Blocked Changes

```text
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

- This PR improves dashboard readability only.
- This PR does not implement new live features.
- This PR does not implement the wallpaper/photo curator.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.
- This PR does not generate lesson content.
- This PR does not use student data.

## Commands Reference

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --return-to-core-status
bin/chief-of-staff --dashboard-readability-status
bash scripts/chief-of-staff-dashboard-readability-status.sh
```
