# First Production Record — Snapshot / Diff / Restore Pilot Plan

Last updated: 2026-07-03

```text
Status: first_record_audit_complete
Classification: audit proof for first governed record — read-only validation only
Baseline: empty shell baseline (records: [])
Live state: one approved record (records count exactly 1)
```

## Purpose

Document snapshot, diff, and restore proof for the **completed** first governed single-record write. Pre-write snapshot captured; live registry holds exactly one approved record. No restore command or automated snapshot tooling is active.

## Pre-Write Snapshot of Empty Shell (Captured)

pre-write snapshot of empty shell baseline captured before first governed record write.

| Field | Value |
| --- | --- |
| Path | `assistant/curriculum-builder/registry/audit/snapshots/production-registry-20260703T042100Z-pre-write.json` |
| `records` count | `0` |
| Validator | `scripts/curriculum-builder-production-registry-empty-file-validate.sh` |

## Post-Write Live State

| Field | Value |
| --- | --- |
| Path | `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| `records` count | `1` |
| Approved ID | `resource-math-lesson-108-presentation` |
| Validator | `scripts/curriculum-builder-production-registry-first-record-validate.sh` |

## Observed Diff Shape

| Field | Before (snapshot) | After (live) |
| --- | --- | --- |
| `records.length` | `0` | `1` |
| New ID | — | `resource-math-lesson-108-presentation` |
| Other records | — | none |

## Restore Plan (If Validation Fails)

| Step | Action |
| ---: | --- |
| 1 | Replace `production-registry.json` with pre-write snapshot **or** `git revert` merge commit |
| 2 | Run empty-shell validator on restored file |
| 3 | Run `--curriculum-production-registry-empty-file-status` (historical) and confirm snapshot coherence |
| 4 | Document rollback reason in audit notes (manual) |

**Validation after restore to empty shell:**

- `--curriculum-production-registry-empty-file-status` must PASS (historical milestone)
- `--curriculum-production-registry-first-record-status` must FAIL until a new governed write restores the record

**Validation after restore is not required** while live registry validates as one approved record.

## Rollback to Empty Shell vs Keep Record

| Option | When |
| --- | --- |
| Keep one approved record | Default after successful first-record mission (current state) |
| Restore empty shell | Validation failure, Owen-directed rollback, or explicit drill mission |

## Proof Reporting (Completed Mission)

| Proof item | Evidence |
| --- | --- |
| Pre-write snapshot path | `production-registry-20260703T042100Z-pre-write.json` |
| Post-write validator | `--curriculum-production-registry-first-record-status` PASS |
| Diff summary | `0 → 1` record |
| Sentinel | intact — automated writes still blocked |

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md` | General snapshot model |
| `docs/curriculum-builder-production-registry-sentinel-semantics.md` | Sentinel choice A |
| `docs/curriculum-builder-production-registry-first-record.md` | First record closure |

## Non-Activation

No restore command implemented. No automated snapshot tooling. Sentinel remains intact.
