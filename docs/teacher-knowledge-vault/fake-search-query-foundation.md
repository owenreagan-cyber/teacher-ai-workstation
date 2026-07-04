# Teacher Knowledge Vault — Fake Search / Query Foundation (M1)

Last updated: 2026-07-04

```text
Status: fake search examples only — no search runtime
```

## Example Teacher Queries (Fictional)

| Query | Expected behavior (architecture) |
| --- | --- |
| Lesson 21 | Returns resources + representations |
| Power Up | Saxon-related fake resources |
| American Revolution | CKHG history fake resource |
| fractions | Math fake resources |
| teacher guide | Teacher-only representations flagged |
| Canvas ready | Deployment-ready metadata labels |
| only in Canvas | Canvas-only reconciliation flag |
| only in Drive | Drive-only reconciliation flag |
| needs review | Review queue matches |
| teacher-only | Teacher mode — restricted-indexable results |
| AI generated | `12_AI_GENERATED` resources |

## Search Rules (Frozen)

- Search returns **resources**, not raw files only
- Results show representations and sources
- Teacher-only results visible only in **teacher mode**
- Student-facing search filters answer-key/assessment leakage
- `99_DO_NOT_SCAN` **never appears** in any search results

## Fixture

`assistant/teacher-knowledge-vault/m1/fake-search-examples.json`

## M1 Proof

Status script validates fixture presence and policy language — not live search execution.
