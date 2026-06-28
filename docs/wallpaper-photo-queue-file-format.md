# Wallpaper/Photo Queue File Format and Dry-Run Validator

## Purpose

This document defines a local queue file format and dry-run validator for the future **Automated Wallpaper and Photo Curator**. It helps Owen plan how temporary wallpaper and photo-widget candidate queues would be represented as JSON files before any live queue behavior exists.

This PR adds queue file format and dry-run validation only. It does not create live queues, queue folders, or real candidate images.

## Current Status

```text
Current status: Phase G queue file format and dry-run validator only.
```

Queue schema and fictional sample queue live in `assistant/appearance-vibe/wallpaper-photo-curator/`. No live queues, queue folder writes, or image handling exist yet.

## Relationship to Temp Queue Rules

Phase F defined temp queue rules (max 10 wallpaper, max 10 photo-widget, max 20 total, review states, stale handling concepts). Phase G defines how those queues could be serialized as local JSON files and validated in dry-run mode. This PR does not implement live queue behavior.

## Relationship to Metadata Schema

Queue records reference the metadata schema conceptually. Each queue record includes a subset of metadata fields needed for queue position, review state, and traceability. Full metadata records in `metadata-schema.json` remain the canonical candidate shape; queue files group queue-ready fields for future review workflows.

## Relationship to Approve/Dismiss UI Design

Phase H defines how a future review UI would present queue records and support Approve, Dismiss, Block, and Needs More Info decisions. See `docs/wallpaper-photo-approve-dismiss-ui-design.md`. This PR does not implement a live UI or write queue decisions.

## Queue File Concept

A future queue file is a single JSON document describing one temporary candidate queue. It contains queue metadata (`queue_name`, `queue_type`, `max_candidates`) and an array of fictional or approved candidate records. Sample queue files in this repo are planning artifacts only.

## Queue File Structure

```text
schema_version
queue_name
queue_type
max_candidates
records
created_at
updated_at
notes
```

Allowed `queue_type` values:

```text
wallpaper
photo_widget
mixed
```

Allowed `queue_name` values for sample/planning:

```text
temp_wallpaper_candidates
temp_photo_candidates
mixed_demo_queue
```

## Queue Limits

```text
maximum 10 wallpaper candidates
maximum 10 photo-widget candidates
maximum 20 total temporary candidates
queue validator should report over-limit queues as FAIL
queue validator should report unknown queue types as FAIL
```

## Queue Record Fields

Each queue record references the metadata concept and includes:

```text
candidate_id
candidate_type
queue_name
queue_position
queue_added_at
queue_expires_at
review_status
review_decision
source_name
source_url
candidate_url
title
content_rating
nsfw_flag
local_temp_path
processed_output_path
notes
```

## Queue Validation Rules

- JSON must parse locally
- Top-level `records` must be an array
- Record count must not exceed `max_candidates`
- `max_candidates` must not exceed 20
- `queue_type` must be `wallpaper`, `photo_widget`, or `mixed`
- Each record must include all required queue fields
- `candidate_type` must be `wallpaper`, `photo_widget`, or `both`
- `review_status` and `review_decision` must match allowed enums
- `content_rating` must be `safe`, `needs_review`, or `blocked`
- Sample records must use `example.invalid` URLs only
- No `reddit.com`, real image URLs, or `nsfw_flag: true` in samples
- Conceptual `local_temp_path` values must not start with `/` or contain `..`

## Sample Queue File

`sample-queue.json` contains exactly three fictional records with `unreviewed`, `needs_more_info`, and `approved` review statuses. Sample queue records are fictional and safe.

## Dry-Run Validator

`scripts/wallpaper-photo-queue-file-validator.sh` validates queue files read-only. Default target: `sample-queue.json`. Optional path argument supported. No files are created, deleted, moved, or scanned.

## What the Validator Reports

- Per-record PASS/WARN/FAIL status
- Queue-level limit and type checks
- URL and path safety checks
- Dry-run boundary confirmation (no network, no image handling, no macOS automation)
- Parseable Summary block with PASS/WARN/FAIL counts

## What This PR Does Not Implement

- This PR adds queue file format and dry-run validation only.
- This PR does not create live queues.
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

## Human Approval Gates

```text
1. Approve queue file format.
2. Approve dry-run queue validator.
3. Approve sample queue records.
4. Approve actual queue file location.
5. Approve live queue write behavior.
6. Approve approve/dismiss UI behavior.
7. Approve deletion/cleanup behavior.
8. Approve image processing handoff.
9. Approve any source integration.
10. Approve scheduled automation.
```

## Future Implementation Phases

```text
Phase G: Queue file format and dry-run validator
Phase H: Approve/Dismiss UI design
Phase I: Image processing rules
Phase J: Local automation scheduler
Phase K: Approved-source fetcher
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-queue-file-status
bin/chief-of-staff --wallpaper-photo-queue-file-validator
bin/chief-of-staff --wallpaper-photo-approve-dismiss-ui-status
bin/chief-of-staff --wallpaper-photo-temp-queue-status
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-queue-file-status.sh
bash scripts/wallpaper-photo-queue-file-validator.sh
bash scripts/wallpaper-photo-approve-dismiss-ui-status.sh
```
