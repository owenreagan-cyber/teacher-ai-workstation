# Teacher Knowledge Vault — M6 Native Extraction and OCR Approval Packet

Last updated: 2026-07-04

```text
Status: native extraction/OCR approval packet — fake fixtures only
Closure: complete_teacher_knowledge_vault_m6_extraction_ocr_approval_packet
M0–M5: preserved
Runtime extraction/OCR execution: blocked
```

## M6 Doctrine

M6 defines the **future document understanding execution boundary** using fake fixtures only. It shows how native extraction and OCR will support orphan-file naming, smart rename evidence, and classification — without parsing files, running OCR, or calling APIs.

M6 preserves all prior milestones and blocks:

- Real native document extraction (PDF/DOCX/PPTX/XLSX/HTML parsing)
- Real OCR execution or installation (Tesseract, OCRmyPDF, cloud OCR)
- Real file scanning, hashing, or SQLite runtime
- AI/RAG, embeddings, connectors
- `99_DO_NOT_SCAN` absolute exclusion
- `10_TEACHER_ONLY` restricted-indexable extraction

## Document Understanding Escalation Ladder

| Layer | Name | M6 status |
| --- | --- | --- |
| 0 | Source/filesystem metadata | documented |
| 1 | Native document extraction | future only |
| 2 | Local OCR | future only |
| 3 | Rule-based classification | future only |
| 4 | Local AI classification | future only |
| 5 | Cloud AI/API escalation | rare; approval + budget gate |

Native extraction must come before OCR. Local OCR before cloud. Rules before AI. Cloud requires explicit approval and cost gate. Whole-document processing is not default.

Cross-reference: ADR `0008-document-understanding-escalation-ladder.md`

## Deliverables

| Subsystem | Location |
| --- | --- |
| M6 foundation (this doc) | `docs/teacher-knowledge-vault/m6-native-extraction-ocr-approval-packet.md` |
| Native extraction approval | `docs/teacher-knowledge-vault/native-extraction-approval-model.md` |
| OCR escalation approval | `docs/teacher-knowledge-vault/ocr-escalation-approval-model.md` |
| Extraction cache | `docs/teacher-knowledge-vault/extraction-cache-model.md` |
| Extraction evidence package | `docs/teacher-knowledge-vault/extraction-evidence-package.md` |
| Cost/budget gate | `docs/teacher-knowledge-vault/extraction-cost-budget-gate.md` |
| Extraction review queue | `docs/teacher-knowledge-vault/extraction-review-queue-model.md` |
| M6 governance | `docs/teacher-knowledge-vault/m6-governance-status.md` |
| M6 fixtures | `assistant/teacher-knowledge-vault/m6/` |

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| M0–M5 | complete |
| **M6** Extraction/OCR approval packet | **complete** (this mission) |
| M2b / runtime extraction/OCR / search / rename / organization | blocked |
| M7 Drive/NAS/Canvas connectors | blocked |
| M8 AI/RAG | blocked |

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-m6-extraction-ocr-approval-status
bash tests/teacher-knowledge-vault-m6-extraction-ocr-approval-status-test.sh
```

## Non-Activation

PASS on M6 status proves fake documentation and fixtures only — not permission to extract text, run OCR, or call APIs.
