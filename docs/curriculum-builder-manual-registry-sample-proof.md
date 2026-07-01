# Curriculum Builder Manual Registry Sample Proof

Last verified: 2026-06-30

## 1. Purpose

This document is a **static fictional manual registry sample proof** for Curriculum Builder. It demonstrates the planned schema shape from `docs/curriculum-builder-manual-registry-schema-plan.md` using seven placeholder rows only.

The sample is **static documentation proof only** aligned with Registry v0 fictional data. Canonical v0 records live in `assistant/curriculum-builder/registry/v0/registry.json` (read-only validation via CLI; **not loaded by app code** for generation, ingestion, or background jobs).

Planning path:

```text
canonical planning index
→ next-stage readiness audit
→ manual registry schema plan
→ manual registry sample proof plan
→ manual registry sample proof (this document)
→ static sample validation plan
→ static sample validation checks
→ sample format decision
→ CSV placeholder sample plan
→ CSV placeholder sample artifact
→ CSV static validation maintenance
→ future Markdown/CSV alignment proof
```

## 2. Non-Activation Statement

This sample proof does **not**:

- create or act as a live registry; this is **not a live registry**
- load into runtime app code; it is **not loaded by app code**
- create a database, SQLite file, Postgres schema, or Supabase schema; it is **not a database**
- create a schema implementation; it is **not a schema implementation**
- serve as parser input; it is **not a parser input**
- serve as an ingestion source; it is **not an ingestion source**
- **does not scan files** or **does not index folders**
- read curriculum documents
- **does not call APIs** or use OAuth
- activate Google Drive, NAS, iCloud, Canvas, or any other integration
- generate lesson briefs, lesson drafts, or review notes
- **does not use student data**
- use real private curriculum paths or live URLs
- copy raw curriculum files into the repo or app-owned storage

Chief of Staff remains a read-only proof/status/reference surface. It does not own raw curriculum files.

## 3. Relationship to Schema Plan and Sample Proof Plan

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-manual-registry-schema-plan.md` | Defines required fields, status values, and schema vocabulary |
| `docs/curriculum-builder-manual-registry-sample-proof-plan.md` | Defines rules for this static sample artifact |
| This document | Seven fictional rows demonstrating schema shape |

Field names follow the manual registry schema plan. Status values in this sample use fictional placeholder enums where noted in the sample proof plan.

## 4. Fictional Data Rules

- All `registry_id` values use the `sample-` prefix.
- All titles include the word **Placeholder**.
- All `source_reference` values use placeholder URI schemes only.
- No real student or staff names appear in any field.
- No live HTTP or HTTPS URL schemes appear in source references.
- No absolute user home paths appear in any field.
- `created_by_manual_entry` is `true` on every row.
- `activation_status` is `planning_only` or `inactive_placeholder` on every row.

## 5. Placeholder URI Rules

Allowed schemes in this sample:

| Scheme | Used for |
| --- | --- |
| `gdrive://placeholder/...` | Google Drive placeholders |
| `nas://placeholder/...` | NAS archive placeholders |
| `local://placeholder/...` | Local folder placeholders |
| `icloud://placeholder/...` | iCloud placeholders |

Prohibited: real Drive URLs, Canvas web URLs, real NAS/iCloud paths, and absolute local home-directory paths.

## 6. Manual Registry Sample Table

Fictional placeholder rows only. **Not a live registry.**

| registry_id | title | resource_type | source_system | source_reference | source_reference_type | subject | grade_band | course | unit | lesson | pacing_reference | teacher_only | student_facing_allowed | review_status | approval_status | local_first_safety_flags | notes | created_by_manual_entry | activation_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sample-sm5-textbook-001 | SM5 Textbook Placeholder | textbook | google_drive | gdrive://placeholder/sm5/textbook | placeholder_uri | science | SM5 | physical_science | unit_01 | lesson_01 | pacing-sm5-u01-l01 | false | unknown | not_reviewed | not_approved | metadata_only,no_student_data,not_indexed,not_scanned,manual_entry,placeholder_only,no_external_resolution,planning_only | Fictional textbook metadata only | true | planning_only |
| sample-sm5-worksheet-folder-001 | SM5 Worksheet Folder Placeholder | folder_index | google_drive | gdrive://placeholder/sm5/worksheet-folder | placeholder_uri | science | SM5 | physical_science | unit_02 | lesson_03 | pacing-sm5-u02-l03 | true | false | needs_review | not_approved | metadata_only,no_student_data,not_indexed,not_scanned,manual_entry,placeholder_only,no_external_resolution,planning_only | Teacher-only folder index placeholder | true | inactive_placeholder |
| sample-history-slides-001 | History Unit Slides Placeholder | slides | nas | nas://placeholder/archive/history-slides | placeholder_uri | history | grade_7 | world_history | unit_04 | lesson_02 | pacing-history-u04-l02 | false | unknown | not_reviewed | placeholder_approved | metadata_only,no_student_data,not_indexed,not_scanned,manual_entry,placeholder_only,no_external_resolution,planning_only | Archive slides placeholder | true | planning_only |
| sample-science-study-guide-001 | Science Study Guide Placeholder | study_guide | nas | nas://placeholder/archive/science-study-guides | placeholder_uri | science | SM5 | physical_science | unit_03 | lesson_01 | none | false | unknown | reviewed_placeholder | placeholder_approved | metadata_only,no_student_data,not_indexed,not_scanned,manual_entry,placeholder_only,no_external_resolution,planning_only | Study guide placeholder | true | inactive_placeholder |
| sample-canvas-export-folder-001 | Canvas Export Folder Placeholder | canvas_export | canvas_export | local://placeholder/canvas-export | placeholder_uri | science | SM5 | physical_science | unit_01 | lesson_02 | pacing-sm5-u01-l02 | true | false | needs_review | blocked_placeholder | metadata_only,no_student_data,not_indexed,not_scanned,manual_entry,placeholder_only,no_external_resolution,planning_only | Canvas export folder placeholder; not a live Canvas URL | true | planning_only |
| sample-teacher-assessment-001 | Teacher-Only Assessment Placeholder | test | local_folder | local://placeholder/teacher-only-assessment | placeholder_uri | science | SM5 | physical_science | unit_02 | lesson_04 | none | true | false | reviewed_placeholder | blocked_placeholder | metadata_only,no_student_data,not_indexed,not_scanned,manual_entry,placeholder_only,no_external_resolution,planning_only,teacher_only_default | Assessment placeholder; teacher-only | true | inactive_placeholder |
| sample-student-practice-001 | Student-Facing Practice Placeholder | worksheet | icloud | icloud://placeholder/student-facing-practice | placeholder_uri | science | SM5 | physical_science | unit_03 | lesson_02 | pacing-sm5-u03-l02 | false | unknown | not_reviewed | not_approved | metadata_only,no_student_data,not_indexed,not_scanned,manual_entry,placeholder_only,no_external_resolution,planning_only | Practice worksheet placeholder; not student-facing until reviewed | true | planning_only |

## 7. Field Coverage Notes

This sample demonstrates:

- **Multiple source systems:** `google_drive`, `nas`, `local_folder`, `icloud`, `canvas_export`
- **Placeholder URI references only:** every `source_reference` uses a `*://placeholder/...` scheme
- **Resource type variety:** textbook, folder_index, slides, study_guide, canvas_export, test, worksheet
- **Teacher-only and student-facing distinctions:** rows with `teacher_only: true` and rows with `student_facing_allowed: unknown`
- **Review and approval status examples:** `not_reviewed`, `needs_review`, `reviewed_placeholder` and `not_approved`, `placeholder_approved`, `blocked_placeholder`
- **Lesson/unit/pacing relationship placeholders:** `course`, `unit`, `lesson`, `pacing_reference` (including `none` where not applicable)
- **Local-first safety flags:** every row includes `no_student_data`, `metadata_only`, `not_indexed`, `not_scanned`, `manual_entry`, `planning_only`
- **Manual-entry marker:** `created_by_manual_entry: true` on all rows
- **Inactive/planning activation:** `planning_only` or `inactive_placeholder` on all rows

This sample does **not** prove data quality, curriculum correctness, legal/copyright status, instructional alignment, or lesson readiness.

## 8. Safety and Review Coverage Notes

- Teacher-only examples: worksheet folder, canvas export, teacher-only assessment (`teacher_only: true`)
- Student-facing practice placeholder: `teacher_only: false`, `student_facing_allowed: unknown` (not approved for student use)
- No row contains student names, IDs, or grades as data fields
- `approval_status` values are fictional placeholders only; no automated approval workflow exists
- `review_status` values are fictional placeholders only; no real review workflow exists

## 9. What This Sample Does Not Do

- It is not imported, parsed, or validated by runtime code in this PR.
- It does not reference real curriculum file contents.
- It does not trigger document scanning, folder indexing, OCR, embeddings, or AI parsing.
- It does not call Google Drive, Canvas, NAS, or iCloud APIs.
- It does not generate lesson briefs, drafts, or review notes.
- It does not imply Teacher Workstation owns raw curriculum files.

## 10. Future Validation Path

Read-only static checks against this document are implemented in `docs/curriculum-builder-static-sample-validation-checks.md` and enforced by `scripts/curriculum-builder-foundation-status.sh`. See `docs/curriculum-builder-static-sample-validation-plan.md` for the validation rule set. Sample format policy: `docs/curriculum-builder-sample-format-decision.md` (Markdown-only canonical format). CSV plan: `docs/curriculum-builder-csv-placeholder-sample-plan.md`. Maintenance: `docs/curriculum-builder-csv-static-validation-maintenance.md`. **Markdown remains canonical; CSV remains secondary.**

Current verification:

```bash
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
```

## 11. Blocked Capabilities

Unless explicitly approved through `docs/curriculum-builder-approval-gate.md` and completed decision intake:

- live registry behavior consumed by app code
- database schema activation
- no document scanning
- no folder scanning
- file indexing
- OCR, embeddings, vector database
- AI parsing, AI summaries, auto-classification
- real lesson generation
- generated lesson briefs or drafts
- real review notes
- student data handling
- Google Drive API, Canvas API, iCloud integration, NAS crawler
- network calls, OAuth, automation, live integrations
- new runtime services or package dependencies

## 12. PR Handoff Checklist

Before follow-on Curriculum Builder PRs:

- [ ] Start from `docs/curriculum-builder-canonical-planning-index.md`
- [ ] Read schema plan, sample proof plan, and this sample proof
- [ ] Complete `docs/curriculum-builder-future-pr-checklist.md`
- [ ] Confirm no app loader or live registry activation
- [ ] Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL
- [ ] Run `bin/chief-of-staff --dashboard` — no FAIL

## Non-Activation confirmation

This manual registry sample proof is static documentation only. It does not add live registry behavior, database tables, parsers, importers, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, or live integrations.
