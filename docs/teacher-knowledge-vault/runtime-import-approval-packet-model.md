# Teacher Knowledge Vault — Runtime Import Approval Packet Model

Last updated: 2026-07-04

```text
Status: fake approval packet model — gate evidence only
Fixture: assistant/teacher-knowledge-vault/m7d/fake-import-approval-packet.json
```

## Approval Packet Fields

| Field | Description |
| --- | --- |
| `approval_packet_id` | Fake packet identifier |
| `source_preview_run_id` | M7c import preview run reference |
| `fixture_validator_result` | M7c validator PASS/FAIL summary |
| `import_preview_result` | M7c preview summary counts |
| `accepted_candidate_count` | Preview candidates accepted |
| `blocked_record_count` | Records blocked |
| `needs_review_count` | Records needing review |
| `teacher_only_restricted_count` | Teacher-only restricted previews |
| `do_not_scan_blocked_count` | DNS-blocked records |
| `student_data_block_count` | Student-data blocks |
| `target_catalog_label` | Fake local-first catalog label only |
| `backup_required` | Whether backup required before write |
| `rollback_plan_required` | Whether rollback plan required |
| `event_log_required` | Whether event log plan required |
| `allowed_actions` | Gate-allowed planning actions only |
| `blocked_actions` | Runtime import, catalog write, etc. |
| `approval_state` | Gate review state |
| `runtime_import_executed` | Always `false` in M7d |

Approval packets are planning evidence — not permission to write.
