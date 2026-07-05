# Persistent Catalog Backup, Rollback, and Removal (Future Requirements)

Last updated: 2026-07-05

M7f defines requirements for a **future** persistent catalog write mission. M7f creates fake examples only.

## Required capabilities (future M7g+)

- backup/export before import
- import batch ID on every write batch
- created records tracked by batch
- remove imported batch without touching real curriculum files
- verify rollback after batch removal
- event log entries for backup, import, and rollback
- no source file operations during catalog import/rollback
- rollback cannot delete real curriculum files
- catalog backup location fixed and reviewed
- backup retention policy documented
- failed import leaves catalog in a known recoverable state

See `assistant/teacher-knowledge-vault/m7f/fake-backup-rollback-plan.json` and `fake-rollback-proof` patterns in M7e for disposable test catalog analogues.
