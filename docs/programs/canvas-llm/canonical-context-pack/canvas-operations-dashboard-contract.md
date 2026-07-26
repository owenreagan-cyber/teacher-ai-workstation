# Canvas Operations Dashboard Contract

```text
Status: active contract (C1E–C1H operations intelligence)
Authority: canonical-context-pack
Runtime activation: read-only dashboard and preview; controlled fake-mode writes only
```

## Purpose

Define the operational command center that answers:

- What is ready for Canvas?
- What needs my approval?
- What changed?
- What needs repair?
- What will publish if I approve?

## Dashboard States (C1E)

| State | Meaning | Example |
| --- | --- | --- |
| READY TO PUBLISH | Passed validation, approval, and readiness | Weekly Agenda, Assessment Announcement, Newsletter |
| NEEDS REVIEW | Warning or missing teacher coverage | Missing teacher input, validation warning |
| BLOCKED | Cannot publish | Assignment publishing disabled, missing approval |
| DRIFT DETECTED | Canvas content differs from expected artifact | Title/hash mismatch |

### Module

`scripts/canvas_llm_phase22/canvas_operations_dashboard.py`

- `CanvasOperationsDashboard` — ready_items, needs_review_items, blocked_items, drift_items, recent_activity, health_summary
- Command: `bin/chief-of-staff --canvas-operations-dashboard`
- No publishing performed by dashboard

## Deployment Preview (C1F)

`scripts/canvas_llm_phase22/weekly_deployment_center.py`

- `WeeklyDeploymentCenter` — builds `DeploymentPreview` from weekly content packet
- Preview only — no Canvas execution
- Shows CREATE, UPDATE, and BLOCKED changes
- Assignments always BLOCKED with reason

### DeploymentPreview Fields

preview_id, week_code, changes, artifact_count, approved_count, blocked_count, requires_teacher_action, created_at

## Sandbox Connector (C1G)

`scripts/canvas_llm_phase22/canvas_connector.py`

### Modes

| Mode | Status |
| --- | --- |
| fake | Available for local testing |
| sandbox | Requires human-authorized credentials |
| production | Disabled |

### CanvasSandboxConfig

mode, course_id, credential_state, enabled — never stores credentials

### Read APIs

- `list_pages(course_id)`
- `list_announcements(course_id)`
- `find_existing_object(course_id, target_type, ...)`

### Duplicate Prevention

| Result | Action |
| --- | --- |
| MATCH | Do not duplicate |
| CONFLICT | Block create |
| MISSING | Create candidate |

## Drift Detection (C1H)

`scripts/canvas_llm_phase22/canvas_drift.py`

### CanvasDriftReport

artifact_id, expected_hash, actual_hash, difference_type, recommendation, requires_teacher_approval

### Drift Types

CONTENT_CHANGED, OBJECT_MISSING, WRONG_TARGET, STALE_VERSION

### Version Tracking

`CanvasDeploymentVersion` — artifact_id, content_hash, canvas_object_id, revision, published_at, verified_at

Purpose: know what version is on Canvas.

## Repair Center

`scripts/canvas_llm_phase22/canvas_repair_center.py`

- Command: `bin/chief-of-staff --canvas-repair-center`
- Aggregates drift reports into recommendations
- No repairs executed — teacher approval required

## Lifecycle

```text
Generate
  ↓
Validate
  ↓
Approve
  ↓
Preview
  ↓
Teacher Action
  ↓
Publish (controlled, fake-mode simulation only)
  ↓
Verify
  ↓
Monitor
```

## Safety Boundaries

### Allowed

- announcements
- pages
- dashboard summaries
- deployment previews
- drift recommendations
- audit records

### Blocked

- assignments publishing
- grades / gradebook
- modules
- files
- student data
- enrollments
- submissions
- automatic publishing
- background sync
- scheduled deployment
- automatic repair

## Non-Activation

This contract documents operations intelligence posture only. Live Canvas API writes, assignment publishing, automatic deployment, and automatic repair remain blocked unless explicitly approved in a separate mission.
