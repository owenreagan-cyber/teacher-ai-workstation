# Teacher Knowledge Vault — Source Inventory Model

Last updated: 2026-07-04

```text
Status: source inventory schema — fake records only
runtime_connected: false in M7
```

## Source Inventory Fields

| Field | Purpose |
| --- | --- |
| `source_id` | Unique source identifier |
| `source_type` | drive / nas / canvas / manual / etc. |
| `source_label` | Display label |
| `canonical_role` | canonical_storage / mirror_backup / deployment_target / planning_source / local_cache / staging_source |
| `connection_status` | disconnected / manual_only / blocked |
| `approval_level` | Required connector level |
| `auth_status` | not_configured / blocked |
| `allowed_scopes` | Permitted future scopes |
| `blocked_scopes` | content_read / write / scan_root / student_data |
| `student_data_risk` | boolean |
| `teacher_only_risk` | boolean |
| `content_read_allowed` | false in M7 |
| `write_allowed` | false in M7 |
| `runtime_connected` | Must be `false` in M7 |

## Source Roles

- **Google Drive** = primary canonical library target
- **UGREEN NAS** = mirror/backup/fast local access target
- **Canvas** = publishing/deployment target and reconciliation source
- **iCloud** = secondary/personal/legacy source, future only
- **NotebookLM/Gemini** = planning/export sources, not canonical storage
- **local staging/cache** = optional workshop staging, not canonical storage

Fixture: `assistant/teacher-knowledge-vault/m7/fake-source-inventory.json`
