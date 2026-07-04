# Teacher Knowledge Vault — Smart Rename Suggestion Model

Last updated: 2026-07-04

```text
Status: architecture model — suggestions only, never operations
runtime_executed: false
```

## Definition

A smart rename suggestion is a **reviewable recommendation**, not an operation. It proposes canonical identity, filename, and destination for an orphaned or messy source item.

## Required Suggestion Fields

| Field | Purpose |
| --- | --- |
| `current_display_name` | Current placeholder label |
| `current_source_label` | Source system label |
| `current_path_label` | Fake URI path label only |
| `suggested_canonical_filename` | Proposed canonical name |
| `suggested_destination_path` | Proposed taxonomy destination |
| `suggested_resource_identity` | Target resource id/label |
| `suggested_representation_type` | e.g. homework, teacher_guide |
| `suggested_package_id` | Optional package/collection |
| `suggested_audience` | teacher / student / mixed |
| `suggested_indexing_policy` | normal / restricted_indexable / do_not_scan |
| `teacher_only_risk` | elevated when applicable |
| `leakage_risk` | student-facing leakage risk |
| `duplicate_warnings` | Attached duplicate candidate refs |
| `version_warnings` | Attached version candidate refs |
| `evidence_package_id` | Linked evidence |
| `confidence_by_stage` | Per-stage confidence scores |
| `required_review_action` | e.g. manual_review, restricted_review |
| `allowed_next_actions` | approve_later, edit, reject, etc. |
| `blocked_actions` | execute_rename_now, move_now, etc. |
| `runtime_executed` | Must be `false` in M4 |

## Rules

- Suggestions never rename, move, copy, delete, or archive files automatically
- Student-facing mode cannot approve suggestions with teacher-only/assessment risks
- `10_TEACHER_ONLY` suggestions require restricted teacher review
- `99_DO_NOT_SCAN` items never receive rename suggestions

Fixture: `assistant/teacher-knowledge-vault/m4/fake-smart-rename-suggestions.json`
