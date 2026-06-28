# Wallpaper/Photo Metadata Schema

## Purpose

This document defines a local metadata schema and safe fictional sample records for the future **Automated Wallpaper and Photo Curator**. It helps Owen track candidate sources, review decisions, and fit scores without fetching or storing real images.

This PR adds schema and fictional sample records only. It does not fetch images, process images, or automate macOS wallpaper or Photos settings.

## Current Status

```text
Current status: Phase E metadata schema and sample records complete. Phase F temp queue rules complete. Phase G queue file format documented separately.
```

Schema files live in `assistant/appearance-vibe/wallpaper-photo-curator/`. Temp queue rules live in `docs/wallpaper-photo-temp-queue-rules.md`. Queue file format lives in `docs/wallpaper-photo-queue-file-format.md`. No curator runtime, live queues, or real candidate images exist yet.

## Relationship to Queue File Format

Phase G defines a queue file JSON format and dry-run validator for fictional/local queue records. Phase H defines the Approve/Dismiss review UI design. See `docs/wallpaper-photo-approve-dismiss-ui-design.md`.

## Relationship to Temp Queue Rules

Phase F defines planning rules for future temporary candidate queues (max 10 wallpaper, max 10 photo-widget, review states). Optional queue fields in the schema (`queue_name`, `queue_position`, `queue_added_at`, `queue_expires_at`, `stale_after_days`) support future queue metadata only. This PR does not create live queues or queue folders.

## Relationship to the Folder Creation Helper

Phase D created optional manual folder creation under `~/Pictures/`. Phase E defines metadata that future candidates would reference using conceptual paths such as temp queue folders. This PR does not create those folders.

## Metadata Design Principles

- Local-first and fictional samples until source rules are approved
- Every candidate traceable to source metadata
- Review decisions explicit before processing
- Fit scores guide wallpaper vs photo-widget use
- No real image URLs in samples
- Human approval required before real candidates enter rotation folders

## Required Fields

```text
schema_version
candidate_id
candidate_type
source_type
source_name
source_url
candidate_url
title
creator_name
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
reviewed_by
reviewed_at
local_temp_path
processed_output_path
created_at
updated_at
notes
```

## Optional Fields

Optional queue-related fields for future temp queue metadata (not required in v1 records):

```text
queue_name
queue_position
queue_added_at
queue_expires_at
stale_after_days
```

See `docs/wallpaper-photo-temp-queue-rules.md` for queue size limits and review rules.

## Source and Permission Fields

- `source_type`, `source_name`, `source_url`, `candidate_url`
- `license_status`, `permission_note`
- Future Reddit or Devvit sources use `future_reddit_source` or `future_devvit_companion` only in planning enums—not implemented in this PR

## Image Fit Fields

- `width`, `height`, `aspect_ratio`, `file_format`, `file_size_bytes`
- `wallpaper_fit_score`, `photo_widget_fit_score` (0–100)
- `duplicate_risk`, `watermark_risk` (0–100)

## Review Decision Fields

- `review_status`, `review_decision`, `reviewed_by`, `reviewed_at`
- Approve/dismiss/block decisions stay explicit; samples use `unreviewed` or `needs_more_info`

## Safety and Content Fields

- `content_rating`: safe, needs_review, blocked
- `nsfw_flag`: boolean; all samples are `false`
- Block unclear licenses and high watermark risk before processing

## Processing Fields

- `local_temp_path`, `processed_output_path` — conceptual strings only in samples
- Future processing workers would update these after human approval

## Storage Destination Fields

Conceptual paths align with `docs/wallpaper-photo-rotation-folder-design.md`. This PR does not create folders or write real files.

## Sample Records

`sample-records.json` contains exactly three fictional records:

1. wallpaper sample
2. photo_widget sample
3. both sample

All use `https://example.invalid/` URLs and fictional creator names. Sample records are fictional and safe.

## Validation Rules

- JSON must parse locally
- Each record includes all required fields
- Enums must match schema
- Scores must be 0–100
- Samples must not use real image URLs, Reddit, Devvit, or NSFW content

## What This PR Does Not Implement

- This PR adds schema and fictional sample records only.
- This PR does not fetch images.
- This PR does not download images.
- This PR does not process images.
- This PR does not create wallpaper/photo folders.
- This PR does not delete files.
- This PR does not scan folders.
- This PR does not send notifications.
- This PR does not change macOS wallpaper settings.
- This PR does not modify Photos or photo widgets.
- This PR does not add Reddit or Devvit integration.
- This PR does not add network calls.
- This PR does not add APIs, OAuth, or secrets.

## Future Approval Gates

```text
1. Approve metadata schema v1.
2. Approve real candidate metadata format.
3. Approve source URL allowlist rules.
4. Approve temp queue metadata writes.
5. Approve review decision persistence.
6. Approve processing output path updates.
7. Approve notification hooks.
8. Approve image processing metadata.
9. Approve any source integration.
10. Approve scheduled automation.
```

## Future Implementation Phases

```text
Phase E: Metadata schema and sample records
Phase F: Temp queue rules
Phase G: Queue file format and dry-run validator
Phase H: Approve/Dismiss UI design
Phase I: Image processing rules
Phase J: Local automation scheduler
Phase K: Approved-source fetcher
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --wallpaper-photo-temp-queue-status
bin/chief-of-staff --wallpaper-photo-queue-file-status
bin/chief-of-staff --wallpaper-photo-queue-file-validator
bin/chief-of-staff --wallpaper-photo-approve-dismiss-ui-status
bin/chief-of-staff --wallpaper-photo-folder-creation-status
bin/chief-of-staff --wallpaper-photo-dry-run-folder-validator
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-metadata-status.sh
bash scripts/wallpaper-photo-temp-queue-status.sh
bash scripts/wallpaper-photo-queue-file-status.sh
bash scripts/wallpaper-photo-queue-file-validator.sh
bash scripts/wallpaper-photo-approve-dismiss-ui-status.sh
```
