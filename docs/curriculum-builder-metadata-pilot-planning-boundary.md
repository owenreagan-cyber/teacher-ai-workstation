# Curriculum Builder Metadata Pilot — Planning Boundary

Last updated: 2026-07-02

```text
Status: planning_only
Classification: metadata-only pilot planning — no intake
Blocked until: Owen § J items 3, 4, 5 approved + separate mission
```

## Purpose

Define a **future** metadata-only pilot boundary without creating real records or ingesting curriculum. Complements `docs/proposals/blocked/production-registry-real-metadata-intake.md`.

## Metadata vs Content (Pilot Scope)

| Category | Pilot may include (when approved) | Never includes |
| --- | --- | --- |
| Metadata | Owen-entered title, subject, unit, lesson labels | Student names, rosters, grades |
| Source reference | Owen-typed path/URL label string | Auto-fetch, file read, copy |
| Content | — | PDF text, worksheets, answer keys, slides |

## Fake-Only Field Taxonomy Examples (Planning)

These rows use **generic fake placeholders** only:

| field | fake_example | real_allowed_today |
| --- | --- | --- |
| `resource_title` | `sample-unit-alpha-lesson-one` | no |
| `subject_label` | `ela` | no |
| `unit_label` | `sample-unit-alpha` | no |
| `source_reference_label` | `fake-drive-folder-placeholder` | no |
| `review_state` | `draft_fake_fixture` | no |

## Approval Prerequisites

1. Owen approves checklist items 3, 4, 5
2. Owen approves item 2 if metadata will touch production registry
3. Separate scoped implementation or planning mission issued
4. ChatGPT review recommended before implementation prompt

## Manual-First Source Posture

| Source | v1 pilot | Notes |
| --- | --- | --- |
| Manual entry | first | Owen types metadata |
| Labeled local path | later | metadata string only — no scan |
| Drive/NAS/iCloud/Canvas | blocked | separate missions |

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-manual-metadata-boundary.md` | Field boundary detail |
| `docs/curriculum-builder-local-first-storage-reference-model.md` | Files stay external |
| `docs/curriculum-source-readiness-and-intake-boundary-plan.md` | Fake readiness complete |

## Non-Activation

No metadata importers, real titles, real paths, or production registry writes.
