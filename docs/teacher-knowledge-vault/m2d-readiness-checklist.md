# M2d Readiness Checklist — First Owen-Selected Tiny Local Metadata Scan

Last updated: 2026-07-05

**Status: planning gate only — M2d runtime blocked.** This checklist prepares for a future M2d mission. Completing M2c or passing M2c status does **not** authorize M2d.

## Before Owen Names a Path

- [ ] M2c approval gate docs and fake fixtures reviewed
- [ ] M2b repo-owned fixture scan remains the only selected-folder-style scan
- [ ] M7g prototype catalog remains gitignored and fixture-only
- [ ] No M2d CLI commands exist yet
- [ ] No arbitrary path scanner exists
- [ ] Production registry parked (`BLOCKED-NO-WRITES.sentinel` intact)

## Owen Preconditions (explicit, written)

- [ ] Owen names **one exact tiny local test folder path** (not Desktop/Documents/Downloads/home)
- [ ] Folder is non-synced local preferred (not Google Drive/iCloud/NAS/Canvas)
- [ ] Folder is created specifically for metadata-only trial (fixture-like)
- [ ] Folder is unlikely to contain student data, secrets, or `99_DO_NOT_SCAN` content
- [ ] Owen accepts metadata-only (stat) scan — **no content reads**
- [ ] Owen accepts scope limits: max 25 files, depth 2, 10 MB total
- [ ] Owen accepts extension allowlist: `.pdf`, `.docx`, `.pptx`, `.md`, `.txt`
- [ ] Owen accepts fixed generated report under `.local/teacher-knowledge-vault/m2d/`
- [ ] Owen accepts rollback/cleanup plan before any optional M7g import

## Step 1 — Preflight Only (no scan, no import)

- [ ] Path exists and is local
- [ ] Path passes denied-class checks (see `selected-local-folder-denial-rules.md`)
- [ ] Preflight produces approval packet with `owen_approval: false`
- [ ] Packet includes scope limits, policy flags, and denial reasons if any
- [ ] No-content-read proof documented (`content_reads_disabled: true`)
- [ ] OCR/AI/extraction disabled proof documented
- [ ] External access disabled proof documented
- [ ] Catalog import blocked until second approval
- [ ] Owen reviews packet — **no runtime scan yet**

## Step 2 — Metadata Scan (only after Owen approves packet)

- [ ] Owen sets explicit second approval for M2d mission
- [ ] Stat metadata only — no file content reads
- [ ] No symlink traversal, archive expansion, or nested system traversal
- [ ] No write operations to source folder
- [ ] Generated report written to fixed gitignored path only
- [ ] Optional M7g import remains separate explicit approval
- [ ] Cleanup/rollback proof executed after trial

## Blocked Without Separate Approval

- Real curriculum roots
- Student-data-likely folders
- Google Drive / iCloud / NAS / Canvas
- OCR / extraction / AI / RAG / embeddings
- Organization runtime (rename/move/copy/delete/archive/export)
- Production or canonical catalog writes
- Arbitrary path input or recursive deep scan

## Proof Commands (M2c gate — not M2d runtime)

```bash
bin/chief-of-staff --teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status
bash tests/teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status-test.sh
bin/chief-of-staff --teacher-knowledge-vault-m2b-repo-staging-metadata-status
bin/chief-of-staff --teacher-knowledge-vault-m7g-persistent-working-catalog-status
```

## Fake Examples

| Artifact | Location |
| --- | --- |
| Approval packet | `assistant/teacher-knowledge-vault/m2c/fake-selected-folder-approval-packet.json` |
| Preflight denials | `assistant/teacher-knowledge-vault/m2c/fake-path-preflight-denials.json` |
| Safe preflight example | `assistant/teacher-knowledge-vault/m2c/fake-safe-test-folder-preflight.json` |
| Rollback/cleanup plan | `assistant/teacher-knowledge-vault/m2c/fake-rollback-cleanup-plan.json` |

PASS on this checklist being documented does **not** mean M2d is approved or implemented.
