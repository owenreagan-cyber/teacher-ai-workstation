# Selected Folder Metadata Preflight (M2d Step 1)

Last updated: 2026-07-05

Script: `scripts/teacher-knowledge-vault-m2d-selected-folder-preflight.sh`

## Fixed approved path only

`/Users/owen/Projects/teacher-ai-workstation-local-test/m2d-tiny-folder`

Rejects any command-line path arguments (`arbitrary path arguments are not accepted`).

## Preflight checks

- path exists and is local
- path matches fixed approved folder (realpath normalized)
- not home/Desktop/Documents/Downloads
- not Drive/iCloud/NAS/Canvas markers in path
- no symlinks
- max 25 files, depth 2, 10 MB total
- extension allowlist only
- expected file set exactly matches mission list
- no content reads

## Output

`.local/teacher-knowledge-vault/m2d/preflight-approval-packet.json`

No metadata scan or catalog import in Step 1.
