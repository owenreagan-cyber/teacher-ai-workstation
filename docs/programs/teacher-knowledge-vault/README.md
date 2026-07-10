# Teacher Knowledge Vault

The Teacher Knowledge Vault is the canonical resource-intelligence layer for Teacher AI Workstation.

It organizes curriculum resources across:

- local storage
- Google Drive
- NAS
- Canvas references
- future teacher applications

These systems must not become competing sources of truth.

## Goals

- one logical identity per curriculum resource
- human-readable folder organization
- machine-readable metadata
- safe bulk intake
- smart rename proposals
- exact and near-duplicate detection
- teacher-only and student-facing safeguards
- resource-to-lesson/test relationships
- reversible move and rename operations
- Google Drive and NAS synchronization
- missing-resource detection
- reusable resources across planning, worksheets, slides, Canvas, and local AI

## Storage model

One storage root is configured as canonical.

Other locations are mirrors, caches, exports, or references.

Teacher AI Workstation stores:

- metadata
- hashes
- relationships
- operation history
- synchronization state
- thumbnails
- indexes

Large curriculum binaries do not belong in Git.

## Intake workflow

1. Detect a file in `00_INBOX_UNSORTED`.
2. Calculate SHA-256.
3. Check exact duplicates.
4. Extract safe metadata.
5. Classify subject, curriculum, type, and sequence.
6. Detect teacher-only or student-facing sensitivity.
7. Suggest canonical filename.
8. Suggest destination.
9. Show confidence and reasoning.
10. Require approval.
11. Perform reversible copy, move, or rename.
12. Verify destination.
13. Update manifest and indexes.

AI suggestions may never directly delete, overwrite, share, or upload files.

## Duplicate detection

- Exact duplicate: identical SHA-256
- Probable duplicate: identical normalized text or high page-image similarity
- Possible duplicate: filename, subject, sequence, page count, and metadata similarity
- Related variant: blank/completed, teacher/student, worksheet/key, or current/archive edition

Related variants must not be merged as duplicates.

## Canonical filename grammar

`SUBJECT_RESOURCE_SEQUENCE_VARIANT_VERSION.ext`

Examples:

- `SM5_Lesson_005_Student_Textbook_v1.pdf`
- `SM5_Power_Up_A_Practice_v1.pdf`
- `SM5_Study_Guide_012_Blank_v1.pdf`
- `SM5_Study_Guide_012_Completed_v1.pdf`
- `RM4_Lesson_025_Comprehension_C_Page_114_v1.pdf`
- `SPELL_Test_024_Master_List_v1.pdf`
- `ELA4_Chapter_09_CP_031_v1.pdf`

Renames require:

- preview
- collision detection
- approval
- verification
- undo data

## Teacher-only boundary

Teacher-only material must never be:

- linked into student-facing Canvas content
- included in student-facing RAG results
- placed into newsletters or announcements
- shared automatically
- copied into student-facing exports

Answer keys and assessment masters require explicit sensitivity metadata.

## Initial folder taxonomy

- `00_INBOX_UNSORTED`
- `01_MATH`
- `02_READING_MASTERY`
- `03_SPELLING`
- `04_LANGUAGE_ARTS`
- `05_WRITING`
- `06_HISTORY`
- `07_SCIENCE`
- `08_CLASSROOM_APPS`
- `09_PACING_GUIDES`
- `10_TEACHER_ONLY`
- `11_STUDENT_FACING`
- `90_ARCHIVE`
- `99_DO_NOT_SCAN`

The folder taxonomy may evolve without changing stable resource IDs.
