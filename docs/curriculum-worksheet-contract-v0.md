# Worksheet Contract v0

Last updated: 2026-07-01

## Purpose

Worksheet Contract v0 is the third fully validated canonical output contract under Phase 2 Mission 5. It promotes `worksheet_contract` from a planning placeholder into a **bounded, read-only, deterministic schema** with a fictional manual sample.

This is **contract metadata only** — not worksheet generation, PDF output, or rendering.

## Relationship to Other v0 Subsystems

| Subsystem | Role |
| --- | --- |
| [Output Contract v0](curriculum-output-contract-v0.md) | Shared envelope and manifest (`canonical_contracts`) |
| [Direct Instruction slide deck contract](curriculum-output-contract-v0.md) | First canonical contract (presentation-oriented) |
| [Teacher Script Contract v0](curriculum-teacher-script-contract-v0.md) | Second canonical contract (instructional-script-oriented) |
| **Worksheet Contract v0** (this document) | Third canonical contract (practice-worksheet-oriented) |
| [Curriculum Registry v0](curriculum-registry-v0.md) | Source of `registry_references` |
| [Registry–Contract Binding v0](curriculum-binding-v0.md) | Read-only lookup and consistency validation |

## Scope (v0)

Worksheet Contract v0 supports:

- canonical local schema for worksheet output contracts
- fictional/manual sample contract (`sample-contract-worksheet-001`)
- deterministic validation of envelope, registry references, exercise placeholders, review state, and safety flags
- registry reference validation against Registry v0
- binding integration for read-only lookup

Worksheet Contract v0 does **not** support:

- worksheet generation or real worksheet content
- lesson generation, renderers, HTML/PDF, or Canvas packages
- ingestion, scanning, APIs, OAuth, network calls, or student data
- contract writes from CLI

## Canonical Artifacts

| Artifact | Path |
| --- | --- |
| Schema | `assistant/curriculum-builder/output-contract/v0/worksheet-contract-schema.json` |
| Sample contract | `assistant/curriculum-builder/output-contract/v0/contracts/sample-worksheet-001.json` |
| Manifest entry | `canonical_contracts` in `placeholder-manifest.json` |

## Contract Structure

Key fields:

- **Envelope:** `contract_id`, `contract_type`, `contract_version`, `registry_references`, `teacher_only`, `student_facing_allowed`
- **Worksheet context:** `worksheet_context` (`pacing_reference`, `worksheet_format`, `focus_topic`)
- **Exercises:** `exercise_placeholders[]` with `prompt_placeholder`, `response_format_placeholder`, `answer_key_placeholder`, `difficulty_hint_placeholder`
- **Review:** `review_state`, `approval_status`
- **Safety:** `local_first_safety_flags`, `non_activation_flags` (`no_pdf_output`, `no_worksheet_generation`, etc.)
- **Extensions:** `pedagogy_extensions`, `metadata_extensions` (empty objects in v0)

All v0 text fields use **placeholder** wording only.

## Validation

Validated by the shared Output Contract v0 validator:

```bash
bash scripts/curriculum-output-contract-v0-validator.sh
bin/chief-of-staff --curriculum-output-contract-v0-validate
bash tests/curriculum-worksheet-contract-v0-test.sh
```

Binding lookup example:

```bash
bin/chief-of-staff --curriculum-binding-v0-lookup sample-sm5-worksheet-folder-001
```

## Future Use (Not Activated)

Worksheet Contract v0 is designed as a foundation for future:

- renderer-neutral worksheet layout planning
- practice exercise atom references
- review workflow metadata joins
- teacher-reviewed PDF generation hooks

None of these are active in v0.

## no lesson generation

Worksheet Contract v0 does not generate worksheets, lessons, drafts, or curriculum content.

## no renderers

Worksheet Contract v0 does not render HTML, PDF, or printable worksheet artifacts.

## no student data

All v0 worksheet fields use fictional placeholder text. No real student names or student-sensitive data belong in contract files.
