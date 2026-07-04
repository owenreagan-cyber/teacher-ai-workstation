# Teacher Knowledge Vault — M0 Foundation

Last updated: 2026-07-04

```text
Status: documentation/status only
Foundation status: active_m0_architecture_freeze
Implementation approval status: not approved by default for auto-loading, scanning, indexing, or ingestion
```

## Purpose

This document is the **canonical closure summary** for Teacher Knowledge Vault **Milestone 0 (M0) architecture freeze** under approved Phase 1C memory boundaries. It defines the local-first, human-reviewed reference model for user-approved summaries and reusable teaching notes — without auto-loading memory, scanning files, or activating Drive/Gmail/Obsidian connectors.

Cross-references:

- Memory policy: `assistant/memory-policy.md`
- Chief of Staff memory: `assistant/memory/README.md`
- Intake policy: `assistant/intake/intake-policy.md`
- Engineering authority: `docs/engineering-constitution.md`
- Implementation gate: `docs/implementation-approval-gate.md`

## Relationship to Chief of Staff Memory

| Layer | Role |
| --- | --- |
| **Intake review queue** | Candidate material before approval |
| **Knowledge Vault** | User-approved reference summaries and reusable notes |
| **Project / preference / writing-style memory** | Operational continuity and style — distinct from reference vault |

Knowledge Vault stores **approved reference summaries**, not raw intake, full Drive dumps, or unreviewed private data.

## Implemented Subsystems (M0 Architecture Freeze)

| Subsystem | Location | Role |
| --- | --- | --- |
| Architecture freeze plan | `docs/teacher-knowledge-vault/architecture-freeze-plan.md` | M0 scope, sequence, and mission boundaries |
| Folder taxonomy | `docs/teacher-knowledge-vault/folder-taxonomy.md` | Planned `assistant/memory/knowledge/` layout (not populated yet) |
| Intake-to-vault gate | `docs/teacher-knowledge-vault/intake-to-vault-approval-gate.md` | Human approval before any vault promotion runtime |
| Manual entry plan | `docs/teacher-knowledge-vault/manual-entry-plan.md` | Owen-facing manual entry model |
| Blocked runtime boundaries | `docs/teacher-knowledge-vault/blocked-runtime-boundaries.md` | Full blocked-behavior list |
| Knowledge entry schema v0 | `assistant/teacher-knowledge-vault/v0/knowledge-entry-schema.json` | Placeholder entry model schema |
| Sample entries | `assistant/teacher-knowledge-vault/v0/sample-knowledge-entries.json` | Fictional entry fixtures |
| Fake planning fixtures | `assistant/teacher-knowledge-vault/samples/` | Fictional intake promotion and outline samples |
| M0 status | `scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh` | Read-only M0 closure proof |
| Entry validator | `scripts/teacher-knowledge-vault-knowledge-entry-v0-validator.sh` | Deterministic read-only JSON validation |
| M0 status test | `tests/teacher-knowledge-vault-m0-architecture-freeze-status-test.sh` | Status command tests |

Closure marker: `complete_teacher_knowledge_vault_m0_architecture_freeze`

## Chief of Staff Command Surface

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status` | Full Knowledge Vault M0 architecture freeze PASS/WARN/FAIL |
| `bin/chief-of-staff --teacher-knowledge-vault-knowledge-entry-v0-validate` | Read-only knowledge entry v0 validator |
| `bin/chief-of-staff --validate-memory` | Related memory warning check (not vault-specific) |
| `bin/chief-of-staff --dashboard` | Includes Knowledge Vault M0 status in dashboard |

## Validation Suite

```bash
bash scripts/teacher-knowledge-vault-knowledge-entry-v0-validator.sh
bash scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh
bash tests/teacher-knowledge-vault-m0-architecture-freeze-status-test.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

## ID Conventions (v0)

| Kind | Pattern | Example |
| --- | --- | --- |
| Knowledge entry ID | `sample-knowledge-entry-<slug>` | `sample-knowledge-entry-001` |
| Intake reference ID | `fake-intake-ref-<slug>` | `fake-intake-ref-001` |

All v0 vault fixtures use **fictional placeholder** entries only.

## Boundaries (Still Active)

Teacher Knowledge Vault M0 does **not** include:

- real knowledge files in `assistant/memory/knowledge/` (directory not populated by this mission)
- automatic memory loading or CLI default inclusion
- folder scanning, document scanning, indexing, OCR, embeddings, or RAG
- Drive API, Gmail API, Obsidian sync, OAuth, or network calls
- student-sensitive data, parent records, or confidential school records
- background jobs or autonomous promotion from intake

## M0 Definition of Done

Teacher Knowledge Vault M0 architecture freeze is **complete** for the approved scope when:

1. Knowledge entry schema v0 and fictional samples validate deterministically
2. Architecture, taxonomy, intake gate, and manual entry docs cross-link this foundation
3. Chief of Staff command surface is documented and wired
4. Dashboard includes M0 status without regression
5. This document and cross-links are active

## Non-Activation Confirmation

Documentation/status only. No real knowledge files, auto-loading memory, scanning, indexing, OCR, embeddings, RAG, APIs, OAuth, network calls, or automatic intake promotion.
