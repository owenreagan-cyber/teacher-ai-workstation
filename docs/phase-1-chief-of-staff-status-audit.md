# Phase 1 Chief of Staff Status Audit

Last verified: 2026-06-26

## Phase 1 Goal

Phase 1 should turn the existing Chief of Staff foundation into a safer, more useful teacher workflow layer without jumping ahead into connected services or autonomous automation. The near-term goal is a local, inspectable command launcher and status dashboard that helps Owen see Chief of Staff status, memory freshness, intake queue status, and next actions.

This audit is readiness work only. It does not build the full Teacher Chief of Staff agent, a real app, Gmail or Drive integrations, OAuth, paid APIs, or secret handling.

## Current Status Summary

- Phase 0E Vibe Engine is complete and verified.
- The current branch has a runnable Chief of Staff terminal CLI at `bin/chief-of-staff`.
- Phase 1A, 1B, 1C, and 1D foundations are present in docs, memory files, workflows, and intake files.
- Developer Mode is not yet a product mode. It is currently a safe direction for local lesson tools, small classroom helpers, and future app prototypes.
- The safest next build is a Chief of Staff command launcher / status dashboard that stays local and read-only.

## Current Repo Findings

The repository already contains substantial Chief of Staff scaffolding:

- `assistant/chief-of-staff.md` defines the role and behavior.
- `assistant/permissions.md` defines permission levels and keeps Gmail/Drive later.
- `assistant/failure-recovery-policy.md` defines source, confidence, and recovery behavior.
- `assistant/sensitivity-rules.md`, `assistant/model-routing.md`, and `assistant/writing-style.md` support safe operation.
- `assistant/workflows/` includes lesson support, project review, morning brief, intake review, app development support, troubleshooting, and 3D printing coordination workflows.
- `assistant/memory/` contains explicit Markdown memory files.
- `assistant/intake/` contains the Markdown review queue and policy files.
- `docs/chief-of-staff-roadmap.md` describes Phase 1A through later connector phases.
- `docs/interactive-chief-of-staff-cli.md` documents the current CLI.
- `docs/phase-1-readiness-checklist.md` already identifies Phase 1 readiness items and next PR ideas.

## Existing Chief Of Staff Pieces

Present:

- Role definition.
- Permission model.
- Failure and recovery policy.
- Sensitivity rules.
- Source map.
- Model routing guidance.
- Workflow docs.
- Interactive CLI.
- Memory files with explicit inclusion flags.
- Intake review queue with raw/quarantine/approved separation.
- Writing sample structure.
- Training and evaluation docs.

Not present yet:

- A single friendly command dashboard that summarizes Chief of Staff status and next actions.
- A real lesson planning workspace scaffold.
- Developer Mode project templates.
- Selected local folder indexing.
- Gmail, Drive, Calendar, or email integrations.
- Secrets/capability broker.
- Autonomous sending, publishing, deleting, or background operation.

## Existing CLI Functionality

The current CLI is `bin/chief-of-staff`.

Observed supported commands include:

- `--list-workflows`
- `--status`
- `--memory-status`
- `--validate-memory`
- `--intake-status`
- `--intake-summary`
- `--intake-diff`
- `--next-intake-id`
- `--validate-intake`
- `--preflight`
- workflow runs with `--workflow`, `--question`, `--context`, and `--dry-run`

The CLI is local-first. It uses approved Markdown context and explicit user-selected files. It does not scan Gmail, Drive, Apple Mail, or folders automatically.

## Existing Memory And Intake Pieces

Memory exists in `assistant/memory/` and is explicitly included with flags. Current memory files include project memory, teaching context, writing style rules, preferences, decisions, active priorities, review checklist, and memory log.

Intake exists in `assistant/intake/` and separates unreviewed raw files, approved summaries, approved files, rejected context, quarantine records, logs, and templates. Raw and file-based intake folders are ignored by Git except `.gitkeep` files.

Audit note: memory files required small factual updates because they still described earlier phases as current.

## Existing Safety Boundaries

- Level 0 and Level 1 access are the safe current defaults.
- Drive and Gmail scanning are later only.
- Raw intake is not approved context.
- Approved intake must be explicitly requested.
- Memory is Markdown, inspectable, and explicit.
- Destructive actions require confirmation.
- Classroom artifacts require human review.
- Factual, standards-based, history, science, date-based, or curriculum claims require verification.
- Secrets must not be committed.

## What Passed Verification

The new Phase 1 status script should be used for this audit:

```bash
bash scripts/phase-1-status.sh
```

For the Phase 0E to Phase 1 transition check:

```bash
bash scripts/phase-1-status.sh --compare-0e
```

Phase 0E verification remains:

```bash
bash scripts/verify-phase-0e.sh
```

## Missing Pieces

- Chief of Staff status dashboard or launcher command.
- Lesson planning workspace scaffold.
- Developer Mode project templates.
- Safe local indexing plan and implementation.
- Permissioned Drive/Gmail integration plan and implementation.
- Secrets/capability broker.
- Any real external-service automation.
- Real writing samples beyond the approved-samples structure.
- Real wallpaper/image approvals.

## Phase 0E Open Threads Carried Forward

- Reddit API approval pending; Reddit/anime automation paused.
- Unsplash staging exists, but real candidates/images require review.
- Photos widget manual setup may still be pending.
- Spotify playlists documented but not automated.
- Vibe Panel scaffold-only.
- Gmail/Drive/email integrations require explicit future permission and safety review.
- Secrets/capability broker remains a later phase.
- OpenSCAD optional warning may remain unless Owen chooses to install it.

## What Should Not Be Automated Yet

- Gmail or Drive scanning.
- Email sending.
- Calendar operations.
- Canvas publishing.
- Public deployment.
- Paid API setup.
- Production databases.
- Secret creation or storage.
- Background indexing of local folders.
- Autonomous desktop, Photos, Spotify, Reddit, or wallpaper automation.
- Student-data workflows.

## Risks

- Memory can become stale and should be reviewed before serious Chief of Staff work.
- The CLI is useful but still terminal-oriented and may not feel like a daily dashboard yet.
- Future indexing and connectors can become unsafe if they skip the intake and permission gates.
- Developer Mode can sprawl unless it starts with small local templates and clear build boundaries.

## Curriculum Builder Planning Stack Closeout

Curriculum Builder planning stack is complete for now. PRs #107–#124 built, gated, indexed, surfaced, and closed out the planning stack. No implementation behavior is active.

- Canonical entry point: `docs/curriculum-builder-canonical-planning-index.md`
- Dashboard docs now surface the planning index: `docs/chief-of-staff-dashboard.md` and `docs/dashboard-section-summary-polish.md`
- Future implementation requires the approval gate: `docs/curriculum-builder-approval-gate.md`
- Future implementation requires a completed decision intake: `docs/curriculum-builder-decision-intake-template.md`
- Current status command remains: `bin/chief-of-staff --curriculum-builder-foundation-status`
- Dashboard command remains: `bin/chief-of-staff --dashboard`

Unless explicitly approved through the approval gate and completed decision intake, preserve:

- no document scanning
- no folder scanning
- no file indexing
- no OCR
- no embeddings
- no vector database
- no lesson generation
- no generated lesson briefs/drafts
- no real review notes
- no student data
- no network calls
- no APIs
- no OAuth
- no automation
- no live integrations
- no storage migration
- no raw curriculum file duplication
- no registry data
- no schema activation

## Lesson-Planning Placeholder Readiness Closeout

Lesson-planning placeholder readiness is complete for now. The placeholder skeleton and placeholder template registry exist and pass readiness checks. No active implementation behavior exists.

- Placeholder skeleton: `assistant/lesson-planning/templates/lesson-planning-placeholder-skeleton.md`
- Placeholder template registry: `assistant/lesson-planning/templates/placeholder-template-registry.md`
- Status command remains: `bash scripts/lesson-planning-template-readiness-status.sh`
- Dashboard command remains: `bin/chief-of-staff --dashboard`
- Future work requires documentation/status-only approval unless explicitly approved.
- Static template schema planning remains planning-only and must not activate schema file, validator, or generation behavior.

Unless explicitly approved, preserve:

- no document scanning
- no folder scanning
- no file indexing
- no OCR
- no embeddings
- no lesson generation
- no generated lesson briefs/drafts
- no real review notes
- no student data
- no network calls
- no APIs
- no OAuth
- no automation
- no live integrations

## Appearance & Vibe Wallpaper/Vibe Status Audit

The wallpaper/vibe foundation is status/planning/scaffold only. Phase 0E vibe work is a script-first scaffold with optional manual install surfaces. Wallpaper/photo curator work is planning/status/foundation only. `setup/06-wallpapers.sh` is a one-time/manual setup script, not a daemon.

- no live wallpaper app
- no running wallpaper/photo curator daemon or background job
- no implemented WidgetKit widget or per-vibe widget runtime
- no automatic per-vibe shortcut runtime
- appearance/vibe modes are conceptually present and script-scaffolded/manual where applicable, not automated
- existing dashboard/status checks verify readiness and safety only
- live wallpaper/photo curator implementation has not started

Current canonical status surfaces:

- `bin/chief-of-staff --dashboard`
- `bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status`
- `bin/chief-of-staff --return-to-core-status`

Future implementation requires explicit approval.

Unless explicitly approved, preserve:

- no macOS wallpaper changes
- no widget creation
- no shortcut installation
- no scheduler
- no automation
- no API
- no OAuth
- no network call
- no live integration is active

## Repo-Wide Parked Tracks and Active Status Map

Compact map for maintainers, Cursor sessions, and ChatGPT sessions. Tracks below are the current source of truth for what is parked, what is active as status-only, and what must not be restarted without explicit approval.

| Track | Current state | Verification command | Active behavior? | Next allowed work | Blocked without approval |
| --- | --- | --- | --- | --- | --- |
| Curriculum Builder | Parked after planning closeout and canonical index | `bash scripts/curriculum-builder-foundation-status.sh`; `bin/chief-of-staff --curriculum-builder-foundation-status` | No | Approval-gated decision intake or docs/status-only cleanup | Implementation, registry data, scanning, indexing, APIs, lesson generation |
| Lesson-planning placeholder readiness | Parked after placeholder readiness closeout | `bash scripts/lesson-planning-template-readiness-status.sh` | No generation behavior | Docs/status-only planning unless explicitly approved | Schema activation, validators, active template loading, generated lesson briefs/drafts, real review notes |
| Appearance & Vibe wallpaper/photo foundation | Foundation complete for now; live curator not started | `bash scripts/wallpaper-photo-rotation-handoff-safety-status.sh`; `bin/chief-of-staff --return-to-core-status` | No live app/runtime | Docs/status-only planning unless explicitly approved | Wallpaper app, scheduler, widgets, shortcuts, OS-level changes, automation, APIs, network calls |
| Dashboard / Chief of Staff status | Active only as status/dashboard command surface | `bin/chief-of-staff --dashboard` | Read-only status output | Docs/status clarity or read-only checks | Behavior changes, command removals/renames, dashboard health count drift without explicit reason |

### Chief of Staff command surfaces are read-only proof surfaces

`bin/chief-of-staff --dashboard`, `bin/chief-of-staff --curriculum-builder-foundation-status`, `bin/chief-of-staff --return-to-core-status`, and `bin/chief-of-staff --prompt-pack-stale-reference-audit-status` report PASS/WARN/FAIL status only. They do not activate parked tracks, implementation, wallpaper runtime, lesson generation, schema activation, or dashboard behavior changes. Wallpaper/photo status commands are read-only proof surfaces unless explicitly named as dry-run validators.

### Do not restart parked work

- Do not recreate the placeholder skeleton.
- Do not recreate the placeholder registry.
- Do not expand Curriculum Builder planning docs without a clear reason.
- Do not treat Appearance/Vibe status scaffolding as a live app.
- Do not start implementation from any parked track without explicit approval.

### Current source-of-truth commands

```bash
bash scripts/lesson-planning-template-readiness-status.sh
bash scripts/curriculum-builder-foundation-status.sh
bash scripts/wallpaper-photo-rotation-handoff-safety-status.sh
bin/chief-of-staff --return-to-core-status
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
```

Curriculum Builder parked. Lesson-planning placeholder readiness parked. Appearance & Vibe foundation complete for now; live curator not started. Dashboard remains a read-only status surface.

## Build Queue and Status Pointer Consistency

Lesson-planning placeholder readiness is complete for now (PR #125). Curriculum Builder planning stack is complete and parked (PR #124). Placeholder skeleton and registry already exist and are validated. Static template schema planning remains documentation/status-only unless explicitly approved.

- Build queue: `docs/build-queue.md`
- Lesson-planning status: `bash scripts/lesson-planning-template-readiness-status.sh`
- Curriculum Builder status: `bin/chief-of-staff --curriculum-builder-foundation-status`
- Dashboard: `bin/chief-of-staff --dashboard` (health behavior unchanged)

Future follow-ons require documentation/status-only approval unless explicitly approved. No schema file, validator, active template behavior, lesson generation, lesson briefs, lesson drafts, or review notes are active.

## Recommended First Three Phase 1 PRs

Historical audit baseline from 2026-06-26 (completed):

1. Chief of Staff command launcher / status dashboard.
   Scope: one terminal command that shows Chief of Staff status, memory freshness, intake status, and next actions without external services.
2. Lesson planning workspace scaffold.
   Scope: local folders, docs, and templates for lesson planning workflows, with no student data or external integrations.
3. Developer Mode project templates.
   Scope: local starter templates for small lesson tools, apps, and scripts, with no deployment or secrets.

## Recommended Next PR

Parked — lesson-planning placeholder readiness and Curriculum Builder planning stack are complete for now.

Future lesson-planning follow-ons are documentation/status-only unless explicitly approved. Curriculum Builder implementation requires approval gate and completed decision intake. See the closeout sections below and `docs/build-queue.md` for current posture. Dashboard command remains `bin/chief-of-staff --dashboard`.

## Manual Checks For Owen

- Run `bash scripts/phase-1-status.sh`.
- Run `bash scripts/phase-1-status.sh --compare-0e`.
- Review `assistant/memory/active-priorities.md`.
- Review `assistant/memory/projects.md`.
- Confirm whether Photos widget setup is complete.
- Confirm whether OpenSCAD should remain optional.
- Confirm that Gmail, Drive, and email integrations remain permission-gated.
- Use `docs/build-queue.md` and the closeout sections below for current parked posture; do not restart completed skeleton, registry, or Curriculum Builder planning work.
