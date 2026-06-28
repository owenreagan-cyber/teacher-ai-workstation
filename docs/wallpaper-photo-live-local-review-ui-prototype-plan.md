# Wallpaper/Photo Live Local Review UI Prototype Plan

## Purpose

This document defines a local-only planning/status foundation for a future **live local review UI prototype** in the Automated Wallpaper and Photo Curator. It describes what a future review UI would show, how fictional sample UI state should be structured, and how simulated approve/dismiss controls would behave—without implementing a live UI, server, or image rendering.

This PR adds review UI prototype planning/status only. It does not implement a live UI, web server, native app, image rendering, or preview rendering.

## Current Status

```text
Current status: Phase O live local review UI prototype plan only.
```

Review UI prototype planning, fictional sample UI state, and read-only validator live in `assistant/appearance-vibe/wallpaper-photo-curator/`. No live UI, server, queue writes, or image rendering exist yet.

## Relationship to Approve/Dismiss UI Design

Phase H defined Approve/Dismiss UI design concepts for future candidate review. Phase O defines how those concepts would appear in sample UI state with simulated action labels only. See `docs/wallpaper-photo-approve-dismiss-ui-design.md`.

## Relationship to Simulated Discovery

Phase N defined simulated approved-source discovery with fictional candidate-count placeholders. Phase O shows how discovery context would appear in review UI state without real discovery. See `docs/wallpaper-photo-simulated-approved-source-discovery-plan.md`.

## Relationship to Source Allowlist Foundation

Phase Q defined the local source allowlist file format. Phase O references fictional allowlist entries in candidate card source context without fetching. See `docs/wallpaper-photo-source-allowlist-foundation.md`.

## Relationship to Image Processing Rules

Phase I defined image processing rules for approved candidates. Phase O includes simulated links to processing rules context without live processing. See `docs/wallpaper-photo-image-processing-rules.md`.

## Future UI Concept

```text
sample discovery report
→ sample queue records
→ sample metadata records
→ local review UI state
→ candidate cards
→ simulated approve/dismiss controls
→ no queue writes
→ no file changes
→ human review
→ future UI implementation requires separate approval
```

This PR does not implement the UI runtime.

## Sample UI State

Sample UI state lives in `sample-review-ui-state.json` with `mode: simulated` and `network_calls: false`. Sample UI state is fictional/local-only.

## Candidate Card Fields

```text
candidate_id
candidate_type
source_id
source_name
source_type
review_status
review_decision
content_rating
nsfw_flag
license_status
permission_note
wallpaper_fit_score
photo_widget_fit_score
duplicate_risk
watermark_risk
candidate_count_context
image_preview_status
actions_available
blocked_actions
notes
```

## Review Actions

```text
approve_simulated
dismiss_simulated
needs_more_info
open_metadata_details
open_source_details
open_processing_rules
```

These are simulated action labels only. They do not write queues, delete files, or render images.

## Safety and Boundary Labels

```text
No live UI
No server
No image rendering
No image previews
No queue writes
No file deletion
No network calls
No Reddit integration
No Devvit integration
No scheduler
No notifications
```

## Empty, Loading, and Error States

```text
empty queue
no approved sources
discovery report missing
metadata missing
source allowlist missing
candidate blocked
candidate needs review
validator failed
```

## Blocked Automatic Actions

```text
no live UI implementation
no app runtime
no web server
no image rendering
no preview rendering
no approve queue write
no dismiss queue write
no image fetching
no image downloading
no image processing
no file deletion
no network calls
no scheduler behavior
no notifications
no Reddit integration
no Devvit integration
```

## Human Approval Gates

```text
1. Approve review UI prototype plan.
2. Approve sample UI state fields.
3. Approve candidate card layout.
4. Approve simulated action labels.
5. Approve empty/loading/error states.
6. Approve any future live UI runtime separately.
7. Approve any future image rendering separately.
8. Approve any future queue write behavior separately.
9. Approve any future file deletion separately.
10. Approve any future scheduler/notification behavior separately.
```

## What This PR Does Not Implement

- This PR adds review UI prototype planning/status only.
- This PR does not implement a live UI.
- This PR does not implement a web server.
- This PR does not implement a native app.
- This PR does not render images.
- This PR does not render previews.
- This PR does not approve or dismiss real candidates.
- This PR does not write queues.
- This PR does not fetch or download images.
- This PR does not process images.
- This PR does not make network calls.
- This PR does not add Reddit integration.
- This PR does not add Devvit integration.
- This PR does not add scheduler behavior.
- This PR does not send notifications.
- Sample UI state is fictional/local-only.

## Future Implementation Phases

```text
Phase O: Live local review UI prototype plan
Phase P: Image processor foundation
Phase Q: Scheduler foundation
Phase R: Notification foundation
Phase S: Rotation handoff and safety audit
Phase T: Future live UI implementation, only after separate approval
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-review-ui-prototype-status
bin/chief-of-staff --wallpaper-photo-review-ui-state-validator
bin/chief-of-staff --wallpaper-photo-simulated-discovery-status
bin/chief-of-staff --wallpaper-photo-source-allowlist-status
bin/chief-of-staff --wallpaper-photo-approve-dismiss-ui-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-review-ui-prototype-status.sh
bash scripts/wallpaper-photo-review-ui-state-validator.sh
```
