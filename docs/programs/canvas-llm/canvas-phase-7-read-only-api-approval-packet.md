# Canvas LLM Phase 7 - Read-Only Canvas API Approval Packet

```text
Status: canvas_llm_phase_7_read_only_api_approval_packet_complete
Classification: approval packet only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
```

## Purpose

Canvas LLM Phase 7 defines the approval gate for a future read-only Canvas API test.

This phase does not connect to Canvas, call Canvas APIs, use OAuth, use tokens, read live courses, write Canvas content, ingest real curriculum, collect student data, create runtime databases, run RAG, run embeddings, or generate content.

## Course ID Boundary

Real Canvas course IDs are now known for planning, but Phase 7 does not activate them.

Only the demo/sandbox course is named as a candidate for a future first test:

| Source Class | Course Type | Course ID | Status |
| --- | --- | ---: | --- |
| sandbox_demo_canvas_course | Math Automation Sandbox | 24399 | Candidate for future Phase 8 read-only sandbox/demo API test only |

Other course IDs are classified but not listed in this tracked approval packet:

| Source Class | Year | Status |
| --- | --- | --- |
| current_or_upcoming_production_canvas_course | 2026-2027 | Blocked unless separately approved later |
| inactive_historical_canvas_course | 2025-2026 | Approval-gated and requires student/private-data screening |
| inactive_historical_canvas_course | 2024-2025 | Approval-gated and requires student/private-data screening |

## Required Explicit Approval Before Phase 8

A later Phase 8 read-only sandbox/demo API test requires an explicit approval statement from Owen naming:

- Canvas environment or base URL class
- exact allowed course ID
- source class
- allowed endpoint list
- blocked endpoint list
- token handling plan
- local staging path
- allowed output files
- rollback/delete plan
- validation command
- no student data confirmation
- no writes confirmation

## Candidate Phase 8 First Test Scope

The safest future first API target is the demo/sandbox course:

```text
Candidate course ID: 24399
Candidate course type: Math Automation Sandbox
Candidate source class: sandbox_demo_canvas_course
Candidate access: read-only only
Candidate output: local staging metadata only
```

This candidate does not become active until a later prompt explicitly approves Phase 8.

## Allowed Future Read-Only Endpoint Classes

Phase 7 may propose these endpoint classes for later approval, but does not call them:

- course metadata read
- module list read
- module item list read
- page metadata read
- assignment metadata read
- announcement metadata read
- file metadata read

## Blocked Endpoint Classes

The following remain blocked:

- submissions
- grades
- users
- enrollments
- analytics
- conversations/messages
- discussions with student replies
- attendance
- outcomes with student performance
- any endpoint containing student identity or student work
- any create/update/delete/publish endpoint

## Token Handling Requirements

Phase 7 does not create, request, store, validate, or use a token.

A later API phase must use a local-only secret handling plan and must not commit secrets to Git.

Blocked token behaviors:

- no token in tracked files
- no token in docs
- no token in fixtures
- no token in command output
- no token in logs
- no token in PR body
- no token in shell history if avoidable

## Local Staging Requirements

A later approved read-only API test must write only to an approved local staging path.

Minimum requirements:

- staging output is metadata-only
- no student data
- no real curriculum body text unless separately approved
- no production registry writes
- no canonical catalog writes
- no active `--write` without separate approval
- no background sync
- no scheduler
- no automatic import into knowledge DB fixtures

## Phase 7 Safety Boundary

Phase 7 is an approval packet only.

It does not authorize:

- real Canvas API calls
- OAuth
- access tokens
- live Canvas reads
- Canvas writes/publishing
- real curriculum ingestion
- student data
- production course access
- historical course access
- runtime SQLite/database writes
- RAG
- embeddings
- generation
- local model execution
- network integrations
- production writes

## Next Phase

The next possible phase is Phase 8: first read-only sandbox/demo Canvas API fetch to local staging.

Phase 8 must not begin until Owen explicitly approves the exact sandbox/demo course ID, endpoint list, token handling, staging path, and rollback plan.
