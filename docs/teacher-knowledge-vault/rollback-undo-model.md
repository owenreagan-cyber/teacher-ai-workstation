# Teacher Knowledge Vault — Rollback and Undo Model

Last updated: 2026-07-04

```text
Status: rollback planning only — M5 fake plans; execution blocked
```

## Rollback Plan Required Fields

| Field | Purpose |
| --- | --- |
| `rollback_plan_id` | Plan identifier |
| `operation_id` | Linked operation |
| `original_source_label` | Pre-operation source |
| `original_path_label` | Pre-operation path |
| `original_display_name` | Pre-operation name |
| `operation_type` | rename/move/archive/etc. |
| `target_path_label` | Post-operation target |
| `target_display_name` | Post-operation name |
| `preflight_conflict_checks` | Checks before rollback |
| `restore_strategy` | How to restore |
| `rollback_risk` | Risk assessment |
| `rollback_event_entries` | Event ids |
| `verification_checks` | Post-rollback verification |
| `manual_recovery_notes` | Teacher recovery guidance |

## Rules

- Rollback plan is **required before execution**
- Rollback does not mean destructive delete
- M5 uses fake rollback plans only (`runtime_executed: false`)
- Future runtime operations remain blocked

Fixture: `assistant/teacher-knowledge-vault/m5/fake-rollback-plans.json`
