# Canvas LLM Phase Plan

```text
Status: planned/frozen for runtime
Classification: documentation/status only
```

## Phase 0 - Standards Foundation

Status: complete as docs/status/fake-local scaffold.

Keep existing Canvas LLM planning foundation frozen for runtime. Confirm no Canvas API, OAuth, live reads/writes, generation, deployment, or student data. Maintain standards, evidence schema, safe data boundaries, authority/conflict policy, validation tiers, report templates, and fake/local fixture guidance.

## Phase 1 - Canvas Knowledge Sweep

Status: fake/local validator complete; live knowledge sweep not started.

Collect and summarize Canvas standards, export expectations, review states, and safety requirements as local planning docs only. No live Canvas access.

Phase 1 currently validates fake/local fixture evidence only through `scripts/canvas-llm-fake-local-validator.sh` and `bin/chief-of-staff --canvas-llm-phase-1-status`.

## Phase 2 - Manual Evidence Intake

Status: manual/exported redacted evidence intake scaffold complete; no live Canvas access.

Define manual review and export concepts using fake/local examples and Owen-provided redacted evidence only. No package generator, exporter, automatic scanner, live Canvas read, or Canvas write path. Current implementation: `evidence/canvas-llm/`, `docs/programs/canvas-llm/canvas-phase-2-manual-evidence-intake.md`, and `bin/chief-of-staff --canvas-llm-phase-2-status`.

## Phase 3 - Manual Evidence Normalizer

Status: manual evidence normalizer complete for explicit fake/local/redacted packet fixtures only. No live Canvas access, OAuth, automatic export, broad scanning, student data, real curriculum ingestion, generation, indexing, embeddings, RAG, or production writes. Current implementation: `scripts/canvas-llm-manual-evidence-normalizer.sh`, `scripts/canvas-llm-phase-3-status.sh`, `fixtures/canvas-llm/manual-evidence-packets/`, and `bin/chief-of-staff --canvas-llm-phase-3-status`.

## Phase 4 - Canvas Knowledge Architecture And Pattern Catalog

Status: knowledge architecture and pattern catalog complete as docs/status/schema/fake-local fixtures only. No Canvas API/OAuth/live reads, Canvas writes/publishing, real curriculum ingestion, student data, runtime JSON/SQLite writes, generation, embeddings, RAG, or AI runtime behavior. Current implementation: `docs/programs/canvas-llm/canvas-phase-4-knowledge-architecture.md`, `docs/programs/canvas-llm/canvas-knowledge-object-model.md`, `docs/programs/canvas-llm/canvas-pattern-catalog-schema.md`, `docs/programs/canvas-llm/canvas-evidence-levels-and-source-classes.md`, `docs/programs/canvas-llm/canvas-local-storage-schema-plan.md`, `fixtures/canvas-llm/knowledge-architecture/`, `scripts/canvas-llm-phase-4-status.sh`, and `bin/chief-of-staff --canvas-llm-phase-4-status`.

Inactive historical Canvas courses, including 2024-2025 and 2025-2026, are future approval-gated sources that require student/private-data screening. Sandbox/demo Canvas courses are the preferred future API-testing source because they can contain no student data and no historical data. Current production courses remain blocked unless separately approved later.

## Phase 5 - Fake/Local Knowledge DB Prototype

Status: fake/local knowledge DB prototype complete as docs/status/fake-local JSON fixtures only. No Canvas API/OAuth/live reads, Canvas writes/publishing, real curriculum ingestion, student data, runtime SQLite/database writes, generation, embeddings, RAG, or production writes. Current implementation: `docs/programs/canvas-llm/canvas-phase-5-fake-local-knowledge-db.md`, `docs/programs/canvas-llm/canvas-knowledge-db-query-patterns.md`, `fixtures/canvas-llm/knowledge-db/`, `scripts/canvas-llm-phase-5-status.sh`, and `bin/chief-of-staff --canvas-llm-phase-5-status`.

## Phase 6 - Fake/Local Knowledge DB Validator

Status: fake/local knowledge DB relationship validator complete as read-only fixture validation only. No Canvas API/OAuth/live reads, Canvas writes/publishing, real curriculum ingestion, student data, runtime SQLite/database writes, generation, embeddings, RAG, network integrations, or production writes. Current implementation: `docs/programs/canvas-llm/canvas-phase-6-knowledge-db-validator.md`, `scripts/canvas-llm-knowledge-db-validator.py`, `scripts/canvas-llm-phase-6-status.sh`, and `bin/chief-of-staff --canvas-llm-phase-6-status`.

## Phase 7 - Read-Only Canvas API Approval Packet

Status: read-only Canvas API approval packet complete as docs/status approval packet only. No Canvas API/OAuth/live reads, Canvas writes/publishing, real curriculum ingestion, student data, runtime SQLite/database writes, generation, embeddings, RAG, network integrations, or production writes. Current implementation: `docs/programs/canvas-llm/canvas-phase-7-read-only-api-approval-packet.md`, `scripts/canvas-llm-phase-7-status.sh`, and `bin/chief-of-staff --canvas-llm-phase-7-status`.

## Phase 8 - First Read-Only Sandbox/Demo Canvas API Fetch Gate

Status: sandbox/demo Canvas API fetch gate complete as docs/status gate only. No Canvas API/OAuth/live reads, access token use, Canvas writes/publishing, student data, real curriculum ingestion, runtime SQLite/database writes, generation, embeddings, RAG, network integrations, or production writes. Current implementation: `docs/programs/canvas-llm/canvas-phase-8-sandbox-api-fetch-gate.md`, `scripts/canvas-llm-phase-8-status.sh`, and `bin/chief-of-staff --canvas-llm-phase-8-status`.

## Phase 9 - Separately Approved Read-Only Sandbox/Demo Metadata Fetch
