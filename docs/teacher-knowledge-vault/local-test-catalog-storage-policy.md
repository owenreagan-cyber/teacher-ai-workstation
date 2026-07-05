# Teacher Knowledge Vault — Local Test Catalog Storage Policy

Last updated: 2026-07-04

```text
Status: fixed generated-output policy — non-production only
```

## Fixed Generated Path

| Path | Purpose |
| --- | --- |
| `.tmp/teacher-knowledge-vault/m7e/test-catalog.sqlite` | Disposable SQLite test catalog |
| `.tmp/teacher-knowledge-vault/m7e/test-catalog-backup.sqlite` | Pre-import backup copy |
| `.tmp/teacher-knowledge-vault/m7e/import-summary.json` | Deterministic import summary |
| `.tmp/teacher-knowledge-vault/m7e/rollback-proof.json` | Rollback/removal proof metadata |

## Policy

- Path is **fixed** — no arbitrary user input accepted
- Path is **non-production** — not production registry or canonical catalog
- Path is **gitignored** — see `.gitignore` entry `.tmp/teacher-knowledge-vault/m7e/`
- Tests may delete/regenerate **only** this fixed path
- No file operations outside this generated-output directory
- No external paths, home directory paths, or Drive/NAS/iCloud/Canvas paths
