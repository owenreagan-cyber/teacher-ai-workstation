# Canvas Deployment Readiness Contract

## Purpose

The deployment readiness gate determines whether an artifact is eligible for **future** human-authorized deployment.

It answers:

```text
Is this artifact ready for a controlled deployment attempt?
```

It does **not** publish, deploy, write to Canvas, send email, or bypass approval systems.

## Lifecycle

```text
artifact
  ↓
validation
  ↓
health
  ↓
approval queue
  ↓
teacher decision
  ↓
deployment readiness
  ↓
connector
  ↓
execution (blocked)
```

## Model

`DeploymentReadinessRecord` fields:

- `deployment_id`
- `artifact_id`
- `artifact_kind`
- `artifact_title`
- `target_system`
- `target_course`
- `operation_type`
- `approval_status`
- `health_status`
- `validation_status`
- `teacher_decision_status`
- `readiness_status`
- `blockers`
- `warnings`
- `rollback_plan`
- `created_at`
- `updated_at`

## Readiness states

| State | Meaning |
| --- | --- |
| `READY` | All required gates pass; connector available; rollback plan present |
| `NEEDS_REVIEW` | Warnings or missing owner decision require teacher review |
| `BLOCKED` | Missing approval, validation failure, connector disabled, or missing rollback |
| `NOT_ELIGIBLE` | Artifact missing or unsupported for deployment |

## READY requirements

- artifact exists
- validation `PASS`
- health `PASS`
- teacher approval exists
- teacher decision active
- connector available
- rollback plan complete

## BLOCKED examples

- missing approval
- missing target
- validation failure
- connector disabled
- missing rollback plan

## Explicitly blocked

- automatic deployment
- Canvas publishing
- email delivery
- student data access

## Commands

```bash
bin/chief-of-staff --canvas-deployment-readiness-status
python3 scripts/canvas_llm_phase22/deployment_readiness.py self-test
bash tests/canvas-llm-deployment-readiness-test.sh
bash scripts/canvas-llm-deployment-readiness-status.sh
```

## Non-activation

This contract is documentation and read-only evaluation only. It does not activate Canvas writes, publishing, or background jobs.
