# Teacher Knowledge Vault — Local Discovery Dry-Run Design

Last updated: 2026-07-04

```text
Status: architecture/dry-run design only
Real filesystem traversal: blocked
```

## Future Discovery Scope (Blocked Until Separate Approval)

When a future Owen-approved mission authorizes M2b, a selected-folder discovery run may use **metadata only** collection. The run must **never read file contents**.

| Allowed (future, approval-gated) | Blocked (always) |
| --- | --- |
| Scan **one** explicitly selected local staging folder | Home-directory recursive scans |
| Metadata only | Never read file contents |
| Path label, display filename, extension, size, modified/created dates when safe | PDF/DOCX/PPTX/XLSX parsing |
| Source label, parent folder label | OCR, native extraction, AI classification |
| Event-log-style dry-run records | Move/rename/copy/delete/archive |
| Route findings to review queue | Unapproved symlink following |
| Teacher approval for every next step | `99_DO_NOT_SCAN` paths |
| Optional hash **only after separate hash approval** | Drive/iCloud/NAS/Canvas API scans |

## Dry-Run Record Principles

- Every planned discovery run uses `runtime_executed: false`
- `api_cost_estimate_usd: 0.00`
- `real_files_processed: 0`
- Fake placeholder URIs only in fixtures (e.g. `fake-local-staging://...`)

## Fixture Examples

See `assistant/teacher-knowledge-vault/m2/` for fictional dry-run scenarios:

- Approved local staging root
- Blocked `99_DO_NOT_SCAN`
- Teacher-only restricted folder (`10_TEACHER_ONLY`)
- Student-facing folder (`11_STUDENT_FACING`)
- AI-generated folder (`12_AI_GENERATED`)
- Cloud placeholder file
- Symlink escape attempt
- Hidden/system file
- Duplicate-looking filename
- Large file needing later hash approval
- File requiring native extraction later
- File requiring OCR later
- File requiring manual review
- File from unapproved root blocked

Cross-reference: `docs/teacher-knowledge-vault/local-discovery-output-contract.md`
