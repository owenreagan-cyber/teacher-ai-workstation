# First Production Record — Owen Manual Entry Worksheet

Last updated: 2026-07-02

```text
Status: planning_only
Classification: blank worksheet template — not a production record
Usage: Owen fills by hand before future governed single-record write mission
```

## Non-Activation

This worksheet is **not** a JSON record. Do not commit filled real school content without a separate approved write mission. Use placeholders until execution is explicitly authorized.

## Instructions

1. Copy this template locally when preparing for the write mission.
2. Replace `<placeholder>` values with Owen-approved manual labels only.
3. Do not paste curriculum excerpts, student data, resolvable paths, file IDs, or URLs.
4. `source_reference` fields are non-resolving labels only.

## Record Fields (Blank Template)

| Field | Value (Owen enters) |
| --- | --- |
| `id` | `<resource-placeholder-example-001>` |
| `title` | `<short-placeholder-title>` |
| `subject` | `<placeholder-subject-label>` |
| `grade_band` | `<placeholder-grade-band>` |
| `unit_label` | `<placeholder-unit-label>` |
| `lesson_label` | `<placeholder-lesson-label>` |
| `resource_type` | `<placeholder-resource-type>` |
| `audience` | `<teacher_facing \| student_facing>` |
| `review_state` | `<draft \| pending_review \| approved>` |
| `manual_tags` | `<tag-one>, <tag-two>` |
| `notes` | `<short-planning-note-only>` |

## Source Reference (Non-Resolving)

| Field | Value (Owen enters) |
| --- | --- |
| `source_reference.display_label` | `<placeholder-source-label>` |
| `source_reference.source_type` | `<placeholder-source-type>` |
| `source_reference.location_note` | `<non-resolving-location-note>` |
| `source_reference.citation_note` | `<non-resolving-citation-note>` |

## Provenance

| Field | Value (Owen enters) |
| --- | --- |
| `created_by` | `Owen` |
| `created_at` | `<ISO-8601-UTC-placeholder>` |
| `updated_at` | `<ISO-8601-UTC-placeholder>` |

## Pre-Write Sign-Off (Future Mission)

| Check | Owen initial | Date |
| --- | --- | --- |
| Worksheet reviewed against acceptance criteria | | |
| No curriculum excerpts in any field | | |
| No student data | | |
| Source reference is label-only | | |
| `review_state` is `approved` before write | | |
| Go/no-go checklist PASS | | |

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-metadata-pilot-execution-plan.md` | Pilot protocol |
| `docs/curriculum-builder-production-registry-first-record-acceptance-criteria.md` | Acceptance criteria |
| `docs/curriculum-builder-production-registry-manual-metadata-field-contract.md` | Allowed fields |

## Non-Activation

Filling this worksheet does not authorize writing to `production-registry.json`.
