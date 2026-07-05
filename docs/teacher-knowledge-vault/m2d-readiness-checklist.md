# M2d Readiness Checklist — First Owen-Selected Tiny Local Metadata Scan

Last updated: 2026-07-05

**Status: M2d fixed-path scan complete for Owen-approved tiny test folder.** General folder scanning and arbitrary path input remain blocked.

## Before Owen Names a Path

- [x] M2c approval gate docs and fake fixtures reviewed
- [x] M2b repo-owned fixture scan preserved
- [x] M7g prototype catalog remains gitignored
- [x] M2d fixed-path CLI commands exist (no arbitrary path scanner)
- [x] Production registry parked (`BLOCKED-NO-WRITES.sentinel` intact)

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

## Proof Commands (M2d fixed path)

```bash
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-preflight
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-metadata-scan
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-metadata-preview
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-cleanup
bin/chief-of-staff --teacher-knowledge-vault-m2d-selected-folder-status
bin/chief-of-staff --teacher-knowledge-vault-m2c-selected-local-folder-approval-gate-status
```

PASS on M2d status proves metadata-only scan of the fixed Owen-approved folder only — not permission for arbitrary paths or general scanning.
