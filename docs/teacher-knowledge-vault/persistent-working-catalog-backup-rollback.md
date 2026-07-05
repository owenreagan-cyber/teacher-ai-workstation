# Persistent Working Catalog Backup and Rollback

Last updated: 2026-07-05

## Backup command

```bash
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-backup
```

Script: `scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-backup.sh`

- backs up only the fixed prototype catalog sqlite
- writes backup to `.local/teacher-knowledge-vault/working-catalog/backups/`
- records backup metadata in sqlite and `backup-latest.json`
- does not touch source or curriculum files
- rejects arbitrary path arguments

## Cleanup / rollback command

```bash
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-cleanup
```

Script: `scripts/teacher-knowledge-vault-m7g-persistent-working-catalog-cleanup.sh`

- writes rollback record to `.local/teacher-knowledge-vault/working-catalog-rollback-log.json`
- removes only `.local/teacher-knowledge-vault/working-catalog/`
- `cleanup_removes_only_fixed_path`: true
- `no_source_file_deletion`: true
- `batch_removal_supported`: true
- rejects arbitrary path arguments

## Import-time backup

The import command backs up an existing catalog sqlite before overwrite.

## Example fixture

`assistant/teacher-knowledge-vault/m7g/fake-backup-rollback-proof.json`

No production catalog writes. No source file operations.
