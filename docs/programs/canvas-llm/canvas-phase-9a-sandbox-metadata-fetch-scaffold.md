# Canvas LLM Phase 9A - Sandbox Metadata Fetch Scaffold

```text
Status: canvas_llm_phase_9a_sandbox_metadata_fetch_scaffold_complete
Classification: gated read-only metadata fetch scaffold
Runtime activation: dry-run by default
Approved course ID: 24399 only
Canvas API/OAuth/live reads: scaffolded but blocked unless explicit approved flags and local token are present
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum body ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
```

## Purpose

Canvas LLM Phase 9A creates the gated scaffold for a future first read-only sandbox/demo Canvas metadata fetch.

This phase does not require a live fetch. The default behavior must remain dry-run only.

## Approved Scope

Phase 9A is limited to the approved sandbox/demo course:

| Field | Value |
| --- | --- |
| Course ID | `24399` |
| Course type | Math Automation Sandbox |
| Source class | `sandbox_demo_canvas_course` |
| Mode | read-only |
| Output | local staging metadata only |

No other real Canvas course ID is approved.

## Approved Metadata Endpoint Classes

The scaffold may define allowlisted metadata-only endpoint classes for:

- course metadata
- modules
- module items
- pages metadata
- assignments metadata
- announcements metadata
- files metadata

## Blocked Endpoint Classes

The scaffold must reject or omit:

- users
- enrollments
- submissions
- grades
- analytics
- conversations/messages
- discussions with student replies
- attendance
- student work
- student identity data
- create/update/delete/publish endpoints
- any endpoint outside the explicit allowlist

## Required Script Behavior

The Phase 9A scaffold script must:

- default to dry-run mode
- require course ID `24399`
- reject any other course ID
- require an explicit approved-read-only flag before any future live mode
- require a local-only token environment variable before any future live mode
- never print tokens
- never write tokens
- never write outside the approved local staging path
- support a rollback/delete command for staged metadata
- write metadata-only JSON in staging when live mode is explicitly approved later
- avoid real curriculum body ingestion
- avoid student data endpoints
- avoid generation, RAG, embeddings, and runtime database writes

## Token Handling

Phase 9A must not commit secrets.

Allowed future token source:

```text
CANVAS_API_TOKEN
```

Blocked token behaviors:

- no token in tracked files
- no token in docs except the environment variable name
- no token in fixtures
- no token in logs
- no token in command output
- no token in PR body
- no token in shell history where avoidable

## Staging Path

Approved local staging root for this scaffold:

```text
.local/canvas-llm/sandbox-metadata/course-24399/
```

This path is local-only and must remain ignored or untracked.

The scaffold may create a tracked `.gitkeep` only if needed in a non-secret parent folder, but should not commit live fetched metadata.

## Rollback

The scaffold must document or provide a rollback command that removes only the approved local staging path:

```bash
rm -rf .local/canvas-llm/sandbox-metadata/course-24399
```

## Phase 9A Non-Goals

Phase 9A does not approve:

- current production courses
- historical courses
- any course ID other than `24399`
- student data
- users/enrollments/submissions/grades
- Canvas writes/publishing
- real curriculum body ingestion
- automatic import into knowledge DB fixtures
- production registry writes
- canonical catalog writes
- runtime SQLite/database writes
- RAG
- embeddings
- generation
- local model execution

## Definition Of Done

Phase 9A is complete when:

- scaffold doc exists
- dry-run command works without network or token
- course ID guard rejects non-24399 IDs
- endpoint allowlist is explicit
- blocked endpoints are documented
- token handling is local-only
- staging path guard exists
- rollback command is documented
- status command proves Phase 8 continuity
