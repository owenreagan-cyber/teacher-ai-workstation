# Curriculum Output Contract v0

Local-first, read-only output contract validation for Teacher AI Workstation.

## Files

| File | Role |
| --- | --- |
| `contract-envelope-schema.json` | Shared v0 envelope schema |
| `direct-instruction-slide-deck-schema.json` | Canonical DI slide deck contract schema |
| `teacher-script-contract-schema.json` | Canonical teacher script contract schema |
| `worksheet-contract-schema.json` | Canonical worksheet contract schema |
| `review-game-contract-schema.json` | Canonical review game contract schema |
| `contracts/sample-di-slide-deck-001.json` | Fully validated DI fictional contract |
| `contracts/sample-teacher-script-001.json` | Fully validated teacher script fictional contract |
| `contracts/sample-worksheet-001.json` | Fully validated worksheet fictional contract |
| `contracts/sample-review-game-001.json` | Fully validated review game fictional contract |
| `placeholders/` | Planning-only placeholder contract (Canvas package) |
| `placeholder-manifest.json` | Canonical and placeholder contract index |

## Boundaries

- contract metadata only — no generated lesson content, HTML, PDF, or Canvas packages
- read-only validation — no writes from CLI or automation
- manual/fictional entries only
- registry ID references validated against Registry v0 when present
- no lesson generation, renderers, ingestion, RAG, APIs, or student data

## Validation

```bash
bash scripts/curriculum-output-contract-v0-validator.sh
bin/chief-of-staff --curriculum-output-contract-v0-status
```
