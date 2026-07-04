# Teacher Knowledge Vault — Restricted Indexing and Pacing Guardrails

Last updated: 2026-07-04

## `10_TEACHER_ONLY` — restricted-indexable

`10_TEACHER_ONLY` is restricted-indexable for teacher-controlled grounding — not non-indexable. Not student-visible by default.

## `99_DO_NOT_SCAN` — Absolute Exclusion

Non-indexable, non-discoverable, non-extractable, non-embeddable, non-searchable, non-summarizable.

## Student-Facing

Leakage checks required. Teacher-only content must not leak into student-facing outputs.

Use `10_TEACHER_ONLY` — not `09_TEACHER_ONLY`.

ADR: `docs/adr/teacher-knowledge-vault/0006-restricted-indexing-teacher-only.md`
