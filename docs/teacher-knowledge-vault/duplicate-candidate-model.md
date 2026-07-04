# Teacher Knowledge Vault — Duplicate Candidate Model

Last updated: 2026-07-04

```text
Status: architecture model — M3 fake fixtures only
Auto-merge: never
```

## Duplicate Candidate Levels

| Level | Signal | M3 status |
| --- | --- | --- |
| 1. Exact duplicate | Binary hash match | future only — fake fingerprint placeholders |
| 2. Filename duplicate | Normalized filename similarity | fake fixtures |
| 3. Metadata duplicate | Size/type/source/path-label similarity | fake fixtures |
| 4. Text duplicate | Native extraction or OCR text similarity | future only |
| 5. Semantic duplicate | Embeddings/AI similarity | future only — approval-gated |

## Rules

- M3 models levels with fake fingerprints only — no real hashing
- Duplicate candidates are never merged automatically (`auto_merge: false`)
- All duplicates route to review queue
- Teacher approval required before merge/archive/rename/copy/move
- Teacher-only and student-facing representations must not collapse without audience checks
- `99_DO_NOT_SCAN` items never become duplicate candidates — not discovered or indexed

Fixture: `assistant/teacher-knowledge-vault/m3/fake-duplicate-candidates.json`

Cross-reference: `docs/teacher-knowledge-vault/fingerprinting-model.md`, M1 `fake-relationships.json`
