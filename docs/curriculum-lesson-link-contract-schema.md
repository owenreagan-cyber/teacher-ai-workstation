# Curriculum Lesson Link Contract Schema (Program A7)

Last updated: 2026-07-02

```text
Status: documentation/status only — inactive schema draft
Program: A7 — Curriculum Lesson Link Contract
Validator: none
Runtime: not active
Lesson generation: blocked
Canvas API: blocked
```

## Purpose

Define how resources can later connect to lessons, units, pacing, or Canvas references **without** generating lessons or calling Canvas.

## Field Definitions

| Field | Type (conceptual) | Purpose |
| --- | --- | --- |
| `lesson_link_id` | string | Stable fictional ID (`sample-lesson-link-*`) |
| `course` | string | Course label (placeholder) |
| `unit` | string | Unit label |
| `lesson` | string | Lesson label |
| `pacing_reference` | string | Pacing guide placeholder reference |
| `canvas_reference_future` | string \| null | Reserved Canvas placeholder URI |
| `resource_ids` | string[] | A4 resource IDs (fictional) |
| `manual_alignment_status` | enum | unaligned / aligned_placeholder / needs_review |
| `generation_blocked` | boolean | Must be `true` in inactive samples |

## Fictional Sample (Inactive)

```json
{
  "contract_type": "curriculum_lesson_link_contract",
  "contract_version": "0.0.0-inactive",
  "metadata_only": true,
  "read_only": true,
  "lesson_link_id": "sample-lesson-link-001",
  "course": "Example ELA Course",
  "unit": "Unit 1",
  "lesson": "Lesson 1",
  "pacing_reference": "placeholder://pacing/example-unit-1",
  "canvas_reference_future": "placeholder://canvas/example-future-reference",
  "resource_ids": ["sample-resource-worksheet-001"],
  "manual_alignment_status": "aligned_placeholder",
  "generation_blocked": true
}
```

Canonical inactive file: `assistant/curriculum-builder/metadata-contract/v0/samples/sample-lesson-link-001.json`

## Explicitly Blocked

- Lesson generation, lesson briefs, lesson drafts
- Review note generation
- Canvas content creation or API calls
- Automatic alignment from scanned curriculum

## Non-Activation

Planning links only. No generation or Canvas activation.
