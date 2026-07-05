# Persistent Catalog Integrity and Recovery Model (Future)

Last updated: 2026-07-05

Documentation only. No integrity runtime in M7f.

## Future integrity requirements

- schema version check on open
- integrity check before/after import batches
- backup restore plan with fake drill evidence
- failed migration handling (no partial unknown state)
- partial import recovery with batch rollback
- duplicate batch detection
- catalog lock/concurrency notes — no concurrent write loops
- dashboard/validate-all remain read-only; they must not write persistent catalog
- status checks read-only by default

See `assistant/teacher-knowledge-vault/m7f/fake-integrity-recovery-plan.json`.
