# Teacher Decision Contract

## Purpose

The teacher decision record layer remembers teacher decisions safely without granting deployment authority.

It answers:

```text
What did the teacher decide about this artifact?
```

Examples: approved, rejected, needs changes, deferred.

It does **not** publish, deploy, send, write to Canvas, send email, or automatically approve.

## Decision records

`TeacherDecisionRecord` is an audit/history record stored in SQLite table `teacher_decision_records`.

It does **not** mutate artifact drafts or registry ownership fields.

Supported decision types:

- `approve`
- `reject`
- `request_changes`
- `defer`

Supported decision statuses:

- `active`
- `superseded`
- `invalidated`

## Audit history

Decision history is append-oriented:

- new decisions create new records
- prior active decisions may become `superseded`
- invalidated decisions remain in history

Example timeline:

```text
2026-07-26 — Approved — Teacher
2026-07-28 — Content changed — Approval invalidated
2026-07-29 — Approved — Teacher
```

History is read-only in status reporting. Records are not deleted.

## Invalidation rules

A decision is never permanent.

If `artifact_content_hash` changes **or** `artifact_revision` changes relative to a stored decision, the active decision becomes:

```text
decision_status = invalidated
```

Invalidation is derived and persisted on the decision record only. Artifact registry approval fields are not modified directly.

## Revision behavior

Approval readiness combines:

```text
Registry state + Latest Decision Record
```

Derived examples:

| Condition | Derived state |
| --- | --- |
| No decision | `READY_FOR_REVIEW` |
| Active approve + matching hash/revision | `APPROVED_BY_TEACHER` |
| Active reject / request_changes | `CHANGES_REQUESTED` |
| Invalidated or mismatched revision/hash | `REVIEW_REQUIRED` |

## Teacher visibility

Read-only reporting command:

```bash
bin/chief-of-staff --teacher-decision-status
```

Purpose: read-only teacher decision history and approval state summary.

The queue remains visibility-only. Decision records add memory, not authority.

## Lifecycle

```text
Artifact
↓
Validation
↓
Approval Queue
↓
Teacher Decision Record
↓
Future Deployment Eligibility
```

Deployment eligibility remains future work and is not activated in C0S.

## Safety boundaries

Explicitly blocked:

- automatic approval
- Canvas publishing
- email sending
- external connectors
- OAuth / external APIs
- background workers / schedulers
- deployment handlers

No chief-of-staff commands added for:

- `--approve`
- `--reject`
- `--publish`
- `--send`
- `--deploy`

## Duplicate prevention

For the same artifact with the same hash, revision, and decision type, only one active record is kept.

New decisions create history. Changed content invalidates prior approvals instead of deleting them.

## Non-activation

This contract documents local decision persistence and read-only reporting only. It does not activate Canvas writes, email transport, or deployment automation.
