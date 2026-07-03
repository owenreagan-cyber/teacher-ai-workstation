# Production Registry Metadata and Source-Reference Boundaries

Last updated: 2026-07-02

```text
Status: metadata_boundary_refinement_complete
Classification: Owen decision record + refinement closure — planning only, no intake
Closure: metadata_boundaries_approved_awaiting_pilot_and_write_missions
Proof: --curriculum-production-registry-metadata-boundary-status
```

## Non-Approval Statement

```text
Approving items 3 and 4 records boundary policy only.
Metadata-boundary refinement documents field contracts and guardrails only.
It does not authorize production-registry.json creation.
It does not authorize resource-* records.
It does not authorize --write or writer scripts.
It does not authorize sentinel removal.
It does not authorize metadata pilot execution.
It does not authorize real curriculum file reading, copied content, integrations, scanning, OCR, embeddings, RAG, generation, or auto-ingest.
```

## Owen § J Decisions (2026-07-02)

| Item | Status | Boundary |
| --- | --- | --- |
| 3 Real curriculum metadata | **approved** | Manual Owen-entered descriptive metadata only |
| 4 Real source references | **approved** | Manual non-resolving source-reference labels typed by Owen only |

### Item 3 — Approved Wording

Manual Owen-entered descriptive metadata only (title, subject, grade band, unit, lesson, resource type, teacher/student-facing flag, review state, manual tags, notes); no copied curriculum content, no student data, no file parsing, no OCR, no AI summaries, no embeddings/RAG, no auto-ingest.

### Item 4 — Approved Wording

Manual non-resolving source-reference labels typed by Owen only (display label, source_type enum, citation/note string); no API/OAuth, no live Drive/Canvas/NAS/iCloud access, no auto-resolution, no crawling/scanning, no real file reads, no resolvable file IDs or paths.

## Manual-Only Metadata Principle

- All metadata values are **typed by Owen** at write time.
- No file reads, parsers, crawlers, or integrations populate fields.
- Labels describe resources; they do not contain resource content.

## Non-Resolving Source-Reference Principle

- `source_type` values are **label semantics only** — never credentials, IDs, paths, API targets, or fetch targets.
- Allowed `source_type` values: `manual_label`, `print_resource`, `drive_label`, `local_label`, `nas_label`, `icloud_label`, `canvas_label`.
- Strings are opaque human-readable notes; code must not resolve or fetch from them.

## Contract Documents (Refinement)

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-manual-metadata-field-contract.md` | Allowed metadata fields with validator expectations |
| `docs/curriculum-builder-production-registry-source-reference-contract.md` | Allowed `source_reference` shape |
| `docs/curriculum-builder-production-registry-blocked-field-guardrails.md` | Blocked categories and future validator rules |

## Allowed Metadata Fields (Summary)

| Field | Notes |
| --- | --- |
| `id` | `resource-*` namespace in production (item 10) |
| `title`, `subject`, `grade_band`, `unit_label`, `lesson_label` | Owen-typed labels |
| `resource_type`, `audience`, `review_state`, `manual_tags`, `notes` | Descriptive metadata |
| `source_reference` | Non-resolving object per source-reference contract |
| `created_by`, `created_at`, `updated_at` | Provenance and audit |

## Allowed Source-Reference Shape (Planning)

```json
{
  "source_reference": {
    "display_label": "Sample textbook — teacher shelf copy",
    "source_type": "print_resource",
    "location_note": "Example binder, shelf row placeholder",
    "citation_note": "Optional non-resolving note"
  }
}
```

## Blocked Categories (Summary)

Curriculum content, student data, auto-ingest, ML/search artifacts, resolvable source IDs, live fetch URLs, integration artifacts, scanning output, batch/promotion. See blocked-field guardrails doc for full list and validator expectations.

## Fake Planning Example

`assistant/curriculum-builder/samples/metadata-boundary-planning/example-metadata-boundary-record.json` — `example-*` ID, planning-only flags, not production authority.

## Validation / Readiness Expectations

| Surface | Command |
| --- | --- |
| Metadata boundary status | `--curriculum-production-registry-metadata-boundary-status` |
| Planning fixture validator | `scripts/curriculum-builder-production-registry-metadata-boundary-validate.sh` |

Negative guardrails: no `production-registry.json`, no `resource-*` production records, sentinel intact, no writer, no pilot execution.

## Future Mission Prerequisites

| Mission | Prerequisites |
| --- | --- |
| Metadata-boundary refinement | **Complete** — this mission |
| Empty-file mission | Refinement complete; separate explicit prompt |
| Governed single-record write | Empty file + snapshot/rollback; separate prompt |
| Metadata pilot execution | Refinement + separate pilot mission |

## Metadata Pilot Boundary

Pilot **planning** is documented in `docs/curriculum-builder-metadata-pilot-planning-boundary.md`. Pilot **execution** remains blocked.

## Source-Reference Pilot Boundary

Manual non-resolving labels only when a future write mission is approved. No auto-resolution, no integration fetch.

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-owen-checklist-tracker.md` | Canonical Owen decisions |
| `docs/curriculum-builder-manual-metadata-boundary.md` | Legacy field boundary reference |
| `docs/curriculum-builder-metadata-pilot-planning-boundary.md` | Pilot planning — execution blocked |
| `docs/curriculum-builder-production-registry-phase-2-preflight.md` | Phase 2 closure |
| `docs/proposals/backlog/production-registry-write-mission.md` | Write mission backlog |

## Non-Activation

This document does not activate intake, writes, pilots, or integrations.
