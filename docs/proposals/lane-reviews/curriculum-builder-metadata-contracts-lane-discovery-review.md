# Level 2 Lane Discovery Review — Curriculum Builder Metadata Contracts (A4–A7)

Last updated: 2026-07-02

```text
Review level: 2
Lane: Curriculum Builder Metadata Contract Schemas — Programs A4–A7
Prior lane_status: complete_pending_review
New lane_status: reviewed
Implementation: none authorized by this review
```

## Scope Reviewed

`docs/curriculum-builder-canonical-contract-schemas.md`, `assistant/curriculum-builder/metadata-contract/v0/`, `scripts/curriculum-builder-contract-schemas-status.sh`, fixture cross-validation via `--curriculum-registry-a4-a7-fixture-schema-status`.

**Level 1 candidates reviewed:** 1 implemented (A4–A7 fixture cross-validation from CB-REG-HARDEN).

## Findings

**Coherent:** Inactive read-only JSON schemas for A4–A7 contract types. Status script validates schema files, docs, tests, and inactive boundaries.

**Boundaries:** Schemas are planning artifacts — not production registry authority. Cross-validation on fake fixtures does not activate contracts.

**WARNs:** 7 expected WARNs on fixture cross-validation (optional A5 fields, embedded A6 note) — documented, non-blocking.

**Risks:** Agents may treat schema PASS as license to ingest real curriculum — authority map and contracts doc state inactive.

## Proposal Recommendations

| Candidate | Status |
| --- | --- |
| A4–A7 inactive banner in contract status output | **implemented** — contract schemas status banner |
| Schema version alignment with registry v0.2 fixtures | **proposed** |
| Real curriculum parsing mission in blocked/ | **deferred** |
| Contract activation checklist (Owen) | **proposed** |
| Aggregate A4–A7 + registry lane status doc link | **implemented** (registry lane status) |

## Lane Status: `complete_pending_review` → `reviewed`

## Safety Confirmation

Proposal-only. Contracts remain inactive.
