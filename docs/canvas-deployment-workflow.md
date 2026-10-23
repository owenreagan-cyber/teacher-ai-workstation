# Canvas Deployment Workflow (Phase 4)

```text
Status: legacy guarded-deploy design; direct deploy disabled by D-028
Package: scripts/canvas_llm_deploy/
Publisher: bin/canvas-weekly-rollover only
```

## Scope

This document records the older Phase 4 design. The reusable plan, preflight,
transport, and verification primitives remain, but the direct deploy CLI and
Teacher Workstation deploy route are disabled. Per D-028, the Friday rollover
engine is the only weekly-package publisher.

```text
READY_TO_PUBLISH → preflight → owner confirmation → ordered writes
                 → post-write readback → PUBLISHED_VERIFIED
```

It does **not** do broad writes, generic proxies, or automatic rollback.

## Architecture

```text
bin/canvas-weekly-rollover
  └─ scripts/canvas_llm_rollover/rollover.py  (only weekly publisher)
       └─ scripts/canvas_llm_deploy/
            ├─ plan.build_plan          (deterministic package primitives)
            ├─ preflight helpers        (GET-only classification)
            └─ client.LiveDeployClient  (canonical transport adapter)
```

The rollover engine **reuses** the canonical Canvas write helpers in
`scripts/canvas_llm_phase22/` (`Phase22LiveCanvasClient` for writes/readback,
`CanvasReadOnly` for GET-only listings). It never forks assignment routing, page
discovery, announcement behavior, duplicate detection, scheduling semantics,
approval semantics, or course identities.

## Deployment gate

Canvas deployment is permitted **only** when the week lifecycle is
`READY_TO_PUBLISH` **and** all of the following hold:

- source hash current
- artifact hashes current
- all required approvals current
- no blocking questions
- no pending source for required artifacts
- no stale approval
- no stale owner-override conflict
- no duplicate ambiguity
- all required live-object lookups uniquely resolve
- no course/module/page mismatch
- exact write plan generated successfully

Any failure → **STOP BEFORE FIRST WRITE**.

## Preflight (GET-only)

```bash
bin/canvas-intake preflight --quarter 2 --week 3 --production
```

- Resolves course IDs, weekly page identity, module identity, assignment groups,
  existing assignments (duplicate detection), and announcement duplicates.
- Produces a short-lived preflight record (default 15-minute TTL) with an exact
  write plan and live-object identities.
- `--production` does GET-only live lookups; without it, preflight is a local
  dry-run plan (no Canvas GET).

A preflight record is invalidated immediately if the source, approvals, or live
duplicate state changes.

## Direct deploy is disabled

The `canvas-intake` deploy subcommand returns `BLOCKED` for every non-dry-run
request and is not invoked by any LaunchAgent, script, or maintained runbook.
Use `bin/canvas-weekly-rollover`; Owen's current commands are in
`docs/canvas-planner-1-steps.md`.

## Write ordering (stop-on-failure)

1. page backups (local, untracked, no token)
2. page updates
3. page readback verification
4. assignment writes
5. assignment readback verification
6. announcement writes
7. announcement readback verification
8. front-page activation (only if lifecycle requires it — not the default)
9. final verification sweep
10. deployment ledger finalization

On any write/readback failure: **STOP immediately** and record completed /
failed / not-attempted work + a corrective plan. No automatic rollback.

## Post-write verification

- **Pages** — course, page id, title, body (`kl_wrapper_3` + `Reminders`), module.
- **Assignments** — title, course, group, points (100), grading type (percent),
  submission type (on_paper), due date (11:59 PM America/New_York), omit flag.
- **Announcements** — course, title, body, `delayed_post_at` (if scheduled), and
  active-feed state per the corrected scheduling semantics:
  future `delayed_post_at` + absent from active-only feed = **correctly held**
  (never use `posted_at` or `published` as the visibility signal).

## PUBLISHED_VERIFIED gate

`PUBLISHED_VERIFIED` is set only when every intended write completed and every
required readback passed, with every artifact ending in an explicit final
disposition (`PUBLISHED_VERIFIED`, `NOT_REQUIRED`, `OWNER_WAIVED`, `CANCELLED`,
`FAILED`, or `ALREADY_EXISTS`). No "held / never posted" ambiguity.

## Sandbox

The designated sandbox course is `24399` (Math Automation Sandbox). Any future
live sandbox exercise must verify `workflow_state == unpublished` before and
after every write, and must never publish, enroll, or cross-list. This build
performs **zero** live sandbox writes; all write-path testing uses the in-memory
`FakeDeployClient`.

## Production mode

Production writes require `--production` (CLI) or the production toggle (UI),
plus a fresh unexpired preflight, an explicit owner confirmation, and canonical
production course mapping. There is no fallback from sandbox to production.

## Ledger and audit

```text
.local/canvas-llm/deployments/2026-2027/q<q>/w<w>/
  preflight-<id>.json
  deployment-ledger.json
  published-verified-ledger.json
  backups/
```

The ledger records source hash, approval hashes, preflight/confirmation/
deployment timestamps, the write plan, actual writes, Canvas object IDs, readback
results, final verification, and final lifecycle. The token is never stored.

## Security

- No arbitrary Canvas endpoint proxy.
- The Canvas token stays backend-only; it is never sent to the browser or logged.
- No arbitrary shell execution; no path traversal.
- Deployment accepts only canonical semantic identifiers; all course IDs, URLs,
  and write payloads are backend-derived.

## Status

```bash
bin/chief-of-staff --canvas-deployment-status
```

Bounded, local, read-only; it does **not** depend on the full dashboard.
