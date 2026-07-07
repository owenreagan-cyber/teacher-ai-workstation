# Canvas LLM Phase 8 - First Read-Only Sandbox/Demo Canvas API Fetch Gate

```text
Status: canvas_llm_phase_8_sandbox_api_fetch_gate_complete
Classification: API fetch gate only
Runtime activation: no
Canvas API/OAuth/live reads: blocked until explicit execution approval
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
```

## Purpose

Canvas LLM Phase 8 defines the final gate before any future first read-only Canvas API fetch.

This phase does not call Canvas, does not use OAuth, does not read tokens, does not perform network access, does not fetch live Canvas data, and does not write staging output.

## Approved Candidate Scope For A Later Execution Phase

The only candidate for a later first API test is:

| Field | Value |
| --- | --- |
| Candidate source class | `sandbox_demo_canvas_course` |
| Candidate course type | Math Automation Sandbox |
| Candidate course ID | `24399` |
| Candidate mode | read-only |
| Candidate output class | local staging metadata only |
| Candidate activation | blocked until explicit Owen approval |

This candidate is not activated by Phase 8.

## Required Explicit Owen Approval For Any Later Fetch

Before any future command may call Canvas, Owen must explicitly approve:

- exact course ID: `24399`
- source class: `sandbox_demo_canvas_course`
- read-only mode
- exact allowed endpoint list
- exact blocked endpoint list
- token handling method
- local staging path
- allowed output file names
- rollback/delete command
- validation command
- no student data confirmation
- no Canvas writes/publishing confirmation
- no real curriculum body ingestion confirmation

## Allowed Future Endpoint Classes

A later execution phase may request approval for metadata-only reads from:

- course metadata
- modules
- module items
- pages metadata
- assignments metadata
- announcements metadata
- files metadata

These endpoint classes are not called in Phase 8.

## Blocked Endpoint Classes

The following remain blocked:

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
- any endpoint not explicitly approved

## Token Handling Gate

Phase 8 does not create, request, store, validate, print, or use a Canvas token.

A later execution phase must use local-only secret handling and must not commit secrets to Git.

Blocked token behaviors:

- no token in tracked files
- no token in docs
- no token in fixtures
- no token in command output
- no token in logs
- no token in PR body
- no token in shell history where avoidable

## Local Staging Gate

A later execution phase must write only to a separately approved local staging path.

Minimum staging requirements:

- metadata-only output
- no student data
- no real curriculum body text unless separately approved
- no production registry writes
- no canonical catalog writes
- no active `--write` outside the approved staging path
- no background sync
- no scheduler
- no automatic import into knowledge DB fixtures
- rollback/delete command documented before execution

## Phase 8 Non-Activation Statement

Phase 8 is a gate only.

It does not authorize:

- Canvas API calls
- OAuth
- access token use
- live Canvas reads
- Canvas writes/publishing
- student data access
- production course access
- historical course access
- real curriculum ingestion
- runtime SQLite/database writes
- RAG
- embeddings
- generation
- local model execution
- network integrations
- production writes

## Next Phase

The next possible phase is a separately approved Phase 9 execution packet or Phase 8b implementation gate, depending on repo naming.

That later phase must stop unless Owen explicitly approves the exact first fetch scope and confirms that the command may perform read-only network/API access to sandbox/demo course `24399`.
