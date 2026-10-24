# Weekly Planner Agent — Guarded Publish + Notification Delivery

Status: `GUARDED_PUBLISH_BUILT` (orchestration + delivery abstraction; no live
automation activated).

## Purpose

Connects the persisted weekly plan, source-change events, approvals, and
notification drafts to the existing guarded Friday rollover publisher. The
teacher-facing interface is the product: one "Approve Plan" action binds
approval to the exact plan/source versions reviewed, then the existing
`bin/canvas-weekly-rollover` engine performs and verifies the work.

## Canonical workflow

```text
refresh pacing + read-only Canvas observations
 -> persist snapshots + detect changes
 -> reconcile plan + affected artifacts
 -> generate candidate artifacts + notification/Friday-review summary
 -> Owen reviews in the Teacher Workstation UI (plain-language corrections)
 -> Approve Plan (bound to the exact plan version + source fingerprint)
 -> guarded rollover runs only when every gate passes
 -> readback verification
 -> PUBLISHED_VERIFIED
```

`bin/canvas-weekly-rollover` remains the SOLE publisher. No second publishing path.

## Architecture / integration points

```text
scripts/weekly_planner_agent/
  schedule_config.py   configured Friday schedule + delivery gate (email off by default)
  delivery.py          notification delivery abstraction (preview/local/email sinks,
                       DRAFTED/QUEUED/DELIVERED/FAILED/SUPPRESSED, idempotency)
  publish.py           plan-version binding + agent publish gate + guarded-publish
                       orchestration that delegates to the existing rollover
  service.py           approve_plan / publish_gate / publish_now / notifications /
                       deliver_notification surfaces
  models.py            PlanApproval + notification statuses + Friday NEEDS_OWEN state

scripts/teacher_workstation/server.py   /api/agent/{approve,publish,notify,notifications}
apps/teacher-workstation/               Friday Review approval + publish status + preview
bin/chief-of-staff + manifest            --weekly-planner-agent-status
```

Reused (not duplicated): `scripts/canvas_llm_rollover.rollover` (publisher),
`scripts/canvas_llm_deploy.client.DeployClient` (live/fake),
`scripts/canvas_planner.approval_bundle` (canonical per-artifact approval),
`scripts/canvas_planner.friday` (week derivation).

## Plan-version binding

`approve_plan` records a `PlanApproval{plan_version, source_fingerprint}` under
`.local/canvas-planner/agent/`. `plan_version` hashes the approval-relevant plan
content (subject/day lesson, classwork, homework, assessment dates, overrides,
candidate artifacts); `source_fingerprint` hashes the pacing + Canvas snapshot.

`build_publish_gate` blocks when:
- no snapshot / pacing or Canvas stale or unavailable
- an unresolved assessment-date (family-comms) change exists
- the plan is not approved
- the plan or source changed after approval (version mismatch)

It then merges the canonical `rollover.build_readiness` blockers. The canonical
per-artifact approvals are still written by `approval_bundle.approve_course`
during `approve_plan`, so the guarded rollover's readiness gate sees them.

## Notification delivery

`delivery.deliver` routes a record through `preview` (DRAFTED, sends nothing),
`local` (QUEUED, outbox JSONL), or `email` (FAILED unless explicitly enabled +
recipient configured). Idempotency keys suppress duplicate delivery. A record
is never DELIVERED just for being generated or queued. Email is disabled by
default (`schedule_config.DELIVERY_DEFAULT.email_enabled = False`).

## Friday schedule (configured, not hard-coded)

`schedule_config.schedule()` returns `{source_sync_before_review, final_refresh,
approval_ready_email, publish, timezone}` overlaid by local config. No scheduler
runs in this phase.

## Non-activation

No live Canvas writes, no real email, no Canvas Inbox, no LaunchAgent install,
no unattended publishing, no background polling. The existing manually-invoked
guarded publisher is unchanged in authority.

## Validation

```bash
bash scripts/weekly-planner-agent-status.sh
bin/chief-of-staff --weekly-planner-agent-status
python3 -m unittest discover -s tests/weekly_planner_agent
```
