# Canvas LLM Phase 18E — Owner Policy Finalization, Approval-Bound Preconditions & Controlled Write Preparation

```text
Status: implementation (pure pre-execution policy and validation layer)
Runtime activation: none — zero Canvas writes
Writes: 0 (never POST / PUT / PATCH / DELETE)
Write gate: CLOSED
Maximum readiness: READY_FOR_EXECUTION_REVIEW
Dependency: Phase 18D Dry-Run Deployment Packet (read-only)
```

## Objective

Phase 18E is the final contract-hardening phase before any future Canvas write
execution is permitted. It:

1. encodes the owner-approved homework due-time policy,
2. removes the obsolete due-time unresolved blocker,
3. preserves unresolved publish-state safety,
4. connects Phase 18D snapshot contracts to the existing approved read-only
   Canvas infrastructure where safely possible,
5. builds exact execution-precondition contracts,
6. builds a pure adapter from approved Phase 18D intents to future Phase 22
   writer requests,
7. proves that stale, unsafe, unapproved, protected, ambiguous, or
   policy-incomplete operations can never reach the writer,
8. keeps the existing write gate closed.

Phase 18E performs **zero Canvas writes**. It is a pure pre-execution layer:
it describes readiness and a future writer request, never execution.

## Architecture

```text
Evidence / Rules
        ↓
Canonical WeeklyPlan (Phase 18A)
        ↓
Translation (Phase 18B)
        ↓
Teacher Preview (Phase 18C)
        ↓
Dry-Run Deployment Packet (Phase 18D)
        ↓
Read-Only Canvas Snapshot
        ↓
Safety Diff (Phase 18D)
        ↓
Approval Record (Phase 18D contract)
        ↓
Execution Preconditions (Phase 18E)   ← this phase
        ↓
Future Phase 22 Writer Adapter (pure request contract)
        ↓
STOP — WRITES DISABLED
```

`WeeklyPlan` remains authoritative. Phase 18D remains the dry-run / Safety Diff
authority. Phase 22 remains the only future Canvas execution lineage. Phase 18E
only adds owner policy and execution preconditions; it introduces no second
writer, no second connector, and no second write gate.

## Module Layout

```text
scripts/canvas_llm_phase18e/
    __init__.py         pure public surface (excludes snapshot_adapter)
    contracts.py        pure enums/dataclasses (ExecutionPreconditionReport, WriterRequest)
    policy.py           OwnerCanvasPolicy + deterministic due_timestamp
    preconditions.py    evaluate_preconditions (execution-readiness checks)
    validation.py       packet/approval/policy/config/live-state validation + writer-default audit
    adapter.py          pure Phase 18D intent → proposed Phase 22 writer request
    snapshot_adapter.py optional read-only adapter over existing GET/read infra
    cli.py              self-check / report / status only
```

Only `snapshot_adapter.py` may touch read infrastructure, and only via an
injected connector — it is never imported by the pure `__init__` surface.

## Phase 18D dependency

Phase 18E consumes `DryRunPacket`, `DeploymentIntent`, `CanvasSnapshot`,
`SnapshotObject`, and `ApprovalRecord` from `scripts/canvas_llm_phase18d.contracts`.
It does not re-implement dry-run assembly, Safety Diff, or readiness. It only
evaluates whether an already-assembled, already-approved intent may become a
future writer request.

## Owner Canvas policy

The owner has explicitly approved:

> Homework assigned on a school day must appear in Canvas as due on that same
> calendar day at 11:59 p.m., using the canonical school/course timezone.

`OwnerCanvasPolicy` is an immutable (`frozen=True`) dataclass:

```text
schema_version = 1
homework_due_day = "assigned_day"
homework_due_time_local = "23:59"
homework_submission_type = "on_paper"
publish_state = "unresolved"   # owner has NOT approved a default publish decision
publish_decision = ""          # "published" | "unpublished" (only when resolved)
timezone = "America/New_York"
```

The policy serializes deterministically and has a deterministic semantic hash:

```text
policy_hash = sha256(stable_policy_serialization)
```

No volatile timestamps participate. The policy hash is execution authority: if
the policy changes after approval, the old approval becomes invalid and a new
approval cycle is required. A changed policy never silently regenerates a new
due time under an old approval.

## Same-day 11:59 p.m. due-time rule

The due-time derivation is a pure, deterministic helper:

```text
canonical assignment date
+
23:59 local time
+
canonical IANA timezone
=
Canvas-compatible timezone-aware due_at
```

```text
2026-08-24 + America/New_York → 2026-08-24T23:59:00-04:00
2026-01-15 + America/New_York → 2026-01-15T23:59:00-05:00
```

- DST aware (resolved by the `zoneinfo` database, never a hardcoded offset).
- Deterministic (same inputs → same timestamp).
- No wall-clock dependency (never reads the current time).
- Consumes the canonical/runtime timezone rather than embedding a fixed one when
  the architecture already supplies it.
- Unresolved assignment date → raises (blocks due-time generation).
- Canonical blank → no due timestamp.
- Non-assignment artifact → no due timestamp.
- Friday homework stays due Friday at 11:59 p.m. — no "next school day" move.
- The value carries provenance showing it is derived from owner policy.

## Paper-assignment semantics

Homework carries `submission_type = "on_paper"`. The system never infers online
upload, text entry, external tool, or digital submission. It never invents
points, grading type, assignment group, or grade weighting unless authoritative
configuration or canonical evidence supplies them.

> Same-day 11:59 p.m. is intentional Canvas reporting behavior. It does not mean
> the paper must be physically submitted by 11:59 p.m.

The Canvas due date represents the day homework was assigned. The physical
collection happens the following school day; that next-day hand-in convention
does not alter Canvas reporting semantics.

## Publish-state unresolved behavior

Phase 18E does **not** infer publication behavior. There is no implicit
`published = true` or `published = false` as owner policy. Existing Phase 22
writer defaults are implementation details, not authority.

If an operation requires an explicit publication decision and none exists, the
typed state `BLOCKED_PUBLISH_POLICY` is produced and remains visible. A Phase 22
convenience default such as `published=True` can never silently become canonical
policy.

## Policy hash as execution authority

Owner-policy identity participates in every future execution precondition:

```text
packet approved under same-day 11:59 policy
    ↓
owner policy changes
    ↓
old approval rejected (policy:hash_mismatch)
```

A policy change never silently regenerates a new due time under an old approval.

## Approval binding

`evaluate_preconditions` requires:

```text
approval.packet_hash == packet.packet_hash
intent.id ∈ approval.approved_intent_ids
```

and re-validates the recorded approval-time bindings:

```text
canonical_revision, preview_hash, snapshot_hash, policy_hash,
target_environment, config_hash
```

Approval is not transferable and never overrides safety. A valid approval still
blocks when live Canvas changed, ownership changed, the target moved, config
changed, the object belongs to the wrong course, canonical data changed, the
assignment date became unresolved, the publish-state policy is unresolved, a
protected status applies, provenance is lost, a remote teacher edit occurred, or
the operation is no longer valid.

## Execution precondition model

`ExecutionPreconditionReport` is a pure typed model:

```text
packet_hash, intent_id, policy_hash, canonical_revision, preview_hash,
snapshot_hash, approval_identity, target_environment, object_identity,
target_canvas_id, expected_course_id, expected_current_hash, expected_last_updated,
operation, object_type, course,
provenance_valid, ownership_valid, approval_valid, policy_valid, config_valid,
live_state_valid, blockers[], readiness
```

Every boolean gate defaults to `False` (fail closed). `blockers` carries the
reasons; `readiness` is the single authoritative status.

### Readiness states

```text
READY_FOR_EXECUTION_REVIEW   (maximum allowed; never EXECUTED)
NO_CHANGE
BLOCKED_APPROVAL
BLOCKED_STALE_PACKET
BLOCKED_STALE_CANVAS
BLOCKED_CONFIG
BLOCKED_OWNERSHIP
BLOCKED_REMOTE_DRIFT
BLOCKED_UNRESOLVED
BLOCKED_PUBLISH_POLICY
BLOCKED_PROTECTED
BLOCKED_PROVENANCE
BLOCKED_COLLISION
BLOCKED_WRITER_CONTRACT
```

Unknown state → block. Fail closed.

## Read-only snapshot adapter

`snapshot_adapter.py` connects Phase 18D snapshot contracts to the existing
approved read-only Canvas infrastructure via an **injected** connector (the
Phase 22 read-only `CanvasConnector` is never imported at module load):

```text
required DeploymentIntent targets
        ↓
existing Canvas GET/read API
        ↓
Phase 18D CanvasSnapshot
```

- No second HTTP client, no raw `requests`, no account crawl.
- Fetches only the necessary objects.
- No mutation methods.
- Partial fetch, malformed result, or read failure → affected scope blocks.
- No historical fallback.
- Captured payloads are sanitized: credential keys (token, access_token,
  authorization, api_key, secret, password) are stripped before persistence.

## WriterRequest contract

`WriterRequest` is a pure, data-only description of what a future Phase 22
writer call needs:

```text
request_id, packet_hash, intent_id, policy_hash, operation, target_type,
course_id, target_canvas_id, title, body, due_at, submission_type,
assignment_group_id, published, expected_current_hash, expected_last_updated,
provenance
```

No writer import, no execution function, explicit optionality (fields not
relevant to an object type are blank). A request is only generated when an
intent is mutation-eligible, exactly approved, policy-fresh, config-fresh,
ownership-safe, provenance-complete, publish-resolved, and live-state-fresh.
Otherwise zero `WriterRequest`.

## Ownership safeguards

- Unmanaged target → `BLOCKED_OWNERSHIP`.
- System-managed target with changed content vs baseline → `BLOCKED_REMOTE_DRIFT`.
- Teacher-created same-title object → never overwritten.
- Title alone is never proof of ownership; safe identity is `course_id +
  object_type + Canvas object ID + ownership/provenance`.
- UPDATE requires an exact Canvas ID (never targets by title alone); CREATE
  requires the object still absent at freshness check, no collision, no
  ownership ambiguity.

## Protected courses

A protected course yields zero `WriterRequest` even with concrete content, valid
config, valid approval, and an existing Canvas target. Protected status is
authoritative.

## Zero-write guarantee

- Phase 18E import graph loads no writer, connector, mutation transport, or
  `attempt_live_write`.
- Static write-safety scan finds zero mutation paths (`requests.post/put/patch/
  delete`, `urllib.request`, `canvas_writer`, `attempt_live_write`, token usage,
  deploy/apply execution calls).
- Runtime write-safety proves writer invocation = 0, mutation transport
  invocation = 0, and live write-gate execution invocation = 0.
- `DELETE` is rejected explicitly.

## Write-gate status

```text
Write Gate: CLOSED
Maximum readiness: READY_FOR_EXECUTION_REVIEW
```

A fully valid operation may be `READY_FOR_EXECUTION_REVIEW` but never
`EXECUTED`.

## Phase 18F requirements (not implemented here)

A future Phase 18F — Approval-Bound Controlled Canvas Execution Pilot — should:

- consume only Phase 18E validated `WriterRequest`s,
- refresh Canvas immediately before mutation,
- recheck packet hash, policy hash, approval, config, and ownership,
- enforce expected-current-state preconditions,
- route only through the Phase 22 writer/gate,
- limit initial operation/course scope,
- verify results after writes, generate audit evidence, and fail closed on drift.
