# Lesson Blueprint System

Status: **specification layer complete (Milestone 2 — Phases 6–8)**  
Status command: `bin/chief-of-staff --lesson-blueprint-status`  
Runtime activation: **none** — no artifact generation, network, OCR, or scanning.

## Purpose

Transform an approved **Lesson Package Plan** into a fully specified, internally consistent **Lesson Blueprint**. The blueprint defines exactly what future presentations, guided notes, worksheets, teacher scripts, assessments, vocabulary pages, and answer keys must contain — without generating any classroom artifacts.

## Architecture

```text
Curriculum Sources
        ↓
Manual Intake (Phase 5)
        ↓
Lesson Package Plan
        ↓
Lesson Review Packet          ← Phase 6
        ↓
Consistency Engine            ← Phase 7
        ↓
Artifact Blueprints           ← Phase 8
        ↓
Teacher Approval
        ↓
Ready for Generation          ← future milestone (blocked)
```

Preserved upstream systems:

- Instructional Artifact Quality (Phases 1–3): `--artifact-quality-status`
- Curriculum Production Engine (Phase 4): `--curriculum-production-status`
- Manual Lesson Package Workflow (Phase 5): `--lesson-package-status`

## Phase 6 — Lesson Review Packet

Reusable review packet built from a Lesson Package Plan and Content Map.

**Outputs:** Markdown, JSON, optional YAML (`render_review_packet_markdown`, `to_dict`, `render_review_packet_yaml`).

**Includes:**

- Lesson metadata, objectives, standards, vocabulary
- Critical / High Priority / Supporting / Teacher Background / Omitted content
- Assessment targets, instructional sequence, artifact plan
- Validation summary, approval history, teacher notes, production status

Module: `scripts/lesson_blueprint/review_packet.py`

## Phase 7 — Cross-Artifact Consistency Engine

Validates cross-artifact alignment and registry integrity.

**Checks:**

- Vocabulary consistency across artifacts
- Objective coverage via instructional sequence
- Assessment target linkage
- Critical content assignment
- Artifact dependencies
- Teacher key mirroring
- Shared registry validation (duplicates, omissions, broken references)

Module: `scripts/lesson_blueprint/consistency.py`

## Shared Registries

Reusable registries with duplicate, omission, and broken-reference validation:

| Registry | Purpose |
| --- | --- |
| Vocabulary | Terms and artifact cross-references |
| Objective | Lesson objectives mapped to artifacts |
| Example | Worked examples across artifacts |
| Diagram | Diagram references |
| Question | Assessment-linked questions |
| Assessment | Assessment targets |
| Artifact | Planned artifact types |

Module: `scripts/lesson_blueprint/registries.py`

## Phase 8 — Artifact Blueprint Generator

Blueprint models for each planned artifact type:

- Presentation, Guided Notes, Worksheet, Teacher Script
- Vocabulary, Assessment, Teacher Key, Review

Each blueprint defines:

- Purpose, target page/slide counts, sections, expected content
- Content budget, required vocabulary/diagrams/examples
- Assessment links, dependencies, quality gates, approval state

Templates: `configs/lesson-blueprint/blueprint-templates.yaml`  
Budgets: `configs/lesson-blueprint/content-budgets.yaml`

Module: `scripts/lesson_blueprint/blueprints.py`

### Blueprint validation

Verifies required sections, vocabulary, critical content, assessment coverage, budgets, and dependencies. Emits WARN for soft issues and FAIL for broken dependencies or missing blueprints.

Module: `scripts/lesson_blueprint/blueprint_validation.py`

## Content Budgets

Specifications only — no generated files.

| Artifact | Budget |
| --- | --- |
| Presentation | 12–16 slides |
| Guided Notes | 2 pages, 8 meaningful blanks |
| Worksheet | 2 pages, 3 activity sections |
| Teacher Script | 8 instructional stages |
| Vocabulary | 1 page |
| Assessment | 2 pages |
| Teacher Key | Mirrored to student artifacts |

Config: `configs/lesson-blueprint/content-budgets.yaml`

## Approval Workflow

Blueprint review states:

| State | Behavior |
| --- | --- |
| Draft | Initial editable state |
| Needs Review | Awaiting teacher review |
| Approved | Ready for generation gate when validation passes |
| Locked | Prevents mutation without explicit override |

Tracks timestamp, user, reason, and notes.

Module: `scripts/lesson_blueprint/blueprint_approval.py`

## Reports

Built by `scripts/lesson_blueprint/reporting.py`:

- Lesson Blueprint Status
- Artifact Blueprint Status
- Consistency Report
- Vocabulary Report
- Assessment Coverage Report
- Dependency Report
- Content Budget Report

## Orchestration

`scripts/lesson_blueprint/workflow.py` — `build_lesson_blueprint()` ties review packet, registries, blueprints, consistency, validation, and reports together.

Fixtures: `fixtures/lesson-blueprint/{passing,warning,failing}/`

## Future Artifact Generation (blocked)

The following remain **planned only** — not implemented in this milestone:

- Presentation Generator
- Guided Notes Generator
- Worksheet Generator
- Teacher Script Generator
- Package Assembly

No PPTX, DOCX, HTML, or PDF generation is active.

## Validation Fixtures

| Status | Scenario | Fixture |
| --- | --- | --- |
| PASS | Well-formed blueprint | `fixtures/lesson-blueprint/passing/well-formed-blueprint.json` |
| WARN | Vocabulary mismatch | `fixtures/lesson-blueprint/warning/vocabulary-mismatch.json` |
| WARN | Unused Critical content | `fixtures/lesson-blueprint/warning/unused-critical-content.json` |
| WARN | Budget exceeded | `fixtures/lesson-blueprint/warning/budget-exceeded.json` |
| WARN | Duplicate terminology | `fixtures/lesson-blueprint/warning/duplicate-terminology.json` |
| FAIL | Broken dependency | `fixtures/lesson-blueprint/failing/broken-dependency.json` |
| FAIL | Missing blueprint | `fixtures/lesson-blueprint/failing/missing-blueprint.json` |
| FAIL | Missing required section | `fixtures/lesson-blueprint/failing/missing-sections.json` |
| FAIL | Broken registry reference | `fixtures/lesson-blueprint/failing/broken-registry.json` |

## Tests

```bash
python3 tests/lesson_blueprint/test_lesson_blueprint.py
bash tests/lesson-blueprint-status-test.sh
bin/chief-of-staff --lesson-blueprint-status
```

## Safety Boundaries

- No generated classroom artifacts
- No curriculum scanning, OCR, embeddings, or network
- No Canvas, Drive, APIs, or AI lesson generation
- No student data
- Local-first, human-reviewed specifications only
