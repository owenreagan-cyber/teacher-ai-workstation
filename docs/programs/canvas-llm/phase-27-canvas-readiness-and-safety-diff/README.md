# Phase 27 Canvas Readiness and Safety Diff

Phase 27 adds a read-only Canvas comparison lane on top of the approved Phase 26 weekly packet. It stays offline by default, uses synthetic fixtures for validation, and never exposes mutation paths.

## Status

- **Phase 27A** (PR #323, `938171b`): initial scaffold — canonicalization, a
  narrow comparison function, and a preview-manifest shape. Real but shallow;
  see `phase-27-gap-audit.md` for what was actually delivered versus the
  approved specification.
- **Phase 27B** (this recovery, branch
  `canvas-llm-phase-27b-full-audit-and-recovery`): implements the missing
  architecture -- canonical object model with validation, genuinely distinct
  body/metadata/placement/full-operation hashes, a validated Canvas snapshot
  model, deterministic object matching (with cross-course rejection and
  ambiguity handling), a dependency graph (cycle detection, blocked
  propagation, topological order), module placement classification, a real
  SQLite-backed deployment ledger with revision/snapshot-bound approval
  invalidation, deterministic health checks, non-executable rollback
  planning, a transport boundary with verified mutation rejection, pagination
  and rate-limit handling for a future live transport, an export package, and
  the remaining unified-workstation UI panels. Pending human review and
  merge.

Phase 27 remains offline by default, fixture-backed by default, preview-only,
read-only, mutation-disabled, teacher-approved, and locally auditable. The
Canvas assignment due-time convention remains owner-unresolved; no due time
has been invented anywhere in this implementation.

See `phase-27-gap-audit.md`, `validator-quality-audit.md`, and
`cross-phase-validator-audit.md` for the audit that preceded this recovery,
and `implementation-report.md` for what Phase 27B actually delivered.
