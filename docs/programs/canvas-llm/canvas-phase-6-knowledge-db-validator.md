# Canvas LLM Phase 6 - Fake/Local Knowledge DB Validator

```text
Status: canvas_llm_phase_6_fake_local_knowledge_db_validator_complete
Classification: read-only fake/local fixture validator only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
```

## Purpose

Canvas LLM Phase 6 validates the fake/local Canvas knowledge DB prototype created in Phase 5.

This phase proves that fake/local JSON fixtures have reliable internal relationships before any future approval-gated Canvas API work.

## What Phase 6 Validates

- fake Q&A records link to existing fake facts
- fake facts link to existing fake evidence
- fake evidence links to existing fake sources
- fake patterns, pages, modules, assignments, announcements, and files reference valid fixture IDs
- required safety fields are present
- source class remains `fake_local_fixture`
- evidence level remains `Level 0`
- approval status remains `fixture_approved`
- verification status remains `fake_local_verified`
- fixture files do not contain obvious Canvas tokens, email addresses, live Canvas URLs, or student data markers

## Artifacts

- `scripts/canvas-llm-knowledge-db-validator.py`
- `scripts/canvas-llm-phase-6-status.sh`
- `bin/chief-of-staff --canvas-llm-phase-6-status`

## Boundary

Phase 6 does not approve real Canvas course IDs, Canvas API calls, OAuth, access tokens, live Canvas reads, Canvas writes, real curriculum ingestion, student data, runtime database writes, RAG, embeddings, generation, network integrations, or production writes.

## Next Approval Gate

The next safe phase after Phase 6 is a read-only Canvas API approval packet. That future packet must still perform no API calls. It should only document the exact approval requirements for any later sandbox/demo Canvas API test.
