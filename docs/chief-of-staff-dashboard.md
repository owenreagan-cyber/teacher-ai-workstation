# Chief of Staff Dashboard

## Purpose

The Chief of Staff Dashboard is a local, read-only status command for Phase 1 work.

It gives Owen one place to check workstation phase health, available Chief of Staff workflows, LLM CLI readiness, memory status, intake status, the build queue, and current safety reminders before starting deeper Chief of Staff or lesson planning work.

This is the first real Phase 1 utility. It is still not the full Teacher Chief of Staff agent.

## What It Checks

- Phase 0E verification status through `scripts/verify-phase-0e.sh`.
- Phase 1 readiness status through `scripts/phase-1-status.sh`.
- Available Chief of Staff workflows through `bin/chief-of-staff --list-workflows`.
- Whether the `llm` CLI is installed.
- Whether a default `llm` model can be detected through a local `llm` command.
- Whether key memory files are present and mention Phase 0E, Phase 1, Chief of Staff or Developer Mode, and dashboard/command launcher language.
- Whether memory Markdown files may be older than 30 days.
- Intake status through `bin/chief-of-staff --intake-status`.
- The next recommended PR from the `## Next PR` sentinel in `docs/build-queue.md`.

## What It Does Not Do

- It does not call Gmail, Drive, Calendar, Reddit, Spotify, Unsplash, Photos, or web APIs.
- It does not send email.
- It does not read student-sensitive data.
- It does not create journal entries.
- It does not run in watch mode.
- It does not monitor in the background.
- It does not install, configure, or update tools.
- It does not add dependencies.
- It does not build lesson generation.
- It does not build Developer Mode templates.

## Safety Boundaries

- Local/read-only dashboard.
- No Gmail, Drive, Calendar, or email automation yet.
- No OAuth, API keys, paid services, or secrets.
- No student-sensitive data by default.
- Human review before sending, sharing, publishing, or using classroom artifacts.
- Connected services require explicit future permission and safety review.

## How To Run

Run the script directly:

```bash
bash scripts/chief-of-staff-dashboard.sh
```

Or use the Chief of Staff launcher:

```bash
bin/chief-of-staff --dashboard
```

## Expected Output

Expected sections:

- `Teacher Chief of Staff Dashboard`
- `Workstation Phase Status`
- `Available Chief of Staff Workflows`
- `LLM CLI Readiness`
- `Memory Status`
- `Intake Status`
- `Build Queue / Next Action`
- `Safety Reminders`
- `Summary`

Expected summary when the workstation is healthy:

```text
PASS: <count>
WARN: <count>
FAIL: 0
Health: <passing>/<total> checks passing
```

Warnings are not always blockers. Missing future/planned items, missing `llm`, or stale memory may be warnings that Owen can review manually.

## Troubleshooting

If Phase 0E fails, run:

```bash
bash scripts/verify-phase-0e.sh
```

Then inspect the failing section. Do not continue into new automation work until critical failures are fixed.

If Phase 1 status fails, run:

```bash
bash scripts/phase-1-status.sh
```

Review the failing Chief of Staff, memory, intake, or script checks before starting implementation work from a parked track.

If `bin/chief-of-staff` is not executable, run:

```bash
chmod +x bin/chief-of-staff
```

If the `llm` CLI is missing, the dashboard can still run. Chief of Staff workflows that call `llm` may not run yet. Do not install or configure `llm` from the dashboard.

If memory files are stale, review:

```bash
assistant/memory/active-priorities.md
assistant/memory/projects.md
```

Stale memory is a warning, not a failure. Update memory in a separate focused change when the project state has changed.

If intake status fails, run:

```bash
bin/chief-of-staff --intake-status
```

Then review the intake files under `assistant/intake/`. Raw intake is not approved context.

If the build queue next PR cannot be parsed, make sure `docs/build-queue.md` contains this exact sentinel:

```markdown
## Next PR

Pause active lesson-planning implementation.
```

If Phase 0E passes but Phase 1 has warnings for planned/future docs, treat those as planning signals unless the script reports critical failures.

## Relationship To Morning Brief

`assistant/workflows/morning-brief.md` exists as an interactive workflow. Running the dashboard before the morning brief gives current system status and next-action context. The morning brief still uses only provided or approved sources and does not read calendars, notes, tasks, Gmail, or Drive in the background.

## Curriculum Builder Planning Index Visibility

The dashboard includes Curriculum Builder foundation status under Lesson Planning Status. For planning navigation beyond PASS/WARN/FAIL counts, use the canonical planning index.

| Topic | Reference |
| --- | --- |
| Curriculum Builder planning index | `docs/curriculum-builder-canonical-planning-index.md` |
| Approval gate required before implementation | `docs/curriculum-builder-approval-gate.md` |
| Status command to verify readiness | `bin/chief-of-staff --curriculum-builder-foundation-status` |

Additional verification:

```bash
bin/chief-of-staff --dashboard
```

This visibility note is documentation only. It does not change dashboard behavior, dashboard health count, or PASS/WARN/FAIL semantics.

## Chief of Staff Command Surfaces

`bin/chief-of-staff --dashboard` is the main read-only dashboard proof surface. It reports PASS/WARN/FAIL status only and does not change repo or app state.

These commands are also read-only status proof surfaces unless explicitly named as dry-run validators:

- `bin/chief-of-staff --curriculum-builder-foundation-status` (Curriculum Builder parked; approval-gated)
- `bin/chief-of-staff --teacher-app-designer-canvas-llm-status` (Teacher App Designer / Canvas LLM planning only; no live connectors)
- `bin/chief-of-staff --return-to-core-status` (paused tracks / return-to-core proof)
- `bin/chief-of-staff --prompt-pack-stale-reference-audit-status` (prompt-pack reference proof)
- `bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status` (Appearance & Vibe foundation parked; live curator not started)

Status command output is not implementation activation. For parked vs active tracks, see `docs/phase-1-chief-of-staff-status-audit.md` — Repo-Wide Parked Tracks and Active Status Map.

## Future Ideas Not Implemented

- `--json` output.
- `--quiet` output.
- `--watch` mode.
- journal entry logging.
- canonical shared safety reminders doc.

## Recommended Next PR

Parked — lesson-planning placeholder readiness and Curriculum Builder planning stack are complete for now.

Future lesson-planning follow-ons are documentation/status-only unless explicitly approved. Curriculum Builder implementation requires approval gate and completed decision intake. Dashboard health behavior remains unchanged; existing status commands remain the source of truth.
