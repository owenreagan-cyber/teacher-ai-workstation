# Canvas LLM Phase 12: Fake/Local Sandbox Metadata Import Artifact Gate

## Status

Phase 12 adds a tracked fake/local import artifact preview shape for the approved Canvas sandbox demo course `24399`.

This phase is a preview/artifact gate only. It does not import Canvas metadata into any knowledge database, runtime database, production registry, or canonical catalog.

## Approved course scope

Only course `24399` is approved for this phase.

The tracked artifact preserves the reviewed Phase 9B and Phase 11 entity counts and mapping shape, but it does not copy real Canvas metadata records from ignored `.local` staging.

## Artifact

Tracked fixture:

```text
fixtures/canvas-llm/import-preview/fake-local-sandbox-import-artifact-course-24399.json
```

Artifact class:

```text
fake_local_import_preview_artifact
```

Source class:

```text
sandbox_demo_canvas_course
```

## Preserved reviewed counts

```text
course_metadata: 1
modules: 3
pages_metadata: 48
assignments_metadata: 115
announcements_metadata: 0
files_metadata: 220
module_items: 185
```

## Expected preserved warning

```text
WARN: announcements_metadata has 0 records in sandbox staging
```

The warning is expected because the reviewed sandbox staging metadata has zero announcement records.

## Safety flags

The Phase 12 artifact must explicitly preserve these safety decisions:

```text
real_metadata_copied: false
import_performed: false
knowledge_db_write: false
runtime_database_write: false
canvas_api_call: false
production_write: false
canonical_catalog_write: false
student_data: false
real_curriculum_body_ingestion: false
generation_rag_embeddings: false
local_model_ollama_execution: false
tracked_school_canvas_url: false
tracked_tokens_or_secrets: false
local_staging_committed: false
```

## What Phase 12 allows

Phase 12 allows:

- tracked fake/local import artifact shape
- fake IDs
- fake titles
- fake source references
- reviewed aggregate counts
- safety flags
- docs/status validation
- Chief of Staff status wiring

## What Phase 12 blocks

Phase 12 blocks:

- actual import into a knowledge DB
- runtime SQLite/database writes
- production registry writes
- canonical catalog writes
- Canvas API calls
- new live fetches
- copied real Canvas metadata records
- real curriculum body/content ingestion
- student data
- generation, RAG, or embeddings
- local model/Ollama execution
- tracked school Canvas URL
- tracked tokens/secrets
- committing `.local/...` fetched metadata

## Validation

Run:

```bash
bin/chief-of-staff --canvas-llm-phase-12-status
```

The status check proves:

- Phase 12 files exist
- fake/local artifact JSON parses
- artifact contains course `24399` only
- artifact explicitly says no real metadata copied
- artifact explicitly says no import performed
- artifact explicitly says no knowledge DB/runtime DB/production writes
- artifact preserves the expected `announcements_metadata=0` warning
- `.local/...` metadata is ignored and not tracked
- no tracked school Canvas URL exists in the Phase 12 fixture
- no tracked token exists in the Phase 12 fixture
- no exact real non-demo course IDs exist in the Phase 12 fixture other than approved `24399`
- Phase 11 status still passes
