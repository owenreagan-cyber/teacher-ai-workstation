# Weekly Planner Agent — Foundation

Status: `FOUNDATION_BUILT` (planning/review layer only; no background automation,
no autonomous Canvas writes, no LaunchAgent install in this phase).

## Purpose

The Weekly Planner Agent is the teacher-facing product Owen interacts with. It
sits on top of the existing safe Canvas infrastructure (intake, planner, guarded
Friday publisher) and removes the manual toil of the previous workflow: editing
JSON, inspecting hashes, building Canvas HTML, finding page IDs, running raw
rollover commands, and hunting approval files.

## Two workflows (canonical principle)

```text
Teacher-facing:  plain language → proposed plan → review → approve → guarded publish → verify
Technical:       sources → normalized weekly plan → change engine → draft artifacts
                 → approval → publisher → readback verification
```

## Architecture map

```text
scripts/weekly_planner_agent/
  models.py              WeeklyPlan, DayPlan, Assessment, SourceChangeEvent,
                         Notification, FridayReview, Authority hierarchy,
                         Confidence (confirmed/inferred/predicted), PlanStatus
  authority.py           conflict resolution (never silently guess)
  teacher_instructions.py  deterministic plain-language parser → structured ops
  change_engine.py       apply ops, recompute affected artifacts,
                         approval-by-exception invalidation
  assessment_watch.py    Assessment Date Watch
  communication_rules.py first-announcement / day-before-reminder / date-change logic
  notification_model.py  notification types + email drafting (delivery later)
  review_state.py        Friday Review state machine + approval-by-exception
  service.py             TODAY / WEEK PLAN / FRIDAY REVIEW / AGENT projections
                         + local agent state (.local/canvas-planner/agent/)

Reused (not duplicated):
  scripts/canvas_llm_intake/    canonical packet, owner overrides, reminders
  scripts/canvas_planner/       projection service, source_sync, events
  scripts/canvas_llm_rollover/  the only publisher (Friday 4 PM engine)
  scripts/canvas_llm_deploy/    DeployClient (live/fake) — used by all tests
  apps/teacher-workstation/     UI shell (new Weekly Planner Agent view)
  scripts/teacher_workstation/  local HTTP server (new /api/agent/* routes)
```

## Authority hierarchy (lower wins)

1. Owen explicit instruction (owner override)
2. current verified pacing source
3. current verified Canvas state
4. established subject rules
5. historical inference/prediction

Conflicts are surfaced, never silently guessed. Predicted items are never
silently promoted to approved/live.

## Assessment Date Watch

When pacing or verified Canvas state indicates a test date changed and the
change was not already approved by Owen, the agent creates a teacher-attention
event, recomputes the proposed plan and affected drafts, and asks:

> "Would you like me to update the live Canvas items and parent communications?"

It never silently rewrites live family-facing communications.

## Standing assessment communication rules

- **First announcement** — ~one weekend in advance, no later than the Friday
  before the test; created as part of assessment planning.
- **Day-before reminder** — auto-created/scheduled when the first announcement
  is created (delayed send for the day before the test).
- **Date change** — before the reminder posts: reschedule (no duplicate); before
  the first announcement posts: update (no duplicate); after the first
  announcement posts: propose a correction (requires approval); after the
  reminder posts: propose a corrective communication (requires approval).

## State boundaries

`CONFIRMED_SOURCE` (what pacing/Canvas says) → `PLANNED` (what the agent intends)
→ `APPROVED` (what Owen approved) → `LIVE` (what Canvas contains) →
`VERIFIED` (what readback proves).

## Non-activation

This phase delivers no background scheduling, no LaunchAgent install, no
autonomous Canvas writes, no notification delivery, and no live Google Sheets
edits. All agent state is untracked under `.local/canvas-planner/agent/`.

## Active announcement feed fix (non-blocking Q2W3 issue)

`CanvasReadOnly.list_active_announcements()` previously requested
`/api/v1/announcements?active_only=true` without `context_codes[]`, which Canvas
rejects with HTTP 400. It now accepts and passes `context_codes[]` (e.g.
`course_<id>`); the deploy/rollover callers pass their course id.

## Validation

```bash
bash scripts/weekly-planner-agent-status.sh
python3 -m unittest discover -s tests/weekly_planner_agent
```
