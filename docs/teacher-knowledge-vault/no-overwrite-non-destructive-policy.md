# Teacher Knowledge Vault — No-Overwrite and Non-Destructive Policy

Last updated: 2026-07-04

```text
Status: safety policy — enforced in future runtime, documented in M5
```

## Policy

- **no overwrite by default** — target filename conflicts block execution
- **no delete** in early runtime phases
- **archive preferred** over delete
- **copy preferred** before move when uncertain
- **rollback required** before move/rename/archive
- **restore plan required** before execution
- operation cannot proceed if rollback cannot be planned
- teacher-only markers must be preserved in filenames and destinations
- version suffixes must avoid data loss — versions are not overwritten
- event log must preserve old and new labels

Cross-reference: ADR `0007-approved-organization-event-log-rollback.md`
