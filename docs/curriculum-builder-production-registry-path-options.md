# Production Registry Path Options (Owen Path Decision Recorded)

Last updated: 2026-07-02

```text
Status: planning_only
Classification: path decision recorded — not implementation authority
Owen checklist item: 1 — Production registry path (approved 2026-07-02)
Implementation: blocked until Phase 2 preflight complete + separate write mission; items 3 and 4 deferred
```

## Purpose

Document **path options** for the future production registry and record Owen's v1 decision. This doc supports Owen § J checklist item 1. Recording a decision does not authorize writes or file creation.

## Owen Decision (Item 1 — Approved 2026-07-02)

**Option B — separate v0.2 production file** is Owen-approved for v1.

**Canonical production path:**

```text
assistant/curriculum-builder/registry/v0-2/production-registry.json
```

| Rule | Detail |
| --- | --- |
| v0 remains fictional | `registry/v0/registry.json` stays read-only `sample-*` reference |
| File does not exist yet | Path is recorded only; creating the file requires item 2 approval + separate write mission |
| Candidate skeleton | `candidate-v0-2-production/` remains blocked planning skeleton; not the canonical production authority |

## Current Committed Surfaces

| Surface | Path | Role today | Production candidate? |
| --- | --- | --- | --- |
| Registry v0 (live read-only) | `assistant/curriculum-builder/registry/v0/registry.json` | Fictional `sample-*` placeholders | **Not production** — remains read-only reference |
| v0.2 fake fixtures | `assistant/curriculum-builder/samples/registry-v0-2-local-records/` | `fake_fixture_only` envelope | **Not production** |
| **Production registry (future)** | `assistant/curriculum-builder/registry/v0-2/production-registry.json` | **Owen-approved path; file not created** | **Approved path — writes blocked** |
| Candidate skeleton (blocked) | `assistant/curriculum-builder/registry/candidate-v0-2-production/` | Manual-only path shape; no records | **Planning only** — not canonical authority |

## Path Options for Owen

| Option | Shape | Status | Notes |
| --- | --- | --- | --- |
| **A — Extend v0** | Keep `registry/v0/registry.json`; add governed write later | **Not selected for v1** | Would mix fictional `sample-*` with future real IDs; rejected for v1 |
| **B — New v0.2 production file** | `registry/v0-2/production-registry.json` | **Owen-approved** | Separates v0 samples from production; smallest first-write scope |
| **C — Directory of records** | `registry/v0-2/records/*.json` + index manifest | **Future evolution** | Valid later if record count grows; not v1 first-write target |

## Candidate Skeleton (Non-Production)

The repo includes a **blocked** candidate directory (directory-shaped planning artifact):

```text
assistant/curriculum-builder/registry/candidate-v0-2-production/
  README.md
  BLOCKED-NO-WRITES.sentinel
  records/   (empty — no production JSON)
```

This skeleton is **not** the canonical production authority. Owen-approved production path is the single JSON file above. The candidate skeleton must not receive real records without a separate approved write mission.

## ID Namespace (Checklist Item 10 — Approved 2026-07-02)

**Owen-approved namespace:** `resource-*`

| Pattern | Example | Status |
| --- | --- | --- |
| `sample-*` | `sample-sm5-textbook-001` | v0 fictional reference only |
| `example-*` | `example-local-record-001` | v0.2 fake fixture language only |
| **`resource-*`** | `resource-sm5-textbook-001` | **Approved for future production records** |
| `resource-*` | `resource-ela-unit04-worksheet-002` | Approved example |
| `resource-*` | `resource-2026-0001` | Approved example |
| `owen-*` | `owen-ela-unit-04` | Not selected |
| Course-prefixed | `grade5-ela-lesson-12` | Not selected for v1 |

**Rules:**

- `sample-*` remains fictional v0 reference
- `example-*` remains fake/local v0.2 fixture language
- `resource-*` is reserved for future approved production registry records
- Do not create `resource-*` records without item 2 approval + separate write mission

## Rules Until Write Mission

- v0 `registry.json` remains read-only
- `production-registry.json` does **not** exist until separate approved write mission
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

Recording path and namespace decisions does not activate writes, file creation, or intake.
