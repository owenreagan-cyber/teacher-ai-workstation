# Curriculum Builder — Registry Authority Map

Last updated: 2026-07-02

```text
Status: documentation/status only
Closure status: complete_registry_authority_map
Production registry writes: blocked
Fixture validation: not production approval
```

## Purpose

Single reference for **which registry surface is authoritative for what**, so future agents and Owen do not confuse fake fixtures, dry-run candidates, planning docs, and the live v0 registry.

**This map does not authorize production writes.** Passing any status command or validator does **not** approve mutation.

---

## Authority Surfaces

| Surface | Path / command | ID pattern | Authority | Writable? |
| --- | --- | --- | --- | --- |
| **Registry v0 (live)** | `assistant/curriculum-builder/registry/v0/registry.json` | `sample-*` | Active read-only v0 metadata store | **No** — validator only |
| **Registry v0.2 dry-run candidates** | `assistant/curriculum-builder/samples/registry-v0-2-dry-run/` | `example-*` | Fake candidate validation only (CB-IMPL-1) | **No** |
| **Registry v0.2 local fixtures** | `assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json` | `example-*` | Fake fixture envelope only (CB-IMPL-2) | **No** |
| **A4–A7 inactive contracts** | `assistant/curriculum-builder/metadata-contract/v0/` | `sample-*` | Planning schemas; inactive | **No** |
| **Production registry** | `assistant/curriculum-builder/registry/v0-2/production-registry.json` | `resource-*` | Owen-approved path; one governed manual metadata record (`resource-math-lesson-108-presentation`) | **Blocked** — write tooling and second record not approved |
| **Curriculum Source Readiness (fake)** | `assistant/curriculum-builder/samples/curriculum-source-readiness/` | `fake-source-*` | Fake metadata inventory only; not production | **No** |

Expected WARN registry: `docs/curriculum-builder-registry-expected-warns.md`

Aggregate lane proof: `bin/chief-of-staff --curriculum-registry-lane-status`

---

## What Each Layer Does

### Registry v0 (`registry/v0/registry.json`)

- Phase 2 Mission 1 live read-only registry
- Fictional `sample-*` placeholder records
- Validated by `scripts/curriculum-registry-v0-validator.sh`
- **Not superseded** by v0.2 fixture work
- **Not writable** without separate Owen-approved production mission

### CB-IMPL-1 — Dry-run (`--curriculum-registry-dry-run-status`)

- Validates single **candidate** JSON files
- Reports `would_write=false`
- Does **not** mutate `registry.json`, samples, or fixtures
- Dry-run PASS **≠** write authorization

### CB-IMPL-2 — Local fake fixtures (`--curriculum-registry-records-status`)

- Committed multi-record **fixture envelope** under `samples/`
- Flags: `fake_fixture_only`, `no_production_write`, `fixture_only`
- Validated by `scripts/curriculum-builder-registry-v0-2-local-records-validate.sh`
- Fixture PASS **≠** production approval
- Must **never** be copied into `registry/v0/registry.json` without explicit mission

### CB-IMPL-3 — Renderer preview (`--curriculum-registry-renderer-status`)

- Reads **fixture envelope only**
- Markdown/text metadata preview to stdout
- No generation, no file export, no production write

### CB-IMPL-4 — Retrieval hooks (`--curriculum-registry-retrieval-status`)

- Filter/lookup over **fixture records only**
- No crawl, no embeddings, no RAG, no live registry query

### A4–A7 cross-validation (`--curriculum-registry-a4-a7-fixture-schema-status`)

- Proves fixture records align with canonical inactive A4–A7 contract field expectations
- Uses `metadata-contract/v0/inactive-manifest.json` and samples as schema reference
- Structural compatibility only — does not activate A4–A7 validators or production registry

### Production planning brief (`--curriculum-production-registry-planning-status`)

- Planning-only: `docs/curriculum-builder-production-registry-workflow-planning-brief.md`
- Owen approval checklist before any implementation
- Production path: `assistant/curriculum-builder/registry/v0-2/production-registry.json` (one approved record; `resource-math-lesson-108-presentation`)
- ID namespace: `resource-*` (Owen-approved)

### Metadata pilot execution planning (`--curriculum-production-registry-metadata-pilot-plan-status`)

- One-record protocol planning only; execution blocked
- Production path: `assistant/curriculum-builder/registry/v0-2/production-registry.json` (one approved record; `resource-math-lesson-108-presentation`)

### Owen § J checklist tracker (`--curriculum-production-registry-owen-checklist-status`)

- Read-only tracker: `docs/curriculum-builder-production-registry-owen-checklist-tracker.md`
- Owen review packet: `docs/curriculum-builder-production-registry-owen-review-packet.md`
- Governance foundation: `docs/curriculum-builder-production-registry-governance-foundation.md`
- Mirrors planning brief § J rows; metadata-boundary refinement complete 2026-07-02; mutation blocked
- Tracker PASS **≠** implementation authorization
- Expected WARN: deferred checklist items 2, 3, 4 (see expected WARNs doc)

### Governance-first foundation (`--curriculum-production-registry-governance-status`)

- CB-PROD-GOV closure: blocked-write proof, candidate path skeleton, planning stubs
- Candidate skeleton: `assistant/curriculum-builder/registry/candidate-v0-2-production/` (sentinel present)
- Governance PASS **≠** write authorization
- Included in aggregate `--curriculum-registry-lane-status`

### Curriculum Source Readiness (`--curriculum-source-readiness-status`)

- Fake metadata inventory: `assistant/curriculum-builder/samples/curriculum-source-readiness/`
- Readiness planning only — **not** real intake or production registry
- Included in aggregate `--curriculum-registry-lane-status`

### Blocked write surfaces (manifest)

| Command | Status |
| --- | --- |
| `--curriculum-registry-write` | **blocked** |
| `--curriculum-scan-folders` | **blocked** |
| `--curriculum-ingest-files` | **blocked** |
| `--curriculum-generate-lesson` | **blocked** |

---

## Decision Rules for Future Agents

1. **Default read authority for “what is the registry?”** → `registry/v0/registry.json` (read-only).
2. **Default for v0.2 experiments** → `samples/registry-v0-2-*` paths only; never treat as production.
3. **Dry-run or fixture validation success** → does **not** authorize `--write` or registry mutation. See `docs/curriculum-builder-registry-dry-run-fixture-promotion-planning-spec.md`.
4. **Production registry path** → `assistant/curriculum-builder/registry/v0-2/production-registry.json` (Owen-approved 2026-07-02); one governed manual metadata record exists; `resource-*` IDs; write tooling and second record blocked until separate missions.
5. **Real metadata, real paths, student data** → separate explicit approval missions.
6. **When unsure** → run `bin/chief-of-staff --curriculum-registry-lane-status` and read this map.

---

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-registry-v0-2-lane-closure.md` | CB-IMPL-1–4 lane closure |
| `docs/curriculum-builder-registry-v0-2-record-boundaries.md` | Fixture vs live boundaries |
| `docs/curriculum-builder-production-registry-workflow-planning-brief.md` | Future production workflow (planning) |
| `docs/curriculum-builder-registry-dry-run-fixture-promotion-planning-spec.md` | Blocked dry-run → fixture promotion seam |
| `docs/curriculum-source-readiness-and-intake-boundary-plan.md` | Fake curriculum source readiness (no real ingestion) |
| `docs/curriculum-source-readiness-fake-inventory-index.md` | Fake source inventory index |
| `docs/proposals/curriculum-builder-registry-lane-discovery-review.md` | Level 2 review |
| `docs/curriculum-registry-v0.md` | Live v0 registry |
| `docs/curriculum-builder-canonical-contract-schemas.md` | A4–A7 contracts |

## Non-Activation

This map does not activate production writes, intake, scanning, generation, APIs, or network behavior.
