# Selected Local Folder Approval Packet

Last updated: 2026-07-05

Fake approval packet model for future M2d. Example: `assistant/teacher-knowledge-vault/m2c/fake-selected-folder-approval-packet.json`

## Required fields

| Field | M2c example value |
| --- | --- |
| `owen_approval` | `false` |
| `real_folder_scan_executed` | `false` |
| `catalog_import_blocked_until_second_approval` | `true` |
| `requested_folder_path_placeholder` | `/LOCAL_TEST_FOLDER_PLACEHOLDER/OwenSelectedTinyTestFolder` |
| `allowed_decision` | `false` |
| `content_reads_disabled` | `true` |
| `ocr_disabled` | `true` |
| `ai_rag_disabled` | `true` |
| `do_not_scan_policy` | `99_DO_NOT_SCAN must remain blocked and non-indexable` |
| `teacher_only_policy` | `10_TEACHER_ONLY restricted-indexable only` |
| `generated_report_path` | `.local/teacher-knowledge-vault/m2d/selected-folder-metadata-report.json` |
| `rollback_cleanup_plan_required` | `true` |
| `review_valid_until_placeholder` | expiration/review validity period |

## Two-step workflow

1. **Preflight packet** — path safety, scope limits, denial reasons; no catalog import.
2. **Import approval** — only after Owen sets `owen_approval: true` in a separate approved M2d mission.

M2c packets are planning-only. No real path is approved.
