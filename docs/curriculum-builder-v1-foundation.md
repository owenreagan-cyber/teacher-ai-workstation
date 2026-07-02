# Curriculum Builder v1 Foundation

Last updated: 2026-07-01

```text
Status: documentation/status only
Foundation status: active_v1
Implementation approval status: not approved by default for generation, renderers, ingestion, or integrations
```

## Purpose

This document is the **canonical closure summary** for Curriculum Builder v1 foundation under approved Phase 2 boundaries. It describes what exists, how to validate it, what remains blocked, and what future systems depend on it.

Cross-references:

- Program roadmap: `docs/master-build-roadmap.md`
- Planning index: `docs/curriculum-builder-canonical-planning-index.md`
- Section completion audit: `docs/curriculum-builder-section-completion-audit.md`
- Engineering authority: `docs/engineering-constitution.md`

## Implemented Subsystems (v1 Foundation)

| Subsystem | Doc | Role |
| --- | --- | --- |
| Registry v0 | `docs/curriculum-registry-v0.md` | Fictional manual metadata records; read-only validation |
| Output Contract v0 | `docs/curriculum-output-contract-v0.md` | Shared envelope; five canonical contract types |
| Registry–Contract Binding v0 | `docs/curriculum-binding-v0.md` | Read-only lookup and consistency validation |
| DI Slide Deck Contract v0 | `docs/curriculum-output-contract-v0.md` | First canonical contract |
| Teacher Script Contract v0 | `docs/curriculum-teacher-script-contract-v0.md` | Second canonical contract |
| Worksheet Contract v0 | `docs/curriculum-worksheet-contract-v0.md` | Third canonical contract |
| Review Game Contract v0 | `docs/curriculum-review-game-contract-v0.md` | Fourth canonical contract |
| Canvas Package Contract v0 | `docs/curriculum-canvas-package-contract-v0.md` | Fifth canonical contract (metadata only) |
| Metadata contracts A4–A7 | `docs/curriculum-builder-canonical-contract-schemas.md` | Inactive planning schemas (resource, source, review, lesson link) |
| Registry v0.2 dry-run (CB-IMPL-1) | `docs/curriculum-builder-registry-v0-2-manual-entry-dry-run.md` | Fake manual entry candidates; dry-run validation only; no writes |

Artifact roots:

- Registry: `assistant/curriculum-builder/registry/v0/`
- Dry-run samples: `assistant/curriculum-builder/samples/registry-v0-2-dry-run/`
- Contracts: `assistant/curriculum-builder/output-contract/v0/`
- Binding: `assistant/curriculum-builder/binding/v0/`

## Chief of Staff Command Surface

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --curriculum-builder-foundation-status` | Full Curriculum Builder foundation PASS/WARN/FAIL |
| `bin/chief-of-staff --curriculum-contracts-status` | Metadata contract schemas A4–A7 read-only status |
| `bin/chief-of-staff --curriculum-registry-dry-run-status` | Registry v0.2 manual entry dry-run (CB-IMPL-1; no writes) |
| `bin/chief-of-staff --curriculum-registry-v0-status` | Registry v0 status |
| `bin/chief-of-staff --curriculum-registry-v0-validate` | Registry v0 validator |
| `bin/chief-of-staff --curriculum-output-contract-v0-status` | Output contract v0 status |
| `bin/chief-of-staff --curriculum-output-contract-v0-validate` | Output contract v0 validator |
| `bin/chief-of-staff --curriculum-binding-v0-status` | Binding v0 status |
| `bin/chief-of-staff --curriculum-binding-v0-validate` | Binding v0 validator |
| `bin/chief-of-staff --curriculum-binding-v0-lookup <registry_id>` | Read-only binding lookup |
| `bin/chief-of-staff --dashboard` | Includes Curriculum Builder foundation in Lesson Planning Status |

## Validation Suite

```bash
bash scripts/curriculum-builder-registry-v0-2-dry-run.sh
bash scripts/curriculum-builder-registry-v0-2-status.sh
bash tests/curriculum-builder-registry-v0-2-dry-run-test.sh
bash tests/curriculum-builder-registry-v0-2-status-test.sh
bash scripts/curriculum-registry-v0-validator.sh
bash scripts/curriculum-output-contract-v0-validator.sh
bash scripts/curriculum-binding-v0-validator.sh
bash scripts/curriculum-binding-v0-lookup.sh
bash scripts/curriculum-builder-foundation-status.sh
bash tests/curriculum-contract-suite-v0-test.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

Contract-type tests:

- `tests/curriculum-output-contract-v0-test.sh`
- `tests/curriculum-teacher-script-contract-v0-test.sh`
- `tests/curriculum-worksheet-contract-v0-test.sh`
- `tests/curriculum-review-game-contract-v0-test.sh`
- `tests/curriculum-canvas-package-contract-v0-test.sh`
- `tests/curriculum-binding-v0-test.sh`
- `tests/curriculum-registry-v0-test.sh`

## ID Conventions (v0)

| Kind | Pattern | Example |
| --- | --- | --- |
| Registry ID | `sample-<slug>` | `sample-sm5-textbook-001` |
| Contract ID | `sample-contract-<slug>` | `sample-contract-worksheet-001` |
| Slide ID | `slide-NN` | `slide-01` |
| Section ID | `section-NN` | `section-01` |
| Exercise ID | `exercise-NN` | `exercise-01` |
| Round ID | `round-NN` | `round-01` |
| Module ID | `module-NN` | `module-01` |

All v0 records and contracts use **fictional placeholder** text and manual entry only.

## no lesson generation

Curriculum Builder v1 foundation does not generate lessons, drafts, worksheets, games, or curriculum content.

## Boundaries (Still Active)

Curriculum Builder v1 foundation does **not** include:

- real curriculum records or student data
- lesson generation, renderers, HTML/PDF output
- Canvas API, package building, or publishing
- Google Drive/NAS/iCloud resolution or file scanning
- indexing, OCR, embeddings, RAG, or vector database
- APIs, OAuth, network calls, or automation
- contract or registry writes from CLI

Canvas LLM runtime remains **frozen/stopped**. Canvas package contract is metadata only.

## Binding Alignment WARNs

Binding validation may emit optional alignment WARNs when canonical contract metadata fields (`subject`, `grade_band`, `unit`, `lesson`) differ from linked registry records. These are informational only and do not fail validation. See `docs/curriculum-binding-v0.md`.

## Future Approval Gates

| Track | Gate | Doc |
| --- | --- | --- |
| Real registry records | Decision intake + no-student-data confirmation | `docs/implementation-approval-gate.md` |
| Registry manual entry `--write` | Separate approved mission | `docs/master-build-roadmap.md` Mission A4 |
| Renderers | Per-contract renderer intake | Mission A6 |
| Local retrieval hooks | Approved lookup/index mission | Mission A7 |
| Canvas LLM restart | Explicit stop-marker supersede | `docs/canvas-llm-stop-marker-curriculum-builder-return.md` |
| Integrations | Last in build order | `docs/master-build-roadmap.md` Program G |

## What Depends on This Foundation

Future systems that will build on Curriculum Builder v1 foundation when separately approved:

- Chief of Staff daily ops and next-action routing
- Teacher-reviewed renderers per contract type
- Local LLM generation with contract-shaped outputs
- Canvas packaging runtime (when Canvas LLM unfreezes)
- Approved registry records replacing fictional samples
- Retrieval/index hooks over registry + contracts (non-RAG)

None of these are active in v1 foundation.

## v1 Foundation Definition of Done

Curriculum Builder v1 foundation is **complete** for the approved scope when:

1. Registry v0 validated with fictional samples
2. All five output contract types are canonical with schemas, samples, and validators
3. Binding recognizes all canonical contracts
4. Chief of Staff command surface is documented and smoke-tested
5. Dashboard and foundation status scripts are clean
6. This document and cross-links are active

## Non-Activation Confirmation

Documentation/status only. No lesson generation, real curriculum content, renderers, Canvas API, Drive API, scanning, indexing, OCR, embeddings, RAG, vector database, network calls, OAuth, automation, student data, or registry/contract writes.
