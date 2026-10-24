# Weekly Planner Agent — Persistent Change Detection + Live-State Reconciliation

Status: `CHANGE_DETECTION_BUILT` (planning/review layer only — no background
automation, no autonomous Canvas writes, no notification delivery, no
LaunchAgent install in this phase).

## Purpose

The agent can now reliably answer "What changed since the last check?", "Did a
test date move in pacing?", "Does Canvas still reflect the plan?", and "What
needs Owen's attention?" — by comparing a persisted history with current source
data rather than inventing change reports from the current snapshot.

## Architecture map

```text
scripts/weekly_planner_agent/
  snapshot.py            durable versioned snapshots (atomic write, corruption-safe,
                         first-run baseline) under .local/canvas-planner/agent/
  change_detection.py    diff snapshots -> classified SourceChangeEvents (stable IDs)
  event_store.py         lifecycle DETECTED..RESOLVED + resolution/override persistence
  impact.py              affected-artifact analysis + approval invalidation
  canvas_observation.py  read-only Canvas planning adapter (DeployClient-backed)
  freshness.py           source freshness + outage handling (never delete-on-outage)
  reconciliation.py      sync -> detect -> impact -> events -> notify orchestrator
  models.py              + SourceChangeEvent lifecycle/classification fields
  service.py             sync / changes / resolve_event / focus-context + instruct wiring
  teacher_instructions.py  + UPDATE_WITHOUT_REMINDER / KEEP_ASSESSMENT_DATE / SHOW_ANNOUNCEMENT

apps/teacher-workstation/   new "Changes" tab with change cards (old -> new, affected,
                            approve / keep current / ignore)
scripts/teacher_workstation/server.py   /api/agent/{changes,sync,resolve}
```

## Snapshot schema (version 1)

```json
{
  "schema_version": 1,
  "snapshot_id": "<uuid>",
  "week_id": "Q2W3",
  "pacing": {"status": "OK|STALE|UNAVAILABLE", "observed_at": "...",
             "identity": {"name","tab","spreadsheet_id"}, "fingerprint": "...",
             "cells": {"<subject>|<day>": {"lesson","chapter","classwork","homework",
                                           "assessment":{"name","date","day"}}}},
  "canvas": {"status": "OK|...", "observed_at": "...",
             "courses": {"<subject>": {"course_id","front_page","pages","assignments",
                                       "announcements","assignment_groups","read_error"}}}
}
```

- Writes are atomic (tmp + `os.replace`); history is append-only JSONL.
- Unknown schema versions / corrupt JSON raise `SnapshotCorrupt` (fail safely).
- A first observation establishes a baseline — no flood of false change alerts.
- Outages preserve the last successful snapshot and mark it stale; destructive
  conclusions (missing/deleted/conflict) are suppressed for the unavailable source.

## Change classifications

`lesson_changed`, `chapter_changed`, `homework_changed`, `classwork_changed`,
`assessment_date_changed`, `assessment_identity_changed`, `assessment_added`,
`assessment_removed`, `source_identity_changed`, `source_stale`,
`assignment_due_changed`, `assignment_missing`, `assignment_present_unexpectedly`,
`announcement_changed`, `reminder_missing`, `reminder_duplicated`,
`reminder_obsolete`, `page_body_changed`, `front_page_changed`, `canvas_conflict`.

Every event has a stable `event_id` (hash of week/source/subject/classification/
identity/old/new). Repeated polling dedups; a genuinely new change gets a new id.

## Assessment Date Watch (operational)

A test-date change in pacing (or verified Canvas) produces exactly one
`assessment_date_changed` teacher-attention event, recomputes the proposed plan,
identifies the weekly page / assessment assignment / first announcement /
day-before reminder / weekly update as affected, and drafts a notification:

> "Would you like me to update the live Canvas items and parent communications?"

A teacher override (`KEEP_ASSESSMENT_DATE`) persists and outranks subsequent
ordinary refreshes. It never silently rewrites live family-facing content.

## Event lifecycle

`DETECTED → ANALYZING → NEEDS_OWEN → PLAN_UPDATED → APPROVED / IGNORED / RESOLVED / BLOCKED`.
Resolution records who/when/action; "Ignore for now" keeps the event visible.

## Non-activation

No Canvas writes, no notification delivery, no scheduling, no LaunchAgent.
The existing guarded rollover remains the only publisher.

## Validation

```bash
bash scripts/weekly-planner-agent-status.sh
python3 -m unittest discover -s tests/weekly_planner_agent
```
