# Teacher Script Contract v0

Last updated: 2026-07-01

## Purpose

Teacher Script Contract v0 is the second fully validated canonical output contract under Phase 2 Mission 4. It promotes `teacher_script_contract` from a planning placeholder into a **bounded, read-only, deterministic schema** with a fictional manual sample.

This is **contract metadata only** — not teacher script generation, rendering, or runtime execution.

## Relationship to Other v0 Subsystems

| Subsystem | Role |
| --- | --- |
| [Output Contract v0](curriculum-output-contract-v0.md) | Shared envelope and manifest (`canonical_contracts`) |
| [Direct Instruction slide deck contract](curriculum-output-contract-v0.md) | First canonical contract (presentation-oriented) |
| **Teacher Script Contract v0** (this document) | Second canonical contract (instructional-script-oriented) |
| [Curriculum Registry v0](curriculum-registry-v0.md) | Source of `registry_references` |
| [Registry–Contract Binding v0](curriculum-binding-v0.md) | Read-only lookup and consistency validation |

## Scope (v0)

Teacher Script Contract v0 supports:

- canonical local schema for teacher-script output contracts
- fictional/manual sample contract (`sample-contract-teacher-script-001`)
- deterministic validation of envelope, registry references, script sections, review state, and safety flags
- registry reference validation against Registry v0
- binding integration for read-only lookup

Teacher Script Contract v0 does **not** support:

- teacher script generation or real teacher scripts
- lesson generation, renderers, HTML/PDF, or Canvas packages
- dynamic variables, student-name injection, or personalization
- ingestion, scanning, APIs, OAuth, network calls, or student data
- contract writes from CLI

## Canonical Artifacts

| Artifact | Path |
| --- | --- |
| Schema | `assistant/curriculum-builder/output-contract/v0/teacher-script-contract-schema.json` |
| Sample contract | `assistant/curriculum-builder/output-contract/v0/contracts/sample-teacher-script-001.json` |
| Manifest entry | `canonical_contracts` in `placeholder-manifest.json` |

## Contract Structure

Key fields:

- **Envelope:** `contract_id`, `contract_type`, `contract_version`, `registry_references`, `teacher_only`, `student_facing_allowed`
- **Lesson context:** `lesson_context` (`pacing_reference`, `delivery_mode`, `focus_topic`)
- **Script sections:** `script_sections[]` with `teacher_script`, `teacher_prompt`, `student_response_expectation`, `check_for_understanding`, `timing_or_pacing_hint`, `materials_or_prep_note`
- **Review:** `review_state`, `approval_status`
- **Safety:** `local_first_safety_flags`, `non_activation_flags` (`no_dynamic_variables`, `no_student_name_injection`, etc.)
- **Extensions:** `pedagogy_extensions`, `metadata_extensions` (empty objects in v0)

All v0 text fields use **placeholder** wording only.

## Validation

Validated by the shared Output Contract v0 validator:

```bash
bash scripts/curriculum-output-contract-v0-validator.sh
bin/chief-of-staff --curriculum-output-contract-v0-validate
bash tests/curriculum-teacher-script-contract-v0-test.sh
```

Binding lookup example:

```bash
bin/chief-of-staff --curriculum-binding-v0-lookup sample-sm5-textbook-001
```

## Future Use (Not Activated)

Teacher Script Contract v0 is designed as a foundation for future:

- renderer-neutral script presentation planning
- lesson builder instructional atom references
- review workflow metadata joins
- Canvas packaging planning hooks

None of these are active in v0.

## no lesson generation

Teacher Script Contract v0 does not generate scripts, lessons, drafts, or curriculum content.

## no renderers

Teacher Script Contract v0 does not render HTML, PDF, slides, or Canvas artifacts.

## no student data

All v0 teacher script fields use fictional placeholder text. No real student names or student-sensitive data belong in contract files.
