# Wallpaper/Photo Image Processing Rules

## Purpose

This document defines planning/status rules for future image processing in the **Automated Wallpaper and Photo Curator**. It covers output sizing, format preferences, aspect ratio handling, crop/fit strategy, duplicate and watermark risk review, metadata handoff, and approval gates—without implementing live processing.

This PR adds image processing rules only. It does not implement live image processing, fetch images, or create processed output files.

## Current Status

```text
Current status: Phase I image processing rules only.
```

Rules live in this document and the read-only status script. No live processor, image conversion, resizing, cropping, or preview rendering exists yet.

## Relationship to Approve/Dismiss UI Design

Phase H defined a future review UI with Approve, Dismiss, Block, and Needs More Info decisions. Phase I defines what may happen **after** a candidate is approved for processing. Processing must not run until Approve/Dismiss UI behavior and queue write rules are separately approved.

## Relationship to Queue File Format

Phase G defined queue file format and dry-run validation. Future processing would read approved candidates from validated queue records. This PR does not write queue decisions or process queue files.

## Relationship to Metadata Schema

Processing rules reference metadata fields in `metadata-schema.json` and queue records. Required metadata must be present and pass safety checks before any future processor runs.

## Processing Concept

Future processing would follow this conceptual pipeline:

```text
approved candidate
→ verify metadata
→ verify source and permission status
→ verify content safety
→ verify duplicate/watermark risk
→ choose wallpaper/photo-widget output profile
→ calculate fit/crop plan
→ user confirms processing rules
→ future processor writes processed output
→ metadata records output path
```

This PR does not execute that pipeline.

## Wallpaper Output Rules

Future wallpaper targets:

```text
primary wallpaper profile: 16:9 landscape
preferred minimum width: 1920
preferred minimum height: 1080
preferred stronger target: 3840x2160 when available
avoid upscaling low-resolution sources without future approval
preserve original aspect ratio unless crop plan is approved
```

## Photo Widget Output Rules

Future photo-widget targets:

```text
photo widget profile: flexible square/portrait-friendly crop
preferred minimum width: 1024
preferred minimum height: 1024
avoid cropping faces or focal subjects without review
prefer safe center crop only when metadata or future preview supports it
```

## Format Preferences

```text
preferred processed wallpaper format: jpg or png depending on source and quality
preferred processed photo widget format: jpg or png depending on source and quality
avoid animated formats for initial processing
preserve source format only when compatible with destination
future conversion rules require explicit approval
```

## Aspect Ratio Rules

```text
16:9 is preferred for wallpaper
1:1 and 4:5 may be useful for photo widgets
portrait and landscape sources require separate fit decisions
extreme aspect ratios should require manual review
unknown dimensions should block processing
```

## Crop and Fit Rules

```text
no automatic destructive crop without future approval
center crop may be allowed later only with preview/review support
fit-with-padding may be safer than crop for some sources
low-resolution images should be flagged before processing
unknown focal point should require review
```

## Duplicate Risk Rules

```text
duplicate_risk 0-39: low risk
duplicate_risk 40-69: needs review
duplicate_risk 70-100: block processing until reviewed
```

## Watermark Risk Rules

```text
watermark_risk 0-39: low risk
watermark_risk 40-69: needs review
watermark_risk 70-100: block processing until reviewed
```

## Source and Permission Requirements

```text
license_status must not be unknown_needs_review
permission_note must be present
content_rating must be safe
nsfw_flag must be false
blocked content must not be processed
source must be approved or manually reviewed in a future source policy
```

## Metadata Handoff Requirements

Required metadata before future processing:

```text
candidate_id
candidate_type
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
review_status
review_decision
local_temp_path
processed_output_path
notes
```

Future processors would update `processed_output_path` only after human approval and live processor implementation.

## Blocked Automatic Actions

```text
no automatic processing in this PR
no automatic conversion in this PR
no automatic resizing in this PR
no automatic cropping in this PR
no automatic deletion
no automatic queue writes
no automatic wallpaper changes
no automatic Photos changes
no automatic notifications
no automatic Reddit or Devvit use
```

## Human Approval Gates

```text
1. Approve image processing rules.
2. Approve output profiles.
3. Approve format preferences.
4. Approve crop/fit strategy.
5. Approve duplicate-risk thresholds.
6. Approve watermark-risk thresholds.
7. Approve processing handoff metadata.
8. Approve live processor implementation.
9. Approve processed output folder writes.
10. Approve macOS wallpaper/Photos integration later.
```

## What This PR Does Not Implement

- This PR adds image processing rules only.
- This PR does not implement live image processing.
- This PR does not fetch images.
- This PR does not download images.
- This PR does not convert images.
- This PR does not resize images.
- This PR does not crop images.
- This PR does not render previews.
- This PR does not create processed output files.
- This PR does not delete files.
- This PR does not scan folders.
- This PR does not write queue decisions.
- This PR does not create queue folders.
- This PR does not send notifications.
- This PR does not change macOS wallpaper settings.
- This PR does not modify Photos or photo widgets.
- This PR does not add Reddit or Devvit integration.
- This PR does not add network calls.
- This PR does not add APIs, OAuth, or secrets.

Phase I defined image processing rules for approved candidates. Phase J defines local automation scheduler planning. Phase K defines approved-source fetcher planning. See `docs/wallpaper-photo-local-automation-scheduler-plan.md` and `docs/wallpaper-photo-approved-source-fetcher-plan.md`. Future processing must not run on a schedule until scheduler, source, and processor behavior are separately approved.

## Future Implementation Phases

```text
Phase I: Image processing rules
Phase J: Local automation scheduler
Phase K: Approved-source fetcher
Phase L: Live local review UI prototype
Phase M: Dry-run image processor
Phase N: Manual image processor
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-image-processing-status
bin/chief-of-staff --wallpaper-photo-local-scheduler-status
bin/chief-of-staff --wallpaper-photo-source-fetcher-plan-status
bin/chief-of-staff --wallpaper-photo-approve-dismiss-ui-status
bin/chief-of-staff --wallpaper-photo-queue-file-status
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-image-processing-status.sh
bash scripts/wallpaper-photo-local-scheduler-status.sh
bash scripts/wallpaper-photo-source-fetcher-plan-status.sh
```
