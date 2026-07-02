# Curriculum Builder Registry v0.2 — Dry-Run Boundaries

Last updated: 2026-07-02

```text
Status: CB-IMPL-1 dry-run only
Registry writes: no
Active --write: no
Network: no
Student data: no
Real curriculum content: no
```

## Purpose

Hard boundaries for Registry v0.2 manual entry **dry-run** work (CB-IMPL-1).

Governance cross-references:

- `docs/cursor-operating-modes-and-approval-gates.md`
- `docs/teacher-workstation-domain-boundaries.md`
- `docs/curriculum-builder-contract-boundaries.md`
- `docs/implementation-approval-gate.md`

## Allowed Now (CB-IMPL-1)

- Dry-run validation of fake candidate entry JSON files
- Repo-local PASS/WARN/FAIL reporting
- Chief of Staff read-only status command
- Tests proving no writes and no blocked behavior

## Blocked Now (Default)

| Category | Blocked |
| --- | --- |
| Registry mutation | writes to `registry.json`, hidden write paths, `--write` |
| Real data | real records, real paths/URLs, real Canvas IDs, student data |
| Ingestion | file upload, sync, scanning, crawling, OCR, parsing |
| AI / search | embeddings, vector DB, RAG, LLM inference |
| Generation | lessons, briefs, drafts, review notes |
| Integration | APIs, OAuth, network, Drive/NAS/iCloud/Canvas live access |
| Automation | background jobs, schedulers |

## Dry-Run vs Live Registry

| Surface | v0 live read-only store | v0.2 dry-run |
| --- | --- | --- |
| Path | `assistant/curriculum-builder/registry/v0/registry.json` | `assistant/curriculum-builder/samples/registry-v0-2-dry-run/*.json` |
| Mutation | none (read-only validator) | none (dry-run only) |
| Record IDs | `sample-*` fictional | `example-*` fictional candidates (e.g. `example-resource-001`) |
| Envelope flags | n/a | `no_registry_write: true`, `would_write: false` |

Dry-run success does **not** imply approval to write to the live registry.

## Non-Activation

This document does not activate registry writes or external integrations.
