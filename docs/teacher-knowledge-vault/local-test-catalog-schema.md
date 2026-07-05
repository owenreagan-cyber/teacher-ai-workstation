# Teacher Knowledge Vault — Local Test Catalog Schema

Last updated: 2026-07-04

```text
Status: minimal SQLite test catalog schema — M7e only
Fixture: assistant/teacher-knowledge-vault/m7e/fake-test-catalog-schema.json
```

## Storage

SQLite at `.tmp/teacher-knowledge-vault/m7e/test-catalog.sqlite` using Python standard-library `sqlite3` only.

## Tables

| Table | Purpose |
| --- | --- |
| `import_batches` | Import batch metadata |
| `sources` | Source inventory records |
| `resources` | Resource identity records |
| `representations` | Representation records |
| `source_items` | Source item labels |
| `source_reconciliation` | Reconciliation previews |
| `review_queue_items` | Review queue entries |
| `event_log` | Audit event log |
| `blocked_records` | DNS/student-data blocked rows (non-indexable) |

## Required Metadata

- `import_batch_id` on all imported rows
- `fixture_source_ref` linking to M7b/M7c fixture IDs
- `restricted_indexable` flag for `10_TEACHER_ONLY`
- `indexable` / `discoverable` flags (`0` for `99_DO_NOT_SCAN`)
- `created_at` deterministic test timestamp
- `runtime_test_catalog_only` always true
- `production_write` always false
