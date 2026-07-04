# Teacher Knowledge Vault — Connector SDK Contract

Last updated: 2026-07-04

```text
Status: architecture contract only — no implementation
All connectors: blocked until separate approval
```

## Connector Interface (Frozen)

| Method | Purpose |
| --- | --- |
| `discover()` | Discovery run (approval-gated) |
| `listFolders()` | Folder metadata |
| `listFiles()` | File metadata in scope |
| `getMetadata()` | Normalized metadata |
| `getContentPreview()` | Bounded preview (approval-gated) |
| `download()` | Optional — explicit approval |
| `supportsHash()` | Binary hash availability |
| `supportsWatch()` | Change notifications (future) |
| `capabilities()` | Capability manifest |

## Future Connectors (All Blocked)

Local Filesystem, Google Drive, UGREEN NAS, Canvas, iCloud, Dropbox, OneDrive, NotebookLM planning, Gemini planning.

## Rules

- M0/M1 create contracts and fake fixtures only — not connector implementations
- M1 `fake-source-items.json` are not connector implementations
- Connectors return normalized SourceItems — catalog stays source-agnostic

Fixture: `assistant/teacher-knowledge-vault/samples/fake-connector-capabilities.json`

ADR: `docs/adr/teacher-knowledge-vault/0004-connector-sdk-contract.md`
