# Teacher Knowledge Vault — Runtime Manual Import Preconditions

Last updated: 2026-07-04

```text
Status: future runtime import preconditions — not active import
Fixture: assistant/teacher-knowledge-vault/m7d/fake-import-preconditions-checklist.json
```

## Preconditions (Future Runtime Import)

Future runtime manual import must satisfy all of the following before any catalog write:

| # | Precondition |
| --- | --- |
| 1 | Owen explicitly approves the runtime import mission |
| 2 | Input path is fixed or selected through an approved UI/CLI path |
| 3 | Input is sanitized (fake/sanitized labels only in current repo phase) |
| 4 | M7c fixture validator passes |
| 5 | No student data present |
| 6 | No secrets/tokens/real IDs/private URLs present |
| 7 | No content/extracted text fields present |
| 8 | `99_DO_NOT_SCAN` records are blocked from normal import |
| 9 | `10_TEACHER_ONLY` records remain restricted-indexable only |
| 10 | Import preview is generated first (M7c dry-run) |
| 11 | Teacher reviews summary counts |
| 12 | Catalog target is local-first and non-production unless separately approved |
| 13 | Backup/export of previous catalog state exists if a catalog exists |
| 14 | Rollback/removal plan exists before write |
| 15 | Event log plan exists |
| 16 | No network/API/OAuth required |
| 17 | No file content reads required |
| 18 | No organization actions bundled with import |

Preconditions are documented requirements only. M7d does not execute import.
