# Wallpaper/Photo Notification Foundation

## Purpose

This document defines a local-only planning/status foundation for future **notification design and dry-run notification helper** behavior in the Automated Wallpaper and Photo Curator. It combines notification copy rules, review-ready summary fields, user-control rules, fictional sample notification plans, and read-only validation—without sending real notifications.

This PR adds notification foundation planning/status only. It does not send notifications, call macOS notification tools, use `osascript`, or use terminal-notifier.

## Current Status

```text
Current status: Phase R notification foundation only.
```

Notification foundation planning, fictional sample notification plan, and read-only validator live in `assistant/appearance-vibe/wallpaper-photo-curator/`. No real notifications, notification mechanism, scheduler runtime, or unattended runs exist yet.

## Relationship to Scheduler Foundation

Phase Q defined scheduler foundation with run intents, cadence options, and preflight checks. Phase R defines what future notifications would report before any notification mechanism exists. A future scheduler must not send notifications until notification behavior is separately approved. See `docs/wallpaper-photo-scheduler-foundation.md`.

## Relationship to Review UI Prototype Plan

Phase O defined sample review UI state with simulated controls. Phase R shows how review-ready summary fields would appear in fictional notification previews without opening a live UI or approving candidates. See `docs/wallpaper-photo-live-local-review-ui-prototype-plan.md`.

## Relationship to Image Processor Foundation

Phase P defined image processor foundation with output intents and manual-only gates. Notification previews may reference fictional counts only—they must not trigger image processing. See `docs/wallpaper-photo-image-processor-foundation.md`.

## Future Notification Concept

```text
scheduler foundation status
→ review UI prototype status
→ simulated discovery status
→ image processor foundation status
→ notification plan
→ dry-run notification preview
→ no notification sent
→ no approve/dismiss action
→ no queue write
→ human review
→ future real notification helper requires separate approval
```

This PR does not send notifications.

## Future Dry-Run Notification Helper Concept

```text
dry-run notification helper may only be considered after:
1. notification copy is approved
2. notification types are approved
3. review-ready summary fields are approved
4. user controls are approved
5. scheduler integration is approved separately
6. real notification mechanism is approved separately
7. notification permissions are approved separately
```

## Notification Types

```text
review_ready
dry_run_complete
safety_blocked
scheduler_paused
manual_attention_needed
disabled
```

No notification type is enabled in this PR.

## Review-Ready Summary Fields

```text
notification_id
notification_type
mode
would_send_notification
candidate_count
wallpaper_candidate_count
photo_widget_candidate_count
blocked_candidate_count
needs_review_count
source_count
message_title
message_body
action_labels
blocked_actions
manual_approval_required
notes
```

Foundation rules:

```text
mode must be simulated
would_send_notification must be false
manual_approval_required must be true
notifications must not approve candidates
notifications must not dismiss candidates
notifications must not delete files
notifications must not fetch images
notifications must not process images
notifications must not write queues
```

## Notification Copy Rules

```text
copy must be short
copy must be non-alarming
copy must summarize counts only
copy must not include real image URLs
copy must not include private data
copy must not include student data
copy must not imply automation is active
copy must clearly say review is manual
```

## User Control Rules

```text
notifications default to disabled
user can keep notifications disabled
user can preview notification copy in dry-run mode
user must approve notification type
user must approve notification timing
user must approve notification mechanism
user must approve any scheduler connection separately
```

## Never-Action-From-Notification Rules

```text
no approve from notification
no dismiss from notification
no delete from notification
no image download from notification
no image processing from notification
no queue write from notification
no wallpaper change from notification
no Photos change from notification
no Reddit or Devvit action from notification
```

## Failure Handling

If any preflight or safety check fails, notifications remain disabled. Dry-run notification previews must report blocked status and require manual review. No fallback notification mechanism may activate automatically.

## Manual-Only Approval Gates

```text
1. Approve notification foundation.
2. Approve dry-run notification report fields.
3. Approve notification types.
4. Approve notification copy rules.
5. Approve user control rules.
6. Approve never-action-from-notification rules.
7. Approve future notification mechanism separately.
8. Approve future scheduler connection separately.
9. Approve future notification permissions separately.
10. Approve future real notification implementation separately.
```

## Blocked Automatic Actions

```text
no real notifications
no macOS notification calls
no osascript
no terminal-notifier
no scheduler implementation
no launch agents
no cron jobs
no background jobs
no unattended runs
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

- This PR adds notification foundation planning/status only.
- This PR does not send notifications.
- This PR does not call macOS notification tools.
- This PR does not use `osascript`.
- This PR does not use terminal-notifier.
- This PR does not implement a scheduler.
- This PR does not add launch agents, cron jobs, or background jobs.
- This PR does not run unattended.
- This PR does not make network calls.
- This PR does not fetch, download, or process images.
- This PR does not read or write image files.
- This PR does not write queues.
- This PR does not approve or dismiss real candidates.
- This PR does not add Reddit or Devvit integration.
- This PR does not change macOS wallpaper or Photos.
- Sample notification plan is fictional/local-only.

## Future Implementation Phases

```text
Phase R: Notification foundation
Phase S: Rotation handoff and safety audit
Phase T: Future dry-run notification helper implementation, only after separate approval
Phase U: Future real notification helper implementation, only after separate approval
Phase V: Future scheduler-notification connection, only after separate approval
```

Phase R defined notification foundation with review-ready summary fields and dry-run notification previews. Phase S defines rotation handoff and safety audit with readiness gates before any file handoff. See `docs/wallpaper-photo-rotation-handoff-safety-audit.md`.

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-notification-foundation-status
bin/chief-of-staff --wallpaper-photo-notification-plan-validator
bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status
bin/chief-of-staff --wallpaper-photo-rotation-handoff-validator
bin/chief-of-staff --wallpaper-photo-scheduler-foundation-status
bin/chief-of-staff --wallpaper-photo-review-ui-prototype-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-notification-foundation-status.sh
bash scripts/wallpaper-photo-notification-plan-validator.sh
bash scripts/wallpaper-photo-rotation-handoff-safety-status.sh
bash scripts/wallpaper-photo-rotation-handoff-validator.sh
```
