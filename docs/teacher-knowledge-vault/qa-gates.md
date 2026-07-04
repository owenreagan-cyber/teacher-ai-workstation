# Teacher Knowledge Vault — Three-Level QA Gates

Last updated: 2026-07-04

## Gate 1 — Build Quality

TypeScript/lint/tests, status scripts pass, no runtime commands without manifest + ADR.

## Gate 2 — Architecture Quality

Engine boundaries, connector contract compliance, no shortcuts around review/approval, ADR for architecture changes.

## Gate 3 — Product Quality

`10_TEACHER_ONLY` restricted-indexable, `99_DO_NOT_SCAN` exclusion, cost limits, approval workflow, rollback, no auto-destructive ops, pacing-aware leakage checks.

ADR: `docs/adr/teacher-knowledge-vault/0009-governance-qa-cost-controls.md`
