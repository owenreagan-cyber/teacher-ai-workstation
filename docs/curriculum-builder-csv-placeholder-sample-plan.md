# Curriculum Builder CSV Placeholder Sample Plan

Last verified: 2026-06-30

## 1. Purpose

This document plans a **future CSV placeholder sample** for the Curriculum Builder manual registry proof stack. PR #139 decided that Markdown remains the canonical sample format and that CSV is the preferred future secondary format candidate. This PR defines CSV-specific safety rules, field mapping, static-check expectations, and future PR boundaries **before any CSV file is created**.

This is a **planning document only**. It does not create a CSV artifact, parser, importer, loader, or runtime validator.

Planning path:

```text
canonical planning index
→ next-stage readiness audit
→ manual registry schema plan
→ manual registry sample proof plan
→ manual registry sample proof
→ static sample validation plan
→ static sample validation checks
→ sample format decision
→ CSV placeholder sample plan (this document)
→ future CSV placeholder sample artifact
```

## 2. Non-Activation Statement

This CSV placeholder sample plan does **not**:

- create a CSV, JSON, YAML, or database sample artifact
- create a parser, importer, loader, or runtime validator
- create a live registry consumed by app code
- create a database, SQLite file, Postgres schema, or Supabase schema
- create a schema implementation
- scan curriculum files or index folders
- resolve placeholder URIs
- call APIs or use OAuth
- activate Google Drive, Canvas, NAS, or iCloud integrations
- generate lesson briefs, lesson drafts, or review notes
- use AI parsing, OCR, embeddings, or summaries
- use student data
- add network calls, background jobs, automation, or new package dependencies

Chief of Staff remains a read-only proof/status/reference surface. This PR plans future documentation format policy only.

## 3. Relationship to Sample Format Decision

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-sample-format-decision.md` | Records Markdown-only canonical format; names CSV as future secondary candidate |
| `docs/curriculum-builder-manual-registry-sample-proof.md` | Canonical seven-row Markdown sample |
| `docs/curriculum-builder-static-sample-validation-checks.md` | Static checks on the Markdown sample |
| This document | CSV-specific safety rules and future artifact expectations |

The format decision must be read before any future CSV artifact PR. Markdown remains canonical even after a CSV placeholder is added.

## 4. Current Canonical Sample

The canonical sample proof remains **Markdown documentation only**:

```text
docs/curriculum-builder-manual-registry-sample-proof.md
```

A future CSV sample would be a **secondary static placeholder artifact only**. It must not replace, override, or supersede the Markdown sample as the canonical planning proof.

## 5. Why CSV Is a Future Secondary Candidate

CSV is the preferred future secondary format because:

- it matches tabular registry thinking without JSON/YAML parser semantics
- prior planning already identified `docs/examples/curriculum-builder-manual-registry-sample.csv` as a candidate path
- it can mirror the seven Markdown rows for validator **planning** on paper
- it supports future static text checks without requiring a runtime loader

CSV is more machine-readable than Markdown, so it requires stronger non-activation language than the Markdown sample.

## 6. Why No CSV File Is Added Yet

This PR does not create the CSV file because:

- PR #139 required CSV-specific safety planning before any artifact exists
- adding CSV before this plan would split proof surfaces without documented guardrails
- static validation for CSV must be designed alongside the artifact, not retrofitted
- no approved PR has yet authorized the fictional CSV rows

**No CSV file is created in this PR.**

## 7. CSV-Specific Safety Rules

CSV is more machine-readable than Markdown, so it needs stronger non-activation language:

- CSV must be stored under `docs/examples/` or another clearly documentation/example-only path
- CSV must not be referenced by runtime commands as input
- CSV must not be imported by app code
- CSV must not be parsed by a loader
- CSV must not be used to populate a database
- CSV must not be treated as a real registry
- CSV must not contain real file paths, live URLs, real identifiers, student data, copyrighted excerpts, generated lesson text, or review notes
- CSV validation must remain static, repo-local, text-based, and dependency-free

**CSV quoting expectations:**

- keep sample values simple
- avoid multiline cells
- avoid commas inside unquoted values; quote cells when needed
- use pipe-delimited safety flags inside one field (for example `manual_entry|placeholder_only|no_external_resolution`)
- keep booleans as lowercase `true` or `false`
- keep activation statuses limited to `planning_only` or `inactive_placeholder`

## 8. Future CSV Artifact Scope

Future approved artifact path (candidate only):

```text
docs/examples/curriculum-builder-manual-registry-sample.csv
```

This file **must not** be created in this PR.

If a future approved PR creates it, the file must:

- contain fictional placeholder rows only
- mirror the seven Markdown sample concepts
- use the same required field names as CSV headers
- use placeholder URI references only
- avoid live URLs and real paths
- avoid student data
- avoid copyrighted excerpts
- avoid generated lesson content
- avoid generated review notes
- remain static documentation/example data only
- not be read by app code
- not be imported by any command
- not be treated as a live registry

## 9. Future CSV Field Mapping

Each CSV column maps one-to-one to the manual registry schema plan and Markdown sample table header. A future CSV sample must use the same field vocabulary — no renamed columns, no omitted required fields, no extra implementation-specific columns without an approved schema plan update.

Boolean fields (`teacher_only`, `student_facing_allowed`, `created_by_manual_entry`) use lowercase `true` or `false`.

`local_first_safety_flags` may use pipe-delimited tokens inside one quoted CSV cell to avoid comma conflicts (for example `metadata_only|no_student_data|not_indexed|not_scanned|manual_entry|placeholder_only|no_external_resolution|planning_only`).

## 10. Required CSV Columns

A future CSV sample must use these required columns exactly:

```text
registry_id
title
resource_type
source_system
source_reference
source_reference_type
subject
grade_band
course
unit
lesson
pacing_reference
teacher_only
student_facing_allowed
review_status
approval_status
local_first_safety_flags
notes
created_by_manual_entry
activation_status
```

A future CSV artifact PR must verify the header row matches this list exactly or document any deliberate deviation in the PR description and planning docs.

## 11. Future CSV Row Coverage

A future CSV sample should mirror the seven Markdown sample concepts:

1. SM5 textbook placeholder
2. SM5 worksheet folder placeholder
3. history unit slides placeholder
4. science study guide placeholder
5. Canvas export folder placeholder
6. teacher-only assessment placeholder
7. student-facing practice placeholder

Expected future fictional `registry_id` values:

```text
sample-sm5-textbook-001
sample-sm5-worksheet-folder-001
sample-history-slides-001
sample-science-study-guide-001
sample-canvas-export-folder-001
sample-teacher-assessment-001
sample-student-practice-001
```

Expected future placeholder `source_reference` values:

```text
gdrive://placeholder/sm5/textbook
gdrive://placeholder/sm5/worksheet-folder
nas://placeholder/archive/history-slides
nas://placeholder/archive/science-study-guides
local://placeholder/canvas-export
local://placeholder/teacher-only-assessment
icloud://placeholder/student-facing-practice
```

These are **future CSV row expectations only**. This PR does not create the rows.

## 12. Placeholder URI Rules

Allowed placeholder URI scheme prefixes in a future CSV sample:

| Scheme | Example |
| --- | --- |
| `gdrive://placeholder/` | `gdrive://placeholder/sm5/textbook` |
| `nas://placeholder/` | `nas://placeholder/archive/history-slides` |
| `local://placeholder/` | `local://placeholder/canvas-export` |
| `icloud://placeholder/` | `icloud://placeholder/student-facing-practice` |

Every `source_reference` must use `source_reference_type: placeholder_uri`.

Placeholder URIs must not be resolved, opened, or validated against external storage.

## 13. Prohibited Reference Rules

A future CSV sample must **not** contain:

| Prohibited pattern | Reason |
| --- | --- |
| `https://drive.google.com` | Live Google Drive URL |
| `canvas.instructure.com` | Live Canvas URL |
| `file:///Users/` | Absolute user home file URI |
| `/Users/` | Absolute local user path marker |
| `C:\Users\` | Windows user home path |
| `http://` | Live HTTP URL scheme |
| `https://` | Live HTTPS URL scheme (except in prohibition documentation outside the CSV file) |

Prohibited patterns must not appear in CSV data rows. Planning docs may describe prohibitions without embedding live examples in the CSV artifact.

## 14. Fictional Data Rules

Future CSV rows must follow the same fictional data rules as the Markdown sample:

- all `registry_id` values use the `sample-` prefix
- all titles include the word **Placeholder**
- no real student or staff names
- no real curriculum file contents
- `created_by_manual_entry` is `true` on every row
- `activation_status` is `planning_only` or `inactive_placeholder` on every row
- review and approval status values are fictional placeholders only

## 15. Safety and Review Status Rules

Future CSV rows must represent:

**Review status values:** `not_reviewed`, `needs_review`, `reviewed_placeholder`

**Approval status values:** `not_approved`, `placeholder_approved`, `blocked_placeholder`

**Source systems:** `google_drive`, `nas`, `local_folder`, `icloud`, `canvas_export`

Teacher-only examples must include `sample-teacher-assessment-001` and rows with `teacher_only: true`. Student-facing practice placeholder must include `sample-student-practice-001`.

## 16. Activation Status Rules

Future CSV rows must use only:

- `planning_only`
- `inactive_placeholder`

Prohibited activation wording in CSV data rows:

- `active_registry`
- `runtime_enabled`
- `production_enabled`
- `live_registry`

A future CSV sample must not imply runtime registry activation.

## 17. Manual Entry Rules

Every future CSV row must include:

- `created_by_manual_entry: true`
- `local_first_safety_flags` containing at minimum: `manual_entry`, `placeholder_only`, `no_external_resolution`, `metadata_only`, `no_student_data`, `not_indexed`, `not_scanned`, `planning_only` (pipe-delimited in one CSV cell)

Manual entry means static documentation proof only — not live data import.

## 18. Static Validation Expectations

A **future** CSV sample artifact PR may add repo-local static checks for:

- CSV file exists at the approved path
- CSV header includes required columns
- expected seven fictional IDs appear
- expected placeholder URIs appear
- placeholder scheme prefixes are represented
- prohibited references are absent from CSV data
- source systems are represented
- `placeholder_uri` appears
- teacher-only and student-facing examples are represented
- review and approval statuses are represented
- activation status remains planning-only or inactive
- manual-entry marker appears
- local-first safety flags appear
- CSV is not referenced by app code as input
- no parser, importer, or loader is added

**This PR does not implement CSV-specific checks** because the CSV artifact does not exist yet. This PR adds doc-presence checks for this plan document only.

## 19. What the Future CSV Must Not Do

A future CSV placeholder sample must **not**:

- be imported by app code
- be parsed by a runtime loader
- become a live registry
- populate a database
- be referenced by CLI commands as runtime input
- trigger document scanning, folder indexing, OCR, or embeddings
- call Google Drive, Canvas, NAS, or iCloud APIs
- generate lesson briefs, drafts, or review notes
- use student data
- copy raw curriculum files into the repo or app

## 20. Blocked Capabilities

Unless explicitly approved through `docs/curriculum-builder-approval-gate.md` and completed decision intake:

- CSV artifact without this plan and a separate approved artifact PR
- parser, importer, loader, or runtime validator implementation
- live registry behavior consumed by app code
- database schema activation
- document scanning, folder scanning, or file indexing
- OCR, embeddings, vector database, AI parsing, or auto-classification
- real lesson generation, generated briefs/drafts, or real review notes
- student data handling
- Google Drive API, Canvas API, iCloud integration, NAS crawler, or local folder crawler
- network calls, OAuth, automation, live integrations, or new runtime services

## 21. Recommended Next PR

**PR #141 — Curriculum Builder CSV Placeholder Sample Artifact**

Scope:

- create `docs/examples/curriculum-builder-manual-registry-sample.csv` with seven fictional placeholder rows
- add repo-local static text checks against the CSV file (grep/header/negative guards only)
- cross-link from canonical planning index and this plan doc
- no parser, importer, loader, or runtime validator
- no app code consumption of the CSV
- Markdown sample remains canonical

## 22. PR Handoff Checklist

Before follow-on Curriculum Builder PRs:

- [ ] Start from `docs/curriculum-builder-canonical-planning-index.md`
- [ ] Read sample format decision, Markdown sample proof, and this CSV plan
- [ ] Complete `docs/curriculum-builder-future-pr-checklist.md`
- [ ] Confirm no parser, importer, loader, or CSV artifact activation without approval
- [ ] Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL
- [ ] Run `bin/chief-of-staff --dashboard` — no FAIL

## Non-Activation confirmation

This CSV placeholder sample plan is documentation and status proof only. It does not add a CSV file; live registry behavior; parsers; importers; loaders; runtime validators; connectors; APIs; automation; scanning; indexing; OCR; embeddings; lesson generation; student data; network calls; OAuth; or new dependencies.
