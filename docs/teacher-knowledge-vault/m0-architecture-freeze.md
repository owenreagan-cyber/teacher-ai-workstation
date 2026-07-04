# Teacher Knowledge Vault — M0 Architecture Freeze

Last updated: 2026-07-04

```text
Status: documentation/status/fake fixtures only — M0 freeze active
Closure: complete_teacher_knowledge_vault_m0_architecture_freeze
Expansion alignment: complete_teacher_knowledge_vault_m0_expansion_m1_alignment
Implementation: not approved by this doc alone
Runtime: blocked — connectors, scanning, OCR, AI, file operations, publishing
```

## Mission Doctrine

Teacher Knowledge Vault is a **teacher-controlled curriculum digital asset management and intelligence platform**. It transforms scattered teaching resources into a well-organized, searchable, intelligently indexed, source-aware curriculum map.

| Role | System |
| --- | --- |
| **Canonical file storage** | Google Drive and/or UGREEN NAS |
| **Intelligence layer** | Teacher Knowledge Vault (metadata, identity, rules, search, governance, review) |
| **Development workshop** | MacBook Pro M5 — optional local staging/cache only |
| **Minimum classroom runtime** | MacBook Air M1, iPad Air A16 |
| **Publishing / deployment** | Canvas (future) — not canonical storage |

The Vault is **not file storage**. All rename, move, copy, delete, archive, OCR, AI, API, connector, and publishing actions require explicit approval gates and must be auditable.

## Architecture Freeze / Anti-Drift Rule

**M0 freezes v1 architecture.** Future changes require ADRs (`docs/adr/teacher-knowledge-vault/`) or Owen approval.

| Rule | Requirement |
| --- | --- |
| No casual engines | Do not add engines without ADR |
| Clear boundaries | Do not blur engine responsibilities |
| Planning ≠ runtime | Do not implement from planning docs alone |
| M1 ≠ M2 permission | Fake fixtures do not authorize scanning or connectors |
| ADR or Owen | Architecture changes require ADR or explicit approval |

## Taxonomy Guardrails (Frozen)

- `10_TEACHER_ONLY` — restricted-indexable; not student-visible by default
- `11_STUDENT_FACING` — leakage checks required
- `12_AI_GENERATED` — approval-gated outputs
- `99_DO_NOT_SCAN` — absolute exclusion from discovery, indexing, extraction, and search

Details: `docs/teacher-knowledge-vault/canonical-storage-and-taxonomy.md`, `docs/teacher-knowledge-vault/restricted-indexing-and-pacing-guardrails.md`

## Frozen v1 Subsystems

| Subsystem | Document |
| --- | --- |
| v1 architecture spec | `docs/teacher-knowledge-vault/v1-architecture-spec.md` |
| Canonical storage & taxonomy | `docs/teacher-knowledge-vault/canonical-storage-and-taxonomy.md` |
| Connector SDK contract | `docs/teacher-knowledge-vault/connector-sdk-contract.md` |
| Resource identity model | `docs/teacher-knowledge-vault/resource-identity-model.md` |
| Fingerprinting model | `docs/teacher-knowledge-vault/fingerprinting-model.md` |
| Classification Rule DSL | `docs/teacher-knowledge-vault/classification-rule-dsl.md` |
| Human review workspace | `docs/teacher-knowledge-vault/human-review-workspace.md` |
| Observability & metrics | `docs/teacher-knowledge-vault/observability-and-metrics.md` |
| Three-level QA gates | `docs/teacher-knowledge-vault/qa-gates.md` |
| Plugin extension points | `docs/teacher-knowledge-vault/plugin-extension-points.md` |
| Document understanding pipeline | `docs/teacher-knowledge-vault/document-understanding-pipeline.md` |
| Smart rename policy | `docs/teacher-knowledge-vault/smart-rename-policy.md` |
| Evidence & confidence model | `docs/teacher-knowledge-vault/evidence-package-and-confidence-model.md` |
| Restricted indexing & pacing | `docs/teacher-knowledge-vault/restricted-indexing-and-pacing-guardrails.md` |
| Source reconciliation | `docs/teacher-knowledge-vault/source-reconciliation-model.md` |
| Event log foundation | `docs/teacher-knowledge-vault/event-log-foundation.md` |
| AirPlay classroom runtime | `docs/teacher-knowledge-vault/airplay-classroom-runtime-requirements.md` |
| ADR set | `docs/adr/teacher-knowledge-vault/` |
| M0 samples fixtures | `assistant/teacher-knowledge-vault/samples/` |
| M1 fake catalog | `assistant/teacher-knowledge-vault/m1/` |

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| **M0** Architecture freeze (expanded) | **complete** |
| **M1** Fake catalog foundation | **complete** (PR #254) |
| **M2** Local discovery approval packet | **complete** |
| **M3** Fake duplicate/search/package foundation | **complete** |
| **M4** Smart rename foundation | **complete** |
| **M5** Approved organization + rollback | **complete** |
| **M6** Native extraction/OCR approval packet | **complete** |
| **M7** Read-only connector approval packet | **complete** |
| M2b Selected-folder metadata prototype | blocked |
| Runtime search/duplicate detection | blocked |
| Runtime smart rename | blocked |
| Runtime organization operations | blocked |
| Runtime extraction/OCR | blocked |
| Drive/NAS/Canvas connector implementation | blocked |
| M8 AI/RAG | blocked |

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status
bin/chief-of-staff --teacher-knowledge-vault-m1-fake-catalog-status
```
