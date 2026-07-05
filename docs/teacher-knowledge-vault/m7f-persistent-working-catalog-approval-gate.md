# Teacher Knowledge Vault — M7f Persistent Local Working Catalog Approval Gate

Last updated: 2026-07-05

```text
Status: approval gate only — no persistent catalog implementation
Closure: complete_teacher_knowledge_vault_m7f_persistent_working_catalog_approval_gate
M0–M7e: preserved
Persistent catalog writes: blocked
Production catalog writes: blocked
Real source ingestion: blocked
OAuth/API/network/scanning/file-read: blocked
```

## M7f Doctrine

M7f is an **approval gate only**. It defines the explicit safety, storage, backup, rollback, lifecycle, validation, and approval requirements before any **future** persistent local working catalog may be created or written.

M7e proved a bounded runtime write into a **disposable** local SQLite test catalog using committed fake/sanitized fixtures only. M7f does not create a persistent catalog, persistent SQLite file, or production catalog.

M7f clarifies:

- M7e test catalog is disposable and gitignored under `.tmp/teacher-knowledge-vault/m7e/`.
- M7f documents requirements; it does not implement a persistent catalog.
- Future persistent catalog creation requires a separate Owen-approved runtime mission (e.g. M7g).
- Persistent catalog must remain local-first and must not imply production/canonical storage.
- Google Drive/NAS remain canonical/mirror storage targets **later** — not touched in M7f.
- Canvas remains deployment/reconciliation target **later** — not touched in M7f.

M7f preserves M0–M7e, validation-tier smoke/deep boundaries from PR #268, teacher-only restricted-indexing policy, and `99_DO_NOT_SCAN` absolute exclusion.

## Deliverables

| Subsystem | Location |
| --- | --- |
| M7f foundation (this doc) | `docs/teacher-knowledge-vault/m7f-persistent-working-catalog-approval-gate.md` |
| Approval levels | `docs/teacher-knowledge-vault/persistent-catalog-approval-levels.md` |
| Storage policy | `docs/teacher-knowledge-vault/persistent-catalog-storage-policy.md` |
| Schema readiness | `docs/teacher-knowledge-vault/persistent-catalog-schema-readiness.md` |
| Import preconditions | `docs/teacher-knowledge-vault/persistent-catalog-import-preconditions.md` |
| Backup/rollback/removal | `docs/teacher-knowledge-vault/persistent-catalog-backup-rollback-removal.md` |
| Integrity/recovery | `docs/teacher-knowledge-vault/persistent-catalog-integrity-recovery.md` |
| M7f governance | `docs/teacher-knowledge-vault/m7f-governance-status.md` |
| M7f fixtures | `assistant/teacher-knowledge-vault/m7f/` |

## Commands

```bash
bin/chief-of-staff --teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status
bash tests/teacher-knowledge-vault-m7f-persistent-working-catalog-approval-gate-status-test.sh
```

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| M0–M7e | complete |
| **M7f** Persistent local working catalog approval gate | **complete** (this mission) |
| M7g persistent local working catalog runtime | blocked |
| M2b / connectors / extraction / organization | blocked |

## Non-Activation

PASS on M7f status proves approval-gate documentation and fake fixtures only — not permission to create or write a persistent local working catalog.
