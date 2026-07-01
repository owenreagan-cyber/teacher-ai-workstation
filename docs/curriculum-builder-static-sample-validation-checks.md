# Curriculum Builder Static Sample Validation Checks

Last verified: 2026-06-30

## 1. Purpose

This document describes the **repo-local, text-only, read-only static validation checks** implemented in PR #138 against the fictional manual registry sample proof in `docs/curriculum-builder-manual-registry-sample-proof.md`.

These checks strengthen confidence that the static sample artifact remains safe, complete, placeholder-only, non-live, and aligned with the manual registry schema plan. They are enforced by `scripts/curriculum-builder-foundation-status.sh` and surfaced through `bin/chief-of-staff --curriculum-builder-foundation-status`.

Planning path:

```text
canonical planning index
→ next-stage readiness audit
→ manual registry schema plan
→ manual registry sample proof plan
→ manual registry sample proof
→ static sample validation plan
→ static sample validation checks (this document)
→ sample format decision
→ CSV placeholder sample plan
→ CSV placeholder sample artifact
→ future CSV static validation maintenance
```

## 2. Non-Activation Statement

These static validation checks do **not**:

- create a live registry
- implement a runtime validator, parser, importer, or registry loader
- create a database, SQLite file, Postgres schema, or Supabase schema
- create a schema implementation
- resolve placeholder URIs
- inspect curriculum files or folders
- inspect external storage or user directories
- call APIs or use OAuth
- scan, index, or parse curriculum content
- generate lesson briefs, lesson drafts, or review notes
- use student data
- add network calls, background jobs, automation, or new package dependencies

Chief of Staff remains a read-only proof/status/reference surface. These checks inspect **only** repo-local Markdown text in the static sample proof document and this checks documentation.

## 3. Relationship to Static Sample Validation Plan

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-static-sample-validation-plan.md` | Defines planned validation rule categories and future expansion path |
| `docs/curriculum-builder-manual-registry-sample-proof.md` | Seven-row fictional sample artifact under validation |
| `scripts/curriculum-builder-foundation-status.sh` | Enforces read-only static text checks |
| This document | Describes checks implemented in PR #138 |

The validation plan remains the authoritative rule catalog. This document records which rules are now enforced as static text checks.

## 4. Implemented Check Categories

| Category | Description |
| --- | --- |
| A. Sample artifact presence and non-activation | Title, Non-Activation Statement, and static non-live boundary phrases |
| B. Required field header coverage | All planned manual registry field names in the sample table header |
| C. Fictional row ID coverage | Seven expected `sample-` registry IDs |
| D. Placeholder URI coverage | Seven placeholder `source_reference` values and four scheme prefixes |
| E. Prohibited reference negative guards | No live URLs, real paths, or HTTP/HTTPS schemes in sample scope |
| F. Source system coverage | `google_drive`, `nas`, `local_folder`, `icloud`, `canvas_export` |
| G. Source reference type coverage | `placeholder_uri` |
| H. Teacher-only and student-facing coverage | Field names, boolean values, teacher assessment and student practice IDs |
| I. Review and approval status coverage | Placeholder review and approval enum values |
| J. Activation status coverage | `planning_only` and `inactive_placeholder`; negative guards for activation wording |
| K. Manual entry and local-first safety coverage | `created_by_manual_entry`, safety flag vocabulary |

## 5. Sample Artifact Scope

Static checks inspect **only**:

```text
docs/curriculum-builder-manual-registry-sample-proof.md
```

Checks do not open referenced files, resolve placeholder URIs, or read any path outside this document.

## 6. Positive Checks

Positive checks verify the sample proof document contains:

- non-activation boundary language (`static documentation proof only`, `not a live registry`, `not loaded by app code`, and related phrases)
- all required field header names from the manual registry schema plan
- seven fictional registry IDs (`sample-sm5-textbook-001` through `sample-student-practice-001`)
- seven placeholder URI examples across `gdrive://`, `nas://`, `local://`, and `icloud://` schemes
- five source system values and `placeholder_uri` reference type
- `teacher_only`, `student_facing_allowed`, `true`, and `false` representations
- review statuses: `not_reviewed`, `needs_review`, `reviewed_placeholder`
- approval statuses: `not_approved`, `placeholder_approved`, `blocked_placeholder`
- activation statuses: `planning_only`, `inactive_placeholder`
- manual-entry and local-first safety markers: `created_by_manual_entry`, `manual_entry`, `placeholder_only`, `no_external_resolution`

## 7. Negative Checks

Negative checks verify the sample proof document does **not** contain:

- `https://drive.google.com`
- `canvas.instructure.com`
- `file:///Users/`
- `/Users/`
- `C:\Users\`
- `http://`
- `https://`
- `active_registry`, `runtime_enabled`, or `production_enabled` activation wording

Prohibited patterns must not appear in sample table rows or elsewhere in the checked document scope.

## 8. What These Checks Prove

These checks prove that:

- the sample artifact exists as repo-local documentation
- required field names are represented in the sample table header
- seven expected fictional sample rows are represented by registry ID
- placeholder URI examples are represented with allowed scheme prefixes
- unsafe live URL and path markers are absent from the checked static sample scope
- teacher-only and student-facing examples are represented
- inactive/planning activation values are represented
- non-activation and blocked-capability language remains present

## 9. What These Checks Do Not Prove

These checks do **not** prove:

- curriculum correctness or instructional alignment
- legal or copyright status
- file existence at referenced placeholder locations
- source availability on Drive, NAS, iCloud, or Canvas
- lesson readiness or pacing accuracy
- data quality beyond static placeholder proof
- runtime registry behavior, parsing, or import correctness

## 10. Blocked Capabilities

Unless explicitly approved through `docs/curriculum-builder-approval-gate.md` and completed decision intake:

- live registry behavior consumed by app code
- runtime validator, parser, or importer implementation
- database schema activation
- document scanning, folder scanning, or file indexing
- OCR, embeddings, vector database, AI parsing, or auto-classification
- real lesson generation, generated briefs/drafts, or real review notes
- student data handling
- Google Drive API, Canvas API, iCloud integration, NAS crawler, or local folder crawler
- network calls, OAuth, automation, live integrations, or new runtime services

## 11. Future Expansion Path

Future approved PRs may add:

- table-region-scoped checks (sample rows only) for stricter negative guards
- row-count verification for exactly seven data rows
- structured field-value pairing checks per row type
- cross-doc consistency checks between sample proof, schema plan, and validation plan
- future CSV placeholder sample artifact in `docs/examples/curriculum-builder-manual-registry-sample.csv` (secondary; Markdown canonical)
- future CSV static validation maintenance checklist

See `docs/curriculum-builder-static-sample-validation-plan.md` for the full rule catalog.

## 12. PR Handoff Checklist

Before follow-on Curriculum Builder PRs:

- [ ] Start from `docs/curriculum-builder-canonical-planning-index.md`
- [ ] Read schema plan, sample proof plan, sample proof, validation plan, and this checks doc
- [ ] Complete `docs/curriculum-builder-future-pr-checklist.md`
- [ ] Confirm no app loader, runtime validator, or live registry activation
- [ ] Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL
- [ ] Run `bin/chief-of-staff --dashboard` — no FAIL

## Non-Activation confirmation

These static sample validation checks are documentation and status proof only. They do not add live registry behavior, database tables, parsers, importers, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, network calls, OAuth, or new dependencies.
