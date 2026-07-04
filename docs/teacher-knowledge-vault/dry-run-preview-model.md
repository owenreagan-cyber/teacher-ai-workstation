# Teacher Knowledge Vault — Dry-Run Preview Model

Last updated: 2026-07-04

```text
Status: preview model only — preview is not execution
```

## Preview Requirements

Every future organization operation must generate a dry-run preview **before** execution showing:

- current display name and proposed filename
- current source/path label and proposed destination
- operation type
- files/folders affected (labels only)
- duplicate/version warnings
- teacher-only/student-facing warnings
- overwrite risk
- missing destination risk
- cloud placeholder risk
- symlink/path escape risk
- expected event log entries
- rollback availability
- approval required flag

## Rules

- Dry-run preview must be generated before execution
- Preview itself is not execution (`runtime_executed: false`)
- M5 includes fake previews only

Fixture: `assistant/teacher-knowledge-vault/m5/fake-dry-run-previews.json`
