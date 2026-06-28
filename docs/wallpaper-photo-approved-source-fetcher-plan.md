# Wallpaper/Photo Approved-Source Fetcher Plan

## Purpose

This document defines a planning/status design for future approved-source fetching in the **Automated Wallpaper and Photo Curator**. It covers source allowlist requirements, permission notes, safe dry-run discovery, rate-limit boundaries, source safety checks, and explicit approval before any future network call—without implementing a fetcher.

This PR adds approved-source fetcher planning only. It does not implement a fetcher, make network calls, or add API clients.

## Current Status

```text
Current status: Phase K approved-source fetcher plan only.
```

Fetcher plan lives in this document and the read-only status script. No fetcher, network calls, API clients, OAuth, secrets, Reddit integration, or Devvit integration exist yet.

## Relationship to Local Scheduler Plan

Phase J defined local automation scheduler planning with dry-run first and never-run-unattended rules. Phase K defines what sources may be considered before any future scheduler triggers discovery. A future scheduler must not fetch sources until approved-source rules and network behavior are separately approved.

## Relationship to Image Processing Rules

Phase I defined image processing rules for approved candidates. Source fetching must happen only after source allowlist and permission review; processing must not run on unapproved or unknown sources.

## Relationship to Metadata Schema

Source metadata in `metadata-schema.json` uses `source_type`, `source_name`, `source_url`, `license_status`, and `permission_note`. Phase Q defines the local source allowlist file format and dry-run validator. See `docs/wallpaper-photo-source-allowlist-foundation.md`. Future allowlist entries would extend those concepts with explicit approval fields before any fetcher runs.

## Approved Source Concept

Future approved-source behavior would follow this conceptual pipeline:

```text
candidate source proposed
→ source permission reviewed
→ source allowlist entry approved
→ dry-run discovery only
→ candidate metadata preview
→ rate-limit and terms review
→ human approval
→ future fetcher may be implemented separately
```

This PR does not execute that pipeline.

## Source Allowlist Requirements

Future allowlist entries should include:

```text
source_id
source_name
source_type
source_url
allowed_content_types
permission_note
license_review_status
rate_limit_note
terms_review_note
robots_or_policy_note
requires_auth
approved_by
approved_at
status
notes
```

Allowed future `source_type` values:

```text
future_approved_site
future_reddit_source
future_local_folder
manual_entry
future_devvit_companion
```

Allowed future `status` values:

```text
proposed
approved_for_dry_run
approved_for_fetching_later
paused
blocked
needs_more_info
```

## Source Permission Requirements

```text
permission note must be present
license status must be reviewed before fetching
unknown permission blocks fetching
blocked sources must not be fetched
source terms must be reviewed before implementation
rate limits must be documented before implementation
```

## Future Dry-Run Discovery

```text
dry-run discovery reports candidate counts only
dry-run discovery reports source status only
dry-run discovery reports rate-limit assumptions only
dry-run discovery does not download images
dry-run discovery does not write queues
dry-run discovery does not create files
dry-run discovery does not process images
dry-run discovery does not call APIs until network behavior is separately approved
```

## Future Rate-Limit Boundaries

```text
default to conservative request limits
stop on errors
do not retry aggressively
do not bypass source restrictions
do not scrape when prohibited
do not use private or authenticated data unless explicitly approved
```

## Reddit as a Future Source

```text
Reddit may be a future approved source only after source rules are approved.
Reddit integration is not implemented in this PR.
No Reddit API client is added in this PR.
No Reddit OAuth or credentials are added in this PR.
No Reddit content is fetched in this PR.
```

## Devvit as a Future Companion

```text
Devvit may be a future Reddit-native companion only.
Devvit is not the core local Mac fetcher runtime.
Devvit integration is not implemented in this PR.
No Devvit app, Redis, triggers, scheduler, API calls, or publishing workflow is added in this PR.
```

## Source Metadata Requirements

Before future fetching, source records should align with metadata fields including:

```text
source_type
source_name
source_url
candidate_url
license_status
permission_note
content_rating
nsfw_flag
review_status
review_decision
notes
```

Unknown or blocked sources must not proceed to fetching.

## Blocked Automatic Actions

```text
no automatic source fetching
no automatic image downloading
no automatic image processing
no automatic queue writes
no automatic scheduler behavior
no automatic notifications
no automatic Reddit or Devvit use
no automatic network calls
no automatic wallpaper changes
no automatic Photos changes
```

## Failure Handling

```text
future fetcher should stop on permission or allowlist failure
future fetcher should stop on rate-limit or terms violations
future fetcher should prefer report-only behavior before any download
future fetcher should never retry blocked sources automatically
future fetcher should require clear local logs before implementation
```

## Human Approval Gates

```text
1. Approve approved-source fetcher plan.
2. Approve source allowlist fields.
3. Approve source permission rules.
4. Approve dry-run discovery behavior.
5. Approve rate-limit boundaries.
6. Approve first source type to test.
7. Approve any network call.
8. Approve any API client or OAuth flow.
9. Approve queue write behavior.
10. Approve image download behavior separately.
```

## What This PR Does Not Implement

- This PR adds approved-source fetcher planning only.
- This PR does not implement a fetcher.
- This PR does not make network calls.
- This PR does not add API clients.
- This PR does not add OAuth.
- This PR does not add secrets or API keys.
- This PR does not fetch images.
- This PR does not download images.
- This PR does not process images.
- This PR does not scan folders.
- This PR does not write queues.
- This PR does not create queue folders.
- This PR does not add Reddit integration.
- This PR does not add Devvit integration.
- This PR does not send notifications.
- This PR does not add a scheduler.
- This PR does not add launch agents, cron jobs, or background jobs.
- This PR does not change macOS wallpaper settings.
- This PR does not modify Photos or photo widgets.

## Future Implementation Phases

```text
Phase K: Approved-source fetcher plan
Phase L: Live local review UI prototype
Phase M: Dry-run image processor
Phase N: Manual image processor
Phase O: Dry-run scheduler
Phase P: Manual scheduler helper
Phase Q: Source allowlist file format
Phase R: Source allowlist dry-run validator
Phase S: First approved-source dry-run discovery
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-source-fetcher-plan-status
bin/chief-of-staff --wallpaper-photo-source-allowlist-status
bin/chief-of-staff --wallpaper-photo-source-allowlist-validator
bin/chief-of-staff --wallpaper-photo-local-scheduler-status
bin/chief-of-staff --wallpaper-photo-image-processing-status
bin/chief-of-staff --wallpaper-photo-metadata-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-source-fetcher-plan-status.sh
bash scripts/wallpaper-photo-source-allowlist-status.sh
bash scripts/wallpaper-photo-source-allowlist-validator.sh
```
