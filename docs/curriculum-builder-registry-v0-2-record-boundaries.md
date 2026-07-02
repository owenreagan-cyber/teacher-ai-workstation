# Curriculum Builder Registry v0.2 — Record Boundaries

Last updated: 2026-07-02

```text
Status: CB-IMPL-2 fake fixture records only
Production registry writes: no
no_production_write: true
fixture_only: true
Student data: no
Real curriculum content: no
```

## Allowed Now (CB-IMPL-2)

- Committed fake fixture registry JSON under `assistant/curriculum-builder/samples/registry-v0-2-local-records/`
- `example-*` placeholder IDs and `placeholder://` URIs only
- Read-only validation of fixture envelope and records
- Cross-reference checks against A4–A7 field concepts (embedded in fixture)

## Blocked Now

| Category | Blocked |
| --- | --- |
| Production mutation | writes to live `registry.json`, `--write`, hidden write paths |
| Real data | real records, real paths/URLs, Canvas IDs, student data |
| Ingestion | scanning, crawling, OCR, parsing, imports from user folders |
| Generation | lessons, worksheets, presentations, review notes |
| Integration | APIs, OAuth, network, Drive/NAS/iCloud/Canvas live access |

## Fixture vs Live Registry

| Surface | Live v0 registry | v0.2 local fixture |
| --- | --- | --- |
| Path | `assistant/curriculum-builder/registry/v0/registry.json` | `assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json` |
| IDs | `sample-*` | `example-*` |
| Mutation | read-only validator only | fixture-only; no production write |

Fixture validation success does **not** authorize production registry writes.

## Non-Activation

This document does not activate production writes or external integrations.
