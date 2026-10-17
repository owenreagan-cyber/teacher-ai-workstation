# Teacher Workstation UI

```text
Status: local interactive planning UI (read-only vs Canvas)
Command: bin/teacher-workstation
Module: Canvas Weekly Planner
```

## Architecture

The UI is a **cockpit** over the existing intake engine. It reads and mutates
only local staging/planning state under `.local/canvas-llm/` and reuses the
existing intake/teacher-input/override modules. It duplicates no curriculum,
Canvas, pacing, approval, or lifecycle business logic.

```text
UI (apps/teacher-workstation, vanilla JS)
  └─ local JSON API (scripts/teacher_workstation/server.py, stdlib http.server)
       ├─ adapter (read-only reads; scripts/teacher_workstation/adapter.py)
       └─ mutate   (local-state edits; scripts/teacher_workstation/mutate.py)
            └─ canvas_llm_intake (intake / owner_overrides / teacher_input / approval)
```

## Stack

Python stdlib `http.server` (no new dependencies) + vanilla HTML/CSS/JS (no
framework). Matches the repo's existing plain-JS apps.

## Local-only boundary

- Binds to `127.0.0.1` only (never `0.0.0.0`).
- Default port `4310`.
- No external hosting, cloud deployment, tunnel, or remote access.

## Launcher

```bash
bin/teacher-workstation            # start (prints URL; does NOT open browser)
bin/teacher-workstation --no-open  # same; browser opening is not implemented
bin/teacher-workstation --help
```

## Read-only API (GET)

```text
GET /api/status
GET /api/home
GET /api/weeks
GET /api/week/{quarter}/{week}
GET /api/week/{quarter}/{week}/questions
GET /api/completed
```

## Local mutation API (POST/DELETE — local state only, never Canvas)

```text
POST   /api/weeks/{q}/{w}/overrides          create/update a day override
POST   /api/weeks/{q}/{w}/restore-source     remove a day override
POST   /api/weeks/{q}/{w}/mark-pending       mark a day pending
POST   /api/weeks/{q}/{w}/mark-blank         mark a day intentionally blank
POST   /api/weeks/{q}/{w}/questions/{id}/answer   answer a question
POST   /api/weeks/{q}/{w}/assignments        REJECT / RESTORE an assignment proposal
POST   /api/weeks/{q}/{w}/announcements      edit weekly-update transition wording
POST   /api/weeks/{q}/{w}/approve            approve one artifact (hash-bound)
POST   /api/weeks/{q}/{w}/revoke-approval    revoke one artifact approval
POST   /api/weeks/{q}/{w}/preflight          guarded deployment preflight (dry-run or GET-only)
POST   /api/weeks/{q}/{w}/deploy             guarded production deploy (production-gated)
```

The deployment routes are the **only** routes that can reach Canvas mutation
code. They delegate to `scripts/canvas_llm_deploy/` (the guarded coordinator),
require explicit production mode + confirmation, and never expose a generic
Canvas proxy. See `docs/canvas-deployment-workflow.md`.

`PUT`/`PATCH` are not implemented (405). No local route reaches Canvas
mutation code — the server source statically forbids importing the Canvas
write transport.

### Approval payload (POST /approve)

```json
{ "source_hash": "<packet source hash>",
  "subject": "math",
  "artifact_type": "page | assignments | announcement | assessment_reminder",
  "expected_artifact_hash": "<current draft hash>" }
```

Rejects (never coerces): unknown subject/artifact type, hash mismatch
(`409 STALE`), stale source (`409 STALE`), artifact blocked by pending source
or unresolved question, or an already-stale artifact.

## Interactive planning (Phase 2)

- **Day/subject editing** — click a grid cell to set In Class, At Home, status,
  and a teacher note. Semantic fields only (no raw HTML editing).
- **Owner overrides** — structured, auditable ledger
  (`owner-overrides.json`), recording `source_value` + `owner_value`,
  `created_at`/`updated_at`, and `source=OWNER_INPUT`. Restore Source
  deactivates the override (history preserved) and regenerates.
- **Partial-week** — subjects may be partially planned; unplanned days show
  `PENDING` (not FAIL). `Mark Intentionally Blank` and `Mark Pending` are
  explicit day-level states.
- **Impact preview** — before save, show which artifacts are affected
  (page / weekly announcement / assessment reminder / approvals) and which are
  unaffected.
- **Targeted regeneration** — after an edit, only affected artifacts are
  rebuilt; approvals are invalidated only where changed.
- **Stale-edit protection** — mutations carry the packet `source_hash`;
  a mismatch returns `409 STALE` and the client must refresh.
- **Question answering** — answer, use recommended default, or defer; recorded
  with `source=OWNER_INPUT`; original question preserved.
- **Assignment proposals** — KEEP / REJECT / RESTORE (local only).

## Safety constraints

- Canvas writes: `POST=0 PUT=0 PATCH=0 DELETE=0`.
- Email sends: 0 · Canvas Inbox sends: 0.
- The Canvas token, Authorization headers, verifier-bearing URLs, and secrets
  are never emitted to the browser, API JSON, HTML, JS, or logs.
- No student names, grades, submissions, parent emails, health info, or PII.
- No browser storage of sensitive state (browser is display-only).
- Payload validation + unknown-field rejection; no shell/command execution
  from browser input; no path traversal.

## Approval controls (Phase 3)

Approval is an **explicit, hash-bound, local-only** workflow. It reuses the
single canonical approval engine (`scripts/canvas_llm_intake/approval.py`) —
the UI does **not** create a second approval system.

- **Granularity** — per subject per artifact: `page`, `assignments`,
  `announcement`, `assessment_reminder`. Assignments are approved as a
  **subject-level bundle** bound to a deterministic bundle hash (adding,
  removing, or changing any member changes the bundle hash).
- **Hash binding** — each approval records the exact artifact `draft_hash` and
  the packet `source_hash`. If either changes, the approval becomes
  `PENDING`/`STALE` automatically (never silently re-bound).
- **Targeted invalidation** — editing one artifact invalidates only that
  artifact's approval (and, for the announcement, anything that embeds its
  content). Unrelated subjects and artifacts stay `APPROVED`.
- **Provenance** — UI approvals record `approved_by = OWNER_UI`; CLI approvals
  record `OWNER`. Both read/write the same `approval-manifest.json` (no
  parallel ledgers).
- **History** — every state change appends an audit event
  (`approved` / `revoke` / `invalidated`) with timestamp, source, and reason.
- **`NOT_REQUIRED`** — owner-confirmed-blank artifacts are marked
  `NOT_REQUIRED` and do not require fake content or approval.
- **Pending-source gate** — a subject with pending-source days (or an
  unresolved question) is blocked (`BLOCKED BY PENDING SOURCE`); its artifacts
  cannot be approved until resolved.
- **Confirmation UX** — approval requires an explicit confirm step; there is no
  blind "Approve All".

### READY_TO_PUBLISH gate

A week reaches `READY_TO_PUBLISH` only when **all** of the following hold:

- no unresolved blocking questions
- no required `PENDING_SOURCE`
- no stale source conflict
- all required artifacts generated
- all required artifact hashes current
- all required artifacts `APPROVED` (or `NOT_REQUIRED`)
- no approval points at an old hash

`READY_TO_PUBLISH` **does not deploy**. It shows
"All required artifacts are approved. Nothing has been written to Canvas."
There is no DEPLOY / PUBLISH NOW / SEND TO CANVAS button.

## Approval / deployment

Approval is local only. Deployment is a **separate guarded workflow** (Phase 4)
behind the Deploy screen and the narrowly-scoped `/preflight` and `/deploy`
routes. `READY_TO_PUBLISH` does not deploy. See
`docs/canvas-deployment-workflow.md`.

## Future phases (documented only — not implemented)

- **Phase 5** — Homeroom/newsletter module.
- **Phase 6** — broader Teacher Workstation modules.
