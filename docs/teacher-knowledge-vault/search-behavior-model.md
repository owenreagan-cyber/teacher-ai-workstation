# Teacher Knowledge Vault — Search Behavior Model

Last updated: 2026-07-04

```text
Status: fake search examples only — no search runtime
search_runtime_executed: false
```

## Search Principles

- Search returns **resources and packages first**, not raw files only
- Results show representations and sources
- Teacher mode may see restricted-indexable teacher-only metadata
- Student-facing mode filters teacher-only/assessment/answer-key leakage
- `99_DO_NOT_SCAN` never appears in any search result
- All M3 search is over fake catalog fixtures only

## Fake Query Examples

| Query | Expected behavior |
| --- | --- |
| `Lesson 21` | Saxon lesson 21 resources/packages |
| `Power Up` | Saxon power-up materials |
| `American Revolution` | CKHG history resources |
| `fractions` | Math student-facing + lesson resources |
| `teacher guide` | Teacher-only metadata — teacher mode |
| `Canvas ready` | Drive+Canvas reconciliation candidates |
| `only in Canvas` | Canvas-only resources |
| `only in Drive` | Drive-only resources |
| `needs review` | Review-queue flagged resources |
| `teacher-only` | Restricted-indexable — student mode excluded |
| `AI generated` | `12_AI_GENERATED` resources |
| `possible duplicates` | Duplicate candidate groups |
| `possible versions` | Version candidate groups |
| `complete package` | Full resource packages |
| `missing from canonical storage` | Reconciliation gaps |

Fixtures: `assistant/teacher-knowledge-vault/m3/fake-search-queries.json`, `fake-search-results-by-mode.json`

Cross-reference: M1 `fake-search-examples.json`, `docs/teacher-knowledge-vault/source-reconciliation-model.md`
