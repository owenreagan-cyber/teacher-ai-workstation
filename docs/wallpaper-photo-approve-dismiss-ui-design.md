# Wallpaper/Photo Approve/Dismiss UI Design

## Purpose

This document defines a planning/status design for a future local review UI for the **Automated Wallpaper and Photo Curator**. It describes how Owen would review wallpaper and photo-widget candidates and choose Approve, Dismiss, Block, or Needs More Info—without building a live UI in this PR.

This PR adds UI design only. It does not implement a live UI, render images, or write queue decisions.

## Current Status

```text
Current status: Phase H Approve/Dismiss UI design only.
```

Design lives in this document and the read-only status script. No live UI, queue writes, or image handling exist yet.

## Relationship to Queue File Format

Phase G defined queue file JSON format and dry-run validation. Phase H describes how a future UI would read queue records from validated queue files and present them for human review. Phase O defines sample review UI state with simulated action labels only. See `docs/wallpaper-photo-live-local-review-ui-prototype-plan.md`. This PR does not write queue decisions or create live queue files.

## Relationship to Temp Queue Rules

Phase F defined temp queue limits (max 10 wallpaper, max 10 photo-widget, max 20 total) and review states. The future UI would respect those limits and map decision buttons to `review_status` and `review_decision` values defined in temp queue rules. This PR does not enforce limits at runtime.

## Relationship to Metadata Schema

The candidate detail view shows fields from `metadata-schema.json`. Queue list view shows queue-specific fields from queue records. Full metadata remains the canonical record shape; the UI design specifies which fields are visible at list vs detail level.

## Review UI Concept

A future local review UI would include:

```text
candidate list
candidate detail panel
metadata summary
source and permission summary
queue status summary
decision buttons
safety warnings
decision confirmation area
audit/history area
```

No live UI exists in this PR. The design is planning/status only.

## Candidate List View

The list view would show:

```text
candidate_id
candidate_type
queue_name
queue_position
title
source_name
content_rating
review_status
review_decision
queue_added_at
queue_expires_at
```

## Candidate Detail View

The detail view would show:

```text
candidate_id
title
creator_name
source_name
source_url
candidate_url
license_status
permission_note
content_rating
nsfw_flag
width
height
aspect_ratio
file_format
file_size_bytes
wallpaper_fit_score
photo_widget_fit_score
duplicate_risk
watermark_risk
local_temp_path
processed_output_path
notes
```

## Decision Buttons

Future decision buttons (exact labels):

```text
Approve
Dismiss
Block
Needs More Info
```

## Approve Behavior

Future intended behavior:

```text
Approve marks a candidate as approved for future processing.
Approve should not immediately change wallpaper.
Approve should not immediately modify Photos.
Approve should not delete anything.
Approve should require the candidate to have safe content status and acceptable permission notes.
Approve should write a future queue decision only after live queue behavior is approved.
```

## Dismiss Behavior

Future intended behavior:

```text
Dismiss marks a candidate as dismissed.
Dismiss should not delete anything until deletion behavior is separately approved.
Dismiss should prefer reporting and queue state changes before destructive cleanup.
Dismiss should retain source traceability metadata unless future cleanup policy says otherwise.
```

## Block Behavior

Future intended behavior:

```text
Block marks a candidate or source as blocked.
Block should require an additional confirmation before future source-level blocking.
Block should not call any external service.
Block should not delete files automatically.
Block should retain audit notes explaining why the item was blocked.
```

## Needs More Info Behavior

Future intended behavior:

```text
Needs More Info marks a candidate for review follow-up.
Needs More Info should not approve, dismiss, delete, process, or move anything.
Needs More Info should preserve notes and source traceability.
```

## Safety Warnings

The future UI should show warnings for:

```text
unknown license status
needs_review content rating
blocked content rating
nsfw_flag true
high duplicate risk
high watermark risk
missing source URL
missing permission note
external source not yet allowlisted
source-level block confirmation
deletion not implemented
macOS wallpaper changes not implemented
Photos changes not implemented
```

## Human Approval Gates

```text
1. Approve UI design.
2. Approve decision-state mapping.
3. Approve safety warning copy.
4. Approve queue write behavior.
5. Approve audit/history behavior.
6. Approve deletion/cleanup behavior.
7. Approve image preview behavior.
8. Approve processing handoff.
9. Approve notification behavior.
10. Approve any source integration.
```

## What This PR Does Not Implement

- This PR adds UI design only.
- This PR does not implement a live UI.
- This PR does not render images.
- This PR does not create live queues.
- This PR does not write queue decisions.
- This PR does not create queue folders.
- This PR does not fetch images.
- This PR does not download images.
- This PR does not process images.
- This PR does not move files.
- This PR does not delete files.
- This PR does not scan folders.
- This PR does not send notifications.
- This PR does not change macOS wallpaper settings.
- This PR does not modify Photos or photo widgets.
- This PR does not add Reddit or Devvit integration.
- This PR does not add network calls.
- This PR does not add APIs, OAuth, or secrets.

## Future Implementation Phases

```text
Phase H: Approve/Dismiss UI design
Phase I: Image processing rules
Phase J: Local automation scheduler
Phase K: Approved-source fetcher
Phase O: Live local review UI prototype plan
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-approve-dismiss-ui-status
bin/chief-of-staff --wallpaper-photo-review-ui-prototype-status
bin/chief-of-staff --wallpaper-photo-review-ui-state-validator
bin/chief-of-staff --wallpaper-photo-image-processing-status
bin/chief-of-staff --wallpaper-photo-local-scheduler-status
bin/chief-of-staff --wallpaper-photo-queue-file-status
bin/chief-of-staff --wallpaper-photo-queue-file-validator
bin/chief-of-staff --wallpaper-photo-temp-queue-status
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-approve-dismiss-ui-status.sh
bash scripts/wallpaper-photo-review-ui-prototype-status.sh
bash scripts/wallpaper-photo-review-ui-state-validator.sh
bash scripts/wallpaper-photo-image-processing-status.sh
bash scripts/wallpaper-photo-local-scheduler-status.sh
```
