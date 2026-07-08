# Canvas LLM Phase 15: Historical-to-Current Readiness and Relationship Report

## Status

Phase 15 reads the ignored Phase 14B local metadata manifest and creates a tracked safe readiness report.

This phase performs no Canvas API calls, no live fetches, no Canvas writes, no file downloads, no file content reads, no page body ingestion, no announcement body ingestion, no assignment body ingestion, no student data access, no database writes, no RAG, no embeddings, no local model execution, and no lesson generation.

Raw fetched metadata remains ignored under `.local/canvas-llm/approved-course-metadata/...` and is not committed.

## Fetch Source

```text
.local/canvas-llm/approved-course-metadata/manifest.json
```

Fetched course count: `19`

## Executive Summary

- Current 2026-2027 courses exist but are mostly empty shells.
- Historical 2024-2025 and 2025-2026 courses contain enough files, folders, modules, module items, pages, and assignment metadata to guide Canvas setup.
- Homeroom/newsletter courses are included but kept separate from academic course readiness scoring.
- Announcements metadata is consistently zero across fetched courses and should be treated as a known Canvas/source pattern for now.
- Phase 16 should produce a safe module/file/page relationship report before any rename, move, copy, or upload preview.

## Current Course Readiness

| Subject | Current Course ID | Readiness | Files | Folders | Modules | Module Items | Pages | Assignments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Math | 26404 | metadata_only_shell | 0 | 1 | 0 | 0 | 0 | 0 |
| Reading/Spelling | 26442 | metadata_only_shell | 0 | 1 | 0 | 0 | 0 | 0 |
| Language Arts | 26495 | metadata_only_shell | 0 | 1 | 0 | 0 | 0 | 0 |
| History | 26493 | metadata_only_shell | 0 | 1 | 0 | 0 | 0 | 0 |
| Science | 26496 | metadata_only_shell | 0 | 1 | 0 | 0 | 0 | 0 |
| Homeroom | 26427 | metadata_only_shell | 0 | 1 | 0 | 0 | 0 | 0 |

## Best Historical Template By Subject

| Subject | Recommended Template Course ID | School Year | Files | Folders | Modules | Module Items | Pages | Assignments | Structure Score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Math | 19428 | 2024-2025 | 351 | 17 | 4 | 330 | 39 | 150 | 891 |
| Reading/Spelling | 19419 | 2024-2025 | 326 | 40 | 8 | 65 | 39 | 173 | 651 |
| Language Arts | 19426 | 2024-2025 | 143 | 13 | 5 | 161 | 38 | 56 | 416 |
| History | 21934 | 2025-2026 | 114 | 45 | 12 | 150 | 40 | 52 | 413 |
| Science | 21970 | 2025-2026 | 59 | 19 | 7 | 46 | 40 | 35 | 206 |
| Homeroom | 19424 | 2024-2025 | 40 | 9 | 3 | 46 | 42 | 0 | 140 |

## Historical Academic Course Counts

| Course ID | Year | Subject | Prefixes | Files | Folders | Modules | Module Items | Pages | Assignments | Structure Score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21970 | 2025-2026 | Science | N/A | 59 | 19 | 7 | 46 | 40 | 35 | 206 |
| 21919 | 2025-2026 | Reading | RM4, SPELL | 137 | 24 | 5 | 48 | 42 | 172 | 428 |
| 21957 | 2025-2026 | Math | SM5 | 209 | 37 | 3 | 174 | 56 | 150 | 629 |
| 21944 | 2025-2026 | Language Arts | ELA4 | 137 | 52 | 5 | 70 | 41 | 52 | 357 |
| 21934 | 2025-2026 | History | N/A | 114 | 45 | 12 | 150 | 40 | 52 | 413 |
| 19419 | 2024-2025 | Reading | RM4, SPELL | 326 | 40 | 8 | 65 | 39 | 173 | 651 |
| 19428 | 2024-2025 | Math | SM5 | 351 | 17 | 4 | 330 | 39 | 150 | 891 |
| 19426 | 2024-2025 | Language Arts | ELA4 | 143 | 13 | 5 | 161 | 38 | 56 | 416 |
| 19423 | 2024-2025 | History B | N/A | 38 | 7 | 3 | 47 | 39 | 36 | 170 |
| 19422 | 2024-2025 | History A | N/A | 29 | 10 | 3 | 47 | 38 | 34 | 161 |

## Homeroom / Newsletter Comparison

| Course ID | Year | Role | Files | Folders | Modules | Module Items | Pages | Assignments | Structure Score | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 26427 | 2026-2027 | current_homeroom_newsletter_course | 0 | 1 | 0 | 0 | 0 | 0 | 1 | current target shell |
| 22254 | 2025-2026 | historical_homeroom_newsletter_course | 11 | 4 | 26 | 42 | 44 | 0 | 127 | supporting reference |
| 19424 | 2024-2025 | historical_homeroom_newsletter_course | 40 | 9 | 3 | 46 | 42 | 0 | 140 | best newsletter model |

## Subject Readiness Gaps

### Math

- Current course `26404` readiness: `metadata_only_shell`.
- Recommended historical model: `19428` from `2024-2025`.
- Approximate metadata gap: `890` structure-count units.
- Next safe action: build a preview-only relationship map from historical `19428` to current `26404`.

### Reading/Spelling

- Current course `26442` readiness: `metadata_only_shell`.
- Recommended historical model: `19419` from `2024-2025`.
- Approximate metadata gap: `650` structure-count units.
- Next safe action: build a preview-only relationship map from historical `19419` to current `26442`.

### Language Arts

- Current course `26495` readiness: `metadata_only_shell`.
- Recommended historical model: `19426` from `2024-2025`.
- Approximate metadata gap: `415` structure-count units.
- Next safe action: build a preview-only relationship map from historical `19426` to current `26495`.

### History

- Current course `26493` readiness: `metadata_only_shell`.
- Recommended historical model: `21934` from `2025-2026`.
- Approximate metadata gap: `412` structure-count units.
- Next safe action: build a preview-only relationship map from historical `21934` to current `26493`.

### Science

- Current course `26496` readiness: `metadata_only_shell`.
- Recommended historical model: `21970` from `2025-2026`.
- Approximate metadata gap: `205` structure-count units.
- Next safe action: build a preview-only relationship map from historical `21970` to current `26496`.

### Homeroom

- Current course `26427` readiness: `metadata_only_shell`.
- Recommended historical model: `19424` from `2024-2025`.
- Approximate metadata gap: `139` structure-count units.
- Next safe action: build a preview-only relationship map from historical `19424` to current `26427`.

## Safety Boundaries Preserved

- Phase 15 reads local ignored metadata summary only.
- Phase 15 does not fetch from Canvas.
- Phase 15 does not write to Canvas.
- Phase 15 does not download files.
- Phase 15 does not ingest page, announcement, assignment, or file bodies.
- Phase 15 does not access student data, rosters, grades, submissions, analytics, messages, or discussion replies.
- Phase 15 does not write to a knowledge DB, runtime DB, production system, or canonical catalog.
- Phase 15 does not run RAG, embeddings, local model/Ollama, or lesson generation.
- Phase 15 does not track the school Canvas URL or tokens.

## Recommended Next Phase

```text
Canvas LLM Phase 16: Preview-Only Canvas Module/File/Page Relationship Map
```

Phase 16 should read the same ignored Phase 14B metadata and produce preview-only mapping recommendations for modules, folders, files, pages, and current-course setup order. It should still block Canvas writes, file downloads, body ingestion, and raw metadata commits.
