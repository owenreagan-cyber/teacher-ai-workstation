# Curriculum Resource Contract Schema (Program A4)

Last updated: 2026-07-02

```text
Status: documentation/status only — inactive schema draft
Program: A4 — Curriculum Resource Contract
Validator: none
Runtime: not active
Ingestion: blocked
```

## Purpose

Define metadata for a **curriculum resource** without storing, reading, parsing, scanning, indexing, or ingesting resource content.

This contract is a planning schema. It is **not** a validator, **not** connected to file ingestion, and **not** implementation authority by itself.

## Scope

| Allowed (planning) | Blocked |
| --- | --- |
| Field definitions and fictional samples | Reading real resource files |
| Cross-reference to source reference IDs | Scanning folders or drives |
| Teacher Workstation / Chief of Staff doc links | OCR, embeddings, RAG |
| Inactive JSON sample under `metadata-contract/v0/samples/` | Lesson or worksheet generation |

## Field Definitions

| Field | Type (conceptual) | Purpose |
| --- | --- | --- |
| `resource_id` | string | Stable fictional ID (`sample-resource-*`) |
| `title` | string | Human-readable title (placeholder only) |
| `resource_type` | enum | worksheet, study_guide, slides, test, textbook_section, pacing_link, etc. |
| `subject` | string | Subject label (e.g. `Example Math Course`) |
| `grade_band` | string | Grade band label |
| `course` | string | Course label |
| `unit` | string | Unit label |
| `lesson` | string | Lesson label |
| `topic` | string | Topic label |
| `teacher_only` | boolean | Teacher-only resource flag |
| `student_facing_allowed` | boolean | Whether student-facing use may be approved later |
| `review_status` | enum | planned / under_review / approved_placeholder / blocked |
| `source_reference_id` | string | Link to A5 source reference (no resolution) |
| `notes` | string | Teacher planning notes (placeholder text only) |

## Fictional Sample (Inactive)

```json
{
  "contract_type": "curriculum_resource_contract",
  "contract_version": "0.0.0-inactive",
  "metadata_only": true,
  "read_only": true,
  "resource_id": "sample-resource-worksheet-001",
  "title": "Sample Worksheet",
  "resource_type": "worksheet",
  "subject": "Example Math Course",
  "grade_band": "Example Grade 5",
  "course": "Example Math Course",
  "unit": "Unit 1",
  "lesson": "Lesson 1",
  "topic": "Example Topic Placeholder",
  "teacher_only": false,
  "student_facing_allowed": true,
  "review_status": "approved_placeholder",
  "source_reference_id": "sample-source-drive-001",
  "notes": "Fictional placeholder resource metadata only."
}
```

Canonical inactive file: `assistant/curriculum-builder/metadata-contract/v0/samples/sample-resource-001.json`

## Relationship to Registry v0

Registry v0 records overlap conceptually but use the active `registry_id` envelope. A4 defines a **resource contract** shape for future normalization. Registry v0 remains the active read-only store until explicit approval extends it.

## Non-Activation

No file access, no ingestion, no generation, no student data, no real curriculum content.
