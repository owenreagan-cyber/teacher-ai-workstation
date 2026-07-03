# Production Registry Snapshot / Diff / Restore Readiness

Last updated: 2026-07-02

```text
Status: planning_readiness_only
Classification: future write-mission prerequisite — no tooling active
Implementation: documentation and negative tests only
```

## Purpose

Define the **future** snapshot, diff, and restore model for governed production registry writes. No snapshot files, diff reports, or restore commands exist today. The **empty shell baseline** (`production-registry.json` with `records: []`) is the restore target before any record mission.

## Empty Shell Baseline

| Field | Value |
| --- | --- |
| Path | `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| `version` | `0.2` |
| `registry_type` | `production` |
| `records` | `[]` |

Future restore proof must restore to this exact empty shell before any governed single-record write mission. Future diff expectations start from `records: []`.

## Future Snapshot File Naming (Planning)

```text
assistant/curriculum-builder/registry/audit/snapshots/
  production-registry-YYYYMMDDTHHMMSSZ-pre-write.json
  production-registry-YYYYMMDDTHHMMSSZ-post-write.json
  production-registry-YYYYMMDDTHHMMSSZ-rollback-restore.json
```

Rules:

- ISO-8601 UTC timestamp in filename
- `pre-write` mandatory before any mutation
- `post-write` captured after successful validator PASS
- `rollback-restore` documents restore target when rollback executed

**Directory not created in Phase 2 preflight.**

## Future Diff Report Format (Planning)

```text
assistant/curriculum-builder/registry/audit/diffs/
  production-registry-YYYYMMDDTHHMMSSZ.diff.json
```

Planned fields:

| Field | Example |
| --- | --- |
| `diff_id` | `diff-20260702T120000Z` |
| `snapshot_before` | path to pre-write snapshot |
| `snapshot_after` | path to post-write snapshot |
| `records_added` | count |
| `records_changed` | count |
| `records_removed` | count |
| `registry_id_changes` | list of `resource-*` IDs affected |
| `validator_pass` | boolean |

Human-readable summary to stdout in future write mission — not implemented today.

## Future Restore Verification (Planning)

After restore:

1. Production path byte-identical to pre-write snapshot OR
2. Validator reports equivalent registry state
3. Diff report shows zero net change from pre-write baseline
4. Status command proves no orphan `resource-*` records

## Rollback Proof Checklist (Future Mission)

| # | Check |
| --- | --- |
| 1 | Pre-write snapshot exists |
| 2 | Write attempted only after `review_state: approved` |
| 3 | Post-write validator run |
| 4 | On FAIL: restore executed |
| 5 | Post-restore validator PASS |
| 6 | Audit log records rollback reason |
| 7 | No student data in any audit artifact |

## Read-Only Checks Today

| Check | Today |
| --- | --- |
| Planning docs exist | yes — this doc + audit preflight |
| `production-registry.json` exists | **yes** — empty shell baseline |
| Snapshot tooling exists | **no** — blocked |
| Restore command exists | **no** — blocked |
| Status proves empty shell | `--curriculum-production-registry-empty-file-status` |

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-empty-file.md` | Empty-file closure |
| `docs/curriculum-builder-production-registry-audit-rollback-preflight.md` | Audit model |
| `docs/curriculum-builder-production-registry-phase-2-preflight.md` | Phase 2 closure |

## Non-Activation

No snapshot of production-registry.json tooling exists yet. No restore from production records (records array is empty). No diff against production records.
