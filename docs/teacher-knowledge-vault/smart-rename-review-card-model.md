# Teacher Knowledge Vault — Smart Rename Review Card Model

Last updated: 2026-07-04

```text
Status: fake UI/data model only — no UI runtime in M4
```

## Review Card Fields

| Section | Fields |
| --- | --- |
| **Current state** | display name, source, path label |
| **Suggestion** | suggested filename, suggested destination |
| **Context** | matched resource, matched package |
| **Evidence** | evidence summary, confidence summary |
| **Warnings** | duplicate warnings, version warnings, teacher-only, leakage |
| **Allowed actions** | Approve later, Edit suggestion, Reject, Mark as duplicate, Mark as version, Send to manual review, Block |
| **Blocked actions** | execute rename now, execute move now, publish now, OCR now, AI classify now, scan more files now |

## Rules

- M4 review cards are documentation and fake JSON fixtures only
- Future UI may support AirPlay/classroom readability; admin review workspace is desktop-first
- No suggestion executes without teacher approval and future M5 organization gate

Fixture: `assistant/teacher-knowledge-vault/m4/fake-review-cards.json`

Cross-reference: `docs/teacher-knowledge-vault/human-review-workspace.md`
