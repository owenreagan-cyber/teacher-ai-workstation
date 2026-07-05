# Teacher Knowledge Vault — Manual Inventory Validator Model

Last updated: 2026-07-04

```text
Status: fixture-only validation model — no runtime ingestion
Scope: committed fake/sanitized M7b fixtures only
```

## Purpose

The M7c fixture validator reads only committed fake/sanitized manual inventory files under fixed repo paths. The validator does not scan folders.

**Policy:** no arbitrary external paths permitted; no arbitrary paths permitted — fixed fixture paths only.

## Fixed Fixture Paths

| Path | Role |
| --- | --- |
| `assistant/teacher-knowledge-vault/m7b/fake-manual-inventory.json` | Primary manual inventory fixture |
| `assistant/teacher-knowledge-vault/m7b/fake-manual-inventory.csv` | CSV mirror (labels only) |
| `assistant/teacher-knowledge-vault/m7c/` | M7c preview/rejection fixtures |

## Validation Checks

| Check | Requirement |
| --- | --- |
| Required fields | `manual_inventory_id`, `source_label`, `runtime_connected`, `runtime_ingested` present per record |
| `runtime_connected` | Must be `false` |
| `runtime_ingested` | Must be `false` |
| OAuth/API/network fields | Must not appear |
| Secrets/tokens | Must not appear |
| Real-looking Drive IDs | Rejected (e.g. 1A2B3C… patterns) |
| Real-looking Canvas IDs | Rejected (numeric course IDs) |
| Raw absolute local paths | Rejected (`/Users/`, `/home/`, `C:\`) |
| Private URLs | Rejected (`http://`, `https://`) |
| Student data fields/values | Rejected |
| Curriculum text / extracted text | Rejected |
| Answer-key/test content | Rejected |
| File content fields | Rejected |
| `10_TEACHER_ONLY` | Restricted-indexable preview only |
| `99_DO_NOT_SCAN` | Blocked/non-indexable/non-discoverable |
| `allowed_next_actions` | Must not include runtime ingestion, scan, content read, connector sync, OCR, AI, rename, move, copy, delete, archive, export, publish |
| API/network/source/file metrics | Must remain zero |

## Validator Script

`scripts/teacher-knowledge-vault-m7c-manual-inventory-fixture-validator.sh` — fixed paths only; no arbitrary path arguments.

## Output

Validation produces PASS/WARN/FAIL summary only. Unsafe rows are documented in `assistant/teacher-knowledge-vault/m7c/fake-rejection-report.json`.
