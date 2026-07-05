# Persistent Working Catalog Storage Policy

Last updated: 2026-07-05

M7g implements a **fixed generated path** for the persistent local working catalog prototype.

## Fixed paths

| Purpose | Path |
| --- | --- |
| Catalog root | `.local/teacher-knowledge-vault/working-catalog/` |
| Database | `.local/teacher-knowledge-vault/working-catalog/working-catalog.sqlite` |
| Backups | `.local/teacher-knowledge-vault/working-catalog/backups/` |
| Import summary | `.local/teacher-knowledge-vault/working-catalog/import-summary.json` |
| Rollback proof | `.local/teacher-knowledge-vault/working-catalog/rollback-proof.json` |
| Backup metadata | `.local/teacher-knowledge-vault/working-catalog/backup-latest.json` |
| Rollback log (on cleanup) | `.local/teacher-knowledge-vault/working-catalog-rollback-log.json` |

All paths are gitignored. Scripts accept **no arbitrary user input** for paths.

## Separation

| Catalog | Path | Role |
| --- | --- | --- |
| M7e disposable test | `.tmp/teacher-knowledge-vault/m7e/` | disposable proof |
| M7g working prototype | `.local/teacher-knowledge-vault/working-catalog/` | persistent prototype |
| Production/canonical | not created | blocked |

## Rules

- clearly non-production naming
- not a curriculum folder
- not under Google Drive, iCloud, NAS, or Canvas paths
- not `~/TeacherAI-Curriculum-Library/`
- backup/export before overwrite when catalog already exists
- cleanup/rollback touches only the fixed M7g generated path

## Lifecycle

1. **Import** — creates or replaces catalog from fixed fixtures; backs up existing sqlite first
2. **Backup** — copies sqlite to `backups/` with backup metadata
3. **Cleanup** — writes rollback record and removes fixed generated path

No source file operations. No external path access.
