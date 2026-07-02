# Curriculum Builder — Contract Boundaries (A4–A7)

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Curriculum Builder — Additional Canonical Contract Schemas (A4–A7)
Scanning: blocked
Ingestion: blocked
Generation: blocked
Network: no
```

## Purpose

Hard boundaries for metadata contract schema work (Programs A4–A7) and all future Curriculum Builder contract extensions until explicit implementation approval.

Governance cross-references:

- `docs/cursor-operating-modes-and-approval-gates.md`
- `docs/teacher-workstation-domain-boundaries.md`
- `docs/implementation-approval-gate.md`

## Allowed Now (A4–A7 Foundation)

- Markdown schema documentation with fictional placeholder examples
- Inactive JSON samples under `assistant/curriculum-builder/metadata-contract/v0/`
- Read-only status script and Chief of Staff command
- Cross-links to Registry v0, Output Contract v0, local-first plan
- Dashboard and phase-1 status integration

## Blocked Now (Default)

| Category | Blocked capabilities |
| --- | --- |
| Scanning / indexing | document scanning, folder scanning, file indexing, folder crawling |
| External storage | Drive crawling, NAS crawling, iCloud crawling, Canvas crawling |
| Parsing / AI | OCR, embeddings, vector DB, RAG, semantic search, LLM inference |
| Ingestion | file upload, file sync, curriculum ingestion, document parsing |
| Generation | lesson generation, briefs, drafts, review notes, worksheets, presentations, quizzes |
| Integration | APIs, OAuth, credentials, network calls, live sync |
| Data | student data, real curriculum content, real paths/URLs |
| Runtime | validators wired to real files, registry writes from crawlers, automation |

## Schema Doc Rules

Contract schema docs must state:

- read-only / inactive / non-runtime
- not a validator
- not connected to ingestion
- not implementation authority by themselves

Status scripts must **not**:

- validate internal field lists as required runtime keys
- infer implementation approval from doc presence
- scan outside the repo

## Relationship to Output Contract v0

Output Contract v0 (five canonical types) remains **active** with validators. Metadata contracts A4–A7 are **inactive planning schemas** until separate intake approves activation.

## Non-Activation

This document does not activate any Curriculum Builder runtime behavior.
