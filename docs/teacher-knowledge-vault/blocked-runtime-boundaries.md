# Teacher Knowledge Vault — Blocked Runtime Boundaries

Last updated: 2026-07-04

```text
Status: planning-only boundary reference
M0 architecture freeze does not authorize any runtime below
```

## Blocked Behaviors

| Category | Blocked behavior |
| --- | --- |
| Vault population | Creating real files under `assistant/memory/knowledge/` |
| Auto-loading | Default CLI inclusion of vault entries without explicit flag |
| Intake promotion | Automatic promotion from intake queue to vault |
| Scanning | Folder scanning, document scanning, file crawling |
| Indexing | File indexing, search indexes, embeddings, vector database |
| OCR / RAG | OCR, RAG, or AI summarization of real files into vault |
| Connectors | Drive API, Gmail API, Obsidian sync, OAuth, network calls |
| Student data | Rosters, grades, names, parent info, confidential records |
| Background jobs | Schedulers, watchers, or autonomous memory writers |
| SQLite runtime | Creating or opening live `.db` catalog files |
| M2+ from M1 fixtures | M1 fake catalog does not authorize discovery, connectors, or search runtime |

## Allowed in M0 (Documentation/Status Only)

- Architecture and taxonomy planning docs
- Fictional JSON/Markdown fixtures with `fake_local_planning_only` classification
- Read-only status and validator scripts
- Chief of Staff PASS/WARN/FAIL proof commands

## Negative Assertions (Status Scripts Must Prove)

Status scripts confirm:

- no write action attempted
- no folder scanning attempted
- no network call attempted
- no knowledge directory population attempted
- no auto-load command exposed on CLI

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status
bash tests/teacher-knowledge-vault-m0-architecture-freeze-status-test.sh
```

## Non-Activation

PASS on status commands proves fixture and documentation presence only — not runtime approval.
