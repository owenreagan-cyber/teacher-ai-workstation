# Teacher Knowledge Vault — Manual Source Inventory Review Queue

Last updated: 2026-07-04

```text
Status: review queue states — fake fixtures only
```

## Manual Inventory Review States

| State | Meaning |
| --- | --- |
| `manual_inventory_draft` | Record created, not reviewed |
| `needs_sanitization` | Raw or risky fields detected |
| `needs_source_role` | Source role not assigned |
| `needs_audience_label` | Audience not labeled |
| `needs_indexing_policy` | Indexing policy missing |
| `possible_teacher_only` | Teacher-only risk flagged |
| `possible_student_data_risk` | Student data risk flagged |
| `do_not_scan_blocked` | `99_DO_NOT_SCAN` blocks record |
| `ready_for_fake_catalog_mapping` | Safe for fake catalog mapping |
| `mapped_to_resource_candidate` | Linked to resource candidate |
| `rejected` | Teacher rejected |
| `approved_for_future_import` | Approved for modeling only — not runtime ingestion |

## Rules

- approving a manual inventory record does not scan or ingest files
- approval only means the label/metadata is safe to model in the Vault
- future import into a real catalog remains separate approval

Fixture: `assistant/teacher-knowledge-vault/m7b/fake-manual-review-routing.json`
