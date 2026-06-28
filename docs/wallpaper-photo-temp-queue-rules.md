# Wallpaper/Photo Temp Queue Rules

## Purpose

This document defines local planning and status rules for future **temporary candidate queues** in the Automated Wallpaper and Photo Curator. Queues hold metadata-only candidates awaiting Owen's review before any image fetching or processing occurs.

This PR adds temp queue rules only. It does not create live queues, fetch images, or automate macOS wallpaper or Photos settings.

## Current Status

```text
Current status: Phase F temp queue rules only.
```

Rules are documented only. No queue files, queue folders, or queue runtime exist yet.

## Relationship to Metadata Schema

Queue rules extend `docs/wallpaper-photo-metadata-schema.md` and `assistant/appearance-vibe/wallpaper-photo-curator/metadata-schema.json`. Optional queue fields (`queue_name`, `queue_position`, `queue_added_at`, `queue_expires_at`, `stale_after_days`) may appear in fictional samples for planning.

## Relationship to Folder Creation Helper

Future queues conceptually map to temp folders under `~/Pictures/Wallpaper Curator/Temp Wallpaper Candidates/` and `Temp Photo Candidates/`. This PR does not create queue folders.

## Temporary Queue Concept

A temporary candidate queue holds metadata records for images Owen has not yet approved. Wallpaper and photo-widget candidates stay in separate logical queues with shared review rules.

## Queue Size Limits

```text
maximum 10 wallpaper candidates
maximum 10 photo-widget candidates
maximum 20 total temporary candidates
no automatic expansion without future approval
no background refill without future approval
```

## Candidate Types

```text
wallpaper
photo_widget
both
```

## Review States

```text
unreviewed
approved
dismissed
blocked
needs_more_info
```

## Review Decisions

```text
none
approve_for_processing
dismiss_delete_candidate
block_source
needs_more_info
```

## Allowed Future Queue Actions

```text
add metadata-only candidate
add candidate after approved source check
mark candidate unreviewed
mark candidate approved
mark candidate dismissed
mark candidate blocked
mark candidate needs_more_info
move approved candidate to future processing stage
delete dismissed candidate only after explicit approved deletion behavior exists
retain source metadata for traceability
```

## Blocked Automatic Actions

```text
no automatic approval
no automatic deletion without future approval
no automatic image fetching in this PR
no automatic image downloading in this PR
no automatic image processing in this PR
no automatic folder scanning
no automatic wallpaper changes
no automatic Photos changes
no automatic notifications
no automatic Reddit or Devvit use
```

## Stale Candidate Rules

```text
stale candidates may be identified later
stale candidates must not be deleted automatically yet
stale cleanup requires a separate future approval gate
stale rules should prefer reporting before deletion
```

Cleanup/deletion rules require explicit future approval.

## Cleanup Rules

- Dismissed candidates may be deleted only after Owen approves a future deletion behavior.
- Stale candidates are reported first; automatic cleanup is blocked in this PR.
- No background jobs remove queue entries.

## Metadata Requirements

Queue records should tie to existing metadata fields:

```text
candidate_id
candidate_type
review_status
review_decision
created_at
updated_at
reviewed_at
local_temp_path
processed_output_path
notes
```

Optional queue fields for future use:

```text
queue_name
queue_position
queue_added_at
queue_expires_at
stale_after_days
```

## Human Approval Gates

```text
1. Approve temp queue rules.
2. Approve queue metadata fields.
3. Approve actual queue file format.
4. Approve temp queue folder behavior.
5. Approve stale candidate reporting.
6. Approve deletion/cleanup behavior.
7. Approve review UI behavior.
8. Approve image processing handoff.
9. Approve any source integration.
10. Approve scheduled automation.
```

## What This PR Does Not Implement

- This PR adds temp queue rules only.
- This PR does not create live queues.
- This PR does not create queue folders.
- This PR does not fetch images.
- This PR does not download images.
- This PR does not process images.
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
Phase F: Temp queue rules
Phase G: Queue file format and dry-run validator
Phase H: Approve/Dismiss UI design
Phase I: Image processing rules
Phase J: Local automation scheduler
Phase K: Approved-source fetcher
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-temp-queue-status
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --wallpaper-photo-folder-creation-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-temp-queue-status.sh
```
