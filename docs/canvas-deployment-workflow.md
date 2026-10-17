# Canvas Deployment Workflow (Phase 4)

```text
Status: guarded Canvas deployment + post-write verification (local-first)
Package: scripts/canvas_llm_deploy/
CLI:     bin/canvas-intake preflight | deploy | verify
UI:      Teacher Workstation → Deploy
```

## Scope

This is the **first** component that can reach Canvas mutation code. It follows a
strict, explicit lifecycle:

```text
READY_TO_PUBLISH → preflight → owner confirmation → ordered writes
                 → post-write readback → PUBLISHED_VERIFIED
```

It does **not** do broad writes, generic proxies, or automatic rollback.

## Architecture

```text
UI (Deploy screen)
  └─ POST /api/weeks/{q}/{w}/preflight  (GET-only or dry-run)
  └─ POST /api/weeks/{q}/{w}/deploy     (production-gated)
       └─ scripts/teacher_workstation/deploy.py (thin route handler)
            └─ scripts/canvas_llm_deploy/  (the deployment coordinator)
                 ├─ plan.build_plan          (deterministic write plan, pure)
                 ├─ preflight.run_preflight  (GET-only live resolution + gate)
                 ├─ coordinator.deploy       (ordered writes + readback)
                 └─ client.LiveDeployClient  (delegates to canonical write helpers)
```

The coordinator **reuses** the canonical Canvas write helpers in
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

## Dry run

```bash
bin/canvas-intake deploy --quarter 2 --week 3 --dry-run
```

Prints the exact write plan (deterministic, no Canvas GET, no writes).

## Deploy

```bash
bin/canvas-intake preflight --quarter 2 --week 3 --production   # -> preflight id
bin/canvas-intake deploy --quarter 2 --week 3 --production --preflight-id <id> --confirm "DEPLOY Q2W3"
```

- Requires explicit `--production` mode and an explicit owner confirmation
  containing `DEPLOY`.
- Deletion count > 0 requires the confirmation to be exactly `DEPLOY {WEEK_CODE}`.
- Deployment is **idempotent** after partial failure (skips already-correct
  objects).

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
