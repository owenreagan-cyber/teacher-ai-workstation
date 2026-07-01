# Curriculum Builder CSV Static Validation Maintenance

Last verified: 2026-06-30

## 1. Purpose

This document defines how to **maintain alignment** between the canonical Markdown manual registry sample proof and the secondary CSV placeholder sample artifact after PR #141.

Maintenance is documentation and static-check maintenance only. It does not introduce parsers, importers, loaders, runtime validators, or live registry behavior.

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
→ CSV placeholder sample plan
→ CSV placeholder sample artifact
→ CSV static validation maintenance (this document)
→ future Markdown/CSV alignment proof
```

## 2. Non-Activation Statement

CSV static validation maintenance does **not**:

- create a parser, importer, loader, or runtime validator
- create a live registry consumed by app code
- create a database, SQLite file, Postgres schema, or Supabase schema
- scan curriculum files or index folders
- resolve placeholder URIs
- call APIs or use OAuth
- generate lesson briefs, lesson drafts, or review notes
- use AI parsing, OCR, embeddings, or summaries
- use student data
- add network calls, background jobs, automation, or new package dependencies

Chief of Staff remains a read-only proof/status/reference surface.

## 3. Current Sample Artifacts

| Role | Path | Description |
| --- | --- | --- |
| Canonical Markdown sample | `docs/curriculum-builder-manual-registry-sample-proof.md` | Primary seven-row fictional proof |
| Secondary CSV sample | `docs/examples/curriculum-builder-manual-registry-sample.csv` | Static tabular mirror |
| Markdown static checks | `docs/curriculum-builder-static-sample-validation-checks.md` | Grep checks on Markdown sample |
| CSV artifact doc | `docs/curriculum-builder-csv-placeholder-sample-artifact.md` | CSV boundaries and validation |
| CSV plan | `docs/curriculum-builder-csv-placeholder-sample-plan.md` | CSV safety rules |
| Status script | `scripts/curriculum-builder-foundation-status.sh` | Repo-local PASS/WARN/FAIL checks |

## 4. Canonical vs Secondary Rule

**Markdown sample remains canonical; CSV remains secondary static placeholder proof.**

- Markdown is the source of truth for planning handoffs and schema-shape review.
- CSV exists only to prove a secondary static tabular artifact can mirror the same fictional rows safely.
- CSV must not be consumed by app code, CLI loaders, or background jobs.
- CSV must not supersede Markdown in documentation cross-links or maintainer routing.

## 5. Markdown/CSV Alignment Expectations

When both samples exist, they should remain aligned on:

- seven fictional row concepts
- fictional `registry_id` values
- placeholder `source_reference` URIs
- required field/column vocabulary
- planning-only or inactive activation statuses
- fictional review and approval status enums
- non-activation and safety boundaries

Alignment is maintained through deliberate documentation edits and static grep checks — not through runtime comparison, parsing, or import.

Future sample edits must either:

- update **both** Markdown and CSV together, or
- explicitly document why only one artifact changes, with Markdown remaining canonical

## 6. Required Shared Row Concepts

Both artifacts must continue to represent these seven fictional concepts:

1. SM5 textbook placeholder
2. SM5 worksheet folder placeholder
3. history unit slides placeholder
4. science study guide placeholder
5. Canvas export folder placeholder
6. teacher-only assessment placeholder
7. student-facing practice placeholder

Do not add new row concepts without an approved planning PR that updates schema docs, static checks, and both samples together.

## 7. Required Shared Registry IDs

Both artifacts should continue to use these fictional IDs:

```text
sample-sm5-textbook-001
sample-sm5-worksheet-folder-001
sample-history-slides-001
sample-science-study-guide-001
sample-canvas-export-folder-001
sample-teacher-assessment-001
sample-student-practice-001
```

Future ID changes must be deliberate and should update:

- Markdown sample proof
- CSV sample artifact
- static proof checks in `scripts/curriculum-builder-foundation-status.sh`
- CSV artifact documentation
- this maintenance document

## 8. Required Shared Placeholder References

Both artifacts should continue to use these placeholder references:

```text
gdrive://placeholder/sm5/textbook
gdrive://placeholder/sm5/worksheet-folder
nas://placeholder/archive/history-slides
nas://placeholder/archive/science-study-guides
local://placeholder/canvas-export
local://placeholder/teacher-only-assessment
icloud://placeholder/student-facing-practice
```

Placeholder references must never be resolved by scripts or app code.

## 9. Field and Column Alignment Rules

- Markdown table fields are governed by `docs/curriculum-builder-manual-registry-schema-plan.md`.
- CSV headers must mirror the required schema fields in stable column order.
- Markdown remains easier to review in PRs and therefore canonical.
- CSV exists only to prove secondary static tabular mirroring.

Required fields/columns:

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

CSV column order should remain stable unless a future approved PR updates the schema plan and documents the change.

## 10. Safety Flag Alignment Rules

- Markdown uses comma-separated `local_first_safety_flags` in table cells.
- CSV uses pipe-delimited safety flags in one cell to avoid comma conflicts.
- Both must express the same safety concepts: `metadata_only`, `no_student_data`, `not_indexed`, `not_scanned`, manual-entry markers, `placeholder_only`, `no_external_resolution`, `planning_only`.
- CSV may use `manual_static_entry`; Markdown may use `manual_entry` — document deliberate naming if they differ, but concepts must align.

## 11. Review and Approval Status Alignment Rules

Both artifacts should represent the same fictional review and approval enums:

**Review:** `not_reviewed`, `needs_review`, `reviewed_placeholder`

**Approval:** `not_approved`, `placeholder_approved`, `blocked_placeholder`

Per-row status values should match between Markdown and CSV unless a deliberate documented exception exists.

## 12. Activation Status Alignment Rules

Both artifacts must use only:

- `planning_only`
- `inactive_placeholder`

Prohibited activation wording in sample data: `active_registry`, `runtime_enabled`, `live_registry`, `production_enabled`.

## 13. Prohibited Reference Maintenance Rules

When editing either sample, verify neither artifact contains:

- live Google Drive or Canvas URLs
- real NAS, iCloud, or local home-directory paths
- live HTTP or HTTPS URL schemes in data rows
- student data, copyrighted excerpts, or generated lesson/review content

Negative static checks in `scripts/curriculum-builder-foundation-status.sh` enforce these rules separately per artifact.

## 14. Static Check Maintenance Rules

When sample rows or fields change:

1. Update Markdown first (canonical).
2. Mirror changes in CSV if alignment is required.
3. Update static checks in `scripts/curriculum-builder-foundation-status.sh` for any new required strings or negative guards.
4. Update `docs/curriculum-builder-static-sample-validation-checks.md` if Markdown check categories change.
5. Update `docs/curriculum-builder-csv-placeholder-sample-artifact.md` if CSV scope changes.
6. Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL.
7. Run `bin/chief-of-staff --dashboard` — confirm health unless intentionally changed.

Static checks remain grep and line-count only. No CSV parser dependency.

## 15. Future Edit Checklist

Before merging a PR that changes either sample:

- [ ] Confirm Markdown remains canonical.
- [ ] Confirm CSV remains secondary.
- [ ] Confirm row concepts still match (seven fictional placeholders).
- [ ] Confirm fictional IDs still match across artifacts.
- [ ] Confirm placeholder references still match.
- [ ] Confirm no live URLs or real paths were added.
- [ ] Confirm no student data was added.
- [ ] Confirm no generated lesson content was added.
- [ ] Confirm no generated review notes were added.
- [ ] Confirm activation statuses remain planning-only or inactive.
- [ ] Confirm static checks are updated with any deliberate row/field changes.
- [ ] Confirm no parser, importer, loader, or runtime validator was added.
- [ ] Confirm no app code consumes the CSV.
- [ ] Run full validation suite.
- [ ] Confirm dashboard remains 87/87 unless intentionally changed.

## 16. What Maintenance Must Not Do

Maintenance must **not**:

- treat CSV as canonical
- import or parse CSV in app code
- add row-by-row runtime diff tools without approval
- resolve placeholder URIs
- scan curriculum folders or external storage
- activate registry, database, or schema implementation behavior
- generate lessons, briefs, drafts, or review notes

## 17. Blocked Capabilities

Unless explicitly approved through `docs/curriculum-builder-approval-gate.md` and completed decision intake:

- parser, importer, loader, or runtime validator implementation
- live registry or database activation
- document scanning, folder scanning, or file indexing
- OCR, embeddings, AI parsing, or auto-classification
- real lesson generation or student data handling
- network calls, OAuth, automation, or new runtime services

## 18. Recommended Next PR

**PR #143 — Curriculum Builder Markdown/CSV Alignment Proof**

Scope:

- documentation/status-only proof that Markdown and CSV samples remain aligned on shared IDs and placeholder URIs
- optional additional static grep checks cross-referencing both artifact paths (text-only; no parser)
- no sample row edits unless a documented static proof bug is found
- no parser, importer, loader, or runtime validator

## 19. PR Handoff Checklist

Before follow-on Curriculum Builder PRs:

- [ ] Start from `docs/curriculum-builder-canonical-planning-index.md`
- [ ] Read this maintenance doc before editing either sample
- [ ] Complete `docs/curriculum-builder-future-pr-checklist.md`
- [ ] Confirm Markdown canonical / CSV secondary rule preserved
- [ ] Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL
- [ ] Run `bin/chief-of-staff --dashboard` — no FAIL

## Non-Activation confirmation

This CSV static validation maintenance guide is documentation and status proof only. It does not activate parsers, importers, loaders, runtime validators, live registry behavior, databases, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, network calls, OAuth, or new dependencies.
