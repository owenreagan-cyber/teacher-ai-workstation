# Canvas Local Storage Schema Plan

```text
Status: phase_4_static_storage_plan
Classification: JSON/SQLite schema plan only
Runtime activation: no
Runtime SQLite/database writes: blocked
```

## Purpose

This plan sketches future local JSON and SQLite shapes without creating databases, runtime storage, importers, sync, indexing, RAG, embeddings, generation, or Canvas connections.

All future collections/tables must require source references, evidence levels, verification status, approval status, and blocked-data flags.

## Shared Fields

Every table or collection should include `id`, `source_reference_ids`, `evidence_ids`, `source_class`, `evidence_level`, `verification_status`, `approval_status`, `confidence_level`, `blocked_data_flags`, `created_at`, and `updated_at`.

## Candidate Tables And Collections

| Name | Purpose | Required fields beyond shared | Source/evidence requirement | Blocked data types | Future JSON | Future SQLite |
| --- | --- | --- | --- | --- | --- | --- |
| `canvas_courses` | Course containers | `course_label`, `school_year_id`, `course_source_class_id` | Required | Student/private data, live Canvas payloads | Object per course | Table with FK ids |
| `canvas_modules` | Module structure | `course_id`, `module_title`, `position` | Required | Live module payloads | Array under course or standalone | FK to courses |
| `canvas_pages` | Page metadata | `course_id`, `module_id`, `page_title` | Required | Page body from real courses unless approved | Object per page | FK to courses/modules |
| `canvas_page_sections` | Page regions | `page_id`, `section_label`, `position` | Required | Real unreviewed text | Array under page | FK to pages |
| `canvas_html_blocks` | HTML block metadata | `page_section_id`, `html_block_kind`, `sanitized_preview` | Required | Unsafe HTML, tokens, student data | Sanitized string fields | FK to sections |
| `canvas_banners` | Banner metadata | `page_id`, `banner_kind`, `alt_text_status` | Required | Real images without approval | Metadata only | FK to pages |
| `canvas_assignments` | Assignment setup | `course_id`, `assignment_title`, `assignment_kind` | Required | Submissions, grades, rosters | Object per assignment | FK to courses |
| `canvas_rubrics` | Rubric metadata | `assignment_id`, `criteria_summary` | Required | Student scores/feedback | Array under assignment | FK to assignments |
| `canvas_announcements` | Announcement metadata | `course_id`, `announcement_kind` | Required | Live announcements unless approved | Object per announcement | FK to courses |
| `canvas_files` | File metadata | `folder_id`, `file_label`, `file_kind` | Required | File contents from real courses unless approved | Metadata object | FK to folders |
| `canvas_folders` | Folder organization | `course_id`, `folder_label` | Required | Drive/NAS/iCloud scans | Metadata object | FK to courses |
| `canvas_resources` | Reusable resource metadata | `resource_kind`, `title` | Required | Real curriculum contents | Object per resource | Table with link rows |
| `canvas_pattern_catalog` | Reviewed patterns | `pattern_category`, `pattern_name` | Required | Unreviewed style authority | Object per pattern | Table with category index |
| `canvas_teacher_style_samples` | Reviewed style metadata | `sample_kind`, `style_trait`, `not_authority_reason` | Required | Unapproved voice corpus | Metadata only | Table with evidence FK |
| `canvas_facts` | Source-backed fact candidates | `fact_text`, `fact_kind` | Required | Unsourced claims | Object per fact | Table with source/evidence FKs |
| `canvas_questions` | Future question candidates | `question_text`, `question_kind` | Required | Generated runtime Q&A | Object per question | Table with answer links |
| `canvas_answers` | Future answer candidates | `answer_text`, `question_id` | Required | Uncited answers | Object per answer | FK to questions |
| `canvas_sources` | Source references | `source_label`, `source_class`, `evidence_level` | Required | Secrets, tokens, live URLs when blocked | Object per source | Source table |
| `canvas_evidence` | Evidence records | `source_reference_id`, `evidence_kind` | Required | Student/private data | Object per evidence item | Evidence table |
| `canvas_verification_events` | Review history | `target_id`, `target_type`, `event_status` | Required | Runtime automation logs | Append-only JSON records | Event table |
| `canvas_approval_events` | Approval history | `target_id`, `approval_status`, `reviewer_label` | Required | Unauthorized approvals | Append-only JSON records | Event table |
| `canvas_knowledge_links` | Object relationships | `from_id`, `from_type`, `to_id`, `to_type`, `relationship_type` | Required | Inferred links without review | Link records | Join table |

## Approval State

Default approval is `pending_review` unless the object is a fake/local fixture marked `fixture_approved`. Production course data defaults to `blocked`.

## Static Only

Phase 4 does not create real JSON stores, SQLite databases, migrations, importers, write commands, indexes, embeddings, or retrieval services. The fixture JSON files are examples only.
