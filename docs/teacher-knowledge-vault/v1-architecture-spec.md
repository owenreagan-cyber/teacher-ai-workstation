# Teacher Knowledge Vault — v1 Architecture Specification

Last updated: 2026-07-04

```text
Status: M0 frozen specification — not implementation approval
```

## System Purpose

Teacher Knowledge Vault v1 is the **intelligence, metadata, rules, search, validation, approval, review, and governance layer** for Owen's curriculum digital assets. Files live in Google Drive and/or UGREEN NAS. The Vault answers what exists, where, how items relate, and what operations are safe.

## Core Engines (Frozen Boundaries)

| Engine | Responsibility | Must NOT |
| --- | --- | --- |
| **Catalog** | Resource identity, representations, sources, versions | Store binary files as canonical |
| **Connector layer** | Normalized SourceItem from approved connectors | Hardcode Drive/NAS/Canvas in catalog |
| **Fingerprinting** | Hash and similarity signals | Auto-merge without review |
| **Classification** | Rule DSL evaluation, evidence packages | Execute rename/move without approval |
| **Review workspace** | Teacher inbox, states, approvals | Auto-apply suggestions |
| **Event log** | Auditable history, rollback hooks | Silent mutations |
| **Observability** | Metrics, cost estimates, risk flags | Hide blocked operations |
| **Governance** | QA gates, restricted indexing, pacing checks | Bypass `99_DO_NOT_SCAN` |

## Data Flow (Inactive)

```text
Source → Connector → SourceItem → Fingerprint → Resource/Representation
  → Classification → Evidence → Review → [Approval] → Dry-run → [gate] → Execute (blocked)
  → Event log
```

## Platform Targets

Google Drive (canonical), UGREEN NAS (mirror), MacBook Pro M5 (workshop/staging), MacBook Air M1 / iPad Air A16 (classroom runtime), Canvas (publishing only), AirPlay → Apple TV / Samsung TV (display).

## Anti-Drift

Changes require ADR. See `docs/teacher-knowledge-vault/m0-architecture-freeze.md`.
