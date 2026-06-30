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

## Static Registry Field Inventory Note

This section is planning documentation only. It does not create an active schema, database table, migration, validator, registry data file, importer, scanner, indexer, crawler, parser, or generator.

| Field | Group | Purpose | Future required status | Example allowed values or shape | Safety notes | Current activation status |
| --- | --- | --- | --- | --- | --- | --- |
| `id` | Identity | Stable registry record identifier. | required later | `curriculum-resource-0001` | Must not embed student data. | planning only |
| `title` | Identity | Primary human-readable title. | required later | `Unit 3 Fractions Practice` | Metadata label only. | planning only |
| `display_title` | Identity | Optional display override. | optional later | `Fractions Practice Set` | Must not imply generated lesson content. | planning only |
| `description` | Identity | Short metadata description. | optional later | free text | No student data. | planning only |
| `source_system` | Source reference | Source storage system marker. | required later | `google_drive`, `nas`, `icloud`, `local_folder` | Must match approved planning list. | planning only |
| `source_label` | Source reference | Human-readable source label. | required later | `7th Math Drive Folder` | Reference only. | planning only |
| `source_path_or_url` | Source reference | Stable source location reference. | required later | path or URL string | Must not copy raw files. | planning only |
| `source_reference_type` | Source reference | Reference style marker. | optional later | `manual_link`, `manual_path` | Manual-first only for now. | planning only |
| `source_owner` | Source reference | Stewardship label. | optional later | `teacher`, `department` | No student identifiers. | planning only |
| `source_scope` | Source reference | Active/archive/local scope. | optional later | `active`, `archive` | Planning label only. | planning only |
| `source_last_seen_at` | Source reference | Last manual source check timestamp. | optional later | ISO date string | No automatic file reads now. | planning only |
| `resource_type` | Classification | Curriculum resource category. | required later | `worksheet`, `assessment` | Planning value only. | planning only |
| `subject` | Classification | Subject label. | optional later | `math` | No generated curriculum claims. | planning only |
| `grade` | Classification | Grade or level label. | optional later | `7` | No student roster data. | planning only |
| `course` | Classification | Course label. | optional later | `Math 7` | Metadata only. | planning only |
| `unit` | Classification | Unit label. | optional later | `Unit 3` | Metadata only. | planning only |
| `lesson` | Classification | Lesson label. | optional later | `Lesson 5` | Metadata only. | planning only |
| `topic` | Classification | Topic label. | optional later | `fractions` | Metadata only. | planning only |
| `standard_refs` | Classification | Standards reference labels. | optional later | `TEKS 7.3A` | No auto-standard claims. | planning only |
| `linked_pacing_item` | Relationship | Pacing guide link reference. | optional later | pacing item id | Requires explicit approval later. | planning only |
| `linked_lesson_template` | Relationship | Lesson-planning placeholder link. | optional later | template id | Placeholder reference only. | planning only |
| `linked_canvas_item` | Relationship | Canvas export/item reference. | optional later | canvas item id | No Canvas API activation. | planning only |
| `related_resource_ids` | Relationship | Related registry record ids. | optional later | id list | Metadata links only. | planning only |
| `prerequisite_resource_ids` | Relationship | Prerequisite resource ids. | optional later | id list | Metadata links only. | planning only |
| `teacher_only` | Safety and access | Teacher-only boundary marker. | required later | `true` / `false` | Must not be treated as student-facing when true. | planning only |
| `student_facing` | Safety and access | Student-facing boundary marker. | required later | `true` / `false` | Requires explicit review later. | planning only |
| `answer_key` | Safety and access | Answer-key marker. | conditional later | `true` / `false` | Should default teacher-only later. | planning only |
| `assessment_related` | Safety and access | Assessment-related marker. | conditional later | `true` / `false` | Should default teacher-only later. | planning only |
| `contains_student_data` | Safety and access | Student-data boundary marker. | required later | `false` by default | Must remain false by default. | planning only |
| `external_sharing_allowed` | Safety and access | External sharing planning marker. | optional later | `true` / `false` | No live sharing integration now. | planning only |
| `review_status` | Review/status | Human review state. | required later | `not_reviewed` | No real review workflow now. | planning only |
| `approval_status` | Review/status | Approval planning state. | required later | `metadata_only` | No approval automation now. | planning only |
| `usage_status` | Review/status | Usage planning state. | optional later | `active`, `retired` | Metadata only. | planning only |
| `metadata_status` | Review/status | Metadata completeness marker. | optional later | `draft`, `complete` | Planning only. | planning only |
| `safety_status` | Review/status | Safety review marker. | optional later | `unchecked`, `reviewed` | Human review only later. | planning only |
| `last_verified_at` | Review/status | Last manual verification timestamp. | optional later | ISO date string | No automatic verification now. | planning only |
| `content_hash` | Integrity/reference | Optional change-detection marker. | optional later | hash string | no hashing now | planning only |
| `hash_algorithm` | Integrity/reference | Hash algorithm label for future use. | optional later | `sha256` | no hashing now | planning only |
| `modified_at` | Integrity/reference | Last known modified timestamp. | optional later | ISO date string | Manual metadata only. | planning only |
| `file_size_hint` | Integrity/reference | Optional size hint for planning. | optional later | byte count string | No file reads now. | planning only |
| `version_label` | Integrity/reference | Version or edition label. | optional later | `2024-edition` | Metadata only. | planning only |
| `notes` | Notes | Teacher metadata notes. | optional later | free text | No student data. | planning only |
| `safety_notes` | Notes | Safety boundary reminders. | optional later | free text | No real review notes. | planning only |
| `metadata_notes` | Notes | Metadata quality notes. | optional later | free text | Metadata only. | planning only |

### Field Group Rules

- **Identity fields** describe the registry record only.
- **Source reference fields** point to existing storage and must not copy raw files.
- **Classification fields** support future planning and discovery.
- **Relationship fields** connect resources to pacing, templates, Canvas exports, or other resources only after explicit approval.
- **Safety and access fields** protect teacher-only, assessment-related, answer-key, and student-facing boundaries.
- **Review/status fields** support human-readable readiness and approval tracking.
- **Integrity/reference fields** may support future manual verification, but do not activate hashing or file reads now.
- **Notes fields** are metadata notes only and must not contain student data or real review notes in this phase.

### Future Validation Expectations

Future validation is planning-only. Expected rules for a later separately approved implementation:

- future records should require `id`, `title`, `source_system`, `source_path_or_url`, `resource_type`, `teacher_only`, `student_facing`, `review_status`, and `approval_status`
- `teacher_only` and `student_facing` should not both be true without explicit future policy
- `answer_key` and `assessment_related` should default to teacher-only in a future implementation
- `approved_student_facing` should require `student_facing` true and teacher review later
- `contains_student_data` should remain false for curriculum registry records by default
- `source_system` values should remain from the approved planning list unless expanded by a future PR
- `content_hash` must not be generated unless hashing is explicitly approved later

### Explicit Non-Activation

This note does not add:

- active schema
- no database tables
- no registry data files
- no validators
- no importers
- no scanners
- no crawlers
- no parsers
- no file reads
- no hashing
- no OCR
- no embeddings
- no vector search
- no APIs
- no OAuth
- no network calls
- no automation
- no background jobs
- no generated lesson briefs
- no generated lesson drafts
- no real review notes
- no student data

There is no active schema in this note. This note does not create database tables, registry data files, validators, importers, scanners, crawlers, parsers, file reads, or hashing.

## Static Registry Safety and Status Values Note

This section is planning documentation only. It does not create an active schema, database table, migration, validator, registry data file, importer, scanner, indexer, crawler, parser, review workflow, approval workflow, or generator.

| Field | Planning values | Default future posture | Allowed future transitions | Safety rule | Current activation status |
| --- | --- | --- | --- | --- | --- |
| `teacher_only` | `true`, `false`, `unknown` | `unknown` until manually reviewed | `unknown` → `true` / `false` after review | Answer keys, assessments, restricted materials, and teacher guides should default toward teacher-only in future implementation. | planning only |
| `student_facing` | `true`, `false`, `unknown` | `false` or `unknown` until explicitly reviewed | `unknown` → `false` → `true` only after review | Student-facing use should require explicit future approval. | planning only |
| `answer_key` | `true`, `false`, `unknown` | `unknown` until manually reviewed | `unknown` → `true` should imply teacher-only | `answer_key` true should imply `teacher_only` true in future validation. | planning only |
| `assessment_related` | `true`, `false`, `unknown` | `unknown` until manually reviewed | `unknown` → `true` should default teacher-only | `assessment_related` true should default toward `teacher_only` true unless explicitly reviewed. | planning only |
| `contains_student_data` | `false`, `unknown`, `prohibited` | `false` | must remain `false` | Curriculum registry records must not contain student data. | planning only |
| `external_sharing_allowed` | `true`, `false`, `unknown` | `false` or `unknown` until explicit review | `unknown` → `false` → `true` only after review | External sharing must default to false or unknown until explicit review. | planning only |
| `review_status` | `not_reviewed`, `metadata_only`, `teacher_reviewed`, `needs_update`, `retired` | `not_reviewed` | toward `teacher_reviewed` after manual review | No automated review workflow in this phase. | planning only |
| `approval_status` | `not_approved`, `approved_for_planning`, `approved_student_facing`, `restricted`, `retired` | `not_approved` | toward `approved_for_planning` or `approved_student_facing` after review | `approved_student_facing` requires explicit future policy. | planning only |
| `usage_status` | `active`, `draft`, `archive`, `retired`, `do_not_use` | `draft` | toward `active` or `retired` after review | `do_not_use` blocks future lesson-planning use. | planning only |
| `metadata_status` | `incomplete`, `partial`, `complete`, `needs_verification` | `incomplete` | toward `complete` after manual metadata entry | Metadata completeness is manual only. | planning only |
| `safety_status` | `unchecked`, `safe_for_planning`, `teacher_only_restricted`, `student_facing_approved`, `restricted`, `blocked` | `unchecked` | toward reviewed states after manual review | `restricted` and `blocked` prevent future lesson-planning use. | planning only |
| `activation_status` | `planning_only`, `inactive`, `proposed`, `approved_for_future_build`, `active_later_only` | `planning_only` | toward `approved_for_future_build` only after separate PR | `planning_only` means documentation only and must not activate runtime behavior. | planning only |

### Safety Transition Rules

- `student_facing` must not become true without explicit future human review.
- `approved_student_facing` must not be used unless `student_facing` is true and review status is teacher-reviewed in a future implementation.
- `answer_key` true should require `teacher_only` true in future validation.
- `assessment_related` true should default to teacher-only in future validation.
- `contains_student_data` must remain false for curriculum registry records.
- `external_sharing_allowed` must default to false or unknown until explicit review.
- `restricted`, `blocked`, `retired`, or `do_not_use` statuses must prevent future lesson-planning use.
- `planning_only` means documentation only and must not activate runtime behavior.

### Teacher-Only and Student-Facing Boundary

- Teacher-only resources are not student-facing resources.
- Assessments, answer keys, restricted materials, and teacher guides need conservative defaults.
- Future planning can reference teacher-only materials for teacher preparation only.
- No current lesson generation or student-facing output is activated.

### Status Values Are Not Workflows

- These values are planning vocabulary only.
- This PR does not create an approval workflow.
- This PR does not create real review notes.
- This PR does not create a review UI.
- This PR does not create an automated safety classifier.
- This PR does not process curriculum files.
- This PR does not process student data.

### Explicit Non-Activation

This safety/status values note does not add:

- active schema
- no database tables
- no registry data files
- no validators
- no review workflows
- no approval workflows
- no real review notes
- no automated safety classifiers
- no importers
- no scanners
- no crawlers
- no parsers
- no file reads
- no hashing
- no OCR
- no embeddings
- no vector search
- no APIs
- no OAuth
- no network calls
- no automation
- no background jobs
- no generated lesson briefs
- no generated lesson drafts
- no student data

There is no active schema in this safety/status values note.

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
