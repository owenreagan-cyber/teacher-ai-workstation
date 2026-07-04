# Teacher Knowledge Vault — Manual Entry Plan

Last updated: 2026-07-04

```text
Status: planning-only
Automatic entry creation: blocked
AI-generated vault content: blocked
```

## Purpose

Plan how Owen will **manually** add approved knowledge entries to Teacher Knowledge Vault in a future mission — without automation, scanning, or default memory loading.

## Entry Shape (Planning)

Knowledge entries are **Markdown files** with optional frontmatter labels (planning only — no frontmatter parser in M0):

| Field | Description | Example (fictional) |
| --- | --- | --- |
| `knowledge_entry_id` | Stable ID in JSON fixtures | `sample-knowledge-entry-001` |
| `title` | Human-readable label | `Placeholder Fraction Review Reference` |
| `category` | Taxonomy bucket | `reference_summary` |
| `source_intake_ref` | Optional intake trace | `fake-intake-ref-001` |
| `summary_body` | Approved summary text only | Short fictional placeholder paragraph |
| `review_status` | Human review state | `teacher_reviewed` |
| `metadata_only` | Must remain true in v0 fixtures | `true` |

See `assistant/teacher-knowledge-vault/samples/fake-knowledge-entry-outline.md` for a fictional outline.

## Manual Entry Sequence (Future Mission)

1. Owen completes intake review (if material originated from intake).
2. Owen confirms material is summary-only and sanitized.
3. Owen creates Markdown file under planned taxonomy path (manual edit).
4. Owen logs change in `assistant/memory/memory-log.md`.
5. Future mission: explicit CLI flag to include vault entry in a run (not default).

## What Manual Entry Must Not Include

- student names or identifiable student details
- parent contact information
- grades, behavior, medical, or discipline records
- passwords, API keys, or tokens
- full copyrighted text or proprietary school documents
- live `http://` or `https://` URLs in v0 fixtures (real entries may cite approved links in future missions with separate review)

## Relationship to JSON Schema v0

`assistant/teacher-knowledge-vault/v0/knowledge-entry-schema.json` defines the **fixture record shape** for planning and validation. It does not activate a Markdown parser or file writer.

## Proof

```bash
bin/chief-of-staff --teacher-knowledge-vault-knowledge-entry-v0-validate
bin/chief-of-staff --teacher-knowledge-vault-m0-architecture-freeze-status
```
