# Curriculum Builder — Canonical Contract Schemas (Programs A4–A7)

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Curriculum Builder — Additional Canonical Contract Schemas (A4–A7)
Closure status: complete_a4_a7_metadata_contracts
Classification: read-only metadata contract foundation — no runtime activation
```

## Purpose

Define four **metadata-layer** canonical contract schemas for Curriculum Builder. These complement Output Contract v0 (presentation/worksheet/game/canvas package outputs) and Registry v0 (manual metadata records).

These schemas describe how future registry and planning systems may represent curriculum resources, source references, review state, and lesson links **without** ingesting files, scanning folders, or generating content.

## Relationship to Other Curriculum Builder Layers

| Layer | Doc | Role |
| --- | --- | --- |
| Registry v0 | `docs/curriculum-registry-v0.md` | Active read-only manual metadata store |
| Output Contract v0 | `docs/curriculum-output-contract-v0.md` | Five canonical **output** contract types |
| **Metadata contracts A4–A7** (this program) | See table below | Planning schemas for resource/source/review/link metadata |
| Local-first plan | `docs/curriculum-builder-local-first-foundation-plan.md` | Storage and reference strategy |
| Contract boundaries | `docs/curriculum-builder-contract-boundaries.md` | Non-activation rules for all contract work |

## Programs A4–A7

| Program | Contract | Doc | Status |
| --- | --- | --- | --- |
| A4 | Curriculum Resource Contract | `docs/curriculum-resource-contract-schema.md` | documented; inactive |
| A5 | Curriculum Source Reference Contract | `docs/curriculum-source-reference-contract-schema.md` | documented; inactive |
| A6 | Curriculum Review State Contract | `docs/curriculum-review-state-contract-schema.md` | documented; inactive |
| A7 | Curriculum Lesson Link Contract | `docs/curriculum-lesson-link-contract-schema.md` | documented; inactive |

Inactive sample artifacts (no validator, no runtime):

- `assistant/curriculum-builder/metadata-contract/v0/README.md`
- `assistant/curriculum-builder/metadata-contract/v0/inactive-manifest.json`
- `assistant/curriculum-builder/metadata-contract/v0/samples/*.json`

## Chief of Staff Command Surface

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --curriculum-contracts-status` | Read-only A4–A7 metadata contract foundation status |
| `bin/chief-of-staff --curriculum-builder-foundation-status` | Broader Curriculum Builder v1 foundation (unchanged) |

## Definition of Done (A4–A7)

| # | Deliverable | Status |
| --- | --- | --- |
| 1 | Canonical index (this doc) | complete |
| 2 | Resource contract schema doc | complete |
| 3 | Source reference contract schema doc | complete |
| 4 | Review state contract schema doc | complete |
| 5 | Lesson link contract schema doc | complete |
| 6 | Contract boundaries doc | complete |
| 7 | Inactive sample artifacts | complete |
| 8 | Status script | `scripts/curriculum-builder-contract-schemas-status.sh` |
| 9 | CLI command | `bin/chief-of-staff --curriculum-contracts-status` |
| 10 | Tests | `tests/curriculum-builder-contract-schemas-status-test.sh` |

## Explicitly Blocked

- document scanning, folder scanning, file indexing, OCR
- embeddings, vector DB, RAG, semantic search
- Drive/NAS/iCloud/Canvas crawling or API usage
- curriculum ingestion, file upload, file sync, document parsing
- lesson generation, lesson briefs, lesson drafts, review note generation
- student data, real curriculum content
- network calls, APIs, OAuth, automation

## Orchestrated Proof

```bash
bin/chief-of-staff --curriculum-contracts-status
bash scripts/curriculum-builder-contract-schemas-status.sh
bash tests/curriculum-builder-contract-schemas-status-test.sh
bin/chief-of-staff --dashboard
```

## Recommended Next Mission

**Curriculum Builder — Registry v0.2 Manual Entry Dry-Run** (implementation subtrack; approval-gated). Metadata contract schemas A4–A7 are planning-only until explicit intake approves validators or registry extensions.

## Non-Activation

Markdown and inactive JSON samples only. No validators, parsers, crawlers, or runtime behavior.
