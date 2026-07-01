# Curriculum Resource Registry Plan

## Purpose

This document defines the future metadata-only Curriculum Resource Registry for the local-first Curriculum Builder / Curriculum Library. It expands the foundation plan and source storage strategy with a registry field and status planning model only.

This is a planning/status document only. It does not create an active schema, database, migration, importer, scanner, indexer, parser, crawler, or generator.

For the canonical manual/static registry field schema and fictional placeholder rows, see `docs/curriculum-builder-manual-registry-schema-plan.md`.

For rules governing a future fictional sample registry proof artifact, see `docs/curriculum-builder-manual-registry-sample-proof-plan.md`.

For the static fictional seven-row sample proof, see `docs/curriculum-builder-manual-registry-sample-proof.md`. For static validation checks, see `docs/curriculum-builder-static-sample-validation-checks.md`. For sample format policy, see `docs/curriculum-builder-sample-format-decision.md`. For future CSV placeholder planning, see `docs/curriculum-builder-csv-placeholder-sample-plan.md`.

For future static validation rules for the sample artifact, see `docs/curriculum-builder-static-sample-validation-plan.md`.

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

## Manual-First Registry Entry Workflow Note

This section is planning documentation only. It does not create an active schema, database table, migration, registry data file, validator, entry form, importer, scanner, indexer, crawler, parser, review workflow, approval workflow, automation, or generator.

### Purpose

Future curriculum registry entries should begin as manually recorded metadata references. The teacher identifies the resource and records its source reference. Teacher Workstation stores metadata and references only. Raw files remain in Google Drive, NAS, iCloud, or local folders.

This workflow protects against accidental scanning, indexing, copying, or generated lesson behavior.

### Manual Entry Stages

1. **Identify Resource**
   - Teacher identifies a curriculum resource.
   - No scanning, no crawling, and no automatic discovery.

2. **Record Source Reference**
   - Teacher manually records `source_system`, `source_label`, and `source_path_or_url`.
   - No API calls, no OAuth, no network calls, and no Drive/NAS/iCloud crawlers.

3. **Add Classification Metadata**
   - Teacher manually records title, subject, grade, course, unit, lesson, topic, and `resource_type`.
   - No OCR, no parsing, no embeddings, and no file reads.

4. **Mark Safety Boundaries**
   - Teacher manually records `teacher_only`, `student_facing`, `answer_key`, `assessment_related`, `contains_student_data`, and `external_sharing_allowed` values.
   - Conservative defaults should apply in future implementation.

5. **Mark Review and Approval Status**
   - Teacher manually records `review_status`, `approval_status`, `usage_status`, `metadata_status`, `safety_status`, and `activation_status`.
   - no active review workflow, no active approval workflow, no real review notes, and no automated safety classifier.

6. **Link Future Relationships**
   - Teacher may later link pacing items, lesson templates, Canvas export references, or related resources if explicitly approved.
   - No Canvas API activation and no live integrations.

7. **Reference in Teacher Workstation Later**
   - Future lesson-planning workflows may reference approved metadata.
   - No generated lesson briefs, no generated lesson drafts, and no real lesson generation in this phase.

8. **Report Readiness Through Chief of Staff**
   - Chief of Staff may report planning/status readiness.
   - Chief of Staff does not own raw curriculum files and does not scan, index, or generate content.

### Manual Entry Field Order

Recommended future manual entry order (ordering recommendation only, not a schema):

1. `id`
2. `title`
3. `source_system`
4. `source_label`
5. `source_path_or_url`
6. `source_reference_type`
7. `resource_type`
8. `subject`
9. `grade`
10. `course`
11. `unit`
12. `lesson`
13. `topic`
14. `teacher_only`
15. `student_facing`
16. `answer_key`
17. `assessment_related`
18. `contains_student_data`
19. `review_status`
20. `approval_status`
21. `usage_status`
22. `metadata_status`
23. `safety_status`
24. `activation_status`
25. `notes`
26. `safety_notes`

### Conservative Defaults

Planning-only future defaults:

- `teacher_only`: unknown or true for sensitive resource types
- `student_facing`: false or unknown until explicitly reviewed
- `answer_key`: unknown unless manually marked
- `assessment_related`: unknown unless manually marked
- `contains_student_data`: false
- `external_sharing_allowed`: false or unknown
- `review_status`: not_reviewed
- `approval_status`: not_approved
- `usage_status`: draft or archive until manually approved
- `metadata_status`: incomplete
- `safety_status`: unchecked
- `activation_status`: planning_only

### Manual-First Rules

- Manual entry is not scanning.
- Manual entry is not indexing.
- Manual entry is not OCR.
- Manual entry is not embeddings.
- Manual entry is not a connector.
- Manual entry is not a file import.
- Manual entry is not a lesson generator.
- Manual entry is not a review workflow.
- Manual entry is not a student-data workflow.
- Manual entry must not require network calls, APIs, OAuth, background jobs, or live integrations.

### Future Human Review Expectations

- Student-facing approval should require explicit human review later.
- Teacher-only material should remain teacher-only unless reviewed.
- Answer keys and assessments should default toward restricted teacher-only use.
- Restricted, blocked, retired, or do_not_use resources should not be available for future lesson-planning use.
- Any future review notes must be explicitly approved in a later PR and must not contain student data.

### Explicit Non-Activation

This manual-entry workflow note does not add:

- active schema
- database tables
- migrations
- registry data files
- sample real curriculum resources
- validators
- entry forms
- new commands
- review workflows
- approval workflows
- real review notes
- automated safety classifiers
- importers
- scanners
- crawlers
- parsers
- file reads
- hashing
- OCR
- embeddings
- vector search
- APIs
- OAuth
- network calls
- automation
- background jobs
- generated lesson briefs
- generated lesson drafts
- student data
- live integrations

## Metadata-Only Backup and Export Planning Note

This section is planning documentation only. It does not create an active schema, database table, migration, registry data file, backup script, export script, archive bundle, file cache, importer, scanner, indexer, crawler, parser, review workflow, approval workflow, automation, or generator.

### Purpose

Future backup/export work should protect curriculum registry metadata and source references. Metadata backups/exports should help portability, auditability, disaster recovery, and human review.

Raw curriculum files should remain in Google Drive, NAS, iCloud, or local folders. Teacher Workstation should not create paid duplicate storage for every raw curriculum file.

Chief of Staff may eventually report whether metadata backup/export planning exists, but it should not own raw files or perform backups now.

### Metadata-Only Scope

Future backup/export scope is metadata only. Planning fields may include:

- `id`, `title`
- `source_system`, `source_label`, `source_path_or_url`, `source_reference_type`
- `resource_type`, `subject`, `grade`, `course`, `unit`, `lesson`, `topic`
- `teacher_only`, `student_facing`, `answer_key`, `assessment_related`, `contains_student_data`
- `review_status`, `approval_status`, `usage_status`, `metadata_status`, `safety_status`, `activation_status`
- `linked_pacing_item`, `linked_lesson_template`, `linked_canvas_item`
- `notes`, `safety_notes`

This is not a data file and not an export format in this PR. Exports would preserve source references only, not raw file contents.

### Explicitly Out of Scope

Future metadata backup/export planning does not include:

- copying raw curriculum files
- uploading files to Supabase Storage
- mirroring Google Drive
- mirroring NAS folders
- mirroring iCloud folders
- creating hidden file caches
- exporting student data
- exporting generated lesson briefs
- exporting generated lesson drafts
- exporting real review notes
- reading files
- hashing files
- scanning folders
- indexing folders
- OCR
- embeddings
- vector search
- API pulls
- OAuth flows
- background jobs
- scheduled sync

### Future Export Shape Options

Planning-only export shape options (metadata only, no raw files, no student data, requires explicit future approval before implementation):

| Option | Planning status | Notes |
| --- | --- | --- |
| Markdown summary export | planning only | Human-readable metadata summary for review. |
| CSV metadata export | planning only | Spreadsheet-friendly metadata backup. |
| JSON metadata export | planning only | Structured metadata backup. |
| SQLite metadata backup | planning only | Local-first metadata store option for later. |
| ZIP bundle for metadata-only export artifacts | planning only | Metadata-only archive bundle planning; no raw files. |

### Future Backup Destinations

Planning-only backup destination options:

- local folder backup for metadata only
- NAS metadata backup folder
- Google Drive metadata backup folder
- iCloud metadata backup folder
- repo-excluded local export folder

Destination planning does not activate any file writes. Destination planning does not activate APIs, OAuth, network calls, sync, or automation. Raw curriculum files remain in their source storage.

### Future Export Safety Rules

- metadata exports must not contain student data.
- metadata exports must not include raw curriculum file contents.
- metadata exports must not include generated lesson briefs or lesson drafts.
- metadata exports must not include real review notes unless explicitly approved later.
- `source_path_or_url` values should be treated as sensitive operational metadata.
- `teacher_only`, `answer_key`, `assessment_related`, `restricted`, `blocked`, `retired`, and `do_not_use` statuses must be preserved.
- metadata exports should preserve safety/status fields.
- future exports should be manually triggered only if explicitly approved.
- no scheduled exports or background jobs are active now.

### Relationship to Teacher Workstation

Teacher Workstation may later use metadata backup/export for portability and auditability. Future lesson-planning workflows may reference registry metadata, but not from this PR.

This PR does not create lesson briefs, lesson drafts, or generated lessons.

### Relationship to Chief of Staff

Chief of Staff may eventually report whether metadata backup/export planning is present. Chief of Staff may eventually verify that backup/export boundaries are documented.

Chief of Staff does not back up raw curriculum files. Chief of Staff does not copy files, scan folders, index files, call APIs, or run scheduled exports.

### Explicit Non-Activation

This metadata backup/export planning note does not add:

- active schema
- database tables
- migrations
- registry data files
- no backup scripts
- no export scripts
- no archive bundles
- no file caches
- no raw file copying
- no Drive mirroring
- no NAS mirroring
- no iCloud mirroring
- validators
- entry forms
- new commands
- review workflows
- approval workflows
- real review notes
- automated safety classifiers
- importers
- scanners
- crawlers
- parsers
- no file reads
- no hashing
- no scanning
- no indexing
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
- no live integrations

## Local Registry Validator Planning Note

This section is planning documentation only. It does not create an active validator, schema, database table, migration, registry data file, CLI command, importer, scanner, indexer, crawler, parser, file reader, hashing process, review workflow, approval workflow, automation, or generator.

### Purpose

A future local validator may eventually check metadata-only registry records for completeness, safety boundaries, and planning readiness. The future validator should operate only on explicitly approved registry metadata records.

The future validator must not scan folders, read curriculum files, crawl storage, call APIs, generate hashes, perform OCR, create embeddings, or generate lessons. This PR only documents future expectations. There is no active validator in this PR.

### Future Validator Scope

Planning-only future validator scope may include:

- required metadata fields
- `source_system` allowed values
- `resource_type` allowed values
- `teacher_only` and `student_facing` boundary consistency
- `answer_key` and `assessment_related` safety defaults
- `contains_student_data` prohibited/default false posture
- `review_status` allowed values
- `approval_status` allowed values
- `usage_status` allowed values
- `metadata_status` allowed values
- `safety_status` allowed values
- `activation_status` allowed values
- linked reference shape checks
- `notes` and `safety_notes` presence/absence expectations
- metadata-only backup/export compatibility

No validator is implemented in this PR.

### Future Required Field Expectations

Planning-only future required fields:

- `id`
- `title`
- `source_system`
- `source_path_or_url`
- `source_reference_type`
- `resource_type`
- `teacher_only`
- `student_facing`
- `answer_key`
- `assessment_related`
- `contains_student_data`
- `review_status`
- `approval_status`
- `usage_status`
- `metadata_status`
- `safety_status`
- `activation_status`

These are future validation expectations only. This PR does not create a schema. This PR does not create registry records. This PR does not validate files.

### Future Allowed Value Checks

A future validator may check allowed values for:

- `source_system`
- `resource_type`
- `review_status`
- `approval_status`
- `usage_status`
- `metadata_status`
- `safety_status`
- `activation_status`

Expected values are already defined elsewhere in this registry plan.

### Future Safety Consistency Checks

Planning-only checks:

- `contains_student_data` should be false for registry records.
- `answer_key` true should require `teacher_only` true.
- `assessment_related` true should default toward `teacher_only` true.
- `approved_student_facing` should require `student_facing` true and human review in a future implementation.
- `restricted`, `blocked`, `retired`, or `do_not_use` should prevent future lesson-planning use.
- `external_sharing_allowed` should be false or unknown unless explicitly approved.
- `activation_status` should remain `planning_only` until a future implementation is explicitly approved.

### Future Reference Shape Checks

Planning-only checks:

- source references should point to existing source storage conceptually.
- `source_path_or_url` should be treated as sensitive operational metadata.
- `linked_pacing_item`, `linked_lesson_template`, `linked_canvas_item`, and `related_resource_ids` should remain metadata references only.
- future validators must not dereference links, call APIs, scan folders, read files, or verify remote availability unless explicitly approved later.

### Future PASS/WARN/FAIL Semantics

Planning-only validator output semantics for a future local validator:

- **PASS**: required metadata and safety boundaries are present and internally consistent.
- **WARN**: metadata is incomplete, stale, unknown, or needs human review, but does not violate hard safety boundaries.
- **FAIL**: metadata violates hard safety boundaries, includes prohibited student data, attempts raw file ownership, or implies active scanning/indexing/generation behavior.

This does not alter existing PASS/WARN/FAIL behavior. This does not add a command. This does not add dashboard checks. There are no new command and no dashboard checks in this note.

### Validator Non-Goals

A future validator must not:

- scan folders
- index files
- read curriculum files
- hash files unless explicitly approved
- perform OCR
- create embeddings
- call Google Drive APIs
- call Canvas APIs
- crawl NAS/iCloud/local folders
- generate lesson briefs
- generate lesson drafts
- create review notes
- process student data
- perform network calls
- run background jobs
- run scheduled jobs
- automate approval decisions

### Relationship to Teacher Workstation

Teacher Workstation may later use validator results to understand metadata readiness. Future lesson-planning workflows may only reference approved metadata if explicitly implemented later.

No lesson generation is activated by this note.

### Relationship to Chief of Staff

Chief of Staff may eventually report future validator readiness. Chief of Staff may eventually surface PASS/WARN/FAIL status from a local validator if explicitly approved.

Chief of Staff does not validate raw files, own files, scan folders, call APIs, or generate content in this phase.

### Explicit Non-Activation

This validator planning note does not add:

- active validators
- no active schema
- database tables
- migrations
- no registry data file
- sample real curriculum resources
- backup scripts
- export scripts
- archive bundles
- file caches
- raw file copying
- Drive mirroring
- NAS mirroring
- iCloud mirroring
- entry forms
- no new command
- review workflows
- approval workflows
- real review notes
- automated safety classifiers
- importers
- scanners
- crawlers
- parsers
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
- no live integrations

There is no active validator and no active schema in this note.

## Placeholder Metadata Shape Note

This section is planning documentation only. It uses fake placeholder examples only. It does not create an active schema, database table, migration, registry data file, seed data, real curriculum resource record, validator, entry form, importer, scanner, indexer, crawler, parser, file reader, hashing process, review workflow, approval workflow, automation, or generator.

### Purpose

This note shows the future shape of metadata-only registry records. Examples are fake placeholders only. Raw curriculum files remain in Google Drive, NAS, iCloud, or local folders. Teacher Workstation stores references and metadata only.

Chief of Staff may later report readiness/status only. This PR does not create registry data or implementation behavior.

### Placeholder Record Shape

```json
{
  "id": "placeholder-resource-001",
  "title": "Placeholder Resource Title",
  "display_title": "Placeholder Display Title",
  "description": "Fake placeholder description for planning only.",
  "source_system": "manual_reference",
  "source_label": "Placeholder Source Label",
  "source_path_or_url": "placeholder://source/reference",
  "source_reference_type": "placeholder_reference",
  "source_owner": "placeholder_owner",
  "source_scope": "planning_only",
  "resource_type": "other",
  "subject": "placeholder_subject",
  "grade": "placeholder_grade",
  "course": "placeholder_course",
  "unit": "placeholder_unit",
  "lesson": "placeholder_lesson",
  "topic": "placeholder_topic",
  "standard_refs": [],
  "linked_pacing_item": null,
  "linked_lesson_template": null,
  "linked_canvas_item": null,
  "related_resource_ids": [],
  "prerequisite_resource_ids": [],
  "teacher_only": "unknown",
  "student_facing": "unknown",
  "answer_key": "unknown",
  "assessment_related": "unknown",
  "contains_student_data": false,
  "external_sharing_allowed": "unknown",
  "review_status": "not_reviewed",
  "approval_status": "not_approved",
  "usage_status": "draft",
  "metadata_status": "incomplete",
  "safety_status": "unchecked",
  "activation_status": "planning_only",
  "content_hash": null,
  "hash_algorithm": null,
  "modified_at": null,
  "last_verified_at": null,
  "notes": "Fake placeholder metadata note.",
  "safety_notes": "Fake placeholder safety note."
}
```

- This is not a schema.
- This is not a registry data file.
- This is not seed data.
- This is not a real curriculum resource.
- This is not validated or consumed by any command.
- This does not activate file reads, hashing, scanning, indexing, APIs, OAuth, automation, or generation.

### Placeholder CSV Column Shape

Placeholder column shape only (not an export format, not an import format, not a registry file):

| Column | Planning purpose |
| --- | --- |
| id | Stable placeholder record id |
| title | Placeholder title |
| source_system | Placeholder source system |
| source_label | Placeholder source label |
| source_path_or_url | Placeholder source reference |
| source_reference_type | Placeholder reference type |
| resource_type | Placeholder resource type |
| subject | Placeholder subject |
| grade | Placeholder grade |
| course | Placeholder course |
| unit | Placeholder unit |
| lesson | Placeholder lesson |
| topic | Placeholder topic |
| teacher_only | Placeholder teacher-only marker |
| student_facing | Placeholder student-facing marker |
| answer_key | Placeholder answer-key marker |
| assessment_related | Placeholder assessment marker |
| contains_student_data | Placeholder student-data marker |
| review_status | Placeholder review status |
| approval_status | Placeholder approval status |
| usage_status | Placeholder usage status |
| metadata_status | Placeholder metadata status |
| safety_status | Placeholder safety status |
| activation_status | Placeholder activation status |
| notes | Placeholder notes |
| safety_notes | Placeholder safety notes |

### Placeholder Status Posture

Default fake example posture:

- `review_status`: not_reviewed
- `approval_status`: not_approved
- `usage_status`: draft
- `metadata_status`: incomplete
- `safety_status`: unchecked
- `activation_status`: planning_only
- `contains_student_data`: false
- `teacher_only`: unknown
- `student_facing`: unknown

Placeholder status values should remain conservative. Placeholder records must not imply approval. Placeholder records must not imply student-facing use. Placeholder records must not imply lesson-planning activation.

### Placeholder Safety Rules

- Fake placeholder records must not contain student data.
- Fake placeholder records must not include real file paths, real Drive links, real NAS paths, real iCloud paths, real Canvas IDs, or real curriculum resource names.
- Fake placeholder records must not include generated lesson briefs, generated lesson drafts, or real review notes.
- Placeholder examples are documentation examples only.
- Placeholder examples must not be consumed by runtime code.

### Future Implementation Guardrails

- A future registry implementation must be approved in a later PR.
- A future schema must be approved in a later PR.
- A future data file must be approved in a later PR.
- A future validator must be approved in a later PR.
- A future export/import path must be approved in a later PR.
- Any future sample records must use fake placeholder data unless explicitly approved.
- Any future real registry record must avoid student data and preserve teacher-only/student-facing boundaries.

### Relationship to Teacher Workstation

Teacher Workstation may later use a metadata shape like this for local-first curriculum registry records. Future lesson-planning workflows may reference approved metadata later.

This note does not generate lessons, lesson briefs, or lesson drafts.

### Relationship to Chief of Staff

Chief of Staff may eventually report whether placeholder metadata shape planning exists. Chief of Staff may eventually surface readiness for a future registry implementation if explicitly approved.

Chief of Staff does not own raw curriculum files. Chief of Staff does not consume placeholder examples as data. Chief of Staff does not scan, index, call APIs, validate files, or generate content in this phase.

### Explicit Non-Activation

This placeholder metadata shape note does not add:

- no active schema
- database tables
- migrations
- no registry data files
- no seed data
- no real curriculum resource records
- backup scripts
- export scripts
- archive bundles
- file caches
- raw file copying
- Drive mirroring
- NAS mirroring
- iCloud mirroring
- no active validators
- entry forms
- no new commands
- review workflows
- approval workflows
- real review notes
- automated safety classifiers
- importers
- scanners
- crawlers
- parsers
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
- no live integrations

## Registry Implementation Approval Gate Note

This section is planning documentation only. It defines the explicit approval gate required before any Curriculum Resource Registry implementation work may begin. It does not create an active schema, database table, migration, registry data file, seed data, sample record, real curriculum resource record, validator, entry form, command, importer, exporter, backup script, scanner, indexer, crawler, parser, file reader, hashing process, review workflow, approval workflow, automation, connector, API integration, or generator.

### Purpose

The current Curriculum Resource Registry work remains documentation/status-only. The planning stack defines future concepts, not active behavior.

Any implementation step must be explicitly approved in a later PR. The approval gate protects local-first boundaries, raw-file ownership boundaries, student-data boundaries, and no-generation boundaries.

### Implementation Requires Explicit Future Approval

These future changes require a separate explicit approval PR before implementation:

- active schema file
- database table
- migration
- registry JSON/CSV/YAML data file
- fake placeholder data file
- real curriculum resource record
- sample record
- validator implementation
- CLI command
- dashboard section
- entry form
- import script
- export script
- backup script
- archive bundle
- file cache
- file read
- hashing process
- scanner
- crawler
- parser
- indexer
- OCR
- embeddings
- vector search
- Google Drive API
- Canvas API
- NAS crawler
- iCloud crawler
- OAuth
- network call
- automation
- background job
- scheduler
- review workflow
- approval workflow
- generated review notes
- lesson brief generation
- lesson draft generation
- lesson generation
- student-facing output

### Required Future PR Questions

A future implementation PR must answer these questions before approval:

1. What exact behavior is being activated?
2. What files, commands, scripts, or data artifacts are being added?
3. Does it read any curriculum files?
4. Does it scan or index folders?
5. Does it call any network service or API?
6. Does it require OAuth?
7. Does it create, copy, cache, export, or back up raw curriculum files?
8. Does it create registry records?
9. Are records fake placeholders or real curriculum resources?
10. Does it process or store student data?
11. Does it generate lesson briefs, lesson drafts, review notes, or student-facing content?
12. How does it preserve teacher-only, answer-key, assessment, restricted, blocked, retired, and do_not_use boundaries?
13. How does it preserve existing PASS/WARN/FAIL semantics?
14. How will it be tested locally without network calls unless explicitly approved?
15. What is the rollback path?

### Approval Categories

Planning-only approval categories (planning vocabulary only; they do not activate behavior):

- `docs_only_approved`
- `schema_planning_requested`
- `schema_implementation_requested`
- `metadata_file_requested`
- `fake_placeholder_records_requested`
- `real_registry_records_requested`
- `validator_requested`
- `command_requested`
- `export_requested`
- `backup_requested`
- `connector_requested`
- `lesson_planning_reference_requested`
- `generation_requested`
- `blocked_without_explicit_approval`

### Default Decision Rules

- Documentation-only additions are allowed within the current PR pattern.
- Status-script marker checks are allowed only when read-only and repo-local.
- Any schema/data/validator/command/runtime behavior is blocked without explicit approval.
- Any file read, hashing, scanning, indexing, OCR, embeddings, API, OAuth, connector, automation, or generation behavior is blocked without explicit approval.
- Real curriculum resource records are blocked without explicit approval.
- Student data is blocked.
- Raw file copying, Drive mirroring, NAS mirroring, iCloud mirroring, and hidden file caches are blocked.
- Teacher Workstation may reference planning docs only in this phase.
- Chief of Staff may report planning/status readiness only in this phase.

### Future Readiness Checklist

Planning-only checklist for future implementation readiness:

- storage boundaries documented
- metadata/reference model documented
- registry field inventory documented
- safety/status values documented
- manual-entry workflow documented
- metadata backup/export planning documented
- validator planning documented
- placeholder metadata shape documented
- approval gate documented
- no student data
- no raw file ownership transfer
- no generation behavior
- no network/API/OAuth behavior unless explicitly approved
- rollback path defined in the future PR
- validation commands defined in the future PR

### Relationship to Teacher Workstation

Teacher Workstation may eventually use the registry only after an explicit implementation PR. Future lesson-planning reference behavior must be approved separately.

Future lesson generation remains out of scope unless explicitly approved. Current behavior remains planning/status only.

### Relationship to Chief of Staff

Chief of Staff may continue to report planning/status readiness. Chief of Staff does not own raw curriculum files. Chief of Staff does not consume placeholder metadata examples as data.

Chief of Staff does not validate real registry records in this phase. Chief of Staff does not scan, index, call APIs, back up files, or generate content in this phase.

### Explicit Non-Activation

This implementation approval gate note does not add:

- no active schema
- database tables
- migrations
- no registry data files
- no fake registry data files
- seed data
- no sample records
- no real curriculum resource records
- backup scripts
- export scripts
- archive bundles
- file caches
- raw file copying
- Drive mirroring
- NAS mirroring
- iCloud mirroring
- no active validators
- entry forms
- no new commands
- no dashboard sections
- review workflows
- approval workflows
- real review notes
- automated safety classifiers
- importers
- scanners
- crawlers
- parsers
- indexers
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
- no schedulers
- no generated lesson briefs
- no generated lesson drafts
- no lesson generation
- no student data
- no live integrations

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
