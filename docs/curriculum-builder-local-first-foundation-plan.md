# Curriculum Builder Local-First Foundation Plan

## Purpose

Curriculum Builder / Curriculum Library is the future foundation for organizing curriculum resources for Teacher Workstation. This plan adapts a Curriculum Intelligence Platform concept into a local-first, metadata-oriented registry model that teachers can audit and approve in small phases.

This PR adds documentation and read-only status only. It does not create an active database, schema file, crawler, importer, scanner, parser, or generator.

## Strategic Decision

The workstation will use existing storage first:

- **Google Drive** for the active school/curriculum working library
- **NAS** for archive, backup, and large curriculum vault storage
- **iCloud** as optional convenience sync where useful
- **local folders** where direct filesystem access is appropriate

Raw curriculum files remain in their source storage locations. Teacher Workstation must not duplicate every raw curriculum file into paid hosted storage. There is no Supabase Storage requirement for raw curriculum files and no paid storage dependency for this foundation.

## Source-Reference Model

The workstation stores metadata and references, not paid duplicate copies of all raw files.

Example metadata fields a future registry may track:

| Field | Purpose |
| --- | --- |
| `source_system` | Where the file lives (Google Drive, NAS, iCloud, local folders). |
| `source_path_or_url` | Stable reference to the source location. |
| `source_label` | Human-readable source label for review. |
| `title` | Resource title for discovery and review. |
| `subject` | Subject area label. |
| `grade` | Grade or level label. |
| `unit` | Unit label within a course. |
| `lesson` | Lesson label within a unit. |
| `topic` | Topic or subtopic label. |
| `resource_type` | Worksheet, test, study guide, presentation, textbook section, pacing link, etc. |
| `teacher_only` | Whether the resource is teacher-only. |
| `student_facing` | Whether the resource may be student-facing when approved. |
| `review_status` | Human review state for the reference record. |
| `content_hash` | Optional static hash marker for change detection planning. |
| `modified_at` | Last known modified timestamp from source metadata. |
| `notes` | Teacher review notes about the reference, not generated lesson content. |
| `linked_pacing_item` | Optional pacing-guide link reference. |
| `linked_canvas_item` | Optional Canvas item reference for future planning only. |
| `linked_lesson_template` | Optional link to a lesson-planning placeholder template reference. |

This table is planning documentation only. No registry records are created by this PR.

## Local Curriculum Registry Concept

The future registry is a local-first metadata registry. It records where curriculum resources live, how they are labeled, and how they relate to pacing, Canvas, and lesson-planning placeholders.

This PR does not create:

- an active database
- a live schema file
- a crawler or importer
- a scanner or parser
- a generator
- sync jobs or background workers

## Teacher Workstation Future Use

Future lesson-planning workflows may reference the registry to find approved resources, teacher-only materials, worksheets, tests, study guides, presentations, textbook sections, and pacing links.

No real lesson generation is activated by this foundation. Generated lesson briefs, generated lesson drafts, and real review notes remain out of scope until separately approved.

## Chief of Staff Future Use

Chief of Staff may eventually check whether curriculum registry docs, source references, safety boundaries, and readiness status exist.

Chief of Staff remains a status/orchestration/reference layer. In current practice, Chief of Staff status commands are read-only proof surfaces that report PASS/WARN/FAIL only; they do not orchestrate implementation, activate features, or modify repository state. Chief of Staff does not own curriculum files and does not store raw curriculum copies.

Future registry records may track source references, optional content hashes (planning only), review status, planning status, and relationships between resources.

## Safety Boundaries

Prohibited current capabilities:

- no document scanning
- no folder scanning
- no file indexing
- no OCR
- no embeddings
- no vector database
- no lesson generation
- no generated lesson briefs
- no generated lesson drafts
- no real review notes
- no student data
- no network calls
- no APIs
- no OAuth
- no automation
- no live integrations
- no background jobs
- no scheduler
- no Google Drive API activation
- no NAS crawler
- no iCloud crawler
- no Canvas API activation

## Future Phases

Each phase must remain small, local-first, and auditable. Later phases require separate explicit approval.

### Phase 0 — Documentation/status foundation only

May add planning docs and read-only status checks.

Must not activate scanning, indexing, OCR, embeddings, APIs, generation, jobs, sync, or integrations.

Future registry work must start manual/static (human-authored planning records and doc-only samples) before any automation or connectors.

### Phase 1 — Static source storage strategy docs

May document Google Drive, NAS, iCloud, and local folders usage patterns.

Must not crawl, sync, or import files.

### Phase 2 — Static registry field planning

May define registry field inventories and safety-flag planning.

Must not create a live schema or validator.

### Phase 3 — Manual sample registry planning only

May add fictional or manually authored sample registry planning entries.

Must not read user curriculum files or create real registry records.

### Phase 4 — Read-only local status checks

May add static status scripts that verify docs and safety markers only.

Must not scan folders or index files.

### Phase 5 — Future connector planning only, if explicitly approved

May document connector boundaries for Google Drive, NAS, iCloud, or Canvas.

Must not activate OAuth, APIs, network calls, or live integrations.

### Phase 6 — Future metadata registry implementation, if explicitly approved

May implement a local metadata registry after field planning and safety review.

Must not activate lesson generation, OCR, embeddings, vector search, or background jobs without separate approval.

## Non-Goals

This foundation is not:

- a hosted Curriculum Intelligence Platform build
- a Supabase Storage migration for raw curriculum files
- an OCR or indexing pipeline
- a vector search system
- a lesson-generation system
- a network-connected sync service

## Acceptance Criteria

This PR is complete when:

- `docs/curriculum-builder-local-first-foundation-plan.md` exists and documents the local-first source-reference model
- the plan names Google Drive, NAS, iCloud, and local folders as storage sources
- the plan states that metadata and references are stored, not paid duplicate copies of all raw files
- the plan states Chief of Staff is a status/orchestration/reference layer and does not own curriculum files
- the plan clarifies Chief of Staff status commands are read-only proof surfaces that report PASS/WARN/FAIL only and do not orchestrate implementation
- the plan states future lesson-planning workflows may reference the registry without activating generation
- the plan lists prohibited capabilities including no document scanning, no folder scanning, no file indexing, no OCR, no embeddings, no vector database, no lesson generation, no student data, and no network calls
- `scripts/curriculum-builder-foundation-status.sh` provides read-only PASS/WARN/FAIL verification of the plan doc
- `bin/chief-of-staff --curriculum-builder-foundation-status` calls the status script additively
- existing commands, checks, and PASS/WARN/FAIL semantics remain preserved

## Related Verification Commands

```bash
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
```
