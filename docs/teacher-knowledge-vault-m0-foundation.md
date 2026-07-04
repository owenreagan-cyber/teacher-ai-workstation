# Teacher Knowledge Vault — M0 Foundation

Last updated: 2026-07-04

```text
Status: documentation/status only
Foundation status: active_m0_architecture_freeze
Implementation approval status: not approved by default for auto-loading, scanning, indexing, or ingestion
```

## Purpose

This document is the **canonical closure summary** for Teacher Knowledge Vault **Milestone 0 (M0) expanded architecture freeze** and its relationship to Chief of Staff memory, curriculum DAM intelligence, and M1 fake catalog alignment.

The Vault is the **intelligence layer** — not file storage. Google Drive and/or UGREEN NAS are canonical storage targets.

Cross-references:

- Expanded M0 freeze: `docs/teacher-knowledge-vault/m0-architecture-freeze.md`
- ADR index: `docs/adr/teacher-knowledge-vault/README.md`
- v1 spec: `docs/teacher-knowledge-vault/v1-architecture-spec.md`
- M1 fake catalog: `docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md`
- Memory policy: `assistant/memory-policy.md`
- Engineering authority: `docs/engineering-constitution.md`

## Relationship to Chief of Staff Memory

| Layer | Role |
| --- | --- |
| **Intake review queue** | Candidate material before approval |
| **Knowledge Vault (DAM intelligence)** | Metadata, identity, governance, search, review — not file storage |
| **Chief of Staff memory paths** | Approved summaries at `assistant/memory/knowledge/` (not populated in M0/M1) |
| **Project / preference memory** | Operational continuity — distinct from vault catalog |

## Implemented Subsystems (Expanded M0)

| Subsystem | Location |
| --- | --- |
| M0 architecture freeze | `docs/teacher-knowledge-vault/m0-architecture-freeze.md` |
| v1 architecture spec | `docs/teacher-knowledge-vault/v1-architecture-spec.md` |
| Canonical storage & taxonomy | `docs/teacher-knowledge-vault/canonical-storage-and-taxonomy.md` |
| Connector SDK, resource identity, fingerprinting, rule DSL | `docs/teacher-knowledge-vault/` |
| Human review, observability, QA gates, plugins | `docs/teacher-knowledge-vault/` |
| Document understanding, smart rename, evidence model | `docs/teacher-knowledge-vault/` |
| Restricted indexing, source reconciliation, AirPlay | `docs/teacher-knowledge-vault/` |
| ADR set (0001–0010) | `docs/adr/teacher-knowledge-vault/` |
| M0 sample fixtures | `assistant/teacher-knowledge-vault/samples/` |
| PR #253 memory-path docs | `architecture-freeze-plan.md`, intake gate, v0 entries |
| M0 status | `scripts/teacher-knowledge-vault-m0-architecture-freeze-status.sh` |

Closure marker: `complete_teacher_knowledge_vault_m0_architecture_freeze`

Expansion alignment: `complete_teacher_knowledge_vault_m0_expansion_m1_alignment`

## M1 Fake Catalog Foundation (Post-M0)

M1 builds the internal catalog data model using fake fixtures only. See `docs/teacher-knowledge-vault/m1-fake-catalog-foundation.md` and `bin/chief-of-staff --teacher-knowledge-vault-m1-fake-catalog-status`.

Closure marker: `complete_teacher_knowledge_vault_m1_fake_catalog_foundation`

## Chief of Staff Command Surface

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status` | Full Knowledge Vault M0 architecture freeze PASS/WARN/FAIL |
| `bin/chief-of-staff --teacher-knowledge-vault-m1-fake-catalog-status` | M1 fake catalog foundation PASS/WARN/FAIL |
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
