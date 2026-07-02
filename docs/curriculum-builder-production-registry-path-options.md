# Production Registry Path Options (Owen Decision Pending)

Last updated: 2026-07-02

```text
Status: planning_only
Classification: path decision support — not implementation authority
Owen checklist item: 1 — Production registry path (pending)
Implementation: blocked until Owen chooses
```

## Purpose

Document **open path options** for a future production registry without selecting one. This doc supports Owen § J checklist item 1. Documenting an option does not approve it.

## Current Committed Surfaces

| Surface | Path | Role today | Production candidate? |
| --- | --- | --- | --- |
| Registry v0 (live read-only) | `assistant/curriculum-builder/registry/v0/registry.json` | Fictional `sample-*` placeholders | **Open** — extend vs replace |
| v0.2 fake fixtures | `assistant/curriculum-builder/samples/registry-v0-2-local-records/` | `fake_fixture_only` envelope | **Not production** |
| Candidate skeleton (blocked) | `assistant/curriculum-builder/registry/candidate-v0-2-production/` | Manual-only path shape; no records | **Planning only** |

## Path Options for Owen

| Option | Shape | Pros | Cons | Default recommendation |
| --- | --- | --- | --- | --- |
| **A — Extend v0** | Keep `registry/v0/registry.json`; add governed write later | Single file; existing validator | Mixes fictional samples with future real IDs | Defer until ID namespace decided |
| **B — New v0.2 production file** | `registry/v0-2/production-registry.json` (example) | Separates v0 samples from production | New validator/migration path | **Lean planning default** — keeps v0 read-only reference |
| **C — Directory of records** | `registry/v0-2/records/*.json` + index manifest | Fine-grained audit per record | More tooling complexity | Later if record count grows |

## Candidate Skeleton (Non-Production)

Until Owen decides, the repo includes a **blocked** candidate directory:

```text
assistant/curriculum-builder/registry/candidate-v0-2-production/
  README.md
  BLOCKED-NO-WRITES.sentinel
  records/   (empty — no production JSON)
```

This skeleton defines a **local-first, manual-only** path shape. It must not receive real records without a separate approved write mission.

## ID Namespace (Checklist Item 10 — Pending)

| Pattern | Example | Notes |
| --- | --- | --- |
| `owen-*` | `owen-ela-unit-04` | Teacher-scoped |
| `resource-*` | `resource-2026-001` | Neutral resource IDs |
| Course-prefixed | `grade5-ela-lesson-12` | Curriculum-organized |

Owen must choose before real records are written.

## Rules Until Decision

- v0 `registry.json` remains read-only
- v0.2 fixtures remain `fake_fixture_only`
- Candidate skeleton remains blocked (sentinel present)
- Dry-run PASS does not authorize promotion or writes

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-registry-authority-map.md` | Authority surfaces |
| `docs/curriculum-builder-production-registry-owen-review-packet.md` | Decision table |
| `docs/curriculum-builder-production-registry-governance-foundation.md` | Governance closure |

## Non-Activation

Choosing or documenting a path option does not activate writes or intake.
