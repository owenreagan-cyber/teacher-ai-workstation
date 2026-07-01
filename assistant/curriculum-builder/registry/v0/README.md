# Curriculum Registry v0 (Manual Metadata)

Local-first, read-only, manual metadata registry for Teacher AI Workstation.

## Files

| File | Role |
| --- | --- |
| `registry-schema.json` | v0 record schema definition (metadata only) |
| `registry.json` | Canonical v0 registry store (seven fictional placeholder records) |

## Boundaries

- metadata only — no curriculum file contents
- read-only operation — no writes from CLI or automation
- manual entries only — `created_by_manual_entry` must be true
- no scanning, ingestion, APIs, OAuth, or network resolution
- no student data — fictional placeholder titles and references only

## Validation

```bash
bash scripts/curriculum-registry-v0-validator.sh
bin/chief-of-staff --curriculum-registry-v0-status
```
