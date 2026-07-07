# Canvas LLM Phase 11 - Sandbox Metadata Import Preview Gate

```text
Status: canvas_llm_phase_11_sandbox_metadata_import_preview_gate_complete
Classification: local ignored sandbox metadata import preview gate
Approved course ID: 24399 only
Source: ignored local Phase 9B staged metadata only
Preview only: yes
Knowledge DB import: blocked
Runtime SQLite/database writes: blocked
Canvas API calls: blocked
Production writes: blocked
Student data: blocked
Real curriculum body ingestion: blocked
Generation/RAG/embeddings: blocked
```

## Purpose

Canvas LLM Phase 11 creates a preview-only mapping from reviewed local sandbox Canvas metadata into candidate knowledge-DB-style entities.

This phase does not import data. It does not write a knowledge DB, runtime SQLite database, production registry, canonical catalog, or generated/RAG/embedding pipeline.

## Reviewed Source

Approved local source:

```text
.local/canvas-llm/sandbox-metadata/course-24399/
```

The local metadata is ignored and must not be committed.

## Preview Entity Types

Phase 11 maps endpoint classes into preview-only candidate entity names:

| Endpoint class | Preview entity |
| --- | --- |
| course_metadata | canvas_course_metadata_preview |
| modules | canvas_module_metadata_preview |
| module_items | canvas_module_item_metadata_preview |
| pages_metadata | canvas_page_metadata_preview |
| assignments_metadata | canvas_assignment_metadata_preview |
| announcements_metadata | canvas_announcement_metadata_preview |
| files_metadata | canvas_file_metadata_preview |

Every preview entity has:

```text
would_import: false
would_write_knowledge_db: false
would_write_runtime_database: false
would_write_production: false
```

## Preview Counts

The local Phase 11 import preview observed:

| Endpoint class | Preview record count |
| --- | ---: |
| course_metadata | 1 |
| modules | 3 |
| pages_metadata | 48 |
| assignments_metadata | 115 |
| announcements_metadata | 0 |
| files_metadata | 220 |
| module_items | 185 |

Expected warning:

```text
WARN: announcements_metadata has 0 records in sandbox staging
```

## Safety Checks

Phase 11 validates that:

- course ID is `24399`
- source is local ignored metadata only
- preview is read-only and metadata-only
- no Canvas API call is performed
- no import is performed
- no knowledge DB write is performed
- no runtime database write is performed
- no production write is performed
- no student data is handled
- no real curriculum body ingestion occurs
- no generation, RAG, or embeddings are run
- token/bearer/access-token text patterns are not found
- no tracked school Canvas URL is present
- no non-demo real course IDs are present

## Commands

```bash
bin/chief-of-staff --canvas-llm-phase-11-status
scripts/canvas-llm-sandbox-import-preview.py plan
scripts/canvas-llm-sandbox-import-preview.py preview
```

## Import Gate

Phase 11 explicitly blocks import.

A future phase may propose a fake/local import preview artifact, but it must remain separately approved, tracked as fake/local preview-only, and must not use production registry writes, runtime SQLite/database writes, generation, RAG, embeddings, student data, real curriculum body ingestion, or any course outside `24399`.

## Blocked Work

Still blocked unless separately approved:

- production course access
- historical course access
- other course IDs
- new live Canvas fetches
- Canvas writes/publishing
- student data
- users/enrollments/submissions/grades
- real curriculum body/content ingestion
- actual knowledge DB import
- production registry writes
- canonical catalog writes
- runtime SQLite/database writes
- generation, RAG, embeddings, local model execution
- network integrations beyond separately approved read-only metadata fetches

## Definition Of Done

Phase 11 is complete when:

- Phase 11 import preview script exists
- Phase 11 status command exists
- Chief of Staff command is wired
- preview command passes
- expected sandbox warning is preserved
- Phase 10 continuity passes
- docs/status/roadmap reflect the preview-only import gate
