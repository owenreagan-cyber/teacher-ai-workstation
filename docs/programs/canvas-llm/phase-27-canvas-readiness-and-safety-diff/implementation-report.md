# Implementation Report

## Phase 27A (PR #323, merged)

Introduced deterministic safety-diff scaffolding, a preview manifest shape,
and offline validation fixtures. Real but shallow: see `phase-27-gap-audit.md`
for the concrete evidence. Notably, the status script was 100% hard-coded
`echo` statements, the fixture used `expectedStatus`/`conflict` fields to
force production classifications, `compare` was a no-op, and `validate`
trusted a self-authored constant. None of these represented a deliberate
attempt to mislead -- they read as an honest first pass that stopped at the
scaffold stage -- but the roadmap and status output did not make that scope
gap visible.

## Phase 27B (this recovery)

### What was implemented and verified by direct execution (not just review)

- Canonical object model with real validation (rejects invalid object types,
  credential-like content, unsafe URLs, executable-mutation flags).
- Four genuinely distinct hash domains, each proven independent: a title
  change alters `metadataHash` but not `bodyHash`; a body change alters
  `bodyHash` but not `metadataHash`; a position change alters `placementHash`
  only; a dependency change alters `fullOperationHash` only; timestamps and
  local paths are excluded from every hash.
- A validated Canvas snapshot model, proven to reject student data and
  unsafe hosts.
- Deterministic matching with proven cross-course rejection and
  ambiguity-becomes-conflict behavior (never an auto-pick).
- A dependency graph with proven cycle detection, deterministic topological
  ordering, and blocked-dependency propagation.
- All seven Safety Diff states (CREATE/UPDATE/UNCHANGED/BLOCKED/CONFLICT/
  OMIT/DELETE_CANDIDATE) now emerge from real matching, dependency, and
  policy logic. `expectedStatus` and `conflict` fixture-forcing fields were
  removed entirely; OMIT is grounded in the real, pre-existing
  `assignmentPolicy: disabled` config for History/Science that Phase 22
  already validates.
- Module placement classification (already-correct / needs-placement /
  needs-reorder / missing-module / ambiguous-module / blocked / omitted)
  against a real per-course module registry.
- A real SQLite-backed deployment ledger (11 tables, WAL mode), proven to
  persist across process restart, quarantine a corrupted database file, and
  never modify a `ledger_events` row once written.
- Approval invalidation proven real: an approval is keyed on (objectId,
  manifest revision, snapshot id); bumping the revision or changing the
  snapshot makes a prior approval read back as unapproved with no separate
  "invalidate" step to forget. CONFLICT, blocked, and non-fresh-snapshot
  operations are proven un-approvable.
- Freshness classification (fresh/aging/stale/expired/unknown) from real
  timestamps; stale/expired/unknown block readiness.
- ~20 deterministic health checks, proven to flag real conditions (archived
  courses, missing/ambiguous modules, dependency cycles, ledger integrity,
  mutation-disabled state) rather than printing static text.
- Non-executable rollback planning for UPDATE/CREATE/DELETE_CANDIDATE.
- A transport boundary (`DisabledCanvasTransport`, `FakeCanvasTransport`,
  `SnapshotCanvasTransport`, gated `OptionalReadOnlyCanvasTransport`), proven
  to reject all 13 named mutation methods and every non-GET HTTP verb by
  actually calling them and catching `MutationNotAllowedError`.
- Pagination (opaque `rel=next` following, loop/cap detection) and a bounded
  retry policy (401/403 never retried, `Retry-After` honored) for a future
  live transport -- built and unit-proven, not yet exercised against a real
  network call (none occurred in this mission).
- A real CLI: `build` writes to the ledger; `compare` and `validate`
  independently recompute and were proven to fail against a hand-tampered
  manifest (the prior versions would have stayed green); `ledger-status`
  inspects the real database; `health-check` and `export` are new,
  previously-missing subcommands; `serve` now serves the real app directory
  plus a live, production-computed `/api/phase27/packet` endpoint instead of
  a generic directory listing.
- The status script and test suite were fully rewritten: every PASS line now
  corresponds to a real function call, subprocess invocation, or database
  check, and both were proven to fail (deleting `ledger.py` dropped the
  status script to 6 real FAILs and a nonzero exit) rather than staying
  green regardless of what's broken.
- 8 UI panels (Canvas Snapshot, Transport Readiness, Safety Diff, Module
  Placement, Deployment Manifest, Deployment Ledger, Health Checks, Rollback
  Plan) added to the real unified workstation app, backed by new,
  additive-only endpoints on Phase 26's actual server
  (`/api/phase27/packet`, `/api/phase27/ledger-status`,
  `/api/phase27/approve`, `/api/phase27/revoke`, `/api/phase27/export`).
  Approve/Revoke exercised live over HTTP against the real ledger. No
  deploy/publish/upload/email button exists.

### Two real bugs found and fixed during this recovery

1. `DEFAULT_LEDGER_PATH` / `DEFAULT_EXPORT_ROOT` were relative paths, which
   silently resolved under `apps/unified-weekly-production/` (not the repo
   root) once Phase 26's `serve` command changed the working directory.
   Fixed to be absolute; regression tests added.
2. The manifest's `provenance` field leaked an absolute local filesystem path
   -- caught by the export package's own forbidden-content scanner. Fixed to
   store repo-relative paths; regression test added.

### Known limitations carried forward (not hidden)

- Drift detection is a simplified heuristic derived from comparison status
  and field-diff kinds (Part 14 of the full spec describes 10 categories
  including "manual Canvas edit" vs. "expected local change" distinguished by
  a previously-deployed hash; that hash is not yet persisted per object
  across builds, so this distinction is not yet made).
- Resource-link verification is not implemented; the corresponding health
  check reports `NOT_APPLICABLE` honestly rather than a fabricated PASS.
- The optional live read-only transport is gated and unit-tested but not
  wired to a real HTTP client; no live Canvas request occurred or can occur
  through it in this mission.
- Pagination/rate-limit modules are unit-proven in isolation; they are not
  yet exercised through an end-to-end live request because no live transport
  exists to drive them.

None of these limitations weaken an existing safety guarantee; they are
scope not yet built, and are listed here rather than implied to be done.
