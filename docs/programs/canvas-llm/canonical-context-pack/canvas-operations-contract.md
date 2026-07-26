# Canvas Operations Contract

```text
Status: active contract (C1A–C1D teacher-facing Canvas operations)
Authority: canonical-context-pack
Runtime activation: controlled fake-mode writes only; no live Canvas API writes
```

## Purpose

Define the first teacher-facing Canvas operations workflow. A teacher can prepare classroom Canvas updates from existing approved artifacts through a gated pipeline.

## Allowed Canvas Objects

| Object | Operation | Status |
| --- | --- | --- |
| Announcements | create (controlled) | READY |
| Pages (weekly agenda, homeroom newsletter, monthly information) | create (controlled) | READY |

## Blocked Canvas Objects

| Object | Reason |
| --- | --- |
| Assignments | Extra validation required; C1C preparation only |
| Grades / gradebook | Out of scope |
| Modules | Out of scope |
| Files | Out of scope |
| Student records | Privacy boundary |
| Enrollments | Out of scope |
| Submissions | Out of scope |

## Publishing Lifecycle

Every Canvas mutation requires the full pipeline:

```text
Artifact
  ↓
Validation (artifact health)
  ↓
Approval Queue
  ↓
Teacher Decision
  ↓
Deployment Readiness
  ↓
Write Gate
  ↓
Canvas Writer (announcements and pages only)
  ↓
Verification
  ↓
Audit
```

## Teacher Approval Boundary

- No Canvas write proceeds without an active teacher `approve` decision.
- Teacher decisions are recorded in `teacher_decision_records`; they do not mutate draft content.
- Stale approvals (hash/revision mismatch) invalidate prior decisions.
- Repair recommendations always require teacher approval before any corrective action.

## Verification

`canvas_verification.py` provides:

- `verify_announcement()` — exists, title matches, content hash matches, course matches
- `verify_page()` — exists, title matches, content hash matches, course matches

Verification statuses: `PASS`, `FAIL`, `BLOCKED`, `DRIFT_DETECTED`.

## Repair Recommendations

`canvas_repair.py` detects drift (e.g., expected "August Newsletter", actual "July Newsletter") and creates `RepairRecommendation` records.

- Drift detection only — no automatic repair
- All repair actions require teacher approval
- Recommended actions: `review_and_redeploy`, `request_teacher_approval`, `manual_correction`

## Write Control

- `canvas_writer.py` supports `create_announcement()` and `create_page()` only.
- `create_assignment()` is blocked and raises `RuntimeError`.
- No automatic publishing, background sync, or scheduled publishing.
- Fake connector mode simulates controlled local writes for testing; sandbox/live execution remains blocked by the write gate.

## Module Map

| Module | Phase | Role |
| --- | --- | --- |
| `canvas_announcement_deployment.py` | C1A | Announcement deployment flow |
| `weekly_agenda_publisher.py` | C1B | Weekly agenda page generation and deployment |
| `assignment_deployment_preview.py` | C1C | Assignment preflight (no writes) |
| `canvas_operations.py` | C1D | Newsletter/page pipeline and status reports |
| `canvas_writer.py` | C1A/C1D | Controlled Canvas writer |
| `canvas_verification.py` | C1D | Post-write verification |
| `canvas_repair.py` | C1D | Drift detection and repair recommendations |

## Chief of Staff Commands

| Flag | Output |
| --- | --- |
| `--canvas-operation-status` | Announcements READY, Pages READY, Assignments BLOCKED, Writes Controlled |
| `--canvas-repair-status` | Issue count, needs-approval count, no automatic repairs |

## Safety Boundaries

- No student data in published content
- No grades, enrollments, or submissions
- No email transport
- No Bearer tokens or secrets in audit output
- No Phase 26/27 behavior changes from C1 operations

## Non-Activation

This contract documents controlled Canvas operations posture only. Live Canvas API writes, assignment publishing, and automatic deployment remain blocked unless explicitly approved in a separate mission.
