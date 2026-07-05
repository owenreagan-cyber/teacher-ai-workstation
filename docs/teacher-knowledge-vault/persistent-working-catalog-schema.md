# Persistent Working Catalog Schema

Last updated: 2026-07-05

M7g extends the M7e disposable test catalog schema with prototype metadata and backup/rollback tracking.

## Tables

| Table | Purpose |
| --- | --- |
| `schema_version` | schema version tracking |
| `catalog_metadata` | prototype catalog identity and policy flags |
| `import_batches` | import batch records |
| `sources` | accepted source inventory candidates |
| `resources` | accepted resource candidates |
| `representations` | accepted representation candidates |
| `source_items` | accepted source item candidates |
| `source_reconciliation` | reconciliation preview records |
| `review_queue_items` | review queue records |
| `event_log` | audit trail |
| `blocked_records` | student-data and `99_DO_NOT_SCAN` blocked records |
| `backup_records` | backup metadata |
| `rollback_records` | rollback metadata (reserved) |

## Required catalog metadata

| Field | M7g value |
| --- | --- |
| `catalog_id` | `fake-m7g-working-catalog-001` |
| `catalog_mode` | `persistent_working_prototype` |
| `production_catalog` | `false` |
| `real_curriculum_allowed` | `false` |
| `student_data_allowed` | `false` |
| `external_sources_allowed` | `false` |
| `created_from_fixture_only` | `true` |
| `source_fixture_reference` | M7b + M7c fixture paths |

## Policy preservation

- `10_TEACHER_ONLY` — `restricted_indexable=1`, `indexable=0`, `discoverable=0`
- `99_DO_NOT_SCAN` — blocked in `blocked_records`, not imported as candidates
- student data fields — blocked in `blocked_records`

## Example fixture

`assistant/teacher-knowledge-vault/m7g/fake-persistent-working-catalog-schema.json`

No migration runtime. No production registry writes.
