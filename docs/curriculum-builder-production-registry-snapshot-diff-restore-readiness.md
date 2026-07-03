# Production Registry Snapshot / Diff / Restore Readiness

Last updated: 2026-07-03

```text
Status: first_record_snapshot_proof_complete
Prior classification: planning_readiness_only (historical)
Classification: audit readiness — manual pre-write snapshot captured; no restore tooling active
Implementation: pre-write snapshot artifact + read-only validators
```

## Purpose

Define the snapshot, diff, and restore model for governed production registry writes. The first governed record mission captured a **pre-write empty shell baseline** snapshot and added exactly one manual metadata record. No automated restore command exists.

**Non-activation:** No restore CLI. No automated diff tooling. Pre-write snapshot is audit proof only — does not authorize write tooling or a second record.

## Baselines

### Pre-Write Empty Shell (Historical Restore Target)

| Field | Value |
| --- | --- |
| Snapshot path | `assistant/curriculum-builder/registry/audit/snapshots/production-registry-20260703T042100Z-pre-write.json` |
| `records` | `[]` |
| Role | Rollback target if Owen directs restore to empty shell |

### Live Production Registry (Current)

| Field | Value |
| --- | --- |
| Path | `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| `records` count | exactly **1** |
| Approved ID | `resource-math-lesson-108-presentation` |

Rollback to empty shell uses the pre-write snapshot or `git revert`. Future second-record missions should capture a new pre-write snapshot with `records` count `1`.

## Snapshot File Naming

```text
assistant/curriculum-builder/registry/audit/snapshots/
  production-registry-YYYYMMDDTHHMMSSZ-pre-write.json
  production-registry-YYYYMMDDTHHMMSSZ-post-write.json
  production-registry-YYYYMMDDTHHMMSSZ-rollback-restore.json
```

Rules:

- ISO-8601 UTC timestamp in filename
- `pre-write` mandatory before any mutation
- `post-write` optional audit artifact after validator PASS
- `rollback-restore` documents restore target when rollback executed

## Diff Expectations

First-record mission observed diff:

```text
records.length: 0 → 1
single new resource-* ID: resource-math-lesson-108-presentation
```

## Validation After Write

1. `scripts/curriculum-builder-production-registry-first-record-validate.sh` PASS
2. `--curriculum-production-registry-first-record-status` PASS
3. `BLOCKED-NO-WRITES.sentinel` remains intact

## Validation After Restore to Empty Shell

1. `scripts/curriculum-builder-production-registry-empty-file-validate.sh` PASS on restored file
2. `--curriculum-production-registry-empty-file-status` PASS (historical)
3. No orphan `resource-*` files in production directory

## Non-Activation

No restore CLI. No automated diff tooling. Does not authorize a second record or write tooling.
