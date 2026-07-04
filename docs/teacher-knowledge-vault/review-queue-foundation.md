# Teacher Knowledge Vault — Review Queue Foundation (M1)

Last updated: 2026-07-04

```text
Status: fake review queue fixtures only — no UI/runtime
```

## Review States (M1 Fixtures)

`new_discovery`, `needs_native_extraction`, `needs_ocr`, `needs_classification`, `possible_duplicate`, `possible_version`, `ready_to_organize`, `needs_manual_review`, `approved`, `rejected`, `blocked`, `archived`

## M1 Examples

| Example | State | Notes |
| --- | --- | --- |
| Teacher-only restricted item | `needs_manual_review` | Restricted-indexable — teacher review |
| Student-facing item | `needs_manual_review` | Leakage check required |
| Possible duplicate | `possible_duplicate` | Human merge decision |
| `99_DO_NOT_SCAN` item | `blocked` | Never enters normal review |
| Smart rename suggestion | `ready_to_organize` | `requires_teacher_approval: true` |

## Rule

No suggestion becomes an operation without teacher approval.

## Fixture

`assistant/teacher-knowledge-vault/m1/fake-review-queue.json`
