# Canvas LLM Phase 14A: Course Approval Manifest

## Status

Phase 14A adds a tracked approval manifest for future read-only Canvas metadata fetches.

This phase does not perform any Canvas API call, live fetch, course enumeration, Canvas write, file download, body ingestion, database write, RAG, embedding, local model execution, or lesson generation.

## Manifest

Tracked manifest:

```text
config/canvas-llm/approved-canvas-course-manifest.json
```

## Course roles

The manifest separates courses into:

- current operational academic courses
- current Homeroom/newsletter course
- historical academic courses
- historical Homeroom/newsletter courses
- demo sandbox course

Homeroom/newsletter courses are not scored as academic curriculum courses. They are used later for newsletter/reminder structure and layout analysis.

## Approved course coverage

The manifest includes:

- 2026-2027 current operational courses
- 2026-2027 Homeroom newsletter course
- 2025-2026 historical academic courses
- 2025-2026 historical Homeroom newsletter course
- 2024-2025 historical academic courses
- 2024-2025 historical Homeroom newsletter course
- the approved demo sandbox course `24399`

## Shared course ID handling

Reading and Spelling share a Canvas course ID in each included academic year.

The manifest supports multiple canonical prefixes per course:

```text
26442 -> RM4, SPELL
21919 -> RM4, SPELL
19419 -> RM4, SPELL
```

## Future fetch scope

A later fetch phase may use this manifest to fetch read-only metadata only, including:

- course metadata
- folders metadata
- files metadata
- modules metadata
- module_items metadata
- pages metadata
- announcements metadata
- assignments metadata only for relationship mapping

## Blocked

Phase 14A and later fetch phases continue to block:

- student data
- users/enrollments/rosters
- submissions
- grades
- analytics
- attendance
- conversations/messages
- discussion entries/replies
- quiz responses
- file downloads
- file contents
- page bodies
- announcement bodies
- assignment bodies
- Canvas writes
- renames/moves/deletes/uploads
- publish changes
- knowledge DB writes
- runtime database writes
- production writes
- canonical catalog writes
- RAG/embeddings
- local model/Ollama execution
- lesson generation
- tracked school Canvas URLs
- tracked tokens/secrets
- committed `.local/...` fetched metadata

## Validation

Run:

```bash
bin/chief-of-staff --canvas-llm-phase-14a-status
```
