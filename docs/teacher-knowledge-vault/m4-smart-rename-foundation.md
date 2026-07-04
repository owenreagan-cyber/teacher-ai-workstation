# Teacher Knowledge Vault — M4 Smart Rename Foundation

Last updated: 2026-07-04

```text
Status: smart rename suggestions/evidence/review cards — fake fixtures only
Closure: complete_teacher_knowledge_vault_m4_smart_rename_foundation
M0/M1/M2/M3: preserved
Runtime rename/move/copy/delete: blocked
```

## M4 Doctrine

M4 defines Smart Rename as a **reviewable recommendation**, not an operation. All suggestions use fake fixtures only.

M4 preserves:

- M0 expanded architecture freeze
- M1 fake catalog model
- M2 discovery approval boundaries
- M3 fake duplicate/search/package model
- Resource → Representation → Source identity
- Rule DSL boundaries (data-driven rules, not TypeScript)
- Event log and review queue requirements
- `10_TEACHER_ONLY` restricted-indexable policy
- `99_DO_NOT_SCAN` absolute exclusion
- No runtime rename/move/copy/delete/archive
- No scanner, OCR, native extraction, or AI execution

## Deliverables

| Subsystem | Location |
| --- | --- |
| M4 foundation (this doc) | `docs/teacher-knowledge-vault/m4-smart-rename-foundation.md` |
| Smart rename suggestion model | `docs/teacher-knowledge-vault/smart-rename-suggestion-model.md` |
| Canonical naming convention | `docs/teacher-knowledge-vault/canonical-naming-convention.md` |
| Destination suggestion model | `docs/teacher-knowledge-vault/destination-suggestion-model.md` |
| Review card model | `docs/teacher-knowledge-vault/smart-rename-review-card-model.md` |
| Rule DSL rename examples | `docs/teacher-knowledge-vault/smart-rename-rule-examples.md` |
| M4 governance status | `docs/teacher-knowledge-vault/m4-governance-status.md` |
| M4 fake fixtures | `assistant/teacher-knowledge-vault/m4/` |
| M4 status | `scripts/teacher-knowledge-vault-m4-smart-rename-status.sh` |

Cross-reference: `docs/teacher-knowledge-vault/smart-rename-policy.md`, `docs/teacher-knowledge-vault/evidence-package-and-confidence-model.md`

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| M0–M3 | complete |
| **M4** Smart rename foundation | **complete** (this mission) |
| M2b / runtime search / runtime rename | blocked |
| M5 Approved organization + rollback | blocked |
| M6+ OCR, connectors, AI | blocked |

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-m4-smart-rename-status
bash tests/teacher-knowledge-vault-m4-smart-rename-status-test.sh
```

## Non-Activation

PASS on M4 status proves documentation and fake fixtures only — not permission to rename or move files.
