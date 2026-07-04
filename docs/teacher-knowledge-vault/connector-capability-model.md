# Teacher Knowledge Vault — Connector Capability Model

Last updated: 2026-07-04

```text
Status: capability schema — fake manifests only
runtime_implemented: false in M7
```

## Common Capability Fields

| Field | Purpose |
| --- | --- |
| `connector_id` | Unique connector identifier |
| `connector_type` | google_drive / ugreen_nas / canvas / etc. |
| `display_name` | Human-readable label |
| `supported_operations` | Planned operation list |
| `read_metadata_supported` | Metadata listing (future) |
| `read_content_supported` | Content read (separate approval) |
| `write_supported` | Write/publish (Level 5 only) |
| `watch_supported` | File watchers (blocked) |
| `hash_supported` | Hashing (future) |
| `pagination_supported` | API pagination notes |
| `rate_limit_notes` | Documented before implementation |
| `cost_notes` | Cost documentation |
| `auth_required` | OAuth/token (blocked in M7) |
| `secrets_required` | Secrets (blocked in M7) |
| `network_required` | Network (blocked in M7) |
| `approval_level_required` | Minimum approval level |
| `blocked_by_default` | true in M7 |
| `runtime_implemented` | Must be `false` in M7 |

## Planned Connector Types

Google Drive, UGREEN NAS, Canvas, iCloud, Local Filesystem, NotebookLM export/planning source, Gemini export/planning source, Dropbox, OneDrive

Fixture: `assistant/teacher-knowledge-vault/m7/fake-connector-capabilities.json`
