# Teacher Knowledge Vault — M7c Manual Inventory Validator and Import Preview

Last updated: 2026-07-04

```text
Status: fixture-only validator and import preview — fake/sanitized fixtures only
Closure: complete_teacher_knowledge_vault_m7c_manual_inventory_import_preview
M0–M7b: preserved
Connector runtime: blocked
OAuth/API/network/scanning/file-read/catalog-write: blocked
```

## M7c Doctrine

M7c validates **committed fake/sanitized manual inventory fixtures** from M7b and produces **preview-only** outputs showing what a future import might create — without OAuth, APIs, network access, source scanning, file reads, SQLite writes, or catalog import.

**Import preview does not mean import.** It is a dry-run model showing what would be created later if Owen approves a separate runtime import mission.

M7c preserves all prior milestones:

- M0 architecture freeze
- M1 fake catalog model
- M2 discovery approval boundaries
- M3 duplicate/search/package model
- M4 smart rename suggestion model
- M5 organization/rollback model
- M6 extraction/OCR approval model
- M7 connector approval model
- M7b manual inventory Level 1 model
- Resource → Representation → Source identity
- connector SDK boundaries
- event log requirements
- review queue requirements
- teacher-only restricted-indexing policy
- `99_DO_NOT_SCAN` absolute exclusion

M7c blocks:

- Real connector implementation
- OAuth, secrets, API/network calls
- Real source listing or metadata ingestion
- File content reads and extracted text
- Real catalog import/write
- Runtime ingestion, scan, OCR, AI, rename, move, copy, delete

## Deliverables

| Subsystem | Location |
| --- | --- |
| M7c foundation (this doc) | `docs/teacher-knowledge-vault/m7c-manual-inventory-import-preview.md` |
| Validator model | `docs/teacher-knowledge-vault/manual-inventory-validator-model.md` |
| Rejection report model | `docs/teacher-knowledge-vault/manual-inventory-rejection-report-model.md` |
| Normalized preview model | `docs/teacher-knowledge-vault/manual-inventory-normalized-preview-model.md` |
| Import preview output model | `docs/teacher-knowledge-vault/manual-inventory-import-preview-output.md` |
| M7c governance | `docs/teacher-knowledge-vault/m7c-governance-status.md` |
| M7c fixtures | `assistant/teacher-knowledge-vault/m7c/` |
| Fixture validator | `scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh` |

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| M0–M7b | complete |
| **M7c** Manual inventory validator and import preview | complete |
| **M7d** Runtime manual import approval gate | complete |
| M7e runtime manual import into local test catalog | blocked |
| M2b / Drive/NAS/Canvas connector implementation | blocked |
| Runtime extraction/OCR / organization | blocked |
| M8 AI/RAG | blocked |

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-m7c-manual-inventory-import-preview-status
bash tests/teacher-knowledge-vault-m7c-manual-inventory-import-preview-status-test.sh
bin/chief-of-staff --teacher-knowledge-vault-m7c-manual-inventory-fixture-validator
```

## Non-Activation

PASS on M7c status proves fake/sanitized documentation, fixtures, and preview models only — not permission to connect sources, ingest metadata, read files, or write catalog records.
