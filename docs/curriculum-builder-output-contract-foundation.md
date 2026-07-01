# Curriculum Builder Output Contract Planning Foundation

```text
Status: documentation/status only
Activation status: not active
Output contract status: planning placeholders only
Runtime status: none
Generation status: none
```

## Purpose

This document defines a future Curriculum Builder output-contract planning layer. Output contracts describe what kinds of teacher-facing artifacts the registry may eventually reference or organize — without creating schemas, validators, renderers, or generated content. Planning placeholders only.

## Current Status

- documentation/status only
- planning placeholders only
- no active output contracts
- no schema files
- no validators
- no renderers
- no lesson generation
- no generated drafts

## Non-Activation Boundary

This plan does not add:

- no schema files
- no validators
- no renderers
- no lesson generation
- no generated drafts
- no generated lesson briefs
- no parsing
- no curriculum file ingestion
- no RAG
- no vector database
- no embeddings
- no OCR
- no document scanning
- no folder scanning
- no file indexing
- no APIs
- no network calls
- no OAuth
- no automation
- no student data
- no Canvas API
- no Google Drive API
- no package builders
- no export commands

## Future Output Contract Categories

Planning-only contract categories (not active):

| Contract | Planning label | Future role |
| --- | --- | --- |
| Direct Instruction slide deck | `direct_instruction_slide_deck_contract` | Future slide-deck output shape for teacher review |
| Worksheet | `worksheet_contract` | Future worksheet output shape for teacher review |
| Review game | `review_game_contract` | Future review-game output shape for teacher review |
| Teacher script | `teacher_script_contract` | Future teacher-script output shape for teacher review |
| Canvas export/package | `canvas_export_package_contract` | Future Canvas-ready package reference shape (planning only; no Canvas integration) |

These are vocabulary placeholders only. They do not create files, templates, or runtime behavior.

## Contract Planning Principles

- Output contracts remain metadata/planning references only until separately approved.
- Contracts describe artifact types, not generated content.
- Contracts must not imply lesson generation is active.
- Contracts must not imply curriculum files are ingested or parsed.
- Contracts must not imply RAG, embeddings, or vector search.
- Contracts must not contain student data.
- Contracts must preserve local-first, teacher-reviewed boundaries.
- Any future contract activation requires explicit approval through the Curriculum Builder approval gate and completed decision intake.

## Relationship to Existing Curriculum Builder Docs

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-canonical-planning-index.md` | Canonical entry point |
| `docs/curriculum-builder-planning-stack-summary.md` | Planning stack audit index |
| `docs/curriculum-builder-local-first-foundation-plan.md` | Local-first foundation |
| `docs/curriculum-resource-registry-plan.md` | Metadata-only registry planning |
| `docs/curriculum-builder-approval-gate.md` | Implementation approval gate |
| `docs/canvas-llm-stop-marker-curriculum-builder-return.md` | Return handoff from frozen Canvas LLM track |

Canvas export/package contract planning references the frozen Canvas LLM planning stack only. It does not activate Canvas API, export commands, or package builders.

## Chief of Staff Boundary

Chief of Staff may:

- report static Curriculum Builder foundation status
- confirm this planning doc exists
- show PASS/WARN/FAIL from read-only status scripts

Chief of Staff must not:

- generate lesson content
- render output contracts
- ingest curriculum files
- scan folders
- call APIs
- activate RAG or embeddings
- handle student data

## Future Activation Requirements

Any future output-contract activation requires:

- separate explicit approval
- completed decision intake
- approval gate crossing
- named PR with explicit scope
- dry-run behavior if runtime is proposed
- no student data confirmation
- no network/API/OAuth unless separately approved
- no lesson generation unless separately approved
- no scanning/indexing/OCR/embeddings/vector database unless separately approved

## Validation Expectations

```bash
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
```

## Non-Activation Confirmation

Documentation/status only. Curriculum Builder output contract planning foundation is Markdown-only planning text. No schema files, validators, renderers, lesson generation, generated drafts, parsing, curriculum file ingestion, RAG, vector database, embeddings, OCR, scanning, indexing, APIs, network calls, OAuth, automation, student data, Canvas API, Google Drive API, package builders, export commands, or runtime behavior. Output contracts are planning placeholders only.
