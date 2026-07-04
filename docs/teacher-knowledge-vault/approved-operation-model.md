# Teacher Knowledge Vault — Approved Operation Model

Last updated: 2026-07-04

```text
Status: architecture model — planned operations only
runtime_executed: false in M5
```

## Definition

An approved organization operation is a **planned, reviewed, teacher-approved action** — not an automatic result of a smart rename suggestion.

## Operation Types

rename, copy, move, archive, restore, export, mark_duplicate, mark_version, mark_canonical_representation, no_op, reject_suggestion

## Required Fields

| Field | Purpose |
| --- | --- |
| `operation_id` | Unique operation identifier |
| `operation_type` | One of the types above |
| `source_representation_id` | Catalog representation |
| `source_item_id` | Catalog source item |
| `current_source_label` | Current source |
| `current_path_label` | Fake URI path label |
| `proposed_target_path_label` | Proposed destination |
| `proposed_target_filename` | Proposed canonical name |
| `operation_reason` | Why operation requested |
| `evidence_package_id` | Linked evidence |
| `review_card_id` | Linked M4 review card |
| `teacher_approval_state` | pending / approved / rejected |
| `approval_timestamp` | Placeholder only in M5 |
| `conflict_status` | clear / blocked / manual_review |
| `rollback_plan_id` | Required rollback reference |
| `event_log_chain` | Ordered event ids |
| `runtime_executed` | Must be `false` in M5 |

## Rules

- Smart rename suggestions do not become operations automatically
- Teacher approval is required before any future execution
- Future execution remains blocked until explicit Owen-approved runtime mission

Fixture: `assistant/teacher-knowledge-vault/m5/fake-approved-operations.json`
