# Teacher Knowledge Vault — Extraction Review Queue Model

Last updated: 2026-07-04

```text
Status: review queue states — fake fixtures only
```

## Extraction/OCR Review States

| State | Meaning |
| --- | --- |
| `extraction_requested` | Teacher or system requested extraction |
| `extraction_blocked` | Phase gate blocks execution |
| `native_extraction_eligible` | File has embedded text; future only |
| `ocr_needed` | Image-only file; OCR candidate |
| `ocr_blocked` | OCR not approved |
| `quick_ocr_candidate` | First-page OCR proposed |
| `full_ocr_approval_required` | Full document needs high-friction approval |
| `low_confidence_extraction` | Routes to manual review |
| `teacher_only_restricted_extraction` | `10_TEACHER_ONLY` restricted-indexable |
| `leakage_review_required` | Student-facing leakage check |
| `extraction_evidence_ready` | Evidence package created (fake) |
| `manual_review_required` | Teacher must review |

## Example Scenarios (Fake)

- orphan file needing native extraction
- orphan scan needing quick OCR
- teacher-only manual requiring restricted extraction
- answer key extraction blocked from student-facing mode
- `99_DO_NOT_SCAN` blocked before extraction
- cloud OCR request blocked by cost gate
- AI classification request blocked until later phase

Fixture: `assistant/teacher-knowledge-vault/m6/fake-review-routing.json`
