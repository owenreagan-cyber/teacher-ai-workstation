# Curriculum Builder Static Source Registry Plan

```text
Status: documentation/status only
Activation status: not active
Registry status: metadata/reference-only planning
Runtime status: none
Generation status: none
```

## Purpose

This document defines a future static/manual Curriculum Builder source registry plan. The registry describes how teacher-reviewed curriculum source references may eventually be recorded as metadata-only planning records — without scanning folders, indexing files, resolving cloud paths, or generating lesson content. Planning placeholders only.

## Current Status

- documentation/status only
- metadata/reference-only planning
- no active registry
- no registry data files
- no schema files
- no validators
- no lesson generation
- no student data

## Non-Activation Boundary

This plan does not add:

- no scanning
- no folder crawling
- no file indexing
- no OCR
- no embeddings
- no vector database
- no Drive/NAS/iCloud resolution
- no APIs
- no network calls
- no OAuth
- no automation
- no lesson generation
- no generated drafts
- no generated lesson briefs
- no parsing
- no curriculum file ingestion
- no RAG
- no student data
- no Google Drive API
- no NAS API
- no iCloud API
- no Canvas API

## Static/Manual Registry Model

The future static source registry is **metadata/reference-only**. Records point at source locations by planning strings; they do not copy raw curriculum files into the repo or resolve live cloud paths.

- Records are created by manual teacher entry only after separate explicit approval.
- `source_path_or_url` is a stable planning reference string, not a live resolved path.
- `storage_location_type` classifies where the source is expected to live (for example Drive, NAS, iCloud, local folder) without resolving it.
- The registry stores references, review status, safety flags, and lesson/unit context — not file contents.

## Planned Registry Fields

Planning-only field vocabulary (not active):

| Field | Planning label | Future role |
| --- | --- | --- |
| Registry identifier | `registry_id` | Stable planning ID for a registry record |
| Source system | `source_system` | Source storage system marker (planning vocabulary only) |
| Source path or URL | `source_path_or_url` | Stable planning reference string; not resolved |
| Storage location type | `storage_location_type` | Classification of expected storage location |
| Subject | `subject` | Curriculum subject context |
| Grade | `grade` | Grade or grade-band context |
| Unit | `unit` | Unit context |
| Lesson | `lesson` | Lesson context |
| Resource type | `resource_type` | Resource category (for example textbook, slide deck, worksheet) |
| Teacher only | `teacher_only` | Whether resource is teacher-only |
| Student facing safe | `student_facing_safe` | Whether resource is safe for student-facing use |
| Review status | `review_status` | Teacher review state |
| Notes | `notes` | Freeform teacher notes (no student data) |
| Safety flags | `safety_flags` | Planning safety markers |

These are vocabulary placeholders only. They do not create schema files, seed data, or runtime behavior.

## Registry Planning Principles

- Registry records remain metadata/reference-only until separately approved.
- Records describe source references, not generated content.
- Records must not imply lesson generation is active.
- Records must not imply curriculum files are scanned, crawled, indexed, or parsed.
- Records must not imply RAG, embeddings, or vector search.
- Records must not contain student data.
- Records must preserve local-first, teacher-reviewed boundaries.
- Any future registry activation requires explicit approval through the Curriculum Builder approval gate and completed decision intake.

## Relationship to Existing Curriculum Builder Docs

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-canonical-planning-index.md` | Canonical entry point |
| `docs/curriculum-builder-planning-stack-summary.md` | Planning stack audit index |
| `docs/curriculum-resource-registry-plan.md` | Broader metadata-only registry concept |
| `docs/curriculum-builder-manual-registry-schema-plan.md` | Manual/static schema vocabulary |
| `docs/curriculum-builder-output-contract-foundation.md` | Future output contract planning placeholders |
| `docs/curriculum-builder-approval-gate.md` | Implementation approval gate |
| `docs/curriculum-source-storage-strategy.md` | Source storage ownership (planning only) |

This static source registry plan narrows the manual-first source reference field set for future registry records. It does not supersede approval gates or replace the broader registry plan.

## Chief of Staff Boundary

Chief of Staff may:

- report static Curriculum Builder foundation status
- confirm this planning doc exists
- show PASS/WARN/FAIL from read-only status scripts

Chief of Staff must not:

- scan folders or index files
- resolve Drive/NAS/iCloud paths
- ingest curriculum files
- call APIs
- activate RAG or embeddings
- generate lesson content
- handle student data

## Future Activation Requirements

Any future static source registry activation requires:

- separate explicit approval
- completed decision intake
- approval gate crossing
- named PR with explicit scope
- dry-run behavior if runtime is proposed
- no student data confirmation
- no network/API/OAuth unless separately approved
- no lesson generation unless separately approved
- no scanning/folder crawling/file indexing/OCR/embeddings/vector database unless separately approved
- no Drive/NAS/iCloud resolution unless separately approved

## Validation Expectations

```bash
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
```

## Non-Activation Confirmation

Documentation/status only. Curriculum Builder static source registry plan is Markdown-only planning text. No scanning, folder crawling, file indexing, OCR, embeddings, vector database, Drive/NAS/iCloud resolution, APIs, network calls, OAuth, automation, lesson generation, generated drafts, parsing, curriculum file ingestion, RAG, student data, schema files, validators, registry data files, or runtime behavior. Registry fields are metadata/reference-only planning placeholders.
