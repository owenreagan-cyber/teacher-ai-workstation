# Teacher Knowledge Vault — M2b Repo-Owned Staging Metadata Prototype

Last updated: 2026-07-05

```text
Status: metadata-only discovery — fixed repo-owned staging fixture folder only
Closure: complete_teacher_knowledge_vault_m2b_repo_owned_staging_metadata_prototype
M0–M7g: preserved
Real local folder scanning: blocked
Content reads: blocked
Production catalog writes: blocked
```

## M2b Doctrine

M2b is the **first repo-owned fixture staging metadata-only prototype**. It collects file stat metadata from a fixed committed fake/sanitized staging folder only.

M2b is **not**:

- real local folder scanning
- arbitrary path discovery
- file content reading or parsing
- OCR, extraction, or AI/RAG
- Drive/NAS/Canvas/iCloud access
- real curriculum ingestion
- authorization for future real selected-folder scans by itself

M2b **does**:

- scan stat metadata from `assistant/teacher-knowledge-vault/m2b/fake-staging-folder/` only
- detect policy folders (`10_TEACHER_ONLY`, `99_DO_NOT_SCAN`, etc.)
- write metadata reports to `.local/teacher-knowledge-vault/m2b/`
- import metadata into the M7g persistent working catalog prototype

## Deliverables

| Subsystem | Location |
| --- | --- |
| M2b foundation (this doc) | `docs/teacher-knowledge-vault/m2b-repo-owned-staging-metadata-prototype.md` |
| Staging folder policy | `docs/teacher-knowledge-vault/repo-owned-staging-folder-policy.md` |
| Metadata discovery | `docs/teacher-knowledge-vault/repo-staging-metadata-discovery.md` |
| Catalog import | `docs/teacher-knowledge-vault/repo-staging-metadata-catalog-import.md` |
| M2b governance | `docs/teacher-knowledge-vault/m2b-governance-status.md` |
| Staging fixtures | `assistant/teacher-knowledge-vault/m2b/fake-staging-folder/` |
| Generated output | `.local/teacher-knowledge-vault/m2b/` (gitignored) |

## Commands

```bash
bin/chief-of-staff --teacher-knowledge-vault-m2b-repo-staging-metadata-discovery
bin/chief-of-staff --teacher-knowledge-vault-m2b-repo-staging-metadata-import
bin/chief-of-staff --teacher-knowledge-vault-m2b-repo-staging-metadata-cleanup
bin/chief-of-staff --teacher-knowledge-vault-m2b-repo-staging-metadata-status
```

## Comparison

| Scope | M2b prototype | Future real selected-folder scan |
| --- | --- | --- |
| Folder | committed repo fixture | Owen-selected local path |
| Content reads | no | blocked until separate approval |
| Path input | fixed only | blocked until separate approval |

## Milestone Roadmap

| Milestone | Status |
| --- | --- |
| M0–M7g | complete |
| **M2b** Repo-owned staging metadata prototype | **complete** |
| **M2c** Selected local folder metadata scan approval gate | **complete** (approval gate only — no real scan) |
| **M2d** First Owen-selected tiny local metadata scan | **complete** (fixed path only) |
| **M2e** M7g import from M2d preview | blocked pending explicit approval |
| Real selected local folder metadata scan (general) | blocked |
| Drive/NAS/Canvas connectors | blocked |
| Content extraction/indexing | blocked |

## Non-Activation

PASS on M2b status proves metadata discovery from repo-owned fixtures only — not permission for real folder scanning or curriculum access.

## Explicit Approval Required For

- **Real selected-folder scan** — Owen's local Desktop/Documents/Downloads or curriculum folders
- **Connectors** — Drive/NAS/Canvas runtime
- **Extraction/OCR/AI/RAG**
- **Production catalog**
