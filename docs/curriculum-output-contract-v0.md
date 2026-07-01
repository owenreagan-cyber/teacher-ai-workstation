# Curriculum Output Contract v0

Last updated: 2026-07-01

## Purpose

Curriculum Output Contract v0 is the repository's second approved Phase 2 implementation subsystem. It activates the output contract planning foundation into a **bounded, read-only contract-validation layer** that can validate fictional/manual contract examples and reference Curriculum Registry v0 IDs.

This is **contract foundation only** — not lesson generation, rendering, ingestion, or Canvas packaging.

## Scope (v0)

Output Contract v0 supports:

- local schema files for contract envelopes and one canonical contract type
- fictional/manual sample contract files
- read-only deterministic validation
- registry ID reference checks against Registry v0
- placeholder contracts for future categories (not fully validated)
- versioning (`contract_version: 0.1.0`)

Output Contract v0 does **not** support:

- lesson generation or real curriculum content
- renderers, HTML, or PDF generation
- Canvas package building or Canvas API
- ingestion, scanning, OCR, embeddings, RAG, or vector database
- APIs, OAuth, network calls, automation, or student data
- contract writes from CLI or automation

## Canonical Artifacts

| Artifact | Path |
| --- | --- |
| Contract root README | `assistant/curriculum-builder/output-contract/v0/README.md` |
| Envelope schema | `assistant/curriculum-builder/output-contract/v0/contract-envelope-schema.json` |
| DI slide deck schema | `assistant/curriculum-builder/output-contract/v0/direct-instruction-slide-deck-schema.json` |
| Teacher script schema | `assistant/curriculum-builder/output-contract/v0/teacher-script-contract-schema.json` |
| Worksheet schema | `assistant/curriculum-builder/output-contract/v0/worksheet-contract-schema.json` |
| Canonical DI contract | `assistant/curriculum-builder/output-contract/v0/contracts/sample-di-slide-deck-001.json` |
| Canonical teacher script | `assistant/curriculum-builder/output-contract/v0/contracts/sample-teacher-script-001.json` |
| Placeholder manifest | `assistant/curriculum-builder/output-contract/v0/placeholder-manifest.json` |
| Validator | `scripts/curriculum-output-contract-v0-validator.sh` |
| Status proof | `scripts/curriculum-output-contract-v0-status.sh` |

Planning vocabulary alignment:

- `docs/curriculum-builder-output-contract-foundation.md` — original contract categories
- `docs/curriculum-registry-v0.md` — registry ID reference source

## Contract Categories (v0)

| Contract type | v0 status |
| --- | --- |
| `direct_instruction_slide_deck_contract` | **Canonical** — fully validated fictional sample |
| `teacher_script_contract` | **Canonical** — fully validated fictional sample (see `docs/curriculum-teacher-script-contract-v0.md`) |
| `worksheet_contract` | **Canonical** — fully validated fictional sample (see `docs/curriculum-worksheet-contract-v0.md`) |
| `review_game_contract` | Placeholder only |
| `canvas_export_package_contract` | Placeholder only |

## Canonical Contract Format

The canonical Direct Instruction slide deck contract is metadata only:

```json
{
  "contract_version": "0.1.0",
  "contract_status": "active_v0",
  "metadata_only": true,
  "read_only": true,
  "contract_id": "sample-contract-di-slide-deck-001",
  "contract_type": "direct_instruction_slide_deck_contract",
  "registry_references": ["sample-sm5-textbook-001"],
  "slide_outline_placeholders": []
}
```

Registry references are validated against Registry v0 and cross-linked by Registry–Contract Binding v0. See `docs/curriculum-binding-v0.md`.

- `registry_references` must reference existing Registry v0 `registry_id` values
- `slide_outline_placeholders` contain title/notes placeholders only — no slide HTML or generated content
- `slide_count` must match the number of slide outline placeholders

## Placeholder Contracts

Placeholder contracts use `contract_status: placeholder_v0` and `activation_status: contract_v0_placeholder`. They document future contract categories without full schema validation. They must not include canonical-only fields such as `slide_outline_placeholders`.

## Read-Only Boundary

Validators and status scripts:

- do not generate lesson content or render artifacts
- do not write contract files
- do not scan folders or call APIs
- validate registry references against local Registry v0 data only

## Validation

```bash
bash scripts/curriculum-output-contract-v0-validator.sh
bin/chief-of-staff --curriculum-output-contract-v0-validate
bin/chief-of-staff --curriculum-output-contract-v0-status
bash tests/curriculum-output-contract-v0-test.sh
```

## Versioning and Future Work

| Version | Status |
| --- | --- |
| v0.1.0 | Active — three canonical contracts + two placeholders, read-only validation |
| v0.2+ | Not started — requires separate approved mission |

Future versions may add: full schemas for review game/Canvas contracts, renderers, and generation hooks — each approval-gated.

## Related Governance

- `docs/engineering-constitution.md` — Phase 2 implementation authority
- `docs/implementation-approval-gate.md` — track intake and approval boundaries
- `docs/curriculum-builder-output-contract-foundation.md` — planning foundation plus v0 activation note

## no lesson generation

Output Contract v0 explicitly excludes lesson generation, generated drafts, and curriculum content production.

## no renderers

Output Contract v0 explicitly excludes renderers, HTML/PDF output, and Canvas package building.

## no student data

All v0 contracts use fictional placeholder titles and references. No real student names or student-sensitive data belong in contract files.
