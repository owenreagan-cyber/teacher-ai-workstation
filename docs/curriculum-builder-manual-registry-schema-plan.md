# Curriculum Builder Manual Registry Schema Plan

Last verified: 2026-06-30

## 1. Purpose

This document defines the planned **manual/static Curriculum Resource Registry schema** for Teacher Workstation. The schema describes how future registry records will reference curriculum resources by metadata, source location, review status, safety flags, and lesson/unit/pacing relationships.

This is a **future schema plan only**. It prepares bounded next-stage work so Teacher Workstation can eventually reference approved curriculum resources without duplicating raw files into the repo or app.

Planning path:

```text
canonical planning index
→ next-stage readiness audit
→ manual registry schema plan (this document)
→ manual registry sample proof plan
→ manual registry sample proof
→ future static sample validation planning
```

## 2. Non-Activation Statement

This document does **not**:

- create a live registry
- create a database, SQLite file, Postgres schema, or Supabase schema
- create a parser, importer, crawler, or indexer
- scan files or index folders
- read curriculum documents
- call APIs or use OAuth
- activate Google Drive, NAS, iCloud, Canvas, or any other integration
- generate lesson briefs, lesson drafts, or review notes
- use student data
- copy raw curriculum files into the repo or app-owned storage

Chief of Staff remains a read-only proof/status/reference surface. It does not own raw curriculum files.

## 3. Relationship to Existing Planning Stack

| Prior doc | Relationship |
| --- | --- |
| `docs/curriculum-builder-canonical-planning-index.md` | Canonical entry point and artifact map |
| `docs/curriculum-builder-next-stage-readiness-audit.md` | Next-stage transition note and safe PR categories |
| `docs/curriculum-builder-local-first-foundation-plan.md` | Local-first source-reference foundation |
| `docs/curriculum-source-storage-strategy.md` | Drive/NAS/iCloud/local folder ownership |
| `docs/curriculum-resource-registry-plan.md` | Broader registry concept, field inventory notes, workflows, validator planning |
| `docs/curriculum-builder-approval-gate.md` | Blocks implementation until explicit approval |

This schema plan **narrows** the registry field vocabulary into a single manual/static-first schema table. Where names differ from earlier planning docs, this plan is the canonical schema vocabulary for the next stage. Earlier docs remain valid for workflow, safety values, and approval gates.

**Name alignment notes:**

| This plan | Earlier planning synonym |
| --- | --- |
| `source_reference` | `source_path_or_url`, `source_label` (combined reference string) |
| `grade_band` | `grade` |
| `student_facing_allowed` | `student_facing` |
| `pacing_reference` | `linked_pacing_item` |
| `canvas_reference` | `linked_canvas_item` |

## 4. Manual/Static-First Registry Model

Future registry work must follow this order:

1. **Schema plan** (this document) — prose and tables only
2. **Manual sample/proof PR** — fictional doc-only placeholder rows; no live registry file
3. **Human-authored entries** — teacher manually creates records after explicit approval
4. **Static validator** — read-only PASS/WARN/FAIL checks on approved sample files only, if separately approved
5. **Connectors/automation** — blocked until separate approved PRs

No stage may skip ahead into file reads, scanning, OCR, embeddings, APIs, or generation.

Each record is created by **manual entry** (`created_by_manual_entry: true` in planning examples). No automatic ingestion.

## 5. Source Storage Model

Raw curriculum files remain in source storage:

| `source_system` value | Role |
| --- | --- |
| `google_drive` | Active working curriculum library |
| `nas` | Archive/vault and large curriculum storage |
| `icloud` | Optional convenience sync copies |
| `local_folder` | Manually managed local references only if explicitly approved |

Teacher Workstation stores **metadata, source references, optional content hashes (planning only), review status, planning status, and relationships** — not paid duplicate copies of every raw file.

`source_reference` is a stable planning string pointing at source storage (for example `gdrive://placeholder/sm5/textbook`). It is not a live URL and must not be resolved by automation in this phase.

## 6. Required Fields

| Field | Required | Summary |
| --- | --- | --- |
| `registry_id` | yes | Stable unique identifier for the registry record |
| `title` | yes | Human-readable resource title |
| `resource_type` | yes | Worksheet, test, study guide, slides, textbook section, pacing link, etc. |
| `source_system` | yes | `google_drive`, `nas`, `icloud`, or `local_folder` |
| `source_reference` | yes | Stable source-location reference string (not a live URL) |
| `source_reference_type` | yes | `file`, `folder`, `link`, `export_bundle`, `pacing_item` |
| `subject` | yes | Subject area label |
| `grade_band` | yes | Grade or level band label |
| `course` | yes | Course label within subject |
| `unit` | yes | Unit label within course |
| `lesson` | yes | Lesson label within unit |
| `pacing_reference` | yes | Pacing-guide reference or `none` placeholder |
| `teacher_only` | yes | `true`, `false`, or `unknown` |
| `student_facing_allowed` | yes | `true`, `false`, or `unknown` |
| `review_status` | yes | Human review state (see allowed values) |
| `approval_status` | yes | Approval planning state (see allowed values) |
| `local_first_safety_flags` | yes | Comma-separated or structured safety flag list |
| `notes` | yes | Teacher review notes (may be empty string in examples) |
| `created_by_manual_entry` | yes | Must be `true` for manual/static-first phase |
| `activation_status` | yes | `planning_only` until explicitly approved otherwise |

## 7. Optional Fields

| Field | Summary |
| --- | --- |
| `publisher` | Publisher label for textbooks or licensed materials |
| `edition` | Edition label |
| `isbn` | ISBN when applicable |
| `content_hash` | Optional hash marker for change detection planning only |
| `source_last_modified_at` | Last known modified timestamp from manual observation |
| `school_year` | School year label |
| `standard_reference` | Standards alignment reference string |
| `topic_tags` | Comma-separated topic labels |
| `skill_tags` | Comma-separated skill labels |
| `canvas_reference` | Optional Canvas item reference for future planning |
| `related_resources` | List of other `registry_id` values |
| `replacement_for` | Prior `registry_id` this record replaces |
| `superseded_by` | Successor `registry_id` |
| `copyright_notes` | Copyright or license notes |
| `access_notes` | Access restriction notes |

## 8. Reserved Future Fields

These fields may appear in schema planning but **must remain inactive placeholders** unless a later approved PR explicitly activates the capability:

| Field | Reserved for |
| --- | --- |
| `parsed_text_status` | Document text extraction (blocked) |
| `ocr_status` | OCR pipeline (blocked) |
| `embedding_status` | Embeddings / vector search (blocked) |
| `ai_summary_status` | AI-generated summaries (blocked) |
| `auto_classification_status` | Automatic classification (blocked) |
| `api_sync_status` | Connector/API sync state (blocked) |

Reserved fields must not be populated by automation in the manual/static-first phase.

## 9. Field Definitions

| Field | Definition |
| --- | --- |
| `registry_id` | Opaque stable ID (for example `cr-sm5-textbook-001`). Used for cross-references only in planning examples. |
| `title` | Display title for human review and future discovery. |
| `resource_type` | Resource category: `textbook`, `worksheet`, `study_guide`, `slides`, `test`, `answer_key`, `pacing_link`, `canvas_export`, `folder_index`, etc. |
| `source_system` | Which storage system owns the raw file. |
| `source_reference` | Planning-only reference string to source location. Not resolved automatically. |
| `source_reference_type` | Whether the reference points at a file, folder, link, export bundle, or pacing item. |
| `subject` | Subject label (for example `science`, `history`). |
| `grade_band` | Grade band label (for example `SM5`, `grade_7`). |
| `course` | Course within subject (for example `physical_science`). |
| `unit` | Unit within course. |
| `lesson` | Lesson within unit. |
| `pacing_reference` | Link or label to pacing guide row; use `none` when not applicable. |
| `teacher_only` | Whether the resource is teacher-only. `unknown` until manually reviewed. |
| `student_facing_allowed` | Whether the resource may be student-facing after approval. Must not be `true` when `teacher_only` is `true` without explicit future policy. |
| `review_status` | Where the record is in human review (not automated). |
| `approval_status` | Where the record is in approval planning (not automated). |
| `local_first_safety_flags` | Safety markers (for example `no_student_data,metadata_only,not_indexed`). |
| `notes` | Freeform teacher notes about the reference record. |
| `created_by_manual_entry` | `true` means a human authored the record; no ingestion. |
| `activation_status` | `planning_only` for all records in this phase. |

## 10. Allowed Status Values

### `review_status`

| Value | Meaning |
| --- | --- |
| `not_reviewed` | Default for new manual entries |
| `metadata_only` | Metadata captured; content not reviewed |
| `teacher_reviewed` | Teacher reviewed metadata and boundaries |
| `needs_update` | Metadata stale or needs correction |
| `retired` | No longer used |

### `approval_status`

| Value | Meaning |
| --- | --- |
| `not_approved` | Default |
| `approved_for_planning` | Approved for planning references only |
| `approved_student_facing` | Approved for future student-facing use (requires explicit policy) |
| `restricted` | Restricted from lesson-planning use |
| `retired` | Retired from active use |

### `activation_status`

| Value | Meaning |
| --- | --- |
| `planning_only` | Default for all records in this phase |
| `blocked` | Explicitly blocked pending approval |
| `future_active` | Reserved label for post-approval implementation only |

## 11. Teacher-Only and Student-Facing Safety Fields

Rules for future validation (planning only; no live validator in this PR):

- `teacher_only: true` implies the resource must not be treated as student-facing.
- `student_facing_allowed: true` requires `teacher_only: false` and explicit `approval_status` review.
- Answer keys, assessments, and restricted materials should default toward `teacher_only: true` or `unknown`.
- `local_first_safety_flags` should include `no_student_data` for all planning examples.
- Records must not contain student names, IDs, grades, or other student-sensitive data.

## 12. Source Reference Fields

`source_system` + `source_reference` + `source_reference_type` form the source reference triple.

Planning rules:

- References are **opaque planning strings**, not live paths to Owen's real curriculum.
- Use fictional placeholder URIs such as `gdrive://placeholder/...`, `nas://placeholder/...`, `local://placeholder/...`.
- No network resolution, no Drive API, no NAS crawler, no iCloud sync, no folder walker.
- Raw files stay in source storage; the registry stores the reference only.

## 13. Lesson/Unit/Pacing Relationship Fields

Hierarchy for organization and future lesson-planning references:

```text
subject → grade_band → course → unit → lesson → resource (registry record)
```

`pacing_reference` links a resource to a pacing guide row or document reference without activating lesson generation.

`related_resources`, `replacement_for`, and `superseded_by` express relationships between registry records by `registry_id` only.

## 14. Review Status Fields

`review_status` and `approval_status` are **human-driven only**. No automated review workflow, classifier, or AI approval exists in this phase.

Future Teacher Workstation lesson-planning may reference records only when `review_status` and `approval_status` satisfy separately approved policy. No runtime reference is activated by this schema plan.

## 15. Local-First Safety Flags

`local_first_safety_flags` is a planning field for explicit safety markers. Suggested values (comma-separated in examples):

| Flag | Meaning |
| --- | --- |
| `metadata_only` | Record is metadata/reference only |
| `no_student_data` | Must not contain student data |
| `not_indexed` | No file indexing performed |
| `not_scanned` | No document scanning performed |
| `manual_entry` | Created by manual entry only |
| `teacher_only_default` | Defaults toward teacher-only |
| `planning_only` | Not active for runtime use |

## 16. Example Placeholder Rows

Fictional placeholder rows only. No real student data. No real private paths. No live URLs.

| registry_id | title | resource_type | source_system | source_reference | subject | grade_band | teacher_only | student_facing_allowed | review_status | approval_status | activation_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cr-sm5-textbook-001` | SM5 Textbook Placeholder | textbook | google_drive | `gdrive://placeholder/sm5/textbook` | science | SM5 | false | unknown | not_reviewed | not_approved | planning_only |
| `cr-sm5-worksheets-001` | SM5 Worksheet Folder Placeholder | folder_index | google_drive | `gdrive://placeholder/sm5/worksheets` | science | SM5 | true | false | metadata_only | not_approved | planning_only |
| `cr-history-slides-001` | History Unit Slides Placeholder | slides | nas | `nas://placeholder/archive/history-unit-slides` | history | grade_7 | false | unknown | not_reviewed | not_approved | planning_only |
| `cr-science-guide-001` | Science Study Guide Placeholder | study_guide | nas | `nas://placeholder/archive/science-study-guides` | science | SM5 | false | unknown | not_reviewed | not_approved | planning_only |
| `cr-canvas-export-001` | Canvas Export Folder Placeholder | canvas_export | local_folder | `local://placeholder/canvas-export` | science | SM5 | true | false | metadata_only | not_approved | planning_only |

All examples use `created_by_manual_entry: true` and `local_first_safety_flags: metadata_only,no_student_data,not_indexed,not_scanned,manual_entry,planning_only`.

## 17. Validation Expectations

Future manual/static validator (not active in this PR) should check:

- required fields present
- allowed enum values for status fields
- `source_system` from approved list
- `source_reference` is non-empty planning string (not a live URL fetch)
- `teacher_only` / `student_facing_allowed` consistency
- `created_by_manual_entry` is `true` in manual-first phase
- `activation_status` is `planning_only` unless explicitly approved otherwise
- no student data in field values
- PASS/WARN/FAIL semantics preserved

Current verification remains documentation-only:

```bash
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
```

## 18. Future PR Path

| Stage | PR type | May add | Blocked |
| --- | --- | --- | --- |
| 1 | Schema plan | Prose schema, field tables, fictional examples | Live registry file, DB, parser |
| 2 | Sample proof plan | Rules for future fictional sample artifact | Sample file, file reads, scanning, APIs |
| 3 | Manual registry sample/proof | Doc-only sample rows file or expanded examples | File reads, scanning, APIs |
| 3 | Static validator planning refinement | Validator expectation docs | Active validator |
| 4 | Implementation (gate + intake) | Approved registry file format, manual entry UI | Automation, connectors |
| 5 | Connector planning (separate approval) | Connector boundary docs | Live OAuth/API |

## 19. Blocked Capabilities

Unless explicitly approved through `docs/curriculum-builder-approval-gate.md` and completed decision intake:

- live registry file (JSON/CSV/YAML/SQLite)
- database schema activation
- no document scanning
- no folder scanning
- file indexing
- OCR
- embeddings
- vector database
- AI parsing or AI summaries
- auto-classification
- real lesson generation
- generated lesson briefs or drafts
- real review notes
- student data handling
- Google Drive API
- Canvas API
- iCloud integration
- NAS crawler
- local folder crawler
- network calls
- OAuth
- background jobs
- scheduler
- automation
- live integrations
- hosted storage requirement for raw files
- new runtime services
- new package dependencies

## 20. PR Handoff Checklist

Before opening a follow-on Curriculum Builder PR:

- [ ] Start from `docs/curriculum-builder-canonical-planning-index.md`
- [ ] Read `docs/curriculum-builder-next-stage-readiness-audit.md`
- [ ] Read this schema plan
- [ ] Complete `docs/curriculum-builder-future-pr-checklist.md`
- [ ] Confirm scope is documentation/status or approved implementation only
- [ ] Confirm no live registry, database, or schema file created (unless explicitly approved)
- [ ] Confirm examples are fictional placeholders only
- [ ] Confirm no scanning, indexing, OCR, embeddings, APIs, OAuth, automation, or generation
- [ ] Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL
- [ ] Run `bin/chief-of-staff --dashboard` — no FAIL
- [ ] Document any PASS count changes in PR body

## Non-Activation confirmation

This manual registry schema plan does not add active schema files, database tables, migrations, registry data files, validators, commands, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, or live integrations.
