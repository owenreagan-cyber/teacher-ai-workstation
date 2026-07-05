# Teacher Knowledge Vault — M2d First Selected Folder Metadata Scan

Last updated: 2026-07-05

```text
Status: metadata-only scan — fixed Owen-approved tiny local test folder only
Closure: complete_teacher_knowledge_vault_m2d_first_selected_folder_metadata_scan
Approved folder: /Users/owen/Projects/teacher-ai-workstation-local-test/m2d-tiny-folder
Arbitrary path input: no
Content reads: no
M7g catalog import: preview only
Production catalog writes: no
```

## M2d Doctrine

M2d is the **first Owen-selected tiny local metadata-only scan**, limited to one exact Owen-approved test folder. It collects filesystem stat metadata only.

M2d is **not**:

- a general folder scanner
- arbitrary path input
- content reading, parsing, OCR, or AI/RAG
- automatic M7g catalog import
- production catalog writes
- organization runtime

M2d **does**:

- Step 1 preflight on the fixed approved folder only
- Step 2 stat metadata scan on the fixed approved folder only
- no content reads — filesystem stat metadata only
- generate metadata report and proof artifacts under `.local/teacher-knowledge-vault/m2d/`
- produce M7g-compatible import preview (preview only)
- cleanup generated outputs without touching source files

## Approved Folder (exact path only)

`/Users/owen/Projects/teacher-ai-workstation-local-test/m2d-tiny-folder`

Expected files:

- README.md
- fake-notes.txt
- fake-slide-placeholder.pptx
- fake-worksheet.pdf

## Deliverables

| Subsystem | Location |
| --- | --- |
| M2d foundation (this doc) | `docs/teacher-knowledge-vault/m2d-first-selected-folder-metadata-scan.md` |
| Preflight | `docs/teacher-knowledge-vault/selected-folder-metadata-preflight.md` |
| Metadata scan | `docs/teacher-knowledge-vault/selected-folder-metadata-scan.md` |
| M2d governance | `docs/teacher-knowledge-vault/m2d-governance-status.md` |
| M2c approval gate (preserved) | `docs/teacher-knowledge-vault/m2c-selected-local-folder-approval-gate.md` |
| M2d readiness checklist | `docs/teacher-knowledge-vault/m2d-readiness-checklist.md` |
| Generated output | `.local/teacher-knowledge-vault/m2d/` (gitignored) |

## Commands

```bash
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-preflight
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-metadata-scan
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-metadata-preview
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-cleanup
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-status
bash tests/teacher-knowledge-vault-m2d-selected-folder-preflight-test.sh
bash tests/teacher-knowledge-vault-m2d-selected-folder-metadata-scan-test.sh
bash tests/teacher-knowledge-vault-m2d-selected-folder-status-test.sh
```

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| M0–M7g, M2b, M2c | preserved |
| **M2d** First selected folder metadata scan | **complete** (this mission) |
| M2e M7g import from M2d preview | blocked pending explicit approval |
| General folder scanning | blocked |
| Connectors / extraction / organization / production catalog | blocked |

## Non-Activation

PASS on M2d status proves metadata-only scan of the Owen-approved tiny test folder — not permission for arbitrary paths, content reads, or production catalog writes.
