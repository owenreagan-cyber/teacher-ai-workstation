# Curriculum Builder Manual Metadata Boundary

Last updated: 2026-07-02

```text
Status: planning_only
Classification: field boundary reference — no intake
```

## Purpose

Clarify which metadata fields may eventually appear in a production registry **when a future write mission is approved** — and which fields are permanently prohibited. Canonical boundary record: `docs/curriculum-builder-production-registry-metadata-source-boundaries.md`.

## Allowed Metadata Fields (Future — Owen Approval Required)

| Field family | Examples | Constraints |
| --- | --- | --- |
| Resource labels | title, subject, unit, lesson | Owen-authored only |
| Resource type | worksheet, slide_deck, reference | Enum from planning schema |
| Review state | per review-state model | Human-gated |
| Source reference label | `manual:path-or-url-string` | Owen-typed; no auto-resolution |
| ID | per chosen namespace | No student identifiers |

## Prohibited Fields (Always)

| Field family | Reason |
| --- | --- |
| Student names, IDs, rosters | Student-data prohibition |
| Grades, accommodations, behavior | Student-data prohibition |
| Curriculum content body | Content boundary |
| Textbook excerpts, answer keys | Content boundary |
| Auto-resolved Drive file IDs | Integration boundary |
| Canvas enrollment IDs tied to students | Student-data risk |

## Fake Fixture Alignment

Fake fixtures under `assistant/curriculum-builder/samples/` use generic placeholders (`fake-source-*`, `sample-unit`) — not real curriculum. They validate shape only.

## Chief of Staff Role

Chief of Staff exposes **read-only status** for registry foundations. It is not the curriculum file database. Large files remain in Drive/NAS/iCloud/local folders per local-first model.

## Non-Activation

No field ingestion scripts or real record creation.
