# Teacher Knowledge Vault — Manual Inventory Import Preview Output

Last updated: 2026-07-04

```text
Status: fake import preview output model — dry-run only
Fixture: assistant/teacher-knowledge-vault/m7c/fake-import-preview.json
```

## Purpose

Shows what a **future** manual import might create from validated M7b fixtures. This is not import execution.

## Import Preview Summary Fields

| Field | Description |
| --- | --- |
| `total_fixture_rows` | Rows checked from M7b fixtures |
| `accepted_preview_candidates` | Rows that preview as valid candidates |
| `blocked_records` | Rows rejected or blocked |
| `records_needing_review` | Rows routed to review |
| `student_data_blocks` | Rows blocked for student data risk |
| `secret_token_blocks` | Rows blocked for secrets/tokens |
| `api_network_actions` | Always `0` |
| `runtime_imports` | Always `0` |
| `source_connections` | Always `0` |
| `file_reads` | Always `0` |

## Preview Categories

| Category | Example |
| --- | --- |
| Resource candidates | Valid student-facing file labels |
| Source inventory candidates | Drive/NAS/Canvas source labels |
| Review routed | Teacher-only, sanitization needed, audience label missing |
| Blocked | `99_DO_NOT_SCAN`, student data risk |
| Sanitization needed | Unsafe field patterns detected |
| Teacher-only restricted | `10_TEACHER_ONLY` restricted-indexable preview |
| Reconciliation candidates | Drive-only, Canvas-only, NAS mirror, planning sources |

## Review States

See `assistant/teacher-knowledge-vault/m7c/fake-review-routing.json`:

- `fixture_valid`
- `fixture_rejected`
- `needs_sanitization`
- `needs_audience_label`
- `needs_source_role`
- `teacher_only_restricted_preview`
- `do_not_scan_blocked`
- `ready_for_future_import_approval` — **not** approval to import
- `future_import_blocked_pending_owen_approval`

Future import into SQLite/catalog remains a separate mission requiring explicit Owen approval.
