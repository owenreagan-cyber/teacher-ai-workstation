# Dashboard Section Summary Polish

## Purpose

This document defines a dashboard section summary polish pass after the workflow quick-start guide. It adds compact high-level summary lines for major dashboard groups while preserving every individual check line and PASS/WARN/FAIL semantics.

This PR adds dashboard section summary polish only. This pass is about preserving every dashboard check, preserving PASS/WARN/FAIL semantics, and preserving command behavior while enforcing no command removals and no command renames.

## Current Status

```text
Current status: dashboard section summary polish complete.
```

Teacher planning command organization improves lesson-planning command discoverability. See `docs/teacher-planning-command-organization.md`.

The dashboard prints `Section summary:` lines after major groups using in-group PASS/WARN/FAIL deltas.

## Why Section Summaries Exist

After the workflow quick-start guide, the dashboard runs 54+ checks. Compact section summaries make it easier to see which major group is healthy without hiding individual status lines.

## Summary Goals

```text
make major dashboard groups easier to scan
show high-level section health
preserve every individual check line
preserve final PASS/WARN/FAIL summary
make warnings and failures obvious
keep next recommended PR visible
avoid hiding detailed status lines
avoid changing check behavior
```

## Section Summary Rules

```text
each major section may have a compact summary line
summary lines must not replace individual check lines
summary lines must not hide failures
summary lines must not hide warnings
summary lines should use PASS/WARN/FAIL counts when possible
summary labels should be stable and readable
final health summary must remain parseable
```

## Major Dashboard Sections

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

Section summary lines use these stable group names.

## Lesson Planning Status Planning Index

The Lesson Planning Status dashboard group includes Curriculum Builder foundation status. For maintainer navigation:

- Curriculum Builder planning index: `docs/curriculum-builder-canonical-planning-index.md`
- Approval gate required before implementation: `docs/curriculum-builder-approval-gate.md`
- Status command to verify readiness: `bin/chief-of-staff --curriculum-builder-foundation-status`

See also `docs/chief-of-staff-dashboard.md` for dashboard planning index visibility.

## Chief of Staff Command Surfaces

Dashboard and grouped status commands are read-only proof surfaces. They report PASS/WARN/FAIL only and do not activate parked tracks, implementation, wallpaper runtime, lesson generation, or dashboard behavior changes.

## Failure and Warning Visibility Rules

```text
failures must remain visible in their original status lines
warnings must remain visible in their original status lines
section summaries must not turn failures into passes
section summaries must not reduce final fail count
section summaries must not reduce final warning count
dashboard should still exit nonzero on failures if that is current behavior
```

## Backward Compatibility Rules

```text
do not remove existing status scripts
do not remove dashboard checks
do not remove commands
do not rename commands
do not change command behavior
do not change final summary format
do not change PASS/WARN/FAIL semantics
do not change build queue recommendation semantics
```

## Blocked Changes

```text
no command removals
no command renames
no behavior changes
no dashboard count regression
no PASS/WARN/FAIL semantic changes
no hidden failures
no hidden warnings
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

- This PR adds dashboard section summary polish only.
- This PR does not implement new live features.
- This PR does not implement the wallpaper/photo curator.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.
- This PR does not generate lesson content.
- This PR does not use student data.

## Commands Reference

```bash
bin/chief-of-staff --dashboard-section-summary-status
bin/chief-of-staff --teacher-planning-command-status
bin/chief-of-staff --dashboard
bin/chief-of-staff --workflow-quick-start-status
bash scripts/dashboard-section-summary-status.sh
bash scripts/teacher-planning-command-organization-status.sh
```
