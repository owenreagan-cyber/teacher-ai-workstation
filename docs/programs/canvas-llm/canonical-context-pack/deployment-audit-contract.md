# Deployment Audit Contract

## Purpose

The deployment audit layer records local readiness and review events for future operational traceability.

It answers:

```text
What readiness, approval, and review events occurred for this artifact?
```

It does **not** record successful deployment events in readiness builds.

## Model

`DeploymentAuditEvent` fields:

- `event_id`
- `artifact_id`
- `event_type`
- `actor`
- `timestamp`
- `result`

## Supported event types

- `validation`
- `approval`
- `readiness_check`
- `rollback`

## Blocked event types

- `deployment_attempt` — rejected in readiness builds

No deployment events should occur.

## Redaction

Audit output must redact:

- tokens
- authorization headers
- secrets
- private URLs

## Lifecycle placement

```text
artifact
  ↓
validation        → audit: validation
  ↓
approval queue    → audit: approval
  ↓
teacher decision
  ↓
deployment readiness → audit: readiness_check
  ↓
rollback planning → audit: rollback
  ↓
execution (blocked)
```

## Explicitly blocked

- automatic deployment logging as success
- secret persistence
- student data in audit payloads

## Commands

```bash
bin/chief-of-staff --canvas-audit-status
python3 scripts/canvas_llm_phase22/deployment_audit.py self-test
bash tests/canvas-llm-deployment-audit-test.sh
bash scripts/canvas-llm-audit-status.sh
```

## Non-activation

This contract describes local audit semantics only. It does not activate publishing, email, or live Canvas writes.
