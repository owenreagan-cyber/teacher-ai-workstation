# Wallpaper/Photo Scheduler Foundation

## Purpose

This document defines a local-only planning/status foundation for future **dry-run scheduler and manual scheduler helper** behavior in the Automated Wallpaper and Photo Curator. It combines dry-run scheduler design, manual scheduler helper requirements, fictional sample scheduler run plans, and read-only validation—without implementing a real scheduler.

This PR adds scheduler foundation planning/status only. It does not implement a scheduler, add launch agents, cron jobs, or background jobs.

## Current Status

```text
Current status: Phase Q scheduler foundation only.
```

Scheduler foundation planning, fictional sample scheduler run plan, and read-only validator live in `assistant/appearance-vibe/wallpaper-photo-curator/`. No real scheduler, launch agents, cron jobs, background jobs, unattended runs, or notifications exist yet.

## Relationship to Local Automation Scheduler Plan

Phase J defined local automation scheduler planning with dry-run first and never-run-unattended rules. Phase Q defines scheduler run intents, cadence options, pause/disable behavior, and preflight checks before any scheduler runtime. See `docs/wallpaper-photo-local-automation-scheduler-plan.md`.

## Relationship to Image Processor Foundation

Phase P defined image processor foundation with output intents and manual-only gates. A future scheduler must not process images until processor behavior is separately approved. See `docs/wallpaper-photo-image-processor-foundation.md`.

## Relationship to Review UI Prototype Plan

Phase O defined sample review UI state with simulated controls. A future scheduler must not write queues or approve candidates until review UI and queue write behavior are separately approved. See `docs/wallpaper-photo-live-local-review-ui-prototype-plan.md`.

## Future Dry-Run Scheduler Concept

```text
source allowlist status
→ simulated discovery status
→ review UI prototype status
→ image processor foundation status
→ queue file status
→ metadata status
→ dry-run scheduler run intent
→ report what would run
→ no background job
→ no unattended run
→ no writes
→ human review
→ future manual scheduler helper requires separate approval
```

This PR does not execute scheduling.

## Future Manual Scheduler Helper Concept

```text
manual scheduler helper may only be considered after:
1. dry-run scheduler run plan is approved
2. cadence options are approved
3. pause/disable behavior is approved
4. preflight checks are approved
5. notification boundaries are approved separately
6. queue write behavior is approved separately
7. scheduler launch method is approved separately
```

## Scheduler Run Intent

Required future fields:

```text
run_intent_id
mode
cadence
scheduler_enabled
scheduler_paused
manual_run_required
would_install_launch_agent
would_install_cron_job
would_start_background_job
would_send_notification
would_make_network_calls
would_fetch_images
would_process_images
would_write_queues
would_change_wallpaper
would_modify_photos
preflight_checks
blocked_reason
manual_approval_required
notes
```

Foundation rules:

```text
mode must be simulated
scheduler_enabled must be false
scheduler_paused must be true
manual_run_required must be true
would_install_launch_agent must be false
would_install_cron_job must be false
would_start_background_job must be false
would_send_notification must be false
would_make_network_calls must be false
would_fetch_images must be false
would_process_images must be false
would_write_queues must be false
would_change_wallpaper must be false
would_modify_photos must be false
manual_approval_required must be true
```

## Cadence Options

```text
manual_only
daily_dry_run
weekly_dry_run
on_demand_only
paused
disabled
```

No cadence is enabled in this PR. Sample scheduler plan is fictional/local-only.

## Pause and Disable Rules

Scheduler remains paused in all sample run intents. Disabled and paused cadence examples show how future pause/disable behavior would be represented without enabling any scheduler runtime.

## Required Preflight Checks

```text
dashboard passes
source allowlist status passes
simulated discovery status passes
review UI prototype status passes
image processor foundation status passes
queue file status passes
metadata status passes
folder creation status passes
local repo is clean
scheduler remains paused if any check fails
```

## Never-Run-Unattended Rules

```text
no unattended source fetching
no unattended image downloading
no unattended image processing
no unattended queue writes
no unattended deletion
no unattended wallpaper changes
no unattended Photos changes
no unattended Reddit or Devvit use
no unattended network calls
```

## Failure Handling

If any preflight check fails, the fictional scheduler run plan reports the scheduler as paused with a blocked reason. No unattended retry, background job, or notification is sent in this PR.

## Manual-Only Approval Gates

```text
1. Approve scheduler foundation.
2. Approve dry-run scheduler report fields.
3. Approve manual scheduler helper concept.
4. Approve cadence options.
5. Approve pause and disable behavior.
6. Approve required preflight checks.
7. Approve future notification behavior separately.
8. Approve future queue write behavior separately.
9. Approve future launch method separately.
10. Approve future real scheduler implementation separately.
```

## Blocked Automatic Actions

```text
no real scheduler
no launch agents
no cron jobs
no background jobs
no unattended runs
no notifications
no network calls
no URL fetching
no image fetching
no image downloading
no image processing
no file reads
no file writes
no queue writes
no Reddit integration
no Devvit integration
no macOS wallpaper changes
no Photos changes
```

## What This PR Does Not Implement

- This PR adds scheduler foundation planning/status only.
- This PR does not implement a scheduler.
- This PR does not add launch agents.
- This PR does not add cron jobs.
- This PR does not add background jobs.
- This PR does not run unattended.
- This PR does not send notifications.
- This PR does not make network calls.
- This PR does not fetch, download, or process images.
- This PR does not read or write image files.
- This PR does not write queues.
- This PR does not add Reddit or Devvit integration.
- This PR does not change macOS wallpaper or Photos.
- Sample scheduler plan is fictional/local-only.

## Future Implementation Phases

```text
Phase Q: Scheduler foundation
Phase R: Notification foundation
Phase S: Rotation handoff and safety audit
Phase T: Future dry-run scheduler implementation, only after separate approval
Phase U: Future manual scheduler helper implementation, only after separate approval
Phase V: Future launch method implementation, only after separate approval
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-scheduler-foundation-status
bin/chief-of-staff --wallpaper-photo-scheduler-run-plan-validator
bin/chief-of-staff --wallpaper-photo-local-scheduler-status
bin/chief-of-staff --wallpaper-photo-image-processor-foundation-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-scheduler-foundation-status.sh
bash scripts/wallpaper-photo-scheduler-run-plan-validator.sh
```
