# Teacher Knowledge Vault — Runtime Import Rollback / Removal Plan

Last updated: 2026-07-04

```text
Status: future rollback requirements — fake plans only in M7d
Fixture: assistant/teacher-knowledge-vault/m7d/fake-rollback-removal-plan.json
```

## Future Rollback Requirements

Before any future runtime manual import write:

| Requirement | Description |
| --- | --- |
| Catalog backup | Export or snapshot of catalog state before import |
| Import batch ID | Unique batch identifier for imported records |
| Records by batch | Track all records created in the batch |
| Batch removal | Ability to remove imported batch without source file ops |
| Event log | Import and rollback events logged |
| Post-rollback verification | Counts and integrity check after removal |
| No source file deletion | Rollback removes catalog records only |
| Teacher-only preserved | Restricted-indexing flags preserved after rollback |
| Gate blocker | Import cannot proceed if rollback/removal unavailable |

M7d creates fake rollback/removal plan examples only. No catalog writes occur.
