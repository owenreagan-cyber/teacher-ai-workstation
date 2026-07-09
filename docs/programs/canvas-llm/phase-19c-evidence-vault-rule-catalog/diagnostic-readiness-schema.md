# Diagnostic Readiness Schema

## Status

Preview-only schema specification.

## Purpose

Diagnostic readiness defines when a rule or evidence set is ready for Medical Center checks.

## Readiness Levels

```text
NOT_READY
REVIEW_READY
PREVIEW_READY
DIAGNOSTIC_READY
WRITE_GATE_CANDIDATE
BLOCKED
```

## Readiness Record Schema

| Field | Required | Description |
|---|---:|---|
| readiness_id | yes | Stable ID, for example `READY-CANVAS-0001` |
| target_type | yes | evidence_set, rule, preview, diagnostic, write_gate |
| target_id | yes | Target ID |
| readiness_level | yes | One of the readiness levels |
| reason | yes | Human-readable reason |
| missing_requirements | no | Items blocking promotion |
| required_review | no | Human review required |
| safety_boundary | yes | Safety constraints |
| validation_command | no | Future status command if available |
| created_in_phase | yes | Phase ID |

## Promotion Requirements

A rule can become `DIAGNOSTIC_READY` only when it has:

- approved rule status
- evidence links
- source authority
- validation requirements
- blocked actions
- no unresolved blocking conflicts

A rule can become `WRITE_GATE_CANDIDATE` only when it also has:

- exact operation type
- exact target restriction
- exact approval phrase
- rollback/cleanup expectation
- redaction proof
- post-action validation plan

## Phase 19C Default

All Phase 19C schemas are:

```text
PREVIEW_READY
```

No Phase 19C output is `WRITE_GATE_CANDIDATE`.

## Boundary

Diagnostic readiness does not authorize Canvas writes.
