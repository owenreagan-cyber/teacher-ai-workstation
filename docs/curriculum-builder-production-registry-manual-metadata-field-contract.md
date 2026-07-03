# Production Registry Manual Metadata Field Contract

Last updated: 2026-07-02

```text
Status: metadata_boundary_refinement_planning
Classification: field contract planning — no production records
Authority: supplements docs/curriculum-builder-production-registry-metadata-source-boundaries.md
```

## Non-Activation

This contract documents **future** governed production record fields. It does not authorize `production-registry.json`, `resource-*` records, writes, or metadata pilot execution.

## Manual-Only Principle

Every allowed field value is **typed by Owen** at write time. No parser, crawler, integration, or AI populates these fields.

## Allowed Field Contract

| Field | Purpose | Value shape | Example (fake) | Blocked content | Validator expectation | Required (future) | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `id` | Stable record identifier | `resource-*` string | `resource-example-unit-alpha-001` | `sample-*`, `example-*` in production | Must match `^resource-[a-z0-9-]+$` | yes | Wrong namespace |
| `title` | Human-readable resource label | Short string ≤ 200 chars | `Sample Unit Alpha Lesson One` | Worksheet text, excerpts | Reject content-length spikes | yes | Content smuggling |
| `subject` | Subject label | Short string | `example-science` | Curriculum body | Reject multi-paragraph text | optional | Low |
| `grade_band` | Grade band label | String or range | `example-grade-5` | Student grade data | No numeric grade lists | optional | Student data |
| `unit_label` | Unit label | Short string | `Unit Alpha Placeholder` | Unit content | Label only | optional | Content smuggling |
| `lesson_label` | Lesson label | Short string | `Lesson 1` | Lesson content | Label only | optional | Content smuggling |
| `resource_type` | Resource category | Enum or short string | `lab_guide` | — | Enum check when defined | optional | Low |
| `audience` | Teacher vs student facing | `teacher_facing` \| `student_facing` | `teacher_facing` | Student identifiers | Enum only | optional | Low |
| `review_state` | § D gate state | Review enum | `approved` | — | Per review-state model | yes | Gate bypass |
| `manual_tags` | Owen tags | String array | `["placeholder", "fake"]` | Content blobs | Max tag length; array size cap | optional | Content smuggling |
| `notes` | Short Owen note | String ≤ 500 chars | `Planning note only` | Worksheet text | Length cap; block content patterns | optional | Content smuggling |
| `source_reference` | Non-resolving source label | Object | See source-reference contract | Resolvable IDs/paths | Nested contract validator | optional | Auto-resolution |
| `created_by` | Provenance | String | `owen` | Student names | Fixed or allowlist | yes | Low |
| `created_at` | Creation timestamp | ISO 8601 | `2026-07-02T00:00:00Z` | — | ISO parse | yes | Low |
| `updated_at` | Update timestamp | ISO 8601 | `2026-07-02T00:00:00Z` | — | ISO parse | yes | Low |

## Future Validator Expectations

| Check | Rule |
| --- | --- |
| Namespace | Production `id` must be `resource-*` only |
| Length caps | `title` ≤ 200; `notes` ≤ 500; each tag ≤ 64 |
| Blocked keys | Reject student-data, integration, embedding, OCR field names |
| Content heuristics | Reject multi-paragraph or answer-key-like patterns in label fields |
| Provenance | `created_by` present; timestamps valid ISO |

## Fake Planning Example

See `assistant/curriculum-builder/samples/metadata-boundary-planning/example-metadata-boundary-record.json` — uses `example-*` ID, not production namespace.

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-metadata-source-boundaries.md` | Canonical boundaries |
| `docs/curriculum-builder-production-registry-source-reference-contract.md` | Nested `source_reference` |
| `docs/curriculum-builder-production-registry-blocked-field-guardrails.md` | Blocked categories |
