# Canvas LLM Phase 19F — Title Cleaner Deterministic Prototype Preview

## Status

Preview-only deterministic prototype phase.

## Purpose

Phase 19F creates a local deterministic title-cleaner prototype that uses the Phase 19D seed rules and fixtures, plus the Phase 19E validator boundary, to prove that approved messy title examples can be normalized into preview-only canonical outputs.

## Core Principle

```text
Normalize only committed fixture examples.
Preview only.
Never mutate Canvas.
Ambiguous inputs remain review-required.
```

## Inputs

```text
docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/title-normalization-rules.json
docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/title-normalization-fixtures.md
scripts/canvas-llm-phase-19e-title-cleaner-validator-preview.py
```

## Outputs

```text
README.md
title-cleaner-deterministic-prototype-spec.md
title-cleaner-deterministic-prototype-report.md
preview-only-boundary.md
phase-19f-next-step-recommendation.md
scripts/canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview.py
scripts/canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview-status.sh
bin/chief-of-staff --canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview-status
```

## Boundary

Phase 19F does not authorize:

- Canvas API calls
- Canvas writes
- live Canvas fetches
- page creation
- assignment creation
- announcement creation
- file movement
- file upload
- file delete
- file publish
- body ingestion
- student data access
- raw `.local` metadata reads or commits
- school Canvas URL commits
- token exposure
- app implementation
- database migration
- RAG
- embeddings
- local model/Ollama execution
- silent Canvas mutation
