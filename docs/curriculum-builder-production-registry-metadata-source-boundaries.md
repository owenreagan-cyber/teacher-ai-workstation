# Production Registry Metadata and Source-Reference Boundaries

Last updated: 2026-07-02

```text
Status: metadata_boundaries_approved
Classification: Owen decision record — planning only, no intake
Closure: metadata_boundaries_approved_awaiting_pilot_and_write_missions
```

## Non-Approval Statement

```text
Approving items 3 and 4 records boundary policy only.
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

## Manual-Only Semantics

- All metadata and source-reference values are **typed by Owen** at write time.
- No file reads, parsers, crawlers, or integrations populate fields.
- Labels describe resources; they do not contain resource content.

## Non-Resolving Source-Reference Semantics

- `source_type` values are **label semantics only** — never credentials, IDs, paths, API targets, or fetch targets.
- Allowed `source_type` values: `manual_label`, `print_resource`, `drive_label`, `local_label`, `nas_label`, `icloud_label`, `canvas_label`.
- Strings are opaque human-readable notes; code must not resolve or fetch from them.

## Allowed Metadata Fields (Planning — First Governed Record)

| Field | Notes |
| --- | --- |
| `id` | `resource-*` namespace (item 10) |
| `title` | Owen-typed short label |
| `subject` | Owen-typed |
| `grade_band` | Owen-typed |
| `unit_label` | Label only |
| `lesson_label` | Label only |
| `resource_type` | Enum or Owen-typed |
| `audience` | `teacher_facing` / `student_facing` |
| `review_state` | § D gate model (item 7) |
| `manual_tags` | Owen-typed tags array |
| `notes` | Short Owen note — not worksheet text |
| `source_reference` | See allowed shape below |
| `created_by` | Provenance |
| `created_at` / `updated_at` | Audit timestamps |

## Allowed Source-Reference Shape (Planning Only)

```json
{
  "source_reference": {
    "display_label": "Grade 5 Science textbook — teacher shelf copy",
    "source_type": "print_resource",
    "location_note": "Blue binder, classroom shelf row 2",
    "citation_note": "Optional Owen note — non-resolving"
  }
}
```

## Blocked Metadata and Source-Reference Categories

| Category | Blocked examples |
| --- | --- |
| Curriculum content | Worksheet text, textbook excerpts, answer keys, assessment questions, rubric body |
| Student data | Names, rosters, grades, accommodations, IEP details, student work |
| Auto-ingest | OCR output, file hashes from reading real files, extracted PDF metadata, AI summaries |
| ML / search | Embeddings, vector IDs, RAG chunks |
| Resolvable source IDs | Drive file ID, Canvas course/module ID, NAS mount path, iCloud path usable by code |
| Live fetch URLs | URLs intended for integration fetch |
| Integration artifacts | OAuth tokens, API keys, webhook URLs |
| Scanning output | Crawler-discovered paths, folder indexes, directory listings |
| Batch / promotion | Import manifests, dry-run auto-promotion, bulk record arrays |

## First Governed Production Record (Planning Shape Only)

```json
{
  "id": "resource-sm5-science-unit3-001",
  "title": "Grade 5 Science — Unit 3 Lab Guide",
  "subject": "Science",
  "grade_band": "5",
  "unit_label": "Unit 3: Ecosystems",
  "lesson_label": "Lesson 2",
  "resource_type": "lab_guide",
  "audience": "teacher_facing",
  "review_state": "approved",
  "manual_tags": ["ecosystems", "lab"],
  "notes": "Planning example only — not a real record",
  "source_reference": {
    "display_label": "Grade 5 Science textbook — teacher shelf copy",
    "source_type": "print_resource",
    "location_note": "Blue binder, classroom shelf row 2",
    "citation_note": "Non-resolving label only"
  },
  "created_by": "owen",
  "created_at": "2026-07-02T00:00:00Z",
  "updated_at": "2026-07-02T00:00:00Z"
}
```

**This shape is planning documentation only.** No production file or record exists.

## Future Mission Prerequisites

| Mission | Prerequisites |
| --- | --- |
| Metadata-boundary refinement | Items 3 and 4 approved (this doc); Phase 2 preflight complete |
| Empty-file mission | Boundary refinement docs/status/tests; separate explicit prompt |
| Governed single-record write | Empty file exists; snapshot/rollback ready; separate explicit prompt |
| Metadata pilot execution | Boundary refinement + separate pilot mission — not authorized by this sync |

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-owen-checklist-tracker.md` | Canonical Owen decisions |
| `docs/curriculum-builder-manual-metadata-boundary.md` | Field boundary reference |
| `docs/curriculum-builder-metadata-pilot-planning-boundary.md` | Pilot planning — execution blocked |
| `docs/curriculum-builder-production-registry-phase-2-preflight.md` | Phase 2 closure |
| `docs/proposals/backlog/production-registry-write-mission.md` | Write mission backlog |

## Non-Activation

This document does not activate intake, writes, pilots, or integrations.
