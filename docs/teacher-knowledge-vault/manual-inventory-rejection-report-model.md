# Teacher Knowledge Vault — Manual Inventory Rejection Report Model

Last updated: 2026-07-04

```text
Status: fake rejection report model — preview only
Fixture: assistant/teacher-knowledge-vault/m7c/fake-rejection-report.json
```

## Purpose

Documents how unsafe or blocked manual inventory fixture rows are rejected during M7c validation. All examples are fictional — no real IDs, URLs, paths, or curriculum text.

## Rejection Categories

| Category | Example rejection reason |
| --- | --- |
| Real-looking Drive ID | `blocked_placeholder_drive_id_pattern` |
| Real-looking Canvas ID | `blocked_placeholder_canvas_id_pattern` |
| Student data risk | `student_data_field_blocked` |
| Private URL | `private_url_blocked` |
| Raw local path | `raw_local_path_blocked` |
| Extracted text field | `extracted_text_field_blocked` |
| `99_DO_NOT_SCAN` | `do_not_scan_blocked_from_normal_mapping` |
| Teacher-only | `teacher_only_restricted_indexable_preview_only` |
| Runtime ingestion action | `runtime_ingestion_action_blocked` |

## Rejection Record Shape

Each rejection includes:

- `rejection_id` — fake preview identifier
- `source_manual_inventory_id` — originating M7b record (fake)
- `rejection_reason` — category code
- `rejection_detail` — sanitized explanation
- `blocked_actions` — actions that remain blocked
- `runtime_imported` — always `false`
- `runtime_connected` — always `false`
- `runtime_ingested` — always `false`

Rejections are not catalog records and do not prove real files exist.
