# Teacher Knowledge Vault — Local Discovery Output Contract

Last updated: 2026-07-04

```text
Status: architecture contract only — not a scanner implementation
```

## Discovery Output Record (Future)

| Field | Purpose |
| --- | --- |
| `discovery_run_id` | Planned run identifier |
| `source_id` | Catalog source reference |
| `source_type` | e.g. `local_staging` (future) |
| `approved_root_label` | Human-readable approved root |
| `source_item_id` | Catalog source item id |
| `display_name` | Filename label only |
| `path_label` | Fake URI or path label — no real paths in fixtures |
| `parent_path_label` | Parent folder label |
| `extension` | File extension |
| `size_bytes` | Size when metadata-only read approved |
| `created_at_available` | Whether created date is safe to collect |
| `modified_at_available` | Whether modified date is safe to collect |
| `cloud_placeholder_status` | `local`, `placeholder`, `unavailable` |
| `symlink_status` | `none`, `in_root`, `escape_blocked` |
| `blocked_reason` | When discovery must not proceed |
| `indexing_policy` | `normal`, `restricted_indexable`, `do_not_scan` |
| `audience_risk` | Student-facing leakage risk |
| `teacher_only_risk` | Teacher-only content risk |
| `requires_review` | Teacher review required |
| `allowed_next_actions` | e.g. `["review_only"]` — never auto-operate |
| `runtime_executed` | Must be `false` in M2 |

## Mapping to M1 Catalog Entities

| Discovery output | M1 entity |
| --- | --- |
| Dry-run record | `SourceItem` candidate |
| Blocked item | Event log `source_item_blocked` |
| Review candidate | `ReviewQueueItem` |
| Run summary | `GovernanceStatus` / observability metrics |

Fixture schema example: `assistant/teacher-knowledge-vault/m2/fake-discovery-output-contract.json`

Event/review examples: `assistant/teacher-knowledge-vault/m2/fake-event-log-discovery.json`, `fake-review-routing.json`
