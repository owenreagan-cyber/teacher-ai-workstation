# Curriculum Builder Registry — A4–A7 Fixture Evidence

Last updated: 2026-07-03

```text
Status: documentation/status/fixture evidence only
Closure: complete_a4_a7_fixture_optional_field_enrichment
Classification: fake/local fixtures — not production approval
```

## Purpose

Canonical evidence index for **A4–A7 fake/local fixture optional-field enrichment** on the Curriculum Builder Registry v0.2 local-records lane. PASS on status commands proves fixture/schema coherence only — not real curriculum ingestion or production registry writes.

## Fixture Posture

| Property | Value |
| --- | --- |
| Canonical fixture | `assistant/curriculum-builder/samples/registry-v0-2-local-records/local-registry.json` |
| Schema samples | `assistant/curriculum-builder/metadata-contract/v0/samples/` |
| Inactive manifest | `assistant/curriculum-builder/metadata-contract/v0/inactive-manifest.json` |
| Negative fixtures | `assistant/curriculum-builder/samples/registry-v0-2-local-records/negative/` |
| Production registry | **not mutated** — parked with one governed record |

All content is fake/local labels. No real textbook text, worksheet questions, student data, Drive URLs, NAS paths, or generation prompts.

## A4–A7 Optional-Field Coverage

### A4 — Resource records

| Field | Coverage |
| --- | --- |
| Core required fields | present on both example records |
| Optional `tags` | `["example-tag", "fake-fixture-only"]` on each record |
| Embedded `review_status` (A6-compatible) | `approved_placeholder`, `in_review` |

### A5 — Source references

| Optional field | Coverage |
| --- | --- |
| `source_kind` | `file`, `folder` (fake labels) |
| `owner_context` | `teacher_workstation_planning`, `example-nas-planning-context` |
| `access_notes` | fake planning notes — no API/crawl language implying activation |

All `path_or_url_reference` values use `placeholder://` URI scheme only.

### A6 — Review state

Fixture design **embeds** `review_status` on A4 records. Standalone A6 envelope objects are not required in the v0.2 local-records fixture. Status script reports this as intentional embedded design (PASS), not a missing-schema failure.

### A7 — Lesson links

| Field | Coverage |
| --- | --- |
| `generation_blocked` | `true` on all lesson links |
| `canvas_reference_future` | placeholder URI only |

## Negative Guardrail Coverage

| Negative fixture | Violation tested |
| --- | --- |
| `negative-real-drive-url.json` | Non-placeholder `path_or_url_reference` |
| `negative-student-identifier.json` | Forbidden `student_name` field |
| `negative-generation-not-blocked.json` | `generation_blocked: false` |

## Blocked Boundaries

| Boundary | State |
| --- | --- |
| Real curriculum ingestion | blocked |
| Copied curriculum content | blocked |
| Student data | blocked — absolute |
| Production registry writes | blocked — Option D parked |
| Source auto-resolution | blocked |
| Integrations / API / OAuth | blocked |
| AI generation / lesson runtime | blocked |
| Fixture promotion to production | blocked without Owen mission |

## Relationship to Other Lanes

| Lane | Relationship |
| --- | --- |
| Production registry (parked) | One governed record; fixtures do not add records |
| Renderer Foundation v1 | May consume contract shapes; no runtime render |
| Presentation Engine planning | Separate fake fixtures; no shared production path |
| `--curriculum-registry-lane-status` | Aggregate includes A4–A7 component |

## Status Proof

```bash
bin/chief-of-staff --curriculum-registry-a4-a7-fixture-schema-status
bash scripts/curriculum-builder-registry-a4-a7-fixture-schema-status.sh
bash tests/curriculum-builder-registry-a4-a7-fixture-schema-status-test.sh
```

## What Remains Blocked

- Real curriculum file parsing
- Second production registry record
- Writer scripts / `--write`
- Standalone A6 production envelopes (future production concern)
- Schema activation / runtime validators beyond read-only cross-check

## Non-Activation

`complete_a4_a7_fixture_optional_field_enrichment` is a documentation closure marker only. It does not authorize ingestion, registry mutation, or generation.
