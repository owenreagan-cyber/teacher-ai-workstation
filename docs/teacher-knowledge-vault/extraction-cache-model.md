# Teacher Knowledge Vault — Extraction Cache Model

Last updated: 2026-07-04

```text
Status: cache planning model — fake records only; no real text stored
runtime_executed: false in M6
```

## Cache Record Fields

| Field | Purpose |
| --- | --- |
| `cache_id` | Unique cache identifier |
| `source_item_id` | Linked catalog source item |
| `representation_id` | Linked representation |
| `fingerprint_reference` | Placeholder hash reference |
| `extraction_method` | native / local_ocr / cloud_ocr |
| `extraction_scope` | metadata / first_page / selected_pages |
| `page_range` | e.g. `1` or `1-3` |
| `text_snippet_label` | Placeholder label only — not real extracted text |
| `confidence` | 0.0–1.0 |
| `invalidation_reason` | file_changed / policy_change |
| `restricted_indexing_policy` | teacher_only / student_facing |
| `student_visible` | false for teacher-only |
| `teacher_only_risk` | boolean |
| `leakage_risk` | boolean |
| `api_cost_estimate_usd` | Must be 0.00 in M6 |
| `runtime_executed` | Must be `false` in M6 |

## Rules

- cache prevents repeated OCR/API spend
- unchanged files should not be reprocessed
- cache does not store real text in M6 fixtures
- teacher-only cache is restricted
- `99_DO_NOT_SCAN` never has cache records

Fixture: `assistant/teacher-knowledge-vault/m6/fake-extraction-cache-records.json`
