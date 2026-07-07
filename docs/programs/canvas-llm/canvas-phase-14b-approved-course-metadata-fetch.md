# Canvas LLM Phase 14B: Read-Only Approved Course Metadata Fetch

## Status

Phase 14B performs the approved read-only Canvas metadata fetch for the course IDs listed in:

```text
config/canvas-llm/approved-canvas-course-manifest.json
```

Fetched raw metadata is local-only and ignored under:

```text
.local/canvas-llm/approved-course-metadata/
```

No fetched raw metadata is committed.

Canvas writes remain blocked throughout Phase 14B.

## Credentials

The fetcher uses local environment credentials only:

```text
CANVAS_BASE_URL
CANVAS_API_TOKEN
```

The token value is never printed or written. The school Canvas URL is never tracked in repo files.

## Approved Course Scope

The fetcher accepts only course IDs from the Phase 14A manifest. It preserves each course's:

- course role
- school year
- subject
- Canvas course ID
- canonical prefixes

Homeroom/newsletter courses remain a separate course class from academic/current operational courses and are not scored as academic curriculum courses.

## Approved Metadata Categories

Phase 14B fetches metadata-only records for:

- course metadata
- folders metadata
- files metadata
- modules metadata
- module_items metadata
- pages metadata
- announcements metadata
- assignments metadata for relationship mapping only

Assignments metadata is constrained to relationship mapping. Page bodies, announcement bodies, assignment bodies, file contents, and file downloads remain blocked.

## Blocked

Phase 14B keeps these blocked:

- Canvas writes
- renames, moves, deletes, uploads, publish changes
- file downloads and file contents
- page bodies
- announcement bodies
- assignment bodies
- student data
- users, enrollments, rosters
- submissions, grades, analytics, attendance
- conversations/messages
- discussion entries/replies
- quiz responses
- knowledge DB writes
- runtime database writes
- production writes
- canonical catalog writes
- RAG and embeddings
- local model/Ollama execution
- lesson generation
- tracked school Canvas URLs
- tracked tokens/secrets
- committed `.local/...` fetched metadata

## Local Output Shape

Each approved course is staged under:

```text
.local/canvas-llm/approved-course-metadata/course-<course_id>/
```

Expected files:

```text
course_metadata.json
folders_metadata.json
files_metadata.json
modules_metadata.json
module_items_metadata.json
pages_metadata.json
announcements_metadata.json
assignments_metadata.json
manifest.json
```

Top-level summary:

```text
.local/canvas-llm/approved-course-metadata/manifest.json
```

Empty categories are WARN conditions when structurally allowed.

## Commands

Plan without Canvas API access:

```bash
scripts/canvas-llm-approved-course-metadata-fetch.py plan
```

Validate local guards without Canvas API access:

```bash
scripts/canvas-llm-approved-course-metadata-fetch.py validate
```

Perform the approved read-only fetch:

```bash
scripts/canvas-llm-approved-course-metadata-fetch.py live-fetch --i-understand-this-uses-read-only-canvas-api
```

Status proof:

```bash
bin/chief-of-staff --canvas-llm-phase-14b-status
```

## Validation

Required validation:

```bash
bin/chief-of-staff --canvas-llm-phase-14b-status
bin/chief-of-staff --canvas-llm-phase-14a-status
bin/chief-of-staff --canvas-llm-phase-13-status
bin/chief-of-staff --canvas-llm-phase-12-status
git check-ignore -v .local/canvas-llm/approved-course-metadata
git status --short -- .local/canvas-llm || true
git ls-files .local/canvas-llm
```
