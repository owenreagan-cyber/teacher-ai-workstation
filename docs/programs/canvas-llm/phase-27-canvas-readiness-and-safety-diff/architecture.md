# Architecture

Phase 27 consumes an approved Phase 26 packet, canonicalizes content, matches
it against a validated read-only Canvas snapshot, computes a Safety Diff, and
emits a preview-only deployment manifest plus a local SQLite audit trail.
Nothing in this phase can execute a Canvas mutation.

## Modules (`scripts/canvas_llm_phase27/`)

| Module | Responsibility |
|---|---|
| `models.py` | Validated canonical object model (`DeployableObject`, `SafetyDiffItem`, `Dependency`, `Approval`). Rejects invalid object types, credential-like content, unsafe URLs, and executable-mutation flags. |
| `canonicalize.py` | Deterministic Unicode/whitespace/HTML normalization and four genuinely distinct SHA-256 hash domains: `body_hash`, `metadata_hash`, `placement_hash`, `full_operation_hash`, each extracting its own field subset from the object. |
| `canvas_snapshot.py` | Validated, read-only Canvas snapshot model. Rejects student data, grades, rosters, credentials, and unsafe hosts. Classifies origin as fixture / sanitized-export / local-ignored. |
| `matching.py` | Deterministic matching precedence (saved Canvas ID -> exact slug -> exact title -> approved alias -> unique fuzzy title -> unresolved). Never matches across courses; ambiguous candidates become a `conflict` match result, never an auto-pick. |
| `comparison.py` | Field-level diff between a local desired object and its matched remote object, classified by change kind (material / metadata-only / placement-only / publication-only / date-only). |
| `safety_diff.py` | Orchestrates matching + comparison + dependency + policy state into the seven Safety Diff classifications (CREATE/UPDATE/UNCHANGED/BLOCKED/CONFLICT/OMIT/DELETE_CANDIDATE). Loads subject-assignment policy and archived-course lists from the same canonical `config/curriculum/canvas-course-mappings.json` Phase 22 validates -- no fixture field ever sets a classification directly. |
| `module_placement.py` | Classifies placement as already-correct / needs-placement / needs-reorder / missing-module / ambiguous-module / blocked / omitted, against a real per-course module registry. Never creates a module or module item. |
| `dependency_graph.py` | Cycle detection, deterministic topological ordering, and blocked-dependency propagation (an object depending on a BLOCKED/OMIT/CONFLICT/missing dependency becomes BLOCKED itself). |
| `freshness.py` | fresh/aging/stale/expired/unknown snapshot classification from real timestamps. Unparseable timestamps are `unknown`, never silently `fresh`. |
| `health_checks.py` | ~20 deterministic PASS/WARN/FAIL/BLOCKED/NOT_APPLICABLE checks (snapshot schema, freshness, archived-course protection, module placement, dependency cycles, curriculum policy prohibitions, mutation-disabled state, ledger integrity). No AI judgment. |
| `rollback_plan.py` | Non-executable rollback instructions preserving prior state for UPDATE/CREATE/DELETE_CANDIDATE operations. |
| `transport.py` | `DisabledCanvasTransport`, `SnapshotCanvasTransport`, `FakeCanvasTransport`, gated `OptionalReadOnlyCanvasTransport`. Every mutation method and every non-GET HTTP verb raises `MutationNotAllowedError`. |
| `pagination.py` | Link-header (`rel=next`) pagination: opaque URL following, loop detection, page/item caps. |
| `rate_limit.py` | Bounded, capped-backoff retry policy; 401/403 never retried; `Retry-After` honored. |
| `ledger.py` | Real SQLite-backed deployment ledger (11 tables: schema_migrations, manifests, manifest_revisions, deployment_operations, operation_dependencies, approvals, snapshot_imports, comparison_runs, safety_diff_items, ledger_events, quarantine_events). WAL mode, restart persistence, corruption quarantine, immutable event log. |
| `approval_gate.py` | Approval/revocation keyed on (objectId, manifestRevision, snapshotId) in the ledger -- a revision or snapshot change makes a prior approval read back as unapproved automatically. CONFLICT, blocked, and non-fresh-snapshot operations cannot be approved. |
| `export_package.py` | Generates the 11-file sanitized export package and independently validates it for forbidden content (local paths, credentials, student-data markers) before and after writing. |
| `manifest.py` | Assembles the Deployment Manifest v1 from all of the above: real dependency graph, real freshness-derived readiness, real rollback plan, repo-relative (never absolute) provenance paths. |
| `phase27_readiness.py` | CLI (`build`, `compare`, `validate`, `ledger-status`, `health-check`, `export`, `serve`) and the app-integrated HTTP server (`Phase27RequestHandler`) that serves the real unified workstation directory plus a live `/api/phase27/packet` endpoint computed by real production code. |
| `validate_phase27.py` | Independently recomputes the Safety Diff from the referenced packet and snapshot rather than trusting the manifest's own stored counters. |

## UI integration

`apps/unified-weekly-production/` gained a Phase 27 section with 8 panels
(Canvas Snapshot, Transport Readiness, Safety Diff, Module Placement,
Deployment Manifest, Deployment Ledger, Health Checks, Rollback Plan).
`scripts/canvas_llm_phase26/phase26_workstation.py` (the app's real server)
was extended -- additively only -- with `/api/phase27/packet` (GET),
`/api/phase27/ledger-status` (GET), `/api/phase27/approve` (POST),
`/api/phase27/revoke` (POST), and `/api/phase27/export` (POST). No deploy,
publish, upload, or email control exists anywhere in the UI.

## Safety invariants enforced by construction, not by convention

- `SafetyDiffItem.executable` and `RollbackInstruction.executable` reject any
  value other than `False` at construction time.
- `transport.py`'s mutation methods are generated once via
  `_install_mutation_rejections` and applied to every transport class, so a
  new transport cannot forget to reject a mutation method.
- Approval invalidation is a byproduct of the ledger's lookup key, not a
  separate "invalidate" code path that could be forgotten.
