# Canvas LLM Phase 19E — Title Cleaner Validator Preview

## Status

Preview-only validator phase.

## Purpose

Phase 19E creates a local validator preview for the Phase 19D Canonical Title Cleaner seed data.

The validator proves that Phase 19D machine-readable rules and fixtures are internally checkable before any app implementation.

## Core Principle

```text
Rules must be machine-checkable before they become app behavior.
Fixtures must prove expected normalization before Canvas is touched.
Ambiguous inputs must remain review-required.
```

## Phase 19E Inputs

```text
docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/evidence.json
docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/rules.json
docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/links.json
docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/title-normalization-rules.json
docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/title-normalization-fixtures.md
```

## Phase 19E Outputs

```text
title-cleaner-validator-spec.md
title-cleaner-validator-report.md
preview-only-boundary.md
phase-19e-next-step-recommendation.md
scripts/canvas-llm-phase-19e-title-cleaner-validator-preview.py
scripts/canvas-llm-phase-19e-title-cleaner-validator-preview-status.sh
bin/chief-of-staff --canvas-llm-phase-19e-title-cleaner-validator-preview-status
```

## Boundary

Phase 19E does not implement Canvas behavior.

Phase 19E does not authorize:

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
- raw `.local` metadata commits
- school Canvas URL commits
- token exposure
- app implementation
- database migration
- RAG
- embeddings
- local model/Ollama execution
