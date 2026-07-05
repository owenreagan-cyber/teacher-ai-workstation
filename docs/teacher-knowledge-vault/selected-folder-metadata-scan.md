# Selected Folder Metadata Scan (M2d Step 2)

Last updated: 2026-07-05

Script: `scripts/teacher-knowledge-vault-m2d-selected-folder-metadata-scan.sh`

## Requirements

- Step 1 preflight packet must exist with `allowed_decision: true`
- stat metadata only via `os.scandir` and `DirEntry.stat(follow_symlinks=False)`
- no content reads, parsers, OCR, AI, or embeddings
- traversal confined to approved root; no symlink traversal
- no write operations to source folder

## Reports generated

| Report | Path |
| --- | --- |
| Metadata report | `.local/teacher-knowledge-vault/m2d/selected-folder-metadata-report.json` |
| Scan proof | `.local/teacher-knowledge-vault/m2d/scan-proof.json` |
| No-content-read proof | `.local/teacher-knowledge-vault/m2d/no-content-read-proof.json` |
| Rollback proof | `.local/teacher-knowledge-vault/m2d/rollback-proof.json` |
| Summary | `.local/teacher-knowledge-vault/m2d/summary-report.json` |

## Metadata collected

filename, extension, size_bytes, modified_at_epoch, relative_path, directory_depth, mime_guess_from_extension (extension only).

No automatic M7g import. Use preview command separately.
