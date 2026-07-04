# Teacher Knowledge Vault — Destination Suggestion Model

Last updated: 2026-07-04

```text
Status: suggested targets only — no directory creation, no file moves
Google Drive/NAS organization: future and approval-gated
```

## Destination Mapping Examples

| Artifact type | Suggested destination |
| --- | --- |
| Math homework | `01_MATH/...` or package-specific target |
| Teacher guide/manual | `10_TEACHER_ONLY/...` (restricted_indexable) |
| Student worksheet | `11_STUDENT_FACING/01_worksheets_handouts/...` when approved |
| Canvas package | `11_STUDENT_FACING/04_canvas_packages/...` (publishing candidate) |
| AI-generated review game | `12_AI_GENERATED/...` |
| Archive candidate | `90_ARCHIVE/...` |
| `99_DO_NOT_SCAN` | never suggested into normal taxonomy |

## Rules

- Destinations are suggested targets only
- no directories are created in M4
- No files are moved, copied, renamed, or deleted
- Source reconciliation may flag missing from canonical storage — cannot fix automatically

Fixture: `assistant/teacher-knowledge-vault/m4/fake-destination-suggestions.json`

Cross-reference: `docs/teacher-knowledge-vault/canonical-storage-and-taxonomy.md`
