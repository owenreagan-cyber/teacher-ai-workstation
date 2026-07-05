# Teacher Knowledge Vault — M2c Selected Local Folder Metadata Scan Approval Gate

Last updated: 2026-07-05

```text
Status: approval gate only — no real folder scan implementation
Closure: complete_teacher_knowledge_vault_m2c_selected_local_folder_approval_gate
M0–M7g: preserved
M2b repo-owned fixture scan: preserved
Real folder scanning: blocked
Content reads: blocked
Production catalog writes: blocked
```

## M2c Doctrine

M2c is an **approval gate only**. It defines safety requirements, folder selection rules, preflight checks, denial rules, review packets, and explicit Owen approval workflow before any **future** Owen-selected local folder metadata scan (M2d).

M2b proved metadata-only discovery using a **repo-owned fake/sanitized staging fixture folder**. M2c does **not** scan real folders, accept arbitrary paths, or import real-folder metadata into the catalog.

M2c clarifies:

- M2c does not scan real folders.
- M2c does not approve real selected-folder scanning by itself.
- M2d requires explicit Owen approval and a named tiny local test folder path.
- M2d must be metadata-only (stat) unless separately approved for content reads.
- M2d must use a tiny controlled folder first.
- M2d requires preflight, review packet, rollback/cleanup, and no-content-read proof before import.
- `99_DO_NOT_SCAN` and `10_TEACHER_ONLY` policies remain absolute.

## Deliverables

| Subsystem | Location |
| --- | --- |
| M2c foundation (this doc) | `docs/teacher-knowledge-vault/m2c-selected-local-folder-approval-gate.md` |
| Path policy | `docs/teacher-knowledge-vault/selected-local-folder-path-policy.md` |
| Preflight | `docs/teacher-knowledge-vault/selected-local-folder-preflight.md` |
| Approval packet | `docs/teacher-knowledge-vault/selected-local-folder-approval-packet.md` |
| Denial rules | `docs/teacher-knowledge-vault/selected-local-folder-denial-rules.md` |
| M2c governance | `docs/teacher-knowledge-vault/m2c-governance-status.md` |
| M2d readiness checklist | `docs/teacher-knowledge-vault/m2d-readiness-checklist.md` |
| M2c fixtures | `assistant/teacher-knowledge-vault/m2c/` |

## Commands

```bash
bin/chief-of-staff --teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status
bash tests/teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status-test.sh
```

## Future M2d Two-Step Workflow

| Step | Action | Runtime in M2c |
| --- | --- | --- |
| 1 | Preflight only — Owen names exact path; system checks safety; approval packet produced | blocked (policy only) |
| 2 | Metadata-only scan/import after Owen approves packet | blocked (future M2d) |

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| M0–M7g, M2b | complete |
| **M2c** Selected local folder approval gate | **complete** (this mission) |
| M2d first Owen-selected tiny local metadata scan | blocked |
| Connectors / extraction / organization / production catalog | blocked |

## Non-Activation

PASS on M2c status proves approval-gate documentation and fake fixtures only — not permission to scan Owen's real folders.
