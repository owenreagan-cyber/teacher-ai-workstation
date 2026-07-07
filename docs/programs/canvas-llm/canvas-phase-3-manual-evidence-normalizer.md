# Canvas LLM Phase 3 Manual Evidence Normalizer

```text
Status: canvas_llm_phase_3_manual_evidence_normalizer_complete
Classification: fake/local/manual/redacted fixture normalization only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
Canvas writes/publishing: blocked
Student data: blocked
Real curriculum ingestion: blocked
Automatic broad scanning: blocked
Production writes: blocked
```

## Purpose

Phase 3 adds a deterministic, local-only normalizer status layer for manually prepared Canvas evidence packets. It prepares the repository for future source-backed Canvas knowledge work without fetching, parsing, indexing, summarizing, or learning from real Canvas courses.

The implementation is intentionally narrow:

- packets must be explicitly named by directory.
- current committed examples are fake/local/redacted fixtures.
- output is a dry-run normalized manifest printed to stdout.
- no normalized production registry, search index, embeddings store, RAG corpus, generated Canvas content, or runtime app behavior is created.

## Implemented Surface

- `scripts/canvas-llm-manual-evidence-normalizer.sh` validates one explicit packet directory and prints deterministic normalized fixture status.
- `scripts/canvas-llm-phase-3-status.sh` is a read-only Chief of Staff status proof.
- `bin/chief-of-staff --canvas-llm-phase-3-status` exposes the read-only status command.
- `fixtures/canvas-llm/manual-evidence-packets/sample-redacted-packet/` provides a fake redacted packet fixture.

## Safety Rules

The normalizer rejects:

- missing packet directory arguments.
- broad or sensitive paths such as `/`, `$HOME`, `~/Desktop`, `~/Documents`, `/Volumes`, and parent traversal.
- packet paths outside `fixtures/canvas-llm/manual-evidence-packets/`.
- missing `packet.json` metadata.
- packets that do not affirm redaction and no student data.
- packets that claim Canvas API, OAuth, live Canvas access, production writes, or real curriculum ingestion.
- files containing obvious credential or student-data markers.
- unsupported evidence file extensions.

## Current Non-Authority

Phase 3 packets are not authoritative course knowledge. They are fixture-safe packet shapes and normalization checks only. Future real Canvas source use requires a later approval-gated phase with named source paths, review owner, redaction proof, allowed outputs, and rollback/safety criteria.

## Explicitly Deferred

- live Canvas fetch/export/sync.
- OAuth/API setup.
- Canvas write-back or publishing.
- Google Drive/NAS/iCloud discovery.
- real curriculum folder ingestion.
- OCR, embeddings, RAG, AI generation, or local model execution.
- production/canonical registry writes.
