# Canvas LLM Phase 18D — Canonical Write-Readiness Gate, Dry-Run Deployment Packet & Safety Diff

```text
Status: implementation (read-only pre-execution layer)
Runtime activation: none — zero Canvas writes
Writes: 0 (never POST / PUT / PATCH / DELETE)
Dependency: Phase 18C Teacher Preview (read-only)
```

## Objective

Phase 18D is the final safety boundary between the read-only Teacher Preview
(Phase 18C) and any *future* Canvas write execution.

It transforms a validated Teacher Preview into a deterministic **Dry-Run
Deployment Packet**, compares that intended state against a read-only **live
Canvas snapshot**, computes an exact **Safety Diff**, evaluates all
write-readiness gates, and produces a human-reviewable **approval packet**.

Phase 18D answers only:

> If writes were enabled later, exactly what would the system intend to change,
> why, and is it safe?

It never answers:

> Go change Canvas now.

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
Write-Readiness Evaluation (Phase 18D)
        ↓
Dry-Run Deployment Packet
        ↓
Read-Only Live Canvas Snapshot
        ↓
Safety Diff
        ↓
Approval Packet
        ↓
STOP
```

There is no write execution after the approval packet. `intent generation` and
`execution` are fully separated.

## Package layout

```text
scripts/canvas_llm_phase18d/
    __init__.py      pure re-export of contracts
    contracts.py     pure write-intent contracts (import-safe)
    snapshot.py      CanvasSnapshot model + validation (pure)
    diff.py          deterministic semantic safety diff
    readiness.py     fail-closed packet readiness + approval validation
    deployment.py    assemble_dry_run_packet + build_safety_diff
    cli.py           --selfcheck / --example / --report
```

## Packet model

`DryRunPacket` carries, at minimum:

- `week_code`
- `canonical_plan_identity` / `canonical_revision`
- `preview_identity` / `preview_hash`
- `snapshot_identity` / `snapshot_hash`
- `target_environment`
- `intents[]` (`DeploymentIntent`)
- `blocked[]`
- `warnings[]`
- `no_change[]`
- `provenance`
- `readiness` (typed `PacketReadiness`)
- `packet_hash`

`DeploymentIntent` carries:

- deterministic `id`
- `operation` (`CREATE | UPDATE | NO_CHANGE | BLOCKED | SKIP`)
- `object_type` (`agenda_page | assignment | announcement`)
- `course`, `canonical_source`, `target_locator`
- `desired_state`, `current_state`
- `provenance`, `preconditions`, `blockers`, `risk`, `reason`

No intent contains an execution method.

## Snapshot model

`CanvasSnapshot` holds read-only captured objects (`SnapshotObject`) keyed by
`(course, object_type, locator)`. Each object records `managed` (system-owned
marker) and `baseline_hash` (last system-written content hash) so the layer can
detect remote teacher edits. Snapshot data is supplied by the caller; a future
execution phase may implement capture against the existing read-only connector.

## Safety Diff

`diff.py` compares current vs desired state per field using semantic
normalization (Phase 27 `canonicalize`) so benign whitespace/formatting
differences do not produce meaningless updates, while meaningful instructional
differences are never normalized away. Each intent is classified:

- `NO_CHANGE` — already matches canonical desired state
- `SAFE_CREATE` — absent object, config resolved, no blockers
- `SAFE_UPDATE` — system-managed object, no remote drift, no blockers
- `REVIEW_REQUIRED` — needs human attention
- `BLOCKED` — any blocker present

Risk tiers are `LOW` / `MEDIUM` / `HIGH`.

## Idempotency and duplicate protection

- Intent IDs are deterministic (`sha256` over week + object type + course +
  logical locator).
- `NO_CHANGE` is a first-class result: running the planner against
  already-correct Canvas state yields no update.
- Duplicate/conflicting intents targeting the same logical Canvas object are
  detected and fail closed (`BLOCKED_COLLISION`).

## Ownership and teacher-edit protection

- Config IDs are never guessed. Missing config → `BLOCKED_MISSING_CONFIG`.
- An existing object that is not `managed` → `BLOCKED_OWNERSHIP` (never
  overwrite arbitrary teacher content on title match alone).
- A `managed` object whose `content_hash` differs from `baseline_hash` →
  `BLOCKED_REMOTE_DRIFT`.
- Multiple objects matching one locator → `BLOCKED_COLLISION` (ambiguous target).
- An object belonging to a different course → blocked (wrong course).

## Stale-state protection

The packet is bound to `canonical_revision`, `preview_hash`, and
`snapshot_hash`. `ApprovalRecord` validation rejects a packet when any of these
identities changes, so a future write can never execute against stale plan,
preview, or Canvas state.

## Blockers

| Blocker | Readiness |
| --- | --- |
| unresolved canonical content | `BLOCKED_UNRESOLVED` |
| missing Canvas config | `BLOCKED_MISSING_CONFIG` |
| owner policy unresolved (due time / publish) | `BLOCKED_POLICY` |
| remote teacher edit | `BLOCKED_REMOTE_DRIFT` |
| ownership uncertain / title collision | `BLOCKED_OWNERSHIP` |
| ambiguous / conflicting target | `BLOCKED_COLLISION` |
| protected course | `SKIP` (no writable intent) |
| stale identity | `BLOCKED_STALE` |
| Canvas read failure | `BLOCKED_READ_FAILURE` |

## Due-time behavior

The Canvas assignment due-time convention remains owner-unresolved. Phase 18D
carries this blocker verbatim: assignment intents are `BLOCKED_POLICY` with no
fabricated due time. A due time is only ever emitted when the runtime context
explicitly supplies a resolved value (`due_time_policy == "resolved"` with a
non-empty `resolved_due_time`); the layer never invents or copies one.

## Approval model

`ApprovalRecord` binds an owner approval to an exact `packet_hash` plus
preconditions (`canonical_revision`, `preview_hash`, `snapshot_hash`). It is a
contract only — never executed here. Approval becomes invalid if the packet,
plan, preview, live state, or intent set changes.

## Zero-write boundary

Phase 18D issues no POST / PUT / PATCH / DELETE, uses no tokens, makes no
network calls, and imports no Canvas writer/connector/mutation modules. Static
and runtime tests enforce this.

## Relationship to the existing writer

The existing Phase 22 publisher/writer lineage remains the authoritative future
execution engine. Phase 18D produces pure contracts the existing writer could
consume later; it creates no second writer, publisher, connector, or gate.

## Future write-enabled phase

A later phase may implement execution only when it: requires a matching
`ApprovalRecord`, verifies preconditions (object id / hash / freshness), and
rejects stale packets. That phase is out of scope here.
