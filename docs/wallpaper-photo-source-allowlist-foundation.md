# Wallpaper/Photo Source Allowlist Foundation

## Purpose

This document defines the local source allowlist foundation for the future **Automated Wallpaper and Photo Curator**. It combines source allowlist file format and dry-run validation for fictional, safe, local-only source records—without implementing a fetcher or making network calls.

This PR adds allowlist file format and dry-run validation only. It does not implement a fetcher, make network calls, or add API clients.

## Current Status

```text
Current status: Phase Q source allowlist foundation (file format and dry-run validator).
```

Allowlist schema, fictional sample allowlist, and read-only validator live in `assistant/appearance-vibe/wallpaper-photo-curator/`. No fetcher, network calls, or live source fetching exist yet.

## Relationship to Approved-Source Fetcher Plan

Phase K defined approved-source fetcher planning with allowlist concepts, permission review, dry-run discovery, and rate-limit boundaries. Phase Q defines the local allowlist file format and dry-run validator that future fetcher work would reference. This PR does not implement fetching.

## Relationship to Metadata Schema

Source allowlist entries align with metadata concepts such as `source_type`, `source_name`, `source_url`, `license_status`, and `permission_note`. Allowlist records add explicit approval, terms, robots/policy, and rate-limit notes before any future network behavior.

## Source Allowlist Concept

Future approved sources would follow this conceptual pipeline:

```text
source proposed
→ permission reviewed
→ terms and robots/policy reviewed
→ rate-limit note recorded
→ allowlist entry approved for dry-run
→ dry-run validator checks fictional/local records
→ human approval
→ future fetcher may be implemented separately
```

This PR does not execute fetching.

## Source Allowlist File Structure

Top-level allowlist file shape:

```text
schema_version
allowlist_name
sources
created_at
updated_at
notes
```

Each source entry includes:

```text
source_id
source_name
source_type
source_url
allowed_content_types
permission_note
license_review_status
terms_review_note
robots_or_policy_note
rate_limit_note
requires_auth
status
approved_by
approved_at
last_reviewed_at
notes
```

## Required Source Fields

All source entries must include every field listed above. Sample sources are fictional and safe.

## Source Types

Allowed `source_type` values:

```text
fictional_sample
future_approved_site
future_reddit_source
future_local_folder
manual_entry
future_devvit_companion
```

## Source Statuses

Allowed `status` values:

```text
proposed
approved_for_dry_run
approved_for_fetching_later
paused
blocked
needs_more_info
```

## Permission and License Requirements

```text
permission_note must be present
terms_review_note must be present
rate_limit_note must be present
robots_or_policy_note must be present
unknown_needs_review cannot be approved_for_fetching_later
not_allowed cannot be approved_for_fetching_later
requires_auth true requires future approval before implementation
blocked sources must not be fetched
future_reddit_source remains future-only
future_devvit_companion remains future-only
```

Allowed `license_review_status` values:

```text
fictional_sample
unknown_needs_review
permission_confirmed
public_domain
creative_commons
personal_use_only
not_allowed
```

## Terms, Robots, and Rate-Limit Requirements

Every source entry must document terms review, robots/policy notes, and rate-limit notes before any future fetcher implementation. Dry-run validation checks that these fields are present and non-empty in sample records.

## Reddit Future-Only Boundary

```text
Reddit may be a future approved source only after source rules and network behavior are separately approved.
No Reddit API client is added in this PR.
No Reddit OAuth is added in this PR.
No Reddit content is fetched in this PR.
```

## Devvit Future-Only Boundary

```text
Devvit may be a future Reddit-native companion only.
Devvit is not the core local Mac fetcher runtime.
No Devvit app, Redis, triggers, scheduler, API calls, or publishing workflow is added in this PR.
```

## Dry-Run Validator

`scripts/wallpaper-photo-source-allowlist-validator.sh` validates allowlist files read-only. Default target: `sample-source-allowlist.json`. Optional path argument supported. No network calls, file writes, or fetching.

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

## Human Approval Gates

```text
1. Approve source allowlist foundation.
2. Approve allowlist file format.
3. Approve dry-run allowlist validator.
4. Approve sample allowlist records.
5. Approve first real source type to test.
6. Approve any network call.
7. Approve any API client or OAuth flow.
8. Approve fetcher implementation.
9. Approve queue write behavior.
10. Approve image download behavior separately.
```

## What This PR Does Not Implement

- This PR adds allowlist file format and dry-run validation only.
- This PR does not implement a fetcher.
- This PR does not make network calls.
- This PR does not add API clients.
- This PR does not add OAuth.
- This PR does not add secrets or API keys.
- This PR does not add Reddit integration.
- This PR does not add Devvit integration.
- This PR does not fetch or download images.
- This PR does not process images.
- This PR does not write queues.
- This PR does not add scheduler behavior.
- This PR does not send notifications.
- Sample sources are fictional/safe/local-only.

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
Phase T: Simulated approved-source discovery plan
```

Phase Q and R are combined in this foundation PR.

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-source-allowlist-status
bin/chief-of-staff --wallpaper-photo-source-allowlist-validator
bin/chief-of-staff --wallpaper-photo-source-fetcher-plan-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-source-allowlist-status.sh
bash scripts/wallpaper-photo-source-allowlist-validator.sh
```
