# Curriculum Library Manual Registry Plan

Last updated: 2026-07-04

```text
Status: planning-only — manual entry model only
Real registry file on disk: no
Automatic import/scan: blocked
Student data: blocked — absolute
Proof: assistant/curriculum-library/samples/fake-manual-registry.csv
```

## Purpose

Define how Owen will **manually** record curriculum resource metadata for the local Curriculum Library — one row at a time, human-reviewed — without scanners, importers, or live Drive/NAS resolution.

## Relationship to Curriculum Builder Registry

| Registry | Scope |
| --- | --- |
| Curriculum Builder production registry | Structured lesson/resource records (parked; 1 approved record) |
| Curriculum Library manual registry (this plan) | Source-location metadata for teacher file organization |

They remain separate. This plan does not write to the production registry.

## Manual Entry Principles

- Owen enters rows manually (spreadsheet or future local form).
- Every row starts as `planning_only` or `needs_review`.
- Placeholder URIs only until Owen explicitly approves real path recording.
- No student names, rosters, or grades in registry columns.
- No copied textbook/worksheet/test/answer-key body content in registry fields.

## Planned CSV Columns (v0 Planning)

| Column | Purpose | Example (fictional) |
| --- | --- | --- |
| `registry_id` | Stable id | `fake-lib-reg-001` |
| `title` | Human label | `Placeholder Unit 3 Slides` |
| `resource_type` | Category | `slides`, `worksheet`, `folder_index` |
| `source_system` | Storage class | `local_folder`, `google_drive`, `nas` |
| `source_reference` | Placeholder URI | `local://fake/planning/unit-3-slides` |
| `subject` | Subject label | `science` |
| `grade_band` | Grade band | `SM5` |
| `course` | Course label | `physical_science` |
| `unit` | Unit label | `unit_03` |
| `lesson` | Lesson label | `lesson_02` |
| `canvas_ready` | Canvas export staging flag | `false` |
| `teacher_only` | Teacher-only boundary | `true` |
| `student_facing_allowed` | Student-facing gate | `unknown` |
| `review_status` | Human review | `not_reviewed` |
| `classification_status` | Classification gate | `unclassified` |
| `local_first_safety_flags` | Pipe-separated flags | `fake_local_planning_only\|metadata_only` |
| `activation_status` | Runtime gate | `planning_only` |

See fictional sample: `assistant/curriculum-library/samples/fake-manual-registry.csv`.

## Future Workflow (Blocked Here)

1. Owen creates local library root (future mission).
2. Owen adds files to taxonomy folders manually.
3. Owen adds/edits CSV rows manually.
4. Classification suggestions require gate approval before any runtime.

## Blocked

- Auto-import from Drive/NAS/iCloud
- Folder watchers or sync jobs
- AI-generated registry rows from real file content
- Production registry `--write`

## Non-Activation

Planning columns and fake CSV only. No active registry database or live CSV on Owen's machine from this mission.
