# Review Game Contract v0

Last updated: 2026-07-01

## Purpose

Review Game Contract v0 is the fourth fully validated canonical output contract. It promotes `review_game_contract` from a planning placeholder into a **bounded, read-only, deterministic schema** with a fictional manual sample.

This is **contract metadata only** — not review game generation, interactive runtime, or rendering.

## Relationship to Other v0 Subsystems

| Subsystem | Role |
| --- | --- |
| [Output Contract v0](curriculum-output-contract-v0.md) | Shared envelope and manifest (`canonical_contracts`) |
| [Worksheet Contract v0](curriculum-worksheet-contract-v0.md) | Third canonical contract (practice-worksheet-oriented) |
| **Review Game Contract v0** (this document) | Fourth canonical contract (review-game-oriented) |
| [Curriculum Registry v0](curriculum-registry-v0.md) | Source of `registry_references` |
| [Registry–Contract Binding v0](curriculum-binding-v0.md) | Read-only lookup and consistency validation |

## Scope (v0)

Review Game Contract v0 supports:

- canonical local schema for review game output contracts
- fictional/manual sample contract (`sample-contract-review-game-001`)
- deterministic validation of envelope, registry references, round placeholders, review state, and safety flags
- registry reference validation against Registry v0
- binding integration for read-only lookup

Review Game Contract v0 does **not** support:

- review game generation or real game content
- lesson generation, renderers, HTML/PDF, or Canvas packages
- interactive runtime or student-facing game execution
- ingestion, scanning, APIs, OAuth, network calls, or student data
- contract writes from CLI

## Canonical Artifacts

| Artifact | Path |
| --- | --- |
| Schema | `assistant/curriculum-builder/output-contract/v0/review-game-contract-schema.json` |
| Sample contract | `assistant/curriculum-builder/output-contract/v0/contracts/sample-review-game-001.json` |
| Manifest entry | `canonical_contracts` in `placeholder-manifest.json` |

## Contract Structure

Key fields:

- **Envelope:** `contract_id`, `contract_type`, `contract_version`, `registry_references`, `teacher_only`, `student_facing_allowed`
- **Game context:** `game_context` (`pacing_reference`, `game_format`, `focus_topic`)
- **Rounds:** `round_placeholders[]` with `question_placeholder`, `answer_placeholder`, `timing_hint_placeholder`, `materials_note_placeholder`
- **Review:** `review_state`, `approval_status`
- **Safety:** `local_first_safety_flags`, `non_activation_flags` (`no_game_generation`, `no_interactive_runtime`, etc.)

All v0 text fields use **placeholder** wording only.

## Validation

```bash
bash scripts/curriculum-output-contract-v0-validator.sh
bin/chief-of-staff --curriculum-output-contract-v0-validate
bash tests/curriculum-review-game-contract-v0-test.sh
```

Binding lookup example:

```bash
bin/chief-of-staff --curriculum-binding-v0-lookup sample-student-practice-001
```

## no lesson generation

Review Game Contract v0 does not generate games, lessons, drafts, or curriculum content.

## no renderers

Review Game Contract v0 does not render HTML, slides, or interactive game artifacts.

## no student data

All v0 review game fields use fictional placeholder text. No real student names or student-sensitive data belong in contract files.
