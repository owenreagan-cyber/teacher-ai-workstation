# Teacher Knowledge Vault — M7 Read-Only Connector Approval Packet

Last updated: 2026-07-04

```text
Status: read-only connector approval packet — fake fixtures only
Closure: complete_teacher_knowledge_vault_m7_read_only_connector_approval_packet
M0–M6: preserved
Connector runtime: blocked
OAuth/API/network: blocked
```

## M7 Doctrine

M7 defines **future read-only connector approval boundaries** using fake fixtures only. It prepares Drive, NAS, and Canvas connector planning without implementing connectors, OAuth, API calls, network access, source scanning, metadata ingestion, or file reads.

M7 preserves all prior milestones and blocks:

- Real connector implementation
- OAuth, secrets, tokens, API/network calls
- Real source listing or metadata ingestion
- File content reads
- Scanner, OCR, AI, file operations
- `99_DO_NOT_SCAN` absolute exclusion
- `10_TEACHER_ONLY` restricted-indexing policy

## Connector Approval Levels

| Level | Scope | M7 status |
| --- | --- | --- |
| 0 | Docs/fake fixtures only | **M7 — current** |
| 1 | Manual source inventory | future |
| 2 | Read-only metadata, no content | future |
| 3 | Read-only content preview | future |
| 4 | Download/cache selected file | future |
| 5 | Write/publish/sync | separate high-friction approval |

No connector can be implemented from docs alone. Every connector needs a separate Owen-approved runtime mission. **M7 remains Level 0 only.**

Cross-reference: ADR `0004-connector-sdk-contract.md`, `0002-drive-nas-canonical-storage.md`, `0010-canvas-publishing-target.md`

## Deliverables

| Subsystem | Location |
| --- | --- |
| M7 foundation (this doc) | `docs/teacher-knowledge-vault/m7-read-only-connector-approval-packet.md` |
| Connector approval policy | `docs/teacher-knowledge-vault/connector-approval-policy.md` |
| Connector capability model | `docs/teacher-knowledge-vault/connector-capability-model.md` |
| Source inventory model | `docs/teacher-knowledge-vault/source-inventory-model.md` |
| Google Drive approval packet | `docs/teacher-knowledge-vault/google-drive-connector-approval-packet.md` |
| UGREEN NAS approval packet | `docs/teacher-knowledge-vault/ugreen-nas-connector-approval-packet.md` |
| Canvas approval packet | `docs/teacher-knowledge-vault/canvas-connector-approval-packet.md` |
| Manual source inventory path | `docs/teacher-knowledge-vault/manual-source-inventory-path.md` |
| M7 governance | `docs/teacher-knowledge-vault/m7-governance-status.md` |
| M7 fixtures | `assistant/teacher-knowledge-vault/m7/` |

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| M0–M6 | complete |
| **M7** Read-only connector approval packet | **complete** (this mission) |
| M2b / Drive/NAS/Canvas connector implementation | blocked |
| Runtime extraction/OCR / organization / search / rename | blocked |
| M8 AI/RAG | blocked |

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-m7-connector-approval-status
bash tests/teacher-knowledge-vault-m7-connector-approval-status-test.sh
```

## Non-Activation

PASS on M7 status proves fake documentation and fixtures only — not permission to connect OAuth, call APIs, or read sources.
