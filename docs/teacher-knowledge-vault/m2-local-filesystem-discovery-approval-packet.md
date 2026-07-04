# Teacher Knowledge Vault — M2 Local Filesystem Discovery Approval Packet

Last updated: 2026-07-04

```text
Status: approval packet and dry-run design only — no real scanning
Closure: complete_teacher_knowledge_vault_m2_local_discovery_approval_packet
M0/M1: preserved
Future prototype (M2b): blocked pending separate Owen approval
Runtime scanning: blocked
```

## M2 Doctrine

M2 prepares the repo for a **future** selected-folder **metadata-only** local discovery prototype. This mission does not approve implementation or execution.

M2 preserves:

- M0 expanded architecture freeze (`complete_teacher_knowledge_vault_m0_architecture_freeze`)
- M1 fake catalog model (`complete_teacher_knowledge_vault_m1_fake_catalog_foundation`)
- Resource → Representation → Source identity
- Connector SDK boundaries (no connector implementations)
- Event log and review queue requirements
- `10_TEACHER_ONLY` restricted-indexable policy
- `99_DO_NOT_SCAN` absolute exclusion
- No runtime scanning until a future Owen-approved mission

## What M2 Delivers

| Deliverable | Location |
| --- | --- |
| Approval packet (this doc) | `docs/teacher-knowledge-vault/m2-local-filesystem-discovery-approval-packet.md` |
| Future discovery scope | `docs/teacher-knowledge-vault/local-discovery-dry-run-design.md` |
| Blocked path policy | `docs/teacher-knowledge-vault/local-discovery-blocked-path-policy.md` |
| Discovery output contract | `docs/teacher-knowledge-vault/local-discovery-output-contract.md` |
| Cost/performance guardrails | `docs/teacher-knowledge-vault/local-discovery-cost-performance-guardrails.md` |
| M2 governance status | `docs/teacher-knowledge-vault/m2-governance-status.md` |
| Fake M2 fixtures | `assistant/teacher-knowledge-vault/m2/` |
| M2 status | `scripts/teacher-knowledge-vault-m2-local-discovery-approval-status.sh` |

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| M0 Architecture freeze (expanded) | complete |
| M1 Fake catalog foundation | complete |
| **M2** Local discovery approval packet | **complete** (this mission) |
| M2b Selected-folder metadata prototype | blocked — requires Owen approval |
| M3 Duplicate detection/search | blocked |
| M4 Smart Rename suggestions | blocked |
| M5+ Organization, OCR, connectors, AI | blocked |

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-m2-local-discovery-approval-status
bash tests/teacher-knowledge-vault-m2-local-discovery-approval-status-test.sh
bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status
bin/chief-of-staff --teacher-knowledge-vault-m1-fake-catalog-status
```

## Non-Activation

PASS on M2 status proves approval-packet documentation and fake fixtures only — not permission to scan local folders.
