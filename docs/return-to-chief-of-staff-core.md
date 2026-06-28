# Return to Chief of Staff / Teacher Workstation Core

## Purpose

This document marks a planning/status checkpoint after completing the Appearance & Vibe wallpaper/photo curator foundation stack. It pauses wallpaper/photo work for now and returns build priority to Chief of Staff / Teacher Workstation core workflows.

This PR adds return-to-core planning/status only. It does not implement new apps, automation, fetchers, image processing, schedulers, notifications, or live curator behavior.

## Current Status

```text
Current status: return to Chief of Staff / Teacher Workstation core planning/status only.
```

Appearance & Vibe wallpaper/photo curator foundation stack is complete for now. Live wallpaper/photo curator implementation is not started.

## Why Appearance & Vibe Is Paused

The wallpaper/photo curator needed a full local planning/status foundation before any live implementation. That foundation stack is now complete. Pausing here avoids scope creep into fetchers, processors, schedulers, notifications, or macOS automation before explicit approval and before Chief of Staff / Teacher Workstation core polish catches up.

## Completed Wallpaper/Photo Foundation Stack

```text
Curator plan: complete
Folder design: complete
Dry-run folder validator: complete
Manual folder creation helper: complete
Metadata schema and sample records: complete
Temp queue rules: complete
Queue file format and dry-run validator: complete
Approve/Dismiss UI design: complete
Image processing rules: complete
Local automation scheduler plan: complete
Approved-source fetcher plan: complete
Source allowlist foundation: complete
Simulated approved-source discovery plan: complete
Review UI prototype plan: complete
Image processor foundation: complete
Scheduler foundation: complete
Notification foundation: complete
Rotation handoff and safety audit: complete
```

## What Is Not Implemented

- No real fetcher exists.
- No real image processor exists.
- No real scheduler exists.
- No real notifications exist.
- No live UI exists.
- No macOS wallpaper or Photos automation exists.
- No live queue writes or automatic approve/dismiss behavior exists.
- Reddit remains a possible future source only.
- Devvit remains a possible future Reddit-native companion only.

## Core Workstation Priorities

Candidate future core areas:

```text
Chief of Staff dashboard readability
Teacher planning command organization
Lesson review workflow polish
Local document indexing follow-up
Review notes workflow polish
Command launcher consistency
Project memory cleanup
Testing/checklist consolidation
```

## Recommended Next Core PR

```text
Chief of Staff dashboard readability pass
```

Suggested scope:

```text
Improve dashboard readability and section grouping after the large Appearance & Vibe expansion. No new major feature behavior, no live wallpaper/photo curator implementation, no external integrations, no network calls, no student data, and no automation.
```

## Safety Boundaries

```text
no live wallpaper/photo curator implementation
no image fetching
no image downloading
no image processing
no scheduler implementation
no notifications
no macOS wallpaper changes
no Photos changes
no Reddit integration
no Devvit integration
no network calls
no API clients
no OAuth
no secrets
no student data
```

## Parked Future Work

- Appearance & Vibe live wallpaper/photo curator implementation remains future-only until explicitly approved.
- 3D Design Factory Agent remains parked until Chief of Staff and Teacher Workstation foundations are mature.
- Reddit may be a future source only.
- Devvit may be a future Reddit-native companion only.

## Commands Reference

```bash
bin/chief-of-staff --return-to-core-status
bin/chief-of-staff --dashboard
bash scripts/return-to-chief-of-staff-core-status.sh
```
