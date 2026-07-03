# Production Registry Audit and Rollback Preflight

Last updated: 2026-07-02

```text
Status: audit_rollback_preflight_only
Classification: Phase 2 preflight — no write code, no snapshots
Owen checklist item: 6 — Rollback requirements (approved 2026-07-02)
Implementation: planning/status/test only
```

## Purpose

Phase 2 expansion of audit and rollback requirements for a **future** governed production registry write. Complements `docs/curriculum-builder-production-registry-audit-rollback-planning-stub.md` and `docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md`.

**No audit directory, snapshot tooling, or write code exists today.**

## Governed Write Audit Model (Future)

| Step | Requirement |
| --- | --- |
| 1. Pre-write snapshot | Copy registry target to timestamped audit path before mutation |
| 2. Review gate | `review_state` must be `approved` per § D model |
| 3. Single-record write | One manual record only for first mutation mission |
| 4. Post-write diff | Machine-readable diff of before vs after |
| 5. Post-write validator | Schema/namespace validation PASS |
| 6. Audit log entry | Timestamp, reason, reviewer placeholder — no student data |
| 7. Rollback on failure | Restore snapshot; log rollback reason |
| 8. Manual review | Owen reviews diff before considering mission complete |

## Rollback Procedure (Planning)

1. Identify pre-write snapshot path (see snapshot readiness doc)
2. On validator FAIL or Owen abort: restore snapshot to production path
3. Re-run post-restore validator — must match pre-write state
4. Record rollback in audit log (planning fields only today)
5. Never silently overwrite without snapshot

## Guardrails

| Guardrail | Rule |
| --- | --- |
| No hidden write paths | Only explicit approved mission may mutate |
| No partial writes without snapshot | Snapshot mandatory before first byte changed |
| No batch import in v1 | Single-record only |
| No student data in audit | Absolute prohibition |
| No curriculum content in audit | Metadata labels only when items 3/4 approved |
| Sentinel remains until write mission | `BLOCKED-NO-WRITES.sentinel` |

## Future Audit Path (Placeholder — Not Active)

```text
assistant/curriculum-builder/registry/audit/   # NOT CREATED — future write mission only
```

## Owen Checklist Alignment

| Item | Status | Preflight effect |
| --- | --- | --- |
| 6 Rollback | approved | This doc + readiness model |
| 7 Review states | approved | Gate before write |
| 2 Write behavior | approved in principle | Preflight only — no mutation |

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-audit-rollback-planning-stub.md` | Original stub |
| `docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md` | Snapshot naming and diff format |
| `docs/curriculum-builder-production-registry-phase-2-preflight.md` | Phase 2 closure |

## Non-Activation

No snapshots, audit writes, restore commands, or registry mutation.
