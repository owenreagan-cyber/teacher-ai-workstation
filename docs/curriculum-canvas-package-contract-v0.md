# Canvas Export Package Contract v0

Last updated: 2026-07-01

## Purpose

Canvas Export Package Contract v0 is the fifth fully validated canonical output contract. It promotes `canvas_export_package_contract` from a planning placeholder into a **bounded, read-only, deterministic schema** with a fictional manual sample.

This is **contract metadata only** — not Canvas API integration, package building, or publishing.

## Relationship to Other v0 Subsystems

| Subsystem | Role |
| --- | --- |
| [Output Contract v0](curriculum-output-contract-v0.md) | Shared envelope and manifest (`canonical_contracts`) |
| [Review Game Contract v0](curriculum-review-game-contract-v0.md) | Fourth canonical contract |
| **Canvas Export Package Contract v0** (this document) | Fifth canonical contract (Canvas package metadata only) |
| [Curriculum Registry v0](curriculum-registry-v0.md) | Source of `registry_references` |
| [Registry–Contract Binding v0](curriculum-binding-v0.md) | Read-only lookup and consistency validation |
| Frozen Canvas LLM planning | Historical planning reference only; no runtime activation |

## Scope (v0)

Canvas Export Package Contract v0 supports:

- canonical local schema for Canvas export package planning metadata
- fictional/manual sample contract (`sample-contract-canvas-package-001`)
- deterministic validation of envelope, registry references, module placeholders, and safety flags
- registry reference validation against Registry v0
- binding integration for read-only lookup

Canvas Export Package Contract v0 does **not** support:

- Canvas API calls, OAuth, or network integration
- package building, export commands, or publishing
- lesson generation, renderers, or real Canvas content
- ingestion, scanning, or student data
- contract writes from CLI

## Canonical Artifacts

| Artifact | Path |
| --- | --- |
| Schema | `assistant/curriculum-builder/output-contract/v0/canvas-export-package-contract-schema.json` |
| Sample contract | `assistant/curriculum-builder/output-contract/v0/contracts/sample-canvas-package-001.json` |
| Manifest entry | `canonical_contracts` in `placeholder-manifest.json` |

## Contract Structure

Key fields:

- **Envelope:** `contract_id`, `contract_type`, `registry_references`, `teacher_only`, `student_facing_allowed`
- **Package context:** `package_context` (`pacing_reference`, `export_mode`, `focus_topic`)
- **Modules:** `module_placeholders[]` with `title_placeholder`, `content_type_placeholder`, `planning_note_placeholder`
- **Canvas safety:** `canvas_non_activation_flags` (`no_canvas_api`, `no_package_build`, `no_publish`, etc.)
- **General safety:** `non_activation_flags`, `local_first_safety_flags`

All v0 text fields use **placeholder** wording only.

## Validation

```bash
bash scripts/curriculum-output-contract-v0-validator.sh
bin/chief-of-staff --curriculum-output-contract-v0-validate
bash tests/curriculum-canvas-package-contract-v0-test.sh
```

Binding lookup example:

```bash
bin/chief-of-staff --curriculum-binding-v0-lookup sample-canvas-export-folder-001
```

## no lesson generation

Canvas Export Package Contract v0 does not generate lessons, packages, or curriculum content.

## no renderers

Canvas Export Package Contract v0 does not render HTML, IMSCC, or Canvas-ready artifacts.

## no student data

All v0 Canvas package fields use fictional placeholder text. No real student names or student-sensitive data belong in contract files.
