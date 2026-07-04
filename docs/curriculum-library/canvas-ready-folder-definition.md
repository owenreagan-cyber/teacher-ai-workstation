# Canvas-Ready Folder Definition

Last updated: 2026-07-04

```text
Status: planning-only — definition only
Canvas API/LMS integration: blocked
Automatic upload: blocked
Student data: blocked — absolute
```

## Purpose

Define what makes a local Curriculum Library folder **Canvas-ready** for future manual export workflows — without Canvas API, OAuth, or automated upload.

## Canvas-Ready (Planning Definition)

A folder is **Canvas-ready** when Owen has manually verified:

| Criterion | Requirement |
| --- | --- |
| Content reviewed | All files human-reviewed for classroom use |
| Student-facing gate | `student_facing_allowed` explicitly set (not `unknown`) |
| No answer keys exposed | Answer keys remain under `teacher-only/` or flagged `teacher_only=true` |
| File types | PDF, DOCX, PPTX, PNG, or other approved static formats only |
| Naming | No student names in filenames |
| Registry row | Matching manual registry row with `canvas_ready=true` |
| Export bundle | Optional subfolder `_export/` with flattened copies (future manual step) |

## Canvas-Ready Folder Shape (Fictional)

```text
canvas-ready/
  science-sm5-unit-03-lesson-02/
    README.txt              # Owen notes: manual export checklist
    student-facing/         # Files approved for module upload
    teacher-only/           # Never uploaded without review
```

## Relationship to Manual Registry

Registry column `canvas_ready` (see `docs/curriculum-library/manual-registry-plan.md`) marks planning intent only. `true` does not trigger upload.

## Blocked

- Canvas API, LTI, OAuth, or browser automation upload
- Auto-packaging from scanned folders
- Student roster or gradebook linkage
- Real curriculum body content in repo fixtures

## Non-Activation

Definition and cross-links only. No Canvas connection or export runtime.
