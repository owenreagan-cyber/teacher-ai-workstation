# Canvas LLM Phase 10 - Sandbox Metadata Review And Import Gate

```text
Status: canvas_llm_phase_10_sandbox_metadata_review_gate_complete
Classification: local ignored sandbox metadata review/import gate
Approved course ID: 24399 only
Source: ignored local Phase 9B staged metadata only
Canvas API calls: blocked
Metadata import: blocked
Production writes: blocked
Student data: blocked
Real curriculum body ingestion: blocked
Generation/RAG/embeddings: blocked
```

## Purpose

Canvas LLM Phase 10 reviews the ignored local sanitized metadata fetched during Phase 9B and creates a safety gate before any future import.

This phase is review-only. It does not call Canvas, import metadata into a knowledge DB, write production registries, generate content, run embeddings, or perform RAG.

## Reviewed Source

Approved local source:

```text
.local/canvas-llm/sandbox-metadata/course-24399/
```

The local metadata is ignored and must not be committed.

## Review Results

The Phase 10 reviewer validated the Phase 9B local staging manifest and staged files for course `24399`.

Local endpoint counts observed:

| Endpoint class | Record count |
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

This warning is preserved because the sandbox/demo course currently has no announcements.

## Safety Checks

Phase 10 validates that:

- manifest course ID is `24399`
- staged metadata is read-only and metadata-only
- staged metadata is sanitized
- manifest endpoint classes match the approved review set
- record counts match local staged files
- staged files stay under the approved local staging root
- forbidden body/content/student/grade/enrollment-style keys are not found
- token/bearer/access-token text patterns are not found
- no Canvas API call is performed
- no metadata import is performed
- no production write is performed

## Import Gate

Phase 10 explicitly blocks import.

A later phase may propose an import preview, but it must remain separately approved and should begin as fake/local preview-only. It must not import into a production registry, canonical catalog, runtime SQLite database, or generation/RAG pipeline without a separate approval gate.

## Commands

```bash
bin/chief-of-staff --canvas-llm-phase-10-status
scripts/canvas-llm-sandbox-metadata-review.py plan
scripts/canvas-llm-sandbox-metadata-review.py review
```

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
- import into knowledge DB
- production registry writes
- canonical catalog writes
- runtime SQLite/database writes
- generation, RAG, embeddings, local model execution
- network integrations beyond separately approved read-only metadata fetches

## Definition Of Done

Phase 10 is complete when:

- Phase 10 review script exists
- Phase 10 status command exists
- Chief of Staff command is wired
- local staging metadata is verified ignored
- review command passes
- expected sandbox warning is preserved
- Phase 9B continuity passes
- docs/status/roadmap reflect the import gate
