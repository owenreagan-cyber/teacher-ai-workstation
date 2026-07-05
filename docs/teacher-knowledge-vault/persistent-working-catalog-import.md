# Persistent Working Catalog Import Command

Last updated: 2026-07-05

## Command

```bash
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-import
```

Script: `scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-import.sh`

## Behavior

1. Rejects any command-line path arguments
2. Verifies M7f approval gate preconditions (closure marker, approval packet fixture)
3. Runs M7c fixture validator on fixed M7b/M7c fixtures
4. Backs up existing catalog sqlite if present
5. Imports accepted preview candidates only
6. Stores blocked records separately (`student_data`, `99_DO_NOT_SCAN`)
7. Writes catalog metadata, import batch, event log, review queue
8. Writes import summary and rollback proof JSON

## Fixed fixture inputs

- `assistant/teacher-knowledge-vault/m7b/fake-manual-inventory.json`
- `assistant/teacher-knowledge-vault/m7c/fake-normalized-preview-candidates.json`

## Fixed output

- `.local/teacher-knowledge-vault/working-catalog/working-catalog.sqlite`

## Blocked

- arbitrary file path arguments
- real curriculum files
- external sources
- production registry/catalog writes
- network/API/OAuth

## Validation

```bash
bash tests/teacher-knowledge-vault-m7g-persistent-working-catalog-import-test.sh
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-status
```
