# Canvas LLM Phase 5 - Fake/Local Knowledge Database Prototype

```text
Status: canvas_llm_phase_5_fake_local_knowledge_db_complete
Classification: docs/status/fake-local JSON prototype only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Runtime SQLite/database writes: blocked
Generation/RAG/embeddings: blocked
```

## Purpose

Canvas LLM Phase 5 proves that the Phase 4 Canvas knowledge architecture can be represented as a small, fake/local JSON knowledge database.

This is not a Canvas fetch, Canvas sync, Canvas import/export, runtime database, SQLite migration, RAG index, embedding store, or generation system.

The prototype demonstrates source-backed relationships only:

```text
Question -> Answer -> Fact -> Evidence -> Source Reference -> Source Class -> Evidence Level -> Approval Status
```

## Source Rules

All Phase 5 examples use fake/local data only.

Inactive historical Canvas courses, including 2024-2025 and 2025-2026, remain approval-gated and are not imported in Phase 5.

Sandbox/demo Canvas courses remain preferred future API test targets because they can contain no student data and no historical data, but they are not fetched in Phase 5.

## Phase 5 Artifacts

- `fixtures/canvas-llm/knowledge-db/`
- `docs/programs/canvas-llm/canvas-knowledge-db-query-patterns.md`
- `scripts/canvas-llm-phase-5-status.sh`
- `bin/chief-of-staff --canvas-llm-phase-5-status`

## Blocked In Phase 5

- Canvas API/OAuth/live reads
- Canvas writes/publishing
- Canvas import/export automation or sync
- Real curriculum ingestion, parsing, copying, indexing, or summarizing
- Student data
- Google Drive/NAS/iCloud access
- Runtime SQLite/database writes
- OCR, embeddings, RAG, and generation
- Local model/Ollama execution or probing
- Production registry writes
