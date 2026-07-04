# Teacher Knowledge Vault — OCR Escalation Approval Model

Last updated: 2026-07-04

```text
Status: OCR escalation policy — future only; OCR blocked in M6
runtime_executed: false in M6
```

## OCR Levels (Future Only)

| Level | Scope | Approval |
| --- | --- | --- |
| OCR blocked | default | — |
| Quick OCR | first page only | teacher approval |
| Standard OCR | first 3 pages | teacher approval |
| Full OCR | entire document | high-friction approval only |
| Cloud OCR/API | per-run estimate | rare; explicit approval + budget gate |

## Rules

- local OCR is preferred before cloud/API
- no background bulk OCR
- no OCR on `99_DO_NOT_SCAN`
- teacher-only OCR is restricted-indexable only
- student-facing use requires leakage checks
- low-confidence OCR routes to manual review
- OCR must be cached by fingerprint/hash where available
- OCR runtime remains blocked in M6

Fixture: `assistant/teacher-knowledge-vault/m6/fake-ocr-escalation-candidates.json`
