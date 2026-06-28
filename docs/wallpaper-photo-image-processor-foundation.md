# Wallpaper/Photo Image Processor Foundation

## Purpose

This document defines a local-only planning/status foundation for future **dry-run and manual image processing** in the Automated Wallpaper and Photo Curator. It combines dry-run processor design, manual processor requirements, fictional sample processing plans, and read-only validation—without implementing real image processing.

This PR adds image processor foundation planning/status only. It does not implement real image processing, read real image files, or write image files.

## Current Status

```text
Current status: Phase P image processor foundation only.
```

Image processor foundation planning, fictional sample processing plan, and read-only validator live in `assistant/appearance-vibe/wallpaper-photo-curator/`. No file reads, file writes, conversion, resizing, cropping, previews, or processed outputs exist yet.

## Relationship to Image Processing Rules

Phase I defined image processing rules for approved candidates. Phase P defines how future dry-run and manual processors would report output intents before any file operations. See `docs/wallpaper-photo-image-processing-rules.md`.

## Relationship to Review UI Prototype Plan

Phase O defined sample review UI state with simulated approve/dismiss controls. Phase P shows how approved candidates would map to processing input contracts and output intents without processing. See `docs/wallpaper-photo-live-local-review-ui-prototype-plan.md`.

## Relationship to Scheduler Foundation

Phase Q defines scheduler foundation with run intents, cadence options, and preflight checks. A future scheduler must not process images until processor behavior is separately approved. See `docs/wallpaper-photo-scheduler-foundation.md`.

## Relationship to Metadata Schema

Processing input contracts extend metadata fields such as `candidate_id`, `candidate_type`, dimensions, fit scores, and risk fields from `metadata-schema.json`. Output intents describe future targets before processed files exist.

## Future Dry-Run Processor Concept

```text
sample review UI state
→ sample metadata record
→ image processing rules
→ eligibility check
→ output intent calculation
→ crop/fit intent report
→ duplicate/watermark risk report
→ no file reads
→ no file writes
→ human review
→ future manual processor requires separate approval
```

This PR does not execute processing.

## Future Manual Processor Concept

```text
manual processor may only be considered after:
1. dry-run processing plan is approved
2. input contract is approved
3. output folders are approved
4. crop/fit strategy is approved
5. file write behavior is approved
6. rollback/deletion rules are approved
7. manual-only command behavior is approved
```

## Processing Input Contract

Required future fields:

```text
candidate_id
candidate_type
source_id
review_status
review_decision
content_rating
nsfw_flag
license_status
permission_note
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
processing_status
processing_notes
```

## Processing Output Intent

Output-intent fields:

```text
output_intent_id
candidate_id
target_profile
target_use
intended_width
intended_height
intended_format
fit_strategy
crop_strategy
would_write_file
would_overwrite_file
would_delete_source
blocked_reason
manual_approval_required
notes
```

Foundation rules:

```text
would_write_file must be false in this PR
would_overwrite_file must be false in this PR
would_delete_source must be false in this PR
manual_approval_required must be true
```

## Wallpaper Output Intent

```text
target_profile: wallpaper_landscape
target_use: wallpaper_rotation
preferred aspect ratio: 16:9
minimum target: 1920x1080
stronger target: 3840x2160
fit strategy must be report-only
crop strategy must be report-only
```

## Photo Widget Output Intent

```text
target_profile: photo_widget
target_use: photo_widget_rotation
preferred shapes: 1:1 and 4:5
minimum target: 1024x1024
fit strategy must be report-only
crop strategy must be report-only
```

## Crop and Fit Decision Rules

Fit and crop strategies are report-only labels in this PR. They describe intended non-destructive adjustments without reading, converting, resizing, or cropping real image files.

## Duplicate and Watermark Risk Handling

```text
duplicate_risk 0-39: report as low risk
duplicate_risk 40-69: require review
duplicate_risk 70-100: block future processing until reviewed
watermark_risk 0-39: report as low risk
watermark_risk 40-69: require review
watermark_risk 70-100: block future processing until reviewed
```

## Manual-Only Approval Gates

```text
1. Approve image processor foundation.
2. Approve dry-run processing report fields.
3. Approve manual processor input contract.
4. Approve output intent fields.
5. Approve wallpaper output rules.
6. Approve photo-widget output rules.
7. Approve crop/fit strategy.
8. Approve duplicate/watermark risk thresholds.
9. Approve future file write behavior separately.
10. Approve future real image processing separately.
```

## Blocked Automatic Actions

```text
no real image processing
no file reads from real image paths
no image output writes
no conversion
no resizing
no cropping
no preview rendering
no file deletion
no folder scanning
no queue writes
no network calls
no Reddit integration
no Devvit integration
no scheduler behavior
no notifications
no macOS wallpaper changes
no Photos changes
```

## What This PR Does Not Implement

- This PR adds image processor foundation planning/status only.
- This PR does not implement real image processing.
- This PR does not read real image files.
- This PR does not write image files.
- This PR does not convert, resize, crop, or preview images.
- This PR does not create processed outputs.
- This PR does not delete, move, or rename files.
- This PR does not scan folders.
- This PR does not write queues.
- This PR does not make network calls.
- This PR does not add Reddit or Devvit integration.
- This PR does not add scheduler behavior.
- This PR does not send notifications.
- Sample processing plan is fictional/local-only.

## Future Implementation Phases

```text
Phase P: Image processor foundation
Phase Q: Scheduler foundation
Phase R: Notification foundation
Phase S: Rotation handoff and safety audit
Phase T: Future dry-run image processor implementation, only after separate approval
Phase U: Future manual image processor implementation, only after separate approval
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-image-processor-foundation-status
bin/chief-of-staff --wallpaper-photo-image-processing-plan-validator
bin/chief-of-staff --wallpaper-photo-scheduler-foundation-status
bin/chief-of-staff --wallpaper-photo-scheduler-run-plan-validator
bin/chief-of-staff --wallpaper-photo-image-processing-status
bin/chief-of-staff --wallpaper-photo-review-ui-prototype-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-image-processor-foundation-status.sh
bash scripts/wallpaper-photo-image-processing-plan-validator.sh
bash scripts/wallpaper-photo-scheduler-foundation-status.sh
bash scripts/wallpaper-photo-scheduler-run-plan-validator.sh
```
