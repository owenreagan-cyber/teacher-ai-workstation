# Canvas LLM Phase 19D — Machine-Readable Seed Rule Catalog + Title Cleaner Preview

## Status

Preview-only docs/data/status phase.

## Purpose

Phase 19D turns Phase 19B canonical rules and Phase 19C schemas into machine-readable seed preview data.

It also introduces a Canonical Title Cleaner / Title Normalizer preview for cleaning mislabeled or close-enough teacher inputs into approved Canvas-safe titles.

## Core Principle

```text
Accept messy input.
Classify carefully.
Normalize to canonical output.
Preview before use.
Never silently mutate Canvas.
```

## Phase 19D Files

```text
evidence.json
rules.json
links.json
title-normalization-rules.json
title-normalization-fixtures.md
preview-only-boundary.md
phase-19d-next-step-recommendation.md
```

## Boundary

Phase 19D does not implement app behavior.

Phase 19D does not authorize:

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
- database migration
- RAG
- embeddings
- local model/Ollama execution
