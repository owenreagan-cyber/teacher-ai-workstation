# Wallpaper/Photo Local Automation Scheduler Plan

## Purpose

This document defines a planning/status design for future local automation scheduling in the **Automated Wallpaper and Photo Curator**. It covers user-controlled cadence, dry-run checks, safe notification boundaries, never-running-unattended rules, and approval gates—without implementing a scheduler.

This PR adds scheduler planning only. It does not implement a scheduler, launch agents, cron jobs, background jobs, or unattended runs.

## Current Status

```text
Current status: Phase J local automation scheduler plan only.
```

Scheduler plan lives in this document and the read-only status script. No scheduler, notifications, or automated curator runs exist yet.

## Relationship to Image Processing Rules

Phase I defined image processing rules for approved candidates. Phase J defines when a future scheduler might trigger dry-run checks or report-only workflows—not live processing. Processing must not run until image processing rules and live processor implementation are separately approved.

## Relationship to Approve/Dismiss UI Design

Phase H defined a future review UI. A future scheduler must not approve, dismiss, block, or write queue decisions automatically. Human review remains required before any candidate moves toward processing.

## Relationship to Queue File Format

Phase G defined queue file format and dry-run validation. A future scheduler might report queue file validation status during preflight, but must not write queue files or queue decisions in this PR.

## Scheduling Concept

Future scheduling would follow this conceptual pipeline:

```text
manual approval
→ dry-run scheduler check
→ validate folders
→ validate queue file
→ validate metadata
→ validate approved sources
→ report candidate counts
→ report actions that would run
→ require user confirmation
→ future scheduler may run only approved safe steps
```

This PR does not execute that pipeline.

## Future Cadence Options

```text
manual only
daily dry-run
weekly dry-run
on-demand candidate refresh
pause scheduling
disable scheduling
```

```text
No cadence is enabled in this PR.
No background job is installed in this PR.
```

## Dry-Run First Rule

```text
Every future scheduled behavior must have a dry-run mode first.
Dry-run must report intended actions before any write behavior exists.
Dry-run must never fetch, download, process, delete, or move files.
Dry-run must not modify queues.
Dry-run must not modify macOS wallpaper or Photos.
```

## Preflight Checks

Future preflight checks before any scheduled run:

```text
local repo status is clean
dashboard passes
folder creation status passes
metadata status passes
temp queue status passes
queue file validator passes
approve/dismiss UI status passes
image processing status passes
source allowlist status passes when it exists
network permissions are disabled unless explicitly approved later
scheduler is paused if any safety check fails
```

## User-Controlled Approval Gates

```text
user chooses cadence
user approves dry-run output
user enables any future scheduler manually
user can pause scheduler
user can disable scheduler
user approves notification behavior separately
user approves source fetching separately
user approves image processing separately
user approves queue writes separately
```

## Notification Design Boundaries

```text
notifications are design-only in this PR
no notification command is added
future notifications should only report review-ready candidates
future notifications should not approve, dismiss, delete, fetch, download, or process anything
future notifications should include safe summary counts only
```

## Never-Run-Unattended Rules

```text
no unattended source fetching
no unattended image downloading
no unattended image processing
no unattended deletion
no unattended queue writes
no unattended wallpaper changes
no unattended Photos changes
no unattended Reddit or Devvit use
no unattended network calls
```

## Blocked Automatic Actions

```text
no automatic scheduling in this PR
no launch agents in this PR
no cron jobs in this PR
no background jobs in this PR
no notification sending in this PR
no automatic source fetching
no automatic image downloading
no automatic image processing
no automatic queue writes
no automatic deletion
no automatic wallpaper changes
no automatic Photos changes
no automatic Reddit or Devvit use
```

## Failure Handling

```text
future scheduler should stop on any failed safety check
future scheduler should prefer report-only behavior
future scheduler should never retry destructive actions automatically
future scheduler should never silently continue after failed validation
future scheduler should require clear local logs before implementation
```

## Human Approval Gates

```text
1. Approve scheduler plan.
2. Approve dry-run scheduler behavior.
3. Approve cadence options.
4. Approve pause/disable behavior.
5. Approve notification copy and safety limits.
6. Approve launch method, if any.
7. Approve queue write behavior.
8. Approve source fetching behavior.
9. Approve image processing behavior.
10. Approve macOS wallpaper/Photos integration later.
```

## What This PR Does Not Implement

- This PR adds scheduler planning only.
- This PR does not implement a scheduler.
- This PR does not add launch agents.
- This PR does not add cron jobs.
- This PR does not add background jobs.
- This PR does not run unattended.
- This PR does not send notifications.
- This PR does not fetch images.
- This PR does not download images.
- This PR does not process images.
- This PR does not convert images.
- This PR does not resize images.
- This PR does not crop images.
- This PR does not render previews.
- This PR does not create processed output files.
- This PR does not delete files.
- This PR does not scan folders.
- This PR does not write queue decisions.
- This PR does not create queue folders.
- This PR does not change macOS wallpaper settings.
- This PR does not modify Photos or photo widgets.
- This PR does not add Reddit or Devvit integration.
- This PR does not add network calls.
- This PR does not add APIs, OAuth, or secrets.

## Future Implementation Phases

```text
Phase J: Local automation scheduler plan
Phase K: Approved-source fetcher
Phase L: Live local review UI prototype
Phase M: Dry-run image processor
Phase N: Manual image processor
Phase O: Dry-run scheduler
Phase P: Manual scheduler helper
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-local-scheduler-status
bin/chief-of-staff --wallpaper-photo-image-processing-status
bin/chief-of-staff --wallpaper-photo-approve-dismiss-ui-status
bin/chief-of-staff --wallpaper-photo-queue-file-status
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-local-scheduler-status.sh
```
