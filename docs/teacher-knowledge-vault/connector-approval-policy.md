# Teacher Knowledge Vault — Connector Approval Policy

Last updated: 2026-07-04

```text
Status: approval policy — M7 remains Level 0 only
runtime_implemented: false in M7
```

## Approval Levels

| Level | Description |
| --- | --- |
| Level 0 | Docs/fake fixtures only — **M7** |
| Level 1 | Manual source inventory / pasted/exported metadata only |
| Level 2 | Read-only metadata connector, no file content |
| Level 3 | Read-only content preview, limited and approval-gated |
| Level 4 | Download/cache selected file, approval-gated |
| Level 5 | Write/publish/sync operations, separate high-friction approval |

## Rules

- no connector can be implemented from docs alone
- every connector needs a separate Owen-approved runtime mission
- read-only does not mean unrestricted
- file content reads are separate from metadata reads
- writes/publishing/sync are separate from read-only connectors
- OAuth, secrets, and API calls are blocked in M7

Fixture: `assistant/teacher-knowledge-vault/m7/fake-connector-capabilities.json`
