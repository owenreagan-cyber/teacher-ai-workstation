# Local Retrieval Foundation v0

Last updated: 2026-07-01

```text
Status: documentation/status/interface only
Foundation status: active_v0
Implementation approval status: not approved by default for indexing, semantic search, or automatic resolution
```

## Purpose

This document is the **canonical closure summary** for Local Retrieval Foundation v0 under approved Phase 3 boundaries. It defines manual lookup interfaces, registry lookup contract planning, fictional lookup fixtures, and missing-reference report shapes — without activating retrieval engines, embeddings, RAG, or file indexing.

Cross-references:

- Program roadmap: `docs/master-build-roadmap.md`
- Curriculum Registry v0: `docs/curriculum-registry-v0.md`
- Binding v0: `docs/curriculum-binding-v0.md`
- Renderer Foundation v0: `docs/renderer-foundation-v0.md`
- Engineering authority: `docs/engineering-constitution.md`

## Retrieval Boundary

Local Retrieval is a future **approved local lookup** layer over registry metadata and output contracts. It is not semantic search, not RAG, and not folder crawling.

Local Retrieval Foundation v0 defines **interfaces only**:

- manual lookup request/response planning shapes
- fictional lookup fixtures and missing-reference reports
- deterministic read-only validation
- Chief of Staff status and dashboard proof

## Implemented Subsystems (v0 Foundation)

| Subsystem | Location | Role |
| --- | --- | --- |
| Lookup interface schema | `assistant/local-retrieval/v0/lookup-interface-schema.json` | Placeholder lookup record schema |
| Lookup fixtures | `assistant/local-retrieval/v0/sample-lookup-fixtures.json` | Fictional manual lookup and missing-reference fixtures |
| Foundation status | `scripts/local-retrieval-foundation-status.sh` | Read-only v0 foundation closure proof |
| Lookup validator | `scripts/local-retrieval-foundation-v0-validator.sh` | Deterministic read-only JSON validation |

## Chief of Staff Command Surface

| Command | Purpose |
| --- | --- |
| `bin/chief-of-staff --local-retrieval-foundation-status` | Full Local Retrieval Foundation v0 PASS/WARN/FAIL |
| `bin/chief-of-staff --local-retrieval-foundation-v0-validate` | Read-only lookup fixture v0 validator |
| `bin/chief-of-staff --curriculum-binding-v0-lookup` | Related read-only binding lookup |
| `bin/chief-of-staff --dashboard` | Includes Local Retrieval foundation in dashboard |

## Validation Suite

```bash
bash scripts/local-retrieval-foundation-v0-validator.sh
bash scripts/local-retrieval-foundation-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

## Boundaries (Still Active)

Local Retrieval Foundation v0 does **not** include:

- embeddings, RAG, vector databases, or semantic search
- file indexing, folder crawling, document parsing, or OCR
- LLM retrieval, APIs, OAuth, network calls, or automation
- automatic source resolution or live file checks

## Future Approval Gates

| Track | Gate | Doc |
| --- | --- | --- |
| Approved local lookup engine | Separate intake mission | `docs/implementation-approval-gate.md` |
| Registry-backed lookup writes | Registry write mission | `docs/master-build-roadmap.md` Mission A4 |

## v0 Foundation Definition of Done

Local Retrieval Foundation v0 is **complete** for the approved scope when:

1. Lookup interface schema and fictional fixtures validate deterministically
2. Missing-reference report shape is documented and validated
3. Chief of Staff command surface is documented and wired
4. Dashboard includes foundation status without regression
5. This document and cross-links are active

## Non-Activation Confirmation

Documentation/status/interface only. No embeddings, RAG, vector databases, semantic search, file indexing, folder crawling, OCR, LLM retrieval, network calls, or automatic source resolution.
