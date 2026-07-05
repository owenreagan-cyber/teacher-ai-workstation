# Selected Local Folder Preflight Requirements

Last updated: 2026-07-05

Future M2d preflight must verify before any metadata scan:

## Path checks

- exact folder path named by Owen
- path exists (future runtime only)
- path is local
- path is not home/Desktop/Documents/Downloads by default
- path is not Drive/iCloud/NAS/Canvas by default
- path is not hidden/system folder
- path is not a parent of broad user data
- path is not inside `99_DO_NOT_SCAN`
- path is not likely to contain student data

## Scope limits

| Limit | Default |
| --- | --- |
| max file count | 25 |
| max folder depth | 2 |
| max total bytes | 10 MB |
| extension allowlist | `.pdf`, `.docx`, `.pptx`, `.md`, `.txt` |

## Safety blocks

- content-read commands blocked
- OCR/AI/extraction disabled
- no symlink traversal
- no package/archive expansion
- no nested app/library/system traversal
- no write operations to source folder
- generated report path fixed under `.local/teacher-knowledge-vault/m2d/`
- rollback/cleanup plan exists
- approval packet produced before import
- Owen must explicitly approve import after preview (second approval)

M2c implements policy and fake examples only — no preflight runtime on real paths.
