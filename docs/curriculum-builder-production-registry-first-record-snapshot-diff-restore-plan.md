# First Production Record — Snapshot / Diff / Restore Pilot Plan

Last updated: 2026-07-02

```text
Status: planning_only
Classification: audit proof plan for first record — no snapshot tooling active
Baseline: empty shell baseline (records: [])
```

## Purpose

Define how the **future** governed single-record write mission will prove snapshot, diff, and restore correctness. Includes pre-write snapshot of empty shell baseline. No snapshot files or restore commands exist today.

## Pre-Write Snapshot of Empty Shell

| Step | Action |
| ---: | --- |
| 1 | Confirm `production-registry.json` validates as empty shell |
| 2 | Copy canonical empty shell to planned snapshot path (future mission) |
| 3 | Record snapshot ID and timestamp in audit log (future mission) |
| 4 | Validator PASS on snapshot artifact before any mutation |

Planned snapshot naming (from `docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md`):

```text
assistant/curriculum-builder/registry/audit/snapshots/
  production-registry-YYYYMMDDTHHMMSSZ-pre-write.json
```

**Directory not created in this planning mission.**

## Expected Diff Shape

| Field | Before | After |
| --- | --- | --- |
| `records.length` | `0` | `1` |
| New ID | — | exactly one `resource-*` |
| Other records | — | none |

Diff report fields (planning):

- `records_added`: 1
- `records_changed`: 0
- `records_removed`: 0
- `registry_id_changes`: single new `resource-*` ID

## Post-Write Validation

1. Run metadata-boundary validator on new record shape.
2. Run production registry structural validator.
3. Confirm `records.length === 1`.
4. FAIL → execute restore plan immediately.

## Restore to Empty Shell Proof

| Step | Action |
| ---: | --- |
| 1 | Replace `production-registry.json` with pre-write snapshot |
| 2 | Validator PASS on restored empty shell |
| 3 | Diff shows zero net change from baseline |
| 4 | Status commands confirm `records: []` |

## Validation After Restore

- `--curriculum-production-registry-empty-file-status` must PASS
- No orphan `resource-*` files in production directory
- Audit log records rollback reason

## Final State After Successful Pilot (Future Mission)

Depends on future prompt:

- **Option A:** Keep the one approved record (pilot success).
- **Option B:** Restore to empty shell after proof drill (if mission specifies drill-only).

Default planning assumption: **Option A** only when write mission explicitly commits the record.

## Proof Reporting (Future Mission)

Future write mission completion report must include:

| Proof item | Evidence |
| --- | --- |
| Pre-write snapshot path | File path + hash |
| Post-write validator output | PASS lines |
| Diff summary | `0 → 1` record |
| Rollback tested or waived | Owen sign-off |

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md` | General snapshot model |
| `docs/curriculum-builder-production-registry-audit-rollback-preflight.md` | Audit preflight |
| `docs/curriculum-builder-production-registry-metadata-pilot-execution-plan.md` | Pilot protocol |

## Non-Activation

No snapshot tooling implemented. No restore command. `production-registry.json` remains `records: []`.
