# Persistent Catalog Schema Readiness (Documentation Only)

Last updated: 2026-07-05

M7f documents schema readiness building from M7e. **No migration runtime. No database write.**

## Future persistent catalog tables (minimum)

Future persistent local working catalog schema must include or preserve:

- `sources`
- `resources`
- `representations`
- `source_items`
- `source_reconciliation`
- `review_queue_items`
- `event_log`
- `import_batches`
- `blocked_records`
- `schema_migrations` or `schema_version`
- `catalog_metadata`
- `backup_records`
- `rollback_records`

## Policy preservation

- `99_DO_NOT_SCAN` remains blocked and non-indexable in any future catalog.
- `10_TEACHER_ONLY` remains restricted-indexable only.
- blocked records from M7c/M7e mapping rules carry forward.

See `assistant/teacher-knowledge-vault/m7f/fake-schema-readiness-checklist.json` for fake readiness evidence.
