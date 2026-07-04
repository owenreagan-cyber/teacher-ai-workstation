# Curriculum Library Folder Taxonomy

Last updated: 2026-07-04

```text
Status: planning-only — taxonomy on paper only
Real folders on disk: no
Target root (future): ~/TeacherAI-Curriculum-Library/
Proof: assistant/curriculum-library/samples/fake-folder-tree.json
```

## Purpose

Document the **planned** folder layout for Owen's local Curriculum Library before any folder-creation script runs.

## Planned Root

```text
~/TeacherAI-Curriculum-Library/          # NOT CREATED in this mission
```

## Top-Level Taxonomy (Planning)

| Folder | Purpose |
| --- | --- |
| `_inbox/` | Unsorted drops awaiting manual triage |
| `_staging/` | Items being prepared for Canvas export |
| `by-subject/` | Subject-organized working library |
| `by-course/` | Course-organized mirrors (optional duplicate views) |
| `archive/` | Retired or NAS-mirrored references (metadata links only) |
| `teacher-only/` | Assessments, keys, internal notes — never student-facing by default |
| `registry/` | Manual registry CSV and local index files (future) |
| `canvas-ready/` | Folders meeting Canvas-ready definition |

## Subject Branch Example (Fictional)

```text
by-subject/
  science/
    SM5/
      unit-01/
      unit-02/
  history/
    grade-7/
      unit-04/
```

## Naming Conventions (Planning)

- Lowercase slugs with hyphens: `unit-03-lesson-02`
- No student names in folder names — ever
- Date prefixes optional for drafts: `2026-07-draft-slides`
- `_` prefix for system/meta folders (`_inbox`, `_staging`)

## Fake Fixture

Fictional tree for status validation: `assistant/curriculum-library/samples/fake-folder-tree.json`

Classification: `fake_local_planning_only` — paths are placeholders, not created on disk.

## Blocked

- Creating `~/TeacherAI-Curriculum-Library/` or any subfolder
- Scanning existing Drive/NAS paths to auto-build tree
- Symlinks to school systems without explicit future approval

## Next Mission (Not This One)

**Owen-approved local folder creation script** — may create empty skeleton under `~/TeacherAI-Curriculum-Library/` only after explicit approval.

## Non-Activation

Taxonomy documentation and fake JSON only. No filesystem mutations.
