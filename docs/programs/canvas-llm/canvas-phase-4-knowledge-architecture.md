# Canvas LLM Phase 4 - Canvas Knowledge Architecture And Pattern Catalog

```text
Status: canvas_llm_phase_4_knowledge_architecture_complete
Classification: docs/status/schema/fake-local fixtures only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Generation/RAG/embeddings: blocked
Local JSON/SQLite runtime writes: blocked
```

## Purpose

Canvas LLM Phase 4 defines the future knowledge architecture for Canvas learning without activating data collection, runtime storage, generation, retrieval, Canvas API access, OAuth, live reads, Canvas writes, publishing, real curriculum ingestion, student data handling, embeddings, RAG, or AI runtime behavior.

The architecture answers what kinds of Canvas knowledge objects the workstation may understand later, how those objects must carry source-backed evidence, and how future inactive historical courses and sandbox/demo Canvas courses must be classified before any later approval-gated work.

Phase 4 is a static foundation only. The included fixtures are fake/local schema examples and must not be treated as official course data, official Canvas style, or an approved "Mr. Reagan" voice model.

## Source Class Boundary

Inactive historical Canvas courses include the 2024-2025 and 2025-2026 school years. They remain approval-gated, must be screened for student/private data, and do not authorize Canvas API/OAuth/live reads in Phase 4.

Sandbox/demo Canvas courses are preferred for future API testing because Owen can create them with no student data and no historical data ever associated with them. They are still future-only in Phase 4.

Current production Canvas courses are blocked unless a later phase separately approves a named scope, allowed inputs/outputs, source handling, test plan, and rollback plan.

## Phase 4 Artifacts

- `docs/programs/canvas-llm/canvas-knowledge-object-model.md`
- `docs/programs/canvas-llm/canvas-pattern-catalog-schema.md`
- `docs/programs/canvas-llm/canvas-evidence-levels-and-source-classes.md`
- `docs/programs/canvas-llm/canvas-local-storage-schema-plan.md`
- `fixtures/canvas-llm/knowledge-architecture/`
- `scripts/canvas-llm-phase-4-status.sh`
- `bin/chief-of-staff --canvas-llm-phase-4-status`

## Future Q&A Rule

Future Q&A and fact lookup must be source-backed:

```text
Question -> Answer -> Fact(s) -> Evidence -> Source Reference -> Source Class -> Evidence Level -> Approval Status
```

Every future answer must cite source evidence. Every fact must have source references, explicit confidence, explicit verification status, and explicit approval status. Stale, unverified, or unapproved facts must not be treated as authority.

Generated answers, RAG, embeddings, summarization, and AI runtime behavior are not approved in Phase 4.

## Blocked In Phase 4

- Canvas API/OAuth/live reads
- Canvas writes/publishing
- Canvas import/export automation or sync
- Google Drive/NAS/iCloud access
- Real curriculum ingestion, parsing, copying, indexing, or summarizing
- Student data
- OCR
- Embeddings, RAG, and generation
- Local model/Ollama execution or probing
- Runtime SQLite/database writes
- Production registry writes
- Antigravity install/execution or active `.antigravity` config
