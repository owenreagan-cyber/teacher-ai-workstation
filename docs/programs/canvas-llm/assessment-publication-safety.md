# Assessment publication safety

Status: active contract for the Canvas weekly release path. This document does not approve or publish anything.

## Owner-selected time

A missed Friday 4:00 PM America/New_York window, and any assessment notice whose policy date is today or earlier, stays `OWNER_TIME_REQUIRED` until the owner selects a timezone-aware instant on a later local date.

The selected release time is stored locally in `planner/owner-publication-times.json`:

- `release` applies to the four weekly announcements and the Homeroom family announcement.
- `notices` maps a notice `duplicate_identity` to that notice only.

Intake, `build_plan`, preflight, the rollover manifest, and the coordinator all read that file. A future assessment notice keeps its policy send time. An owner time for a different identity, a naive timestamp, a past timestamp, or a same-day timestamp leaves the notice `BLOCKED`. Changing the time changes the draft hash and invalidates a prior approval. The deployment plan fingerprint then no longer matches the reviewed preflight.

No component invents a publication time.

## Pre-write gate

`rollover.execute()` and `coordinator.deploy()` validate the whole plan before the first Canvas mutation. A blocked page, assignment, weekly announcement, assessment notice, Homeroom announcement, duplicate identity, unverified resource, missing course id, or missing publication time returns `BLOCKED` with zero Canvas writes. Direct `execute()` uses the same gate as `publish_weekly_package()`.

`FUTURE_SCHEDULED` is accepted only when `delayed_post_at` parses as a timezone-aware instant strictly later than the injected clock. A past, naive, or missing instant is `BLOCKED` before any PUT or POST. The label is not evidence.

`execute()` validates a deep copy. It does not rewrite a `BLOCKED` or `OWNER_TIME_REQUIRED` Homeroom announcement into `FUTURE_SCHEDULED` or `CREATE`. The caller's manifest stays unchanged when the gate blocks.

A content release must carry `source_hash`, and that value must equal the current intake manifest hash. A missing snapshot, a missing hash, or a mismatch fails closed. The manifest is not compared with itself, and the approved hash is not replaced.

Every academic page and the Homeroom page in that release must have `approved is True`, a course id, and an approval hash. Missing, null, and false all block. `PENDING` and `BLOCKED` block. A changed page id blocks.

When a preflight file exists, its plan fingerprint must match the manifest and the current plan. A stale preflight blocks before writes. A week already recorded as `PUBLISHED_VERIFIED` returns `already_complete` and does not write again.

`finalize_published_verified()` validates source hash, plan fingerprint, explicit approval, five-course verification, announcement verification, assignment verification, and Homeroom page-first order before it writes the published ledger. It advances the intake manifest only after that ledger reads back intact. A split storage root, a failed write, or a corrupt readback leaves the intake manifest unchanged. Pending approval cannot set `ready_to_publish`. Chief of Staff completion requires the manifest and the published ledger to agree; the manifest status alone is not completion.

## Scheduled versus published

Readback compares course id, title, message, and `delayed_post_at` as timezone-aware instants. A future delay that is not in the active feed is `SCHEDULED_VERIFIED`. It is not `PUBLISHED_VERIFIED`. A missing course id fails readback. An uncertain write is not retried.
