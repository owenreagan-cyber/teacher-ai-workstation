# Selected Local Folder Denial Rules

Last updated: 2026-07-05

M2c documents denial rules for future M2d. Example denials: `assistant/teacher-knowledge-vault/m2c/fake-path-preflight-denials.json`

## Denied by default

- arbitrary path scanning
- home directory
- Desktop
- Documents
- Downloads
- Google Drive
- iCloud Drive
- NAS
- Canvas
- external drives
- system folders
- hidden folders
- `99_DO_NOT_SCAN`
- student-data-likely folders
- broad curriculum roots
- symlinks (traversal escape)
- archive expansion
- file content reads
- OCR/AI/extraction
- organization operations

## Policy preservation

- `10_TEACHER_ONLY` — restricted-indexable only
- `99_DO_NOT_SCAN` — blocked/non-indexable

No real path scans are executed to prove these rules in M2c — docs, fixtures, and status assertions only.
