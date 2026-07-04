# Teacher Knowledge Vault — Manual Source Inventory Schema

Last updated: 2026-07-04

```text
Status: schema definition — fake/sanitized records only
runtime_connected: false
runtime_ingested: false
```

## Schema Fields

| Field | Purpose |
| --- | --- |
| `manual_inventory_id` | Unique manual record identifier |
| `source_label` | Sanitized source label (placeholder URI) |
| `source_type` | drive / nas / canvas / icloud / manual / staging / planning |
| `source_role` | canonical_storage / mirror_backup / deployment_target / planning_source / staging_source |
| `resource_label` | Fake resource label |
| `representation_label` | Fake representation label |
| `display_name_label` | Sanitized display name |
| `path_label` | Sanitized path label — not raw local path |
| `parent_label` | Sanitized parent folder label |
| `item_type` | file / folder / module / page |
| `extension_label` | pdf / docx / etc. |
| `estimated_size_label` | Approximate size label |
| `modified_date_label` | Sanitized date label |
| `audience` | student_facing / teacher_only / mixed |
| `indexing_policy` | restricted_indexable / student_facing / blocked |
| `teacher_only_risk` | boolean |
| `student_data_risk` | boolean |
| `do_not_scan_flag` | boolean |
| `canonical_storage_candidate` | boolean |
| `canvas_deployment_candidate` | boolean |
| `nas_mirror_candidate` | boolean |
| `needs_review` | boolean |
| `allowed_next_actions` | e.g. map_to_fake_catalog |
| `blocked_next_actions` | e.g. runtime_ingest / connector_sync |
| `runtime_connected` | Must be `false` in M7b |
| `runtime_ingested` | Must be `false` in M7b |

## Rules

- labels are preferred over sensitive raw paths
- IDs must be fake/manual labels, not real Drive IDs or Canvas IDs
- no student data fields are allowed
- no file content fields are allowed
- no extracted text fields are allowed
- no secrets or URLs except sanitized placeholders

Fixtures: `assistant/teacher-knowledge-vault/m7b/fake-manual-inventory.json`, `fake-manual-inventory.csv`
