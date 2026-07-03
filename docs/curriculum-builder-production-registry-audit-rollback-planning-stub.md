# Production Registry Audit and Rollback Planning Stub

Last updated: 2026-07-02

```text
Status: planning_stub_only
Classification: future write-mission prerequisite — no write code
Owen checklist item: 6 — Rollback requirements (approved 2026-07-02)
Implementation: blocked until Owen accepts procedure
```

## Purpose

Planning stub for audit and rollback requirements before any future production registry write mission. Mirrors planning brief § E. **No audit directory, snapshot tooling, or write code exists today.**

## Required Before Any Future Write (Planning)

| Requirement | Description |
| --- | --- |
| Before/after diff | Machine-readable diff of registry file(s) before and after write |
| Timestamp | ISO-8601 write timestamp in audit log |
| Commit reference | Git commit or local audit file reference when applicable |
| Reviewer identity | Placeholder only (e.g. `reviewer: owen`) — no student identifiers |
| Reason for change | Short human-entered reason string |
| Rollback procedure | Restore from backup copy or git revert; steps documented before first write |
| Student data | **Prohibited** in audit entries |
| Curriculum content | **Prohibited** — metadata only |

## Rollback Procedure (Planning)

1. Capture pre-write registry snapshot to local audit path (location TBD at implementation)
2. Perform governed write (future mission only)
3. Run post-write validator
4. On failure: restore snapshot; log rollback reason
5. Never silently overwrite without snapshot

## Future Audit Path (Placeholder — Not Created)

```text
assistant/curriculum-builder/registry/audit/   # NOT ACTIVE — do not create writes here without mission
```

Governance foundation does **not** create active audit storage or snapshot jobs.

## Owen Decision

Owen must accept rollback requirements in checklist item 6 before write missions. This stub documents expectations only.

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-workflow-planning-brief.md` | § E source |
| `docs/curriculum-builder-production-registry-audit-rollback-preflight.md` | Phase 2 audit preflight expansion |
| `docs/curriculum-builder-production-registry-snapshot-diff-restore-readiness.md` | Snapshot/diff/restore readiness |

## Non-Activation

No snapshots, audit writes, or registry mutation.
