# Weekly Planner Agent — Live Read-Only Reconciliation

```text
Status: active (implementation)
Phase: weekly-planner-live-reconciliation
Branch: feature/weekly-planner-live-reconciliation
Runtime activation: read-only GET only (Canvas + Google pacing)
Non-destructive: no Canvas writes, no real email, no scheduler activation
```

## What this phase proves

Before any automation is activated, the Weekly Planner Agent can correctly
understand the **live world**: the real credential-gated Canvas courses and the
real Google pacing sheet. This phase is read-only and non-destructive.

## Live sources

- **Google pacing** — the authoritative public `gviz` CSV export
  (`https://docs.google.com/spreadsheets/d/<id>/gviz/tq?tqx=out:csv&sheet=<tab>`),
  fresh-read through `scripts.canvas_llm_phase3.pacing_extractor`. No credentials.
- **Canvas** — the credential-gated `CanvasReadOnly` client
  (`scripts.canvas_llm_intake.canvas_readonly`), GET only. Credentials resolve
  from env or `~/.config/teacher-ai-workstation/canvas.env` (mode 0600); the
  token is never printed, logged, or returned.

## Read-only enforcement

`scripts/weekly_planner_agent/live_sources.py`:

- `ReadOnlyCanvasClient` exposes **only** GET read methods. Any non-GET verb
  (POST/PUT/PATCH/DELETE) — or any unknown method — raises `NonGetVerbError`
  and is recorded in a mutation audit. The live reconciliation path cannot
  issue a write.
- `read_live_pacing()` returns `UNAVAILABLE`/`STALE` (never silently substitutes
  stale cache as "live").
- `read_live_canvas()` observes pages (weekly agenda, body, published state,
  front-page identity), assignments, due dates, assignment groups, and
  announcements (posted vs scheduled), plus the Homeroom course.

## Reconciliation

`service.live_sync(quarter, week)` runs the existing observe→detect→impact→
events pipeline (`reconciliation.sync_and_detect`) against both live sources,
then enriches the result with an Assessment Date Watch. On a source outage the
last successful snapshot is preserved (marked stale/unknown), never emptied.

Classification covers: changed lesson/chapter/test date/assignment due date,
missing/unexpected assignment, stale announcement, stale reminder,
already-posted outdated announcement, reminder scheduled for an obsolete date,
direct Canvas page edit, stale weekly page, wrong front page, and source outage.

## Assessment Date Watch

For each assessment-date change, exactly **one** teacher-attention entry is
produced with: old date, new date, the source that changed, the current Canvas
state (assignment due date, first announcement, day-before reminder), whether
anything already posted, the recommended communication action
(`communication_rules.handle_date_change`), and the ask:

> "Would you like me to prepare the updated Canvas items and parent communications?"

Live Canvas is never changed.

## UI surface

The existing Teacher Workstation `#agent` view gains:

- **Today** — important changes, source freshness, assessment-date alerts.
- **Week plan** — confirmed/inferred/predicted items, teacher overrides, planned
  assignments, announcements/reminders.
- **Changes** — old → new, source, impact, and the approve/keep/ignore actions.
- **Friday review** — pages, assignments, announcements, reminders, Homeroom,
  changed items, blockers, source freshness, approval state.
- **Agent** — plain-language instructions update proposed state; raw technical
  fields stay hidden behind the Advanced panel.

## Headless UI tests

`tests/ui/` contains an isolated headless Playwright suite (local fixture server
on 127.0.0.1:4311). It never drives Owen's visible desktop.

```bash
cd tests/ui && npm install && npx playwright install chromium && npx playwright test
```

## Non-live guarantees

- `email_enabled = false`; delivery mode `preview`.
- The existing Friday rollover remains the **only** publisher.
- The Friday LaunchAgent is **not** installed or loaded.
- No Canvas writes, no Canvas Inbox messages, no real email.

## Status

```bash
bin/chief-of-staff --weekly-planner-agent-status
```

Reports current week, pacing/Canvas freshness, last live GET-only sync,
unresolved changes, Assessment Date Watch alerts, Friday review state, approval
readiness, notification mode, LaunchAgent state, and last publication result.
Live integration is reported PASS only when a real read-only check succeeds.
