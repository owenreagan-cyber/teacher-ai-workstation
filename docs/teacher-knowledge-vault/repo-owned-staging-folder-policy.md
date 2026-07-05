# Repo-Owned Staging Folder Policy

Last updated: 2026-07-05

## Fixed staging fixture folder

| Purpose | Path |
| --- | --- |
| Staging root | `assistant/teacher-knowledge-vault/m2b/fake-staging-folder/` |
| Manifest | `assistant/teacher-knowledge-vault/m2b/fake-staging-manifest.json` |

Scripts accept **no arbitrary user input** for paths.

## Fixture rules

- fake/sanitized placeholder files only
- minimal placeholder text: `[FAKE_PLACEHOLDER_FILE]`
- no real curriculum text
- no student data
- no real local paths
- no copyrighted materials

## Policy folders in fixtures

| Folder | Behavior |
| --- | --- |
| `10_TEACHER_ONLY` | restricted-indexable |
| `11_STUDENT_FACING` | indexable (fixture metadata only) |
| `12_AI_GENERATED` | indexable (fixture metadata only) |
| `99_DO_NOT_SCAN` | blocked/non-indexable |

## Blocked paths

- Owen's home directory
- Downloads, Desktop, Documents
- Google Drive, iCloud, NAS, Canvas
- `~/TeacherAI-Curriculum-Library/`
- arbitrary external paths
