# Approval Queue Contract

## Purpose

The approval queue is a **derived, read-only, local, deterministic** view over the Canvas LLM artifact registry.

It answers:

```text
What needs teacher attention?
```

It does **not** answer:

```text
Approve this artifact.
```

No approval buttons. No mutation. No write commands.

## Queue behavior

The queue is built from existing C0Q registry records:

```text
artifact_registry.py
        ↓
approval_queue.py
        ↓
chief-of-staff --approval-queue-status
```

Generators remain authoritative. The registry remains the discovery layer. The queue adds teacher decision visibility only.

## Artifact sources

Supported artifact kinds (unchanged from C0Q):

| Kind | Source |
| --- | --- |
| `assignment` | Phase 22 `drafts` table |
| `announcement` | Phase 22 `drafts` table |
| `newsletter` | Phase 22 `drafts` table |
| `newsletter_update` | Phase 22 `drafts` table |
| `daily_brief` | Phase 22 `drafts` table |

No new artifact generation is introduced.

## Queue states

### READY

Artifact is preview-generated, validation passes, no blockers, and teacher approval is required.

Example: Daily Teacher Brief preview ready for teacher review while delivery remains `blocked_preview`.

### NEEDS_REVIEW

Artifact has `needs_review=true` or warnings exist.

Example: assessment announcement missing teacher-entered coverage.

### BLOCKED

Artifact has blockers or deployment is blocked.

Example: newsletter update blocked until a verified page URL exists.

### STALE_APPROVAL

Derived-only state when content hash or approval revision no longer matches an approved snapshot.

Example:

```text
approved hash: abc123
current hash:  xyz789
queue result:  STALE_APPROVAL
```

Original approval state is not mutated. Only derived queue health is reported.

## Teacher decision future schema

C0R documents and validates shape only. Decisions are **not persisted**.

`TeacherDecision` fields:

| Field | Purpose |
| --- | --- |
| `decision_id` | Stable decision identifier |
| `artifact_id` | Target artifact |
| `decision_type` | `approve`, `reject`, `request_changes` |
| `status` | `pending`, `approved`, `rejected` |
| `teacher_note` | Optional teacher note |
| `created_at`, `created_by` | Audit metadata |
| `invalidates_on_revision` | Decision invalid when content revision changes |

No mutation APIs are added in C0R.

## Revision invalidation rules

Approval readiness is tied to artifact hashes:

- if `content_hash` changes after approval, queue reports `STALE_APPROVAL`
- if `approval_revision` changes after approval, queue reports `STALE_APPROVAL`
- stale reporting is derived only; stored approval state is unchanged

## Lifecycle

```text
Artifact
↓
Validation
↓
Approval Queue
↓
Teacher Decision
↓
Future Deployment
```

Controlled deployment and transport remain future work.

## Safety boundaries

The queue must not:

- auto-approve artifacts
- approve artifacts silently
- mutate artifact approval states
- create deployment handlers
- call Canvas APIs
- send email
- use external connectors

Output must not include emails, URLs, secrets, local private paths, or database paths.

## Explicitly blocked

- automatic approval
- Canvas writes
- email sends
- external connectors
- background workers
- schedulers
- AI generation

## Command surface

Read-only queue command:

```bash
bin/chief-of-staff --approval-queue-status
```

Purpose: read-only teacher approval queue summary.

Not in scope:

- `--approve`
- `--publish`
- `--send`
- `--deploy`

## Non-activation

This contract documents a read-only queue view only. It does not activate runtime behavior, Canvas writes, email delivery, approval mutation, or external integrations.
