# Curriculum Resource Registry Plan

## Purpose

This document defines the future metadata-only Curriculum Resource Registry for the local-first Curriculum Builder / Curriculum Library. It expands the foundation plan and source storage strategy with a registry field and status planning model only.

This is a planning/status document only. It does not create an active schema, database, migration, importer, scanner, indexer, parser, crawler, or generator.

## Core Decision

The registry will track metadata, references, statuses, and relationships. Raw curriculum files remain in Google Drive, NAS, iCloud, or local folders.

This PR does not create:

- an active schema file
- an active database
- migrations
- seed data
- registry JSON/CSV/YAML data files
- sample real curriculum resources

## Registry Role

The registry is the future bridge between:

- source storage
- curriculum resources
- pacing references
- lesson-planning templates
- Teacher Workstation workflows
- Chief of Staff readiness/status reporting

The registry is not a file store and not a lesson generator. It is a metadata-only planning concept for later manual-first implementation.

## Future Registry Record Concept

A future registry record may combine identity, source reference, curriculum labels, linkage fields, review fields, and safety markers. All fields below are planning only.

| Field | Purpose | Example shape | Future required | Current status |
| --- | --- | --- | --- | --- |
| `id` | Stable registry identifier. | `curriculum-resource-0001` | likely yes | planning only |
| `title` | Human-readable resource title. | `Unit 3 Fractions Practice` | likely yes | planning only |
| `source_system` | Where the file lives. | `google_drive` | likely yes | planning only |
| `source_label` | Human-readable source label. | `7th Math Drive Folder` | likely yes | planning only |
| `source_path_or_url` | Stable source reference. | Drive path or NAS path string | likely yes | planning only |
| `source_reference_type` | Reference style marker. | `manual_link`, `manual_path` | optional | planning only |
| `source_owner` | Stewardship label. | `teacher`, `department` | optional | planning only |
| `source_scope` | Active, archive, or local scope. | `active`, `archive` | optional | planning only |
| `resource_type` | Curriculum resource category. | `worksheet`, `assessment` | likely yes | planning only |
| `subject` | Subject label. | `math` | optional | planning only |
| `grade` | Grade or level label. | `7` | optional | planning only |
| `course` | Course label. | `Math 7` | optional | planning only |
| `unit` | Unit label. | `Unit 3` | optional | planning only |
| `lesson` | Lesson label. | `Lesson 5` | optional | planning only |
| `topic` | Topic label. | `fractions` | optional | planning only |
| `standard_refs` | Standards reference labels. | `TEKS 7.3A` | optional | planning only |
| `linked_pacing_item` | Pacing guide link reference. | pacing item id string | optional | planning only |
| `linked_lesson_template` | Lesson-planning placeholder link. | template id string | optional | planning only |
| `linked_canvas_item` | Canvas item reference for future planning. | canvas item id string | optional | planning only |
| `teacher_only` | Teacher-only boundary marker. | `true` / `false` | likely yes | planning only |
| `student_facing` | Student-facing boundary marker. | `true` / `false` | likely yes | planning only |
| `answer_key` | Answer-key marker. | `true` / `false` | optional | planning only |
| `assessment_related` | Assessment-related marker. | `true` / `false` | optional | planning only |
| `review_status` | Human review state. | `not_reviewed` | likely yes | planning only |
| `approval_status` | Approval planning state. | `metadata_only` | optional | planning only |
| `usage_status` | Usage planning state. | `active`, `retired` | optional | planning only |
| `content_hash` | Optional change-detection marker. | hash string | optional | planning only |
| `modified_at` | Last known modified timestamp. | ISO date string | optional | planning only |
| `last_verified_at` | Last manual verification timestamp. | ISO date string | optional | planning only |
| `notes` | Teacher notes about the reference. | free text | optional | planning only |
| `safety_notes` | Local-first safety reminders. | free text | optional | planning only |

No machine-readable schema file is created by this PR.

## Source System Values

Future `source_system` planning values:

- `google_drive`
- `nas`
- `icloud`
- `local_folder`
- `canvas_export`
- `manual_reference`

These are planning values only. They do not activate connectors, APIs, OAuth, or network calls.

## Resource Type Values

Future `resource_type` planning values:

- `textbook`
- `teacher_guide`
- `worksheet`
- `assessment`
- `quiz`
- `test`
- `study_guide`
- `presentation`
- `answer_key`
- `rubric`
- `project`
- `activity`
- `lab`
- `video_link`
- `external_reference`
- `other`

These are planning values only.

## Review and Safety Status Values

Future status planning values may include:

- `not_reviewed`
- `metadata_only`
- `teacher_reviewed`
- `approved_for_planning`
- `approved_student_facing`
- `teacher_only`
- `restricted`
- `retired`
- `needs_update`

No real review notes or approval workflows are created in this PR.

## Teacher-Only and Student-Facing Rules

- `teacher_only` resources must not be treated as `student_facing`.
- Answer keys and assessments should default to teacher-only in future implementation.
- `student_facing` should require explicit review/approval later.
- This PR does not process student data.

## Relationship to Teacher Workstation

Future Teacher Workstation use may include:

- lesson planning referencing approved resources later
- placeholder templates pointing to registry metadata later
- curriculum resources supporting planning decisions later

No lesson briefs, lesson drafts, or generated lessons are created now. No lesson generation is activated.

## Relationship to Chief of Staff

Future Chief of Staff use may include:

- checking whether registry planning docs exist
- reporting readiness and missing metadata boundaries later

Chief of Staff does not own raw curriculum files. Chief of Staff does not scan folders, index files, call APIs, or generate lessons.

## Manual-First Future Flow

A future manual-first flow may look like this:

1. Teacher identifies a curriculum resource.
2. Teacher records source reference manually.
3. Teacher adds metadata manually.
4. Teacher marks teacher-only/student-facing boundaries.
5. Teacher marks review/approval status.
6. Teacher Workstation references metadata later.
7. Chief of Staff reports readiness/status only.

This PR does not implement the flow.

## Explicit Non-Activation Statement

This PR does not add:

- schema files
- migrations
- database tables
- registry data files
- seed files
- fixtures containing real resources
- scanners
- importers
- crawlers
- sync jobs
- OCR
- embeddings
- vector search
- APIs
- OAuth
- network calls
- automation
- background jobs
- lesson generation
- generated lesson briefs
- generated lesson drafts
- real review notes
- student data

There is no active schema and no active database in this PR.

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

Each phase requires separate explicit approval.

### Phase 0 — Registry planning doc only

May add planning docs and read-only status checks.

Must not create schema files, databases, or registry data files.

### Phase 1 — Static registry field inventory note

May document field inventories and value lists.

Must not create an active schema or validator.

### Phase 2 — Static registry safety/status values note

May document safety and status value planning.

Must not activate review workflows.

### Phase 3 — Manual sample metadata shape, using fake placeholder data only, if explicitly approved

May add fictional sample metadata shapes.

Must not include real curriculum resources or student data.

### Phase 4 — Metadata-only backup/export planning, if explicitly approved

May document metadata export/backup boundaries.

Must not copy raw curriculum files into app storage by default.

### Phase 5 — Read-only local registry validator planning, if explicitly approved

May document static validator expectations.

Must not scan folders or index files.

### Phase 6 — Future local registry implementation, if explicitly approved

May implement a local metadata registry after planning and safety review.

Must not activate lesson generation, OCR, embeddings, vector search, or background jobs without separate approval.

## Acceptance Criteria

This PR is complete when:

- `docs/curriculum-resource-registry-plan.md` exists
- the metadata-only registry concept is explicit
- raw files remain in existing source storage (Google Drive, NAS, iCloud, local folders)
- Teacher Workstation and Chief of Staff relationships are defined
- the field inventory is planning only
- no active schema/database/importer/scanner/generator is created
- safety boundaries are explicit
- `scripts/curriculum-builder-foundation-status.sh` verifies the new doc with read-only PASS/WARN/FAIL checks

## Related Verification Commands

```bash
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
```
