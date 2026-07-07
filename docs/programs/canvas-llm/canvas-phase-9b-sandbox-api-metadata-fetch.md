# Canvas LLM Phase 9B - Sandbox API Metadata Fetch Execution

```text
Status: canvas_llm_phase_9b_sandbox_api_metadata_fetch_complete
Classification: separately approved read-only sandbox metadata fetch execution
Approved course ID: 24399 only
Approved Canvas source: local CANVAS_BASE_URL environment variable only
Approved token source: local CANVAS_API_TOKEN environment variable only
Tracked school URL: blocked
Tracked fetched metadata: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum body ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
```

## Purpose

Canvas LLM Phase 9B performs the first separately approved read-only Canvas API metadata fetch against the sandbox/demo course only.

The fetch is limited to course `24399`, metadata-only endpoint classes, local environment variables, and local ignored staging output.

## Approval Boundary

Approved:

- Course ID `24399` only
- read-only Canvas API `GET` requests only
- metadata-only endpoint classes only
- local environment variable `CANVAS_BASE_URL`
- local environment variable `CANVAS_API_TOKEN`
- local staging output only under `.local/canvas-llm/sandbox-metadata/course-24399/`

Blocked:

- any course ID other than `24399`
- current production course access
- historical course access
- users
- enrollments
- submissions
- grades
- analytics
- conversations/messages
- discussions with student replies
- student work
- student identity data
- create/update/delete/publish endpoints
- real curriculum body/content ingestion
- tracked fetched metadata
- tracked school Canvas URL
- tracked tokens/secrets
- runtime SQLite/database writes
- generation, RAG, embeddings, local model execution
- production writes

## Implementation

Phase 9B adds:

- `.gitignore` rule for `.local/canvas-llm/`
- `scripts/canvas-llm-sandbox-metadata-fetch.py`
- `scripts/canvas-llm-phase-9b-status.sh`
- `bin/chief-of-staff --canvas-llm-phase-9b-status`

## Local Execution Summary

The approved local run used:

```text
CANVAS_BASE_URL: local shell environment variable
CANVAS_API_TOKEN: local shell environment variable, not printed
Course ID: 24399
Mode: live-fetch with explicit read-only approval flag
Output root: .local/canvas-llm/sandbox-metadata/course-24399/
```

The local staging manifest reported sanitized metadata files for:

| Endpoint class | Record count |
| --- | ---: |
| course_metadata | 1 |
| modules | 3 |
| pages_metadata | 48 |
| assignments_metadata | 115 |
| announcements_metadata | 0 |
| files_metadata | 220 |
| module_items | 185 |

The fetched JSON files are intentionally local-only and ignored. They must not be committed.

## Safety Notes

The Phase 9B fetcher sanitizes records by writing allowlisted metadata keys only.

It does not intentionally store page body content, assignment descriptions, announcement messages, syllabus body text, discussion replies, submission data, user data, enrollment data, grades, analytics, or conversations.

## Validation

Required validation:

```bash
bin/chief-of-staff --canvas-llm-phase-9b-status
bin/chief-of-staff --canvas-llm-phase-9a-status
scripts/canvas-llm-sandbox-metadata-fetch.py validate
scripts/canvas-llm-sandbox-metadata-fetch.py --course-id 99999 plan
```

Expected:

```text
Phase 9B: PASS / WARN 0 / FAIL 0
Phase 9A: PASS / WARN 0 / FAIL 0
wrong course rejected
live fetch requires explicit approval flag
```

## Rollback

Remove local fetched staging metadata only:

```bash
rm -rf .local/canvas-llm/sandbox-metadata/course-24399
```

Do not use rollback commands that delete tracked repo files.
