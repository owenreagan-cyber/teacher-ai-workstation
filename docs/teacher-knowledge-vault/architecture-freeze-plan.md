# Teacher Knowledge Vault — M0 Architecture Freeze Plan

Last updated: 2026-07-04

```text
Status: planning-only — not implementation approval
Closure: complete_teacher_knowledge_vault_m0_architecture_freeze
Knowledge directory population: blocked — future Owen-approved mission only
Auto-loading memory: blocked
Folder scanning/indexing: blocked
Network/API/OAuth: blocked
Student data: blocked — absolute
Proof: bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status
```

## Purpose

Freeze the **M0 architecture** for Teacher Knowledge Vault: a local-first, inspectable store of user-approved reference summaries and reusable teaching notes under `assistant/memory/knowledge/` — **without populating real knowledge files**, auto-loading memory, or activating connectors.

This plan extends `docs/teacher-knowledge-vault-m0-foundation.md` with architecture-freeze planning artifacts.

## Relationship to Existing Memory Lanes

| Layer | Document / artifact | Role |
| --- | --- | --- |
| M0 foundation closure | `docs/teacher-knowledge-vault-m0-foundation.md` | Canonical closure summary |
| Architecture freeze (this doc) | `docs/teacher-knowledge-vault/architecture-freeze-plan.md` | M0 scope and mission boundaries |
| Folder taxonomy | `docs/teacher-knowledge-vault/folder-taxonomy.md` | Planned directory layout (not populated yet) |
| Intake-to-vault gate | `docs/teacher-knowledge-vault/intake-to-vault-approval-gate.md` | Human approval before vault promotion |
| Manual entry plan | `docs/teacher-knowledge-vault/manual-entry-plan.md` | Manual Markdown entry model |
| Blocked boundaries | `docs/teacher-knowledge-vault/blocked-runtime-boundaries.md` | Runtime block list |
| Memory policy | `assistant/memory-policy.md` | Knowledge Vault row and privacy rules |
| Intake policy | `assistant/intake/intake-policy.md` | Promotion targets before vault |

## Planned Local Root (Not Populated Yet)

Future Owen-approved mission may populate:

```text
assistant/memory/knowledge/
```

**This mission does not create knowledge files or auto-load them.** No silent writes, no default `--include-memory` expansion for vault paths.

## M0 Architecture Freeze Sequence (Planning Only)

1. Owen reviews folder taxonomy and manual entry outline.
2. Owen reviews intake-to-vault approval gate before any promotion runtime.
3. Owen reviews fictional knowledge entry schema v0 and sample fixtures.
4. Future mission: Owen-approved manual entry of first real knowledge file.
5. Future mission: explicit CLI flag for including approved vault entries (still no auto-load).

## Fake / Local Fixtures

| Fixture | Path |
| --- | --- |
| Intake promotion record (fictional) | `assistant/teacher-knowledge-vault/samples/fake-intake-promotion-record.json` |
| Knowledge entry outline (fictional) | `assistant/teacher-knowledge-vault/samples/fake-knowledge-entry-outline.md` |
| Knowledge entry schema v0 samples | `assistant/teacher-knowledge-vault/v0/sample-knowledge-entries.json` |

All fixtures use `fake_local_planning_only` classification. No real teaching content, student names, or live URLs.

## Blocked Until Separate Approval

```text
assistant/memory/knowledge/ population with real files
automatic memory loading / default CLI inclusion
folder scanning / crawling / indexing / OCR
embeddings / RAG / AI summarization of real files
Drive / Gmail / Obsidian sync / OAuth / network calls
automatic intake promotion into vault
student data / rosters / grades / parent contact info
```

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status
bash tests/teacher-knowledge-vault-m0-architecture-freeze-status-test.sh
```

## Non-Activation

Documentation, fake fixtures, and read-only status only. PASS does not populate knowledge files or activate integrations.
