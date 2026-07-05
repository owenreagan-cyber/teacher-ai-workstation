# Teacher Knowledge Vault — Local Test Catalog Import Command

Last updated: 2026-07-04

```text
Status: fixed-path fixture-only import — no arbitrary paths
```

## Command

```bash
bin/chief-of-staff --teacher-knowledge-vault-m7e-local-test-catalog-import
```

Script: `scripts/teacher-knowledge-vault-m7e-local-test-catalog-import.sh`

## Behavior

1. Rejects any command-line path arguments
2. Runs M7c fixture validator on committed M7b inventory
3. Reads only fixed fixture paths:
   - `assistant/teacher-knowledge-vault/m7b/fake-manual-inventory.json`
   - `assistant/teacher-knowledge-vault/m7c/fake-normalized-preview-candidates.json`
4. Imports accepted M7c preview candidates into `.tmp/teacher-knowledge-vault/m7e/test-catalog.sqlite`
5. Records blocked `99_DO_NOT_SCAN` and student-data rows in `blocked_records` (non-indexable)
6. Writes event log and review queue entries
7. Writes deterministic `import-summary.json`
8. Creates backup at `test-catalog-backup.sqlite` before write

## Blocked

- Arbitrary external paths
- Real file reads
- Network/API/OAuth
- Production catalog writes
