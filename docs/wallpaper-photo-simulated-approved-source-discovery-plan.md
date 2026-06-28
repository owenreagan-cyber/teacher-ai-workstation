# Wallpaper/Photo Simulated Approved-Source Discovery Plan

## Purpose

This document defines a local-only simulated approved-source discovery plan for the future **Automated Wallpaper and Photo Curator**. It describes how future discovery would report fictional candidate-count placeholders using the source allowlist from PR #49—without implementing real discovery or making network calls.

This PR adds simulated discovery planning/status only. It does not implement real discovery, make network calls, or fetch URLs.

## Current Status

```text
Current status: Phase N simulated approved-source discovery plan only.
```

Simulated discovery planning, fictional sample discovery report, and read-only validator live in `assistant/appearance-vibe/wallpaper-photo-curator/`. No fetcher, network calls, or real discovery exist yet.

## Relationship to Source Allowlist Foundation

Phase Q defined the local source allowlist file format and dry-run validator. Phase N uses those fictional allowlist entries as simulated discovery inputs. See `docs/wallpaper-photo-source-allowlist-foundation.md`.

## Relationship to Approved-Source Fetcher Plan

Phase K defined approved-source fetcher planning with allowlist concepts and dry-run discovery boundaries. Phase N defines simulated discovery reporting only. A future fetcher would require separate approval before any network call. See `docs/wallpaper-photo-approved-source-fetcher-plan.md`.

## Simulated Discovery Concept

```text
source allowlist entry
→ source status check
→ permission/license/terms/rate-limit note check
→ simulated candidate-count placeholder
→ simulated report output
→ human review
→ future real discovery requires separate approval
```

This PR does not execute discovery.

## Simulated Discovery Inputs

Simulated discovery reads fictional allowlist entries from `sample-source-allowlist.json` and produces a fictional report in `sample-discovery-report.json`. Inputs include source status, permission notes, license review status, terms/robots/rate-limit notes, and source type.

## Simulated Discovery Report

The sample report includes top-level fields:

```text
schema_version
report_name
source_allowlist_file
generated_at
mode
network_calls
records
notes
```

Each record includes candidate-count placeholders and discovery status fields. Sample discovery output is fictional/local-only.

## Source Status Handling

```text
approved_for_dry_run: may appear in simulated reports
approved_for_fetching_later: may appear in simulated reports only; no fetching occurs
proposed: report as not ready
paused: report as paused
blocked: report as blocked
needs_more_info: report as needs more information
```

## Candidate Count Placeholders

```text
candidate_count_estimate
wallpaper_candidate_estimate
photo_widget_candidate_estimate
blocked_reason
discovery_status
notes
```

These are fictional/simulated counts only. They do not represent real candidates, downloads, or queue entries.

## Reddit Future-Only Boundary

```text
Reddit may be a future approved source only after source rules and network behavior are separately approved.
No Reddit API client is added in this PR.
No Reddit OAuth is added in this PR.
No Reddit content is fetched in this PR.
Any Reddit-related sample remains fictional and uses example.invalid only.
```

## Devvit Future-Only Boundary

```text
Devvit may be a future Reddit-native companion only.
Devvit is not the core local Mac fetcher runtime.
No Devvit app, Redis, triggers, scheduler, API calls, or publishing workflow is added in this PR.
Any Devvit-related sample remains fictional and uses example.invalid only.
```

## Blocked Automatic Actions

```text
no real discovery
no network calls
no URL fetching
no API clients
no OAuth
no secrets
no API keys
no image fetching
no image downloading
no image processing
no queue writes
no scheduler behavior
no notifications
no Reddit integration
no Devvit integration
```

## Human Approval Gates

```text
1. Approve simulated discovery plan.
2. Approve simulated discovery report fields.
3. Approve source status handling.
4. Approve candidate-count placeholder behavior.
5. Approve dry-run report validation.
6. Approve any future network call separately.
7. Approve first real source type separately.
8. Approve queue write behavior separately.
9. Approve image download behavior separately.
10. Approve scheduler behavior separately.
```

## What This PR Does Not Implement

- This PR adds simulated discovery planning/status only.
- This PR does not implement real discovery.
- This PR does not make network calls.
- This PR does not fetch URLs.
- This PR does not add API clients.
- This PR does not add OAuth.
- This PR does not add secrets or API keys.
- This PR does not fetch or download images.
- This PR does not process images.
- This PR does not write queue records.
- This PR does not create queue folders.
- This PR does not add Reddit integration.
- This PR does not add Devvit integration.
- This PR does not add scheduler behavior.
- This PR does not send notifications.
- Sample discovery output is fictional/local-only.

## Future Implementation Phases

```text
Phase N: Simulated approved-source discovery plan
Phase O: Live local review UI prototype plan
Phase P: Dry-run image processor
Phase Q: Manual image processor
Phase R: Dry-run scheduler
Phase S: Manual scheduler helper
Phase T: Notification foundation
Phase U: Rotation handoff and safety audit
```

## Commands Reference

```bash
bin/chief-of-staff --wallpaper-photo-simulated-discovery-status
bin/chief-of-staff --wallpaper-photo-simulated-discovery-validator
bin/chief-of-staff --wallpaper-photo-source-allowlist-status
bin/chief-of-staff --wallpaper-photo-source-fetcher-plan-status
bin/chief-of-staff --dashboard
bash scripts/wallpaper-photo-simulated-discovery-status.sh
bash scripts/wallpaper-photo-simulated-discovery-validator.sh
```
