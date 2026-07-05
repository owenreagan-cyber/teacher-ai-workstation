# Teacher Knowledge Vault — M7g Persistent Local Working Catalog Prototype

Last updated: 2026-07-05

```text
Status: bounded runtime write — persistent local working catalog prototype only
Closure: complete_teacher_knowledge_vault_m7g_persistent_working_catalog_prototype
M0–M7f: preserved
Production catalog writes: blocked
Real curriculum indexing: blocked
```

## M7g Doctrine

M7g is the **first persistent local working catalog prototype**, limited to committed fake/sanitized M7b/M7c fixtures only, written to a fixed gitignored generated path.

M7g is **not**:

- a production catalog
- canonical curriculum storage
- real folder reading or scanning
- real curriculum indexing
- Drive/NAS/Canvas/iCloud access
- authorization for M2b, connectors, extraction/OCR, AI/RAG, or organization runtime

M7g **does**:

- build on M7e disposable test catalog proof and M7f approval gate
- import accepted preview candidates from fixed fixtures only
- persist catalog state under `.local/teacher-knowledge-vault/working-catalog/`
- backup before overwrite when catalog already exists
- `10_TEACHER_ONLY` preserved as restricted-indexable
- `99_DO_NOT_SCAN` preserved as blocked/non-indexable
- support rollback/removal of the fixed generated path only

## Deliverables

| Subsystem | Location |
| --- | --- |
| M7g foundation (this doc) | `docs/teacher-knowledge-vault/m7g-persistent-working-catalog-prototype.md` |
| Storage policy | `docs/teacher-knowledge-vault/persistent-working-catalog-storage.md` |
| Schema | `docs/teacher-knowledge-vault/persistent-working-catalog-schema.md` |
| Import command | `docs/teacher-knowledge-vault/persistent-working-catalog-import.md` |
| Backup/rollback/cleanup | `docs/teacher-knowledge-vault/persistent-working-catalog-backup-rollback.md` |
| M7g governance | `docs/teacher-knowledge-vault/m7g-governance-status.md` |
| M7g fixtures | `assistant/teacher-knowledge-vault/m7g/` |
| Generated output | `.local/teacher-knowledge-vault/working-catalog/` (gitignored) |

## Commands

```bash
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-import
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-backup
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-cleanup
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-status
bash tests/teacher-knowledge-vault-m7g-persistent-working-catalog-import-test.sh
bash tests/teacher-knowledge-vault-m7g-persistent-working-catalog-status-test.sh
```

## Catalog Comparison

| Catalog | Path | Persistence | Purpose |
| --- | --- | --- | --- |
| M7e disposable test catalog | `.tmp/teacher-knowledge-vault/m7e/` | disposable | prove bounded import from fixtures |
| **M7g working prototype** | `.local/teacher-knowledge-vault/working-catalog/` | persistent prototype | local working catalog from fixtures only |
| Future production/canonical | not created | blocked | requires separate Owen approval |

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| M0–M7f | complete |
| **M7g** Persistent local working catalog prototype | **complete** (this mission) |
| M2b selected local staging folder prototype | blocked |
| Drive/NAS/Canvas connector runtime | blocked |
| Extraction/OCR runtime | blocked |
| AI/RAG | blocked |
| Organization runtime | blocked |
| Production/canonical catalog | blocked |

## Non-Activation

PASS on M7g status proves bounded prototype catalog writes from fixtures only — not permission for production import, real curriculum access, connectors, or organization.

## Explicit Approval Required For

- **M2b** — selected local staging folder metadata-only prototype
- **Connectors** — Drive/NAS/Canvas runtime
- **Extraction/OCR** — native extraction execution
- **AI/RAG** — embeddings, local models
- **Organization** — rename/move/copy/delete/archive
- **Production catalog** — canonical curriculum storage
