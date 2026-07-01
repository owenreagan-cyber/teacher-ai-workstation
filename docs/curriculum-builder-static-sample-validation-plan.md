# Curriculum Builder Static Sample Validation Plan

Last verified: 2026-06-30

## 1. Purpose

This document plans **future static validation** of the fictional manual registry sample proof in `docs/curriculum-builder-manual-registry-sample-proof.md`. It defines validation rule categories, safety expectations, allowed placeholder formats, prohibited references, and future validation stages.

This is a **validation planning document only**. It does not implement a live validator, parser, or registry loader.

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
→ CSV static validation maintenance
→ future Markdown/CSV alignment proof
```

## 2. Non-Activation Statement

This validation plan does **not**:

- create a live validator implementation
- parse registry data into app code
- create a registry loader
- create a database, SQLite file, Postgres schema, or Supabase schema
- create a schema implementation
- scan files or index folders
- read curriculum documents
- call APIs or use OAuth
- activate Google Drive, NAS, iCloud, Canvas, or any other integration
- generate lesson briefs, lesson drafts, or review notes
- use student data
- use real private curriculum paths or live URLs
- open or resolve placeholder URIs referenced in the sample

Chief of Staff remains a read-only proof/status/reference surface. It does not own raw curriculum files.

## 3. Relationship to Manual Registry Sample Proof

| Artifact | Role |
| --- | --- |
| `docs/curriculum-builder-manual-registry-sample-proof.md` | Static seven-row fictional sample (PR #136) |
| `scripts/curriculum-builder-foundation-status.sh` | Current read-only doc-presence, static sample text checks, and negative-reference guards on the sample doc |
| `docs/curriculum-builder-static-sample-validation-checks.md` | Describes static validation checks implemented against the sample proof |
| This document | Future validation rule set and expansion path |

Validation applies to **repo-local Markdown text only**. It does not validate curriculum correctness, instructional quality, or external file existence.

## 4. Current Static Proof Checks

PR #136 added initial read-only checks in `scripts/curriculum-builder-foundation-status.sh` against the sample proof document only. PR #138 extended those checks per `docs/curriculum-builder-static-sample-validation-checks.md`.

- sample proof doc exists
- Non-Activation Statement and Manual Registry Sample Table sections exist
- expected fictional registry IDs (`sample-sm5-textbook-001`, `sample-student-practice-001`)
- placeholder URI schemes (`gdrive://placeholder/...`, `icloud://placeholder/...`)
- negative guards: no `https://drive.google.com`, no `canvas.instructure.com`, no absolute user home path marker in sample doc
- `teacher_only` and `student_facing_allowed` fields present
- `planning_only` and `inactive_placeholder` activation values present
- Blocked Capabilities section and canonical index cross-link

These checks are **documentation proof only**. They do not parse table rows into structured data or activate registry behavior.

## 5. Future Validation Goals

A future approved PR may extend static validation to verify:

- complete required field column headers in the sample table
- exactly seven fictional data rows (excluding header)
- all seven required placeholder row types are represented
- every `source_reference` uses an allowed placeholder prefix
- prohibited live URL and path patterns are absent
- teacher-only and student-facing coverage rules
- review and approval status variety
- activation status remains planning-only or inactive placeholder
- non-activation boundaries remain documented

Future validation must remain **static, text-based, and repo-local**.

## 6. Validation Rule Categories

| Category | Future check intent |
| --- | --- |
| Required field presence | Column headers and field names match schema plan |
| Placeholder URI | Allowed schemes only; no live URLs |
| Prohibited reference | Reject Drive, Canvas, HTTP(S), absolute paths, student identifiers |
| Coverage | Seven rows; required resource types; safety distinctions |
| Manual entry | `created_by_manual_entry: true` on all rows |
| Activation | Only `planning_only` or `inactive_placeholder` |
| Local-first safety flags | Required flag tokens present |
| Non-activation | No app loader; no live registry semantics |

## 7. Required Field Presence Rules

Future checks may verify the sample table includes these field names (column headers or equivalent static representation):

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

Missing required field names should FAIL static validation. Extra columns are allowed only if documented in a future approved PR.

## 8. Placeholder URI Rules

Future checks may verify:

- every sample `source_reference` uses a placeholder URI scheme
- allowed placeholder prefixes:
  - `gdrive://placeholder/`
  - `nas://placeholder/`
  - `local://placeholder/`
  - `icloud://placeholder/`
- Canvas export placeholders use `local://placeholder/...` or `canvas_export` as `source_system` without live Canvas URLs
- no `http://` or `https://` in `source_reference` values
- placeholder URIs are not resolved, fetched, or opened

## 9. Prohibited Reference Rules

Future checks may reject these patterns in the sample proof document:

| Pattern | Reason |
| --- | --- |
| `https://drive.google.com` | Live Google Drive URL |
| `canvas.instructure.com` | Live Canvas URL |
| `file:///Users/` | Absolute user home file URI |
| absolute user home path markers | Real private filesystem paths |
| live HTTP/HTTPS source references | Network-resolvable URLs |
| real student names or student identifiers | Student data boundary |

Future validation must scan **only** `docs/curriculum-builder-manual-registry-sample-proof.md` (or an explicitly approved static artifact path). It must not scan curriculum folders or external storage.

## 10. Fictional Data Rules

Future checks may verify:

- all `registry_id` values use the `sample-` prefix
- all titles include **Placeholder**
- no copyrighted text excerpts from real materials
- no generated lesson briefs, drafts, or review notes in field values
- no real private curriculum content in `notes` fields
- row count is exactly seven fictional data rows

## 11. Teacher-Only and Student-Facing Rules

Future checks may verify:

- at least one row with `teacher_only: true` (worksheet folder, canvas export, teacher-only assessment)
- at least one row with `teacher_only: false` and `student_facing_allowed: unknown` or `false` (textbook, student-facing practice)
- no row has `teacher_only: true` and `student_facing_allowed: true` without explicit future policy approval
- `local_first_safety_flags` includes `no_student_data` on every row

## 12. Review and Approval Status Rules

Future checks may verify coverage of fictional status values present in the sample:

### `review_status`

- `not_reviewed`
- `needs_review`
- `reviewed_placeholder`

### `approval_status`

- `not_approved`
- `placeholder_approved`
- `blocked_placeholder`

Status values are placeholders only. No automated review or approval workflow exists.

## 13. Activation Status Rules

Future checks may verify:

- every row uses `planning_only` or `inactive_placeholder` for `activation_status`
- no row uses values implying live runtime activation (for example `active`, `enabled`, `synced`)
- at least one row uses `planning_only` and at least one may use `inactive_placeholder`

## 14. Manual Entry Rules

Future checks may verify:

- `created_by_manual_entry` is `true` on every data row
- no row implies automatic ingestion or connector sync

## 15. Local-First Safety Flag Rules

Future checks may verify every row includes in `local_first_safety_flags`:

- `metadata_only`
- `no_student_data`
- `not_indexed`
- `not_scanned`
- `manual_entry`
- `planning_only`

Optional additional flags (for example `teacher_only_default`) are allowed when documented.

## 16. Future Static Check Expansion Path

| Stage | PR type | May add | Blocked |
| --- | --- | --- | --- |
| 1 | Validation plan (this PR) | Rule documentation only | Validator implementation |
| 2 | Static sample validation checks | Additional grep/doc checks on sample markdown | Row parser, CSV loader, app integration |
| 3 | Optional CSV/JSON sample artifact | Separate static file + checks | Runtime consumption |
| 4 | Implementation (gate + intake) | Approved validator with structured parse | Connectors, scanning, APIs |

This PR completes stage 1 only.

## 17. What Validation Must Not Do

Future validation must **not**:

- open files referenced by placeholder URIs
- resolve placeholder URIs to external storage
- check Google Drive, Canvas, iCloud, or NAS connectivity
- scan local curriculum folders
- read real curriculum documents
- perform OCR, embeddings, or AI summaries
- classify content or generate lessons
- generate review notes
- use student data
- make network calls or use OAuth
- add new package dependencies without separate approval

Validation remains static, text-based, and repo-local unless a later approved PR explicitly changes scope.

## 18. Blocked Capabilities

Unless explicitly approved through `docs/curriculum-builder-approval-gate.md` and completed decision intake:

- live registry behavior
- validator implementation beyond static doc checks
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

## 19. Recommended Next PR

After this plan merges, the recommended next Curriculum Builder PR is:

**Static sample validation checks** — extend `scripts/curriculum-builder-foundation-status.sh` with additional read-only checks documented in this plan (row coverage, field headers, prohibited patterns). Still no parser, no app loader, no live registry.

Alternative safe paths:

- documentation/status hardening only
- pause and return to another repo priority

## 20. PR Handoff Checklist

Before opening the future static validation checks PR:

- [ ] Start from `docs/curriculum-builder-canonical-planning-index.md`
- [ ] Read sample proof and this validation plan
- [ ] Complete `docs/curriculum-builder-future-pr-checklist.md`
- [ ] Confirm checks are static and scoped to repo docs only
- [ ] Confirm no validator implementation or app loader
- [ ] Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL
- [ ] Run `bin/chief-of-staff --dashboard` — no FAIL
- [ ] Document PASS count changes in PR body

## Non-Activation confirmation

This static sample validation plan does not add a live validator, registry loader, database, schema implementation, parser, importer, connector, API, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, or live integrations.
