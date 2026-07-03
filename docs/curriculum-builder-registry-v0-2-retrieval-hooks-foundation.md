# Curriculum Builder Registry v0.2 — Retrieval Hooks Foundation

Last updated: 2026-07-02

```text
Status: fake-record local lookup only
Program: Curriculum Builder — CB-IMPL-4
Closure status: complete_cb_impl_4_retrieval
Semantic search: blocked
Production registry writes: blocked
```

## Purpose

Deterministic **local filter/lookup** over committed fake fixture registry records. Simple field matching only — no filesystem crawling, embeddings, vector DB, RAG, or external services.

## Implemented Now

| Component | Path |
| --- | --- |
| Retrieval script | `scripts/curriculum-builder-registry-v0-2-retrieval-check.sh` |
| Status script | `scripts/curriculum-builder-registry-v0-2-retrieval-status.sh` |
| CLI | `bin/chief-of-staff --curriculum-registry-retrieval-status` |
| Tests | `tests/curriculum-builder-registry-v0-2-retrieval-test.sh` |

## Usage

```bash
# List all fake records
bash scripts/curriculum-builder-registry-v0-2-retrieval-check.sh

# Filter by subject
bash scripts/curriculum-builder-registry-v0-2-retrieval-check.sh --course "Example Math Course"

# Lookup by resource_id
bash scripts/curriculum-builder-registry-v0-2-retrieval-check.sh --resource-id example-resource-001
```

## Blocked

- Searching user files or real curriculum
- Directory crawling / Drive/NAS/iCloud/Canvas access
- Embeddings / vector DB / RAG / semantic search
- LLM / APIs / network

## Non-Activation

Lookup only; no indexing, no generation, no production writes.
