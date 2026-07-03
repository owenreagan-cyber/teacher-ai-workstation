# Curriculum Manual Metadata / Markdown Frontmatter Planning

Last updated: 2026-07-03

```text
Status: planning_only
Closure: complete_curriculum_manual_metadata_frontmatter_planning
Classification: proposal candidate — not implementation approval
Real curriculum ingestion: blocked
Active schema/validator/parser: blocked
Production registry writes: blocked
Student data: blocked — absolute
```

## Purpose

Static planning program for **future manual metadata and markdown frontmatter workflows** in the Teacher AI Workstation. This doc helps Owen and Cursor reason about human-applied labels before any schema activation, parser, validator, or runtime command exists.

**This document does not authorize schemas, validators, fixtures, parsers, commands, file scanning, parsing, generation, integrations, or production writes.**

## Relationship to Prior Work

| Prior artifact | Relationship |
| --- | --- |
| PR #239 Gemini discovery memo | Proposal-candidate source — `docs/external-planning/discovery-classification-memo.md` §6 |
| Gemini intake classification | `docs/proposals/ideas/gemini-discovery-classification-architecture-intake.md` |
| Curriculum Source Readiness | Fake metadata inventory — no real ingestion |
| A4–A7 metadata contracts | Registry-layer contracts — separate from frontmatter planning |
| Manual metadata boundary | `docs/curriculum-builder-manual-metadata-boundary.md` — field prohibition reference |
| Production registry | Parked — one governed record; no `--write` |

## Core Principles

| Principle | Meaning |
| --- | --- |
| **Manual entry** | Owen types labels by hand; no auto-extraction |
| **Local-first** | Planning for offline/local files; no cloud sync |
| **Human review** | Labels are reviewed before any future registry promotion |
| **Fake/local examples only** | Illustrations use placeholder labels — not real curriculum |
| **Planning-only field ideas** | No accepted runtime keys; not parsed; not validated |

## Candidate Field Idea Table

Every row is **conceptual / planning-only / manual-entry candidate**. None are accepted runtime schema keys.

| Field idea | Example placeholder values | Planning notes | Status |
| --- | --- | --- | --- |
| `asset_domain` | `example-mathematics`, `example-language-arts` | Broad subject domain label | conceptual; not parsed |
| `subject` | `example-math-grade-5` | Narrower subject tag | conceptual; not required |
| `grade_band` | `example-grade-5` | Grade band label | conceptual; manual only |
| `curriculum_source_label` | `manual:placeholder-source-label` | Owen-typed source reference | conceptual; no auto-resolve |
| `unit_label` | `example-unit-2-fractions` | Unit pacing label | conceptual; fake only |
| `lesson_label` | `example-lesson-3-practice` | Lesson pacing label | conceptual; fake only |
| `resource_type` | `worksheet`, `study_guide`, `slide_deck` | Resource kind label | aligns with A4 planning — not active |
| `pedagogical_layer` | `independent_practice`, `spiral_review` | Instructional role label | conceptual; not validated |
| `structural_format` | `markdown_document`, `plain_text_list` | File structure label | conceptual; not parsed |
| `teacher_only` | `true` / `false` | Teacher-facing flag idea | conceptual; not enforced |
| `student_facing_safe` | `true` / `false` | Planning flag — not student data | conceptual; not roster-related |
| `review_status` | `draft_placeholder`, `approved_placeholder` | Human review state idea | conceptual; not registry write |
| `source_reference_label` | `placeholder://source/example-label` | Fake source pointer | no Drive/NAS URLs |
| `storage_location_type_label` | `local_folder_planning`, `nas_label_planning` | Storage tier idea — label only | no path scanning |
| `local_storage_tier` | `active_term`, `historical_reference` | Archival classification idea | conceptual only |
| `concept_dependency_tags` | `example-prerequisite-fractions` | Prerequisite tag ideas | not curriculum content |
| `notes` | `Fake planning note only` | Freeform Owen notes | manual only |

**Legend for every field:** not accepted runtime schema · not required · not parsed · not validated · not used by commands.

## Safe Illustrative Examples

### Fake field-values illustration (JSON — not a schema)

See `assistant/curriculum-builder/samples/manual-metadata-frontmatter-planning/example-field-ideas-illustration.json`.

```json
{
  "fixture_classification": "manual_metadata_frontmatter_planning_only",
  "field_ideas_illustration": true,
  "not_a_schema": true,
  "not_parsed": true,
  "asset_domain": "example-mathematics",
  "subject": "example-math-grade-5",
  "grade_band": "example-grade-5",
  "unit_label": "example-unit-2-placeholder",
  "lesson_label": "example-lesson-3-placeholder",
  "resource_type": "worksheet",
  "pedagogical_layer": "independent_practice",
  "review_status": "draft_placeholder",
  "notes": "Fake local illustration only — no real curriculum."
}
```

### Safe markdown frontmatter illustration (comment block — not parsed)

Illustrative only. **No command reads or validates this block.**

```markdown
<!--
PLANNING ILLUSTRATION ONLY — NOT PARSED — NOT A SCHEMA
asset_domain: example-mathematics
subject: example-math-grade-5
grade_band: example-grade-5
unit_label: example-unit-2-placeholder
lesson_label: example-lesson-3-placeholder
resource_type: worksheet
review_status: draft_placeholder
notes: Fake planning illustration only
-->
```

## Unsafe Anti-Patterns (Blocked)

See `assistant/curriculum-builder/samples/manual-metadata-frontmatter-planning/negative/`.

| Anti-pattern | Why blocked |
| --- | --- |
| Real textbook or worksheet body text | Real curriculum content |
| Answer keys or assessment items | Real curriculum content |
| `https://drive.google.com/...` URLs | Integration / live access |
| Absolute NAS or iCloud paths | Integration / scanning risk |
| Canvas course or enrollment IDs | Integration / student-data risk |
| Student names, rosters, grades | Student-data absolute prohibition |
| IEP / accommodation / behavior fields | Student-data absolute prohibition |
| `embedding_id`, `rag_chunk`, `vector_index` | Embeddings / RAG blocked |
| OAuth tokens, API keys | Network / secrets blocked |
| AI generation or Ollama prompts in metadata | Generation / inference blocked |

## Blocked Capabilities

| Capability | State |
| --- | --- |
| Frontmatter parser | blocked |
| Frontmatter validator | blocked |
| Active schema files for frontmatter | blocked |
| Folder scanning / file watching | blocked |
| Real curriculum file reads | blocked |
| Student data in metadata | blocked — absolute |
| Drive / NAS / iCloud / Canvas access | blocked |
| API / OAuth / network | blocked |
| OCR / embeddings / RAG | blocked |
| AI generation / Ollama execution | blocked |
| Production registry writes / `--write` | blocked |

## Future Approval Path

1. Owen reviews this planning program and field idea table
2. Separate mission may promote **specific** fields into registry contracts (A4–A7) — not automatic from this doc
3. Parser/validator missions require explicit implementation approval
4. Production registry writes remain blocked until Option A/B/C Owen decision

## How Cursor May Use This Doc

- Reference field ideas when drafting **planning-only** missions
- Cross-link from proposal ledger and intake classification
- Must not treat field names as accepted keys or implement parsers/validators without approval

## How Chief of Staff May Use This Doc

- Read-only status proof via `--markdown-frontmatter-planning-status`
- Must not parse markdown files, scan folders, or validate frontmatter

## Proof

```bash
bin/chief-of-staff --markdown-frontmatter-planning-status
bash tests/markdown-frontmatter-planning-status-test.sh
```

## Non-Activation

`complete_curriculum_manual_metadata_frontmatter_planning` is a documentation closure marker only. It does not activate schemas, parsers, validators, or runtime metadata workflows.
