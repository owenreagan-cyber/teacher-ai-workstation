# Repo Staging Metadata Catalog Import

Last updated: 2026-07-05

## Command

```bash
bin/chief-of-staff --teacher-knowledge-vault-m2b-repo-staging-metadata-import
```

Script: `scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-import.sh`

## Behavior

1. Runs metadata discovery on fixed staging fixtures
2. Imports metadata into M7g prototype catalog at `.local/teacher-knowledge-vault/working-catalog/working-catalog.sqlite`
3. Writes `staging_metadata`, `source_items`, `blocked_records`, `event_log`, and `review_queue_items`
4. Preserves `99_DO_NOT_SCAN` as blocked/non-indexable
5. Preserves `10_TEACHER_ONLY` as restricted-indexable
6. Writes import summary to `.local/teacher-knowledge-vault/m2b/import-summary.json`
7. Backs up existing catalog sqlite before write when present

## Import batch

- `fake-m2b-batch-001`
- 7 indexable/restricted metadata records imported
- 1 `99_DO_NOT_SCAN` record blocked

## Blocked

- production catalog/registry writes
- real curriculum files
- content reads
- arbitrary paths

## Cleanup

```bash
bin/chief-of-staff --teacher-knowledge-vault-m2b-repo-staging-metadata-cleanup
```

Removes M2b generated outputs and M2b import batch from M7g prototype catalog only.
