# Repo Staging Metadata Discovery

Last updated: 2026-07-05

## Command

```bash
bin/chief-of-staff --teacher-knowledge-vault-m2b-repo-staging-metadata-discovery
```

Script: `scripts/teacher-knowledge-vault-m2b-repo-staging-metadata-discovery.sh`

## Behavior

1. Rejects any command-line path arguments
2. Walks only `assistant/teacher-knowledge-vault/m2b/fake-staging-folder/`
3. Collects **stat metadata only** (size, mtime placeholder, extension, relative path)
4. Detects policy labels from relative path segments
5. Marks `99_DO_NOT_SCAN` as blocked/non-indexable
6. Marks `10_TEACHER_ONLY` as restricted-indexable
7. Writes report to `.local/teacher-knowledge-vault/m2b/repo-staging-metadata-report.json`

## Metadata collected

- filename / display name
- extension
- relative fixture path
- file size
- modified timestamp (deterministic placeholder in report)
- source label: `repo_owned_fake_staging`
- indexing policy flags

## Blocked

- file content reads (`open`, parsers, OCR)
- file hashing (not used)
- arbitrary paths
- external sources

## Validation

```bash
bash tests/teacher-knowledge-vault-m2b-repo-staging-metadata-discovery-test.sh
```
