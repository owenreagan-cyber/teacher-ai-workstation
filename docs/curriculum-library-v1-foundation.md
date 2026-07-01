# Curriculum Library v1 Foundation

Last updated: 2026-07-01

```text
Status: documentation/status only
Foundation status: active_v1
Implementation approval status: not approved by default for scanning, indexing, APIs, or resolution
```

## Purpose

This document is the **canonical closure summary** for Curriculum Library v1 foundation under approved Phase 3 boundaries. It defines the local-first metadata/reference model for curriculum resources stored in Google Drive, NAS, iCloud, and local folders — without duplicating raw files or activating resolution.

Cross-references:

- Program roadmap: `docs/master-build-roadmap.md`
- Local-first plan: `docs/curriculum-builder-local-first-foundation-plan.md`
- Storage strategy: `docs/curriculum-source-storage-strategy.md`
- Resource registry plan: `docs/curriculum-resource-registry-plan.md`
- Curriculum Builder v1: `docs/curriculum-builder-v1-foundation.md`
- Engineering authority: `docs/engineering-constitution.md`

## Relationship to Curriculum Builder

| Layer | Role |
| --- | --- |
| **Curriculum Library** | User-facing metadata/reference catalog for source storage locations |
| **Curriculum Builder** | Registry v0, output contracts, and binding for structured curriculum artifacts |

The library stores references and status. The builder validates structured registry and contract artifacts. They complement each other without merging scopes.

## Implemented Subsystems (v1 Foundation)

| Subsystem | Location | Role |
| --- | --- | --- |
| Storage strategy | `docs/curriculum-source-storage-strategy.md` | Drive/NAS/iCloud/local reference rules |
| Resource registry plan | `docs/curriculum-resource-registry-plan.md` | Future manual registry planning |
| Reference schema v0 | `assistant/curriculum-library/v0/library-reference-schema.json` | Placeholder reference model schema |
| Sample references | `assistant/curriculum-library/v0/sample-library-references.json` | Fictional reference fixtures |
| Foundation status | `scripts/curriculum-library-foundation-status.sh` | Read-only v1 foundation closure proof |
| Reference validator | `scripts/curriculum-library-reference-v0-validator.sh` | Deterministic read-only JSON validation |

## Chief of Staff Command Surface

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --curriculum-library-foundation-status` | Full Curriculum Library v1 foundation PASS/WARN/FAIL |
| `bin/chief-of-staff --curriculum-library-reference-v0-validate` | Read-only library reference v0 validator |
| `bin/chief-of-staff --curriculum-builder-foundation-status` | Related Curriculum Builder foundation status |
| `bin/chief-of-staff --dashboard` | Includes Curriculum Library foundation in dashboard |

## Validation Suite

```bash
bash scripts/curriculum-library-reference-v0-validator.sh
bash scripts/curriculum-library-foundation-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

## ID Conventions (v0)

| Kind | Pattern | Example |
| --- | --- | --- |
| Reference ID | `sample-library-ref-<slug>` | `sample-library-ref-001` |

All v0 library fixtures use **fictional placeholder** references only.

## Boundaries (Still Active)

Curriculum Library v1 foundation does **not** include:

- real curriculum records or student data
- raw file duplication or paid hosted storage
- folder scanning, document scanning, indexing, OCR, embeddings, or RAG
- Drive API, NAS resolution, iCloud resolution, or Canvas API
- OAuth, network calls, automation, or background jobs

## v1 Foundation Definition of Done

Curriculum Library v1 foundation is **complete** for the approved scope when:

1. Reference schema v0 and fictional samples validate deterministically
2. Storage strategy and registry planning docs cross-link this foundation
3. Chief of Staff command surface is documented and wired
4. Dashboard includes foundation status without regression
5. This document and cross-links are active

## Non-Activation Confirmation

Documentation/status only. No real curriculum records, file duplication, scanning, indexing, OCR, embeddings, RAG, APIs, OAuth, network calls, or automatic source resolution.
