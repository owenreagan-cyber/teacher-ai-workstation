# Curriculum Builder CSV Placeholder Sample Artifact

Last verified: 2026-06-30

## 1. Purpose

This document describes the **secondary static CSV placeholder sample** created in PR #141 for the Curriculum Builder manual registry proof stack. The CSV mirrors the seven fictional Markdown rows as documentation/example data only.

**Markdown remains the canonical sample proof.** This CSV is a secondary static placeholder artifact.

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
→ CSV placeholder sample artifact (this document)
→ CSV static validation maintenance
→ future Markdown/CSV alignment proof
```

## 2. Non-Activation Statement

This CSV placeholder sample artifact does **not**:

- replace or supersede the Markdown canonical sample
- create a parser, importer, loader, or runtime validator
- create a live registry consumed by app code
- create a database, SQLite file, Postgres schema, or Supabase schema
- scan curriculum files or index folders
- resolve placeholder URIs
- call APIs or use OAuth
- activate Google Drive, Canvas, NAS, or iCloud integrations
- generate lesson briefs, lesson drafts, or review notes
- use AI parsing, OCR, embeddings, or summaries
- use student data
- add network calls, background jobs, automation, or new package dependencies

Chief of Staff remains a read-only proof/status/reference surface.

## 3. Relationship to Markdown Canonical Sample

| Artifact | Path | Role |
| --- | --- | --- |
| Markdown sample (canonical) | `docs/curriculum-builder-manual-registry-sample-proof.md` | Primary static fictional seven-row proof |
| CSV sample (secondary) | `docs/examples/curriculum-builder-manual-registry-sample.csv` | Secondary static placeholder mirror |
| CSV plan | `docs/curriculum-builder-csv-placeholder-sample-plan.md` | Safety rules and field expectations |
| Static validation checks | `docs/curriculum-builder-static-sample-validation-checks.md` | Markdown sample grep checks |

The CSV must not be consumed by app code. The Markdown sample remains authoritative for planning handoffs.

## 4. CSV Artifact Path

```text
docs/examples/curriculum-builder-manual-registry-sample.csv
```

One header row and seven fictional data rows. No extra columns.

## 5. CSV Header

```text
registry_id,title,resource_type,source_system,source_reference,source_reference_type,subject,grade_band,course,unit,lesson,pacing_reference,teacher_only,student_facing_allowed,review_status,approval_status,local_first_safety_flags,notes,created_by_manual_entry,activation_status
```

## 6. CSV Row Coverage

Seven fictional rows mirroring the Markdown sample:

1. SM5 textbook placeholder (`sample-sm5-textbook-001`)
2. SM5 worksheet folder placeholder (`sample-sm5-worksheet-folder-001`)
3. history unit slides placeholder (`sample-history-slides-001`)
4. science study guide placeholder (`sample-science-study-guide-001`)
5. Canvas export folder placeholder (`sample-canvas-export-folder-001`)
6. teacher-only assessment placeholder (`sample-teacher-assessment-001`)
7. student-facing practice placeholder (`sample-student-practice-001`)

## 7. Placeholder URI Rules

Every `source_reference` uses a placeholder URI scheme:

- `gdrive://placeholder/...`
- `nas://placeholder/...`
- `local://placeholder/...`
- `icloud://placeholder/...`

Every row uses `source_reference_type: placeholder_uri`.

## 8. Prohibited Reference Rules

The CSV data rows must not contain live Google Drive URLs, live Canvas URLs, real NAS or iCloud paths, absolute user home paths, live HTTP or HTTPS URL schemes, student data, copyrighted excerpts, or generated lesson or review content.

Static checks in `scripts/curriculum-builder-foundation-status.sh` enforce negative guards on the CSV file only.

## 9. Static Validation Expectations

Repo-local static text checks verify:

- CSV file exists with eight lines (one header + seven rows)
- required header columns and full header line
- seven fictional registry IDs and placeholder URIs
- source systems, review/approval statuses, activation values
- prohibited reference patterns are absent
- manual-entry and safety-flag vocabulary

Checks are grep and line-count only. No CSV parser dependency.

## 10. What This CSV Proves

This CSV proves that:

- a secondary static placeholder format can mirror the Markdown sample safely
- required field names and fictional row concepts can be represented in CSV
- placeholder URI schemes and safety flags can be documented in pipe-delimited form
- negative guards can extend to a CSV artifact without runtime validation

## 11. What This CSV Does Not Prove

This CSV does **not** prove:

- curriculum correctness or instructional alignment
- file existence at referenced locations
- source availability on Drive, NAS, iCloud, or Canvas
- data quality beyond static placeholder proof
- parser, importer, loader, or registry runtime correctness
- lesson readiness or legal/copyright status

## 12. Blocked Capabilities

Unless explicitly approved through `docs/curriculum-builder-approval-gate.md` and completed decision intake:

- app code consumption of the CSV
- parser, importer, loader, or runtime validator implementation
- live registry or database activation
- document scanning, folder scanning, or file indexing
- OCR, embeddings, AI parsing, or auto-classification
- real lesson generation or student data handling
- network calls, OAuth, automation, or new runtime services

## 13. Future Maintenance Rules

See `docs/curriculum-builder-csv-static-validation-maintenance.md` for the full Markdown/CSV alignment and edit checklist.

When editing the CSV or Markdown sample:

- keep Markdown canonical; update CSV only as a deliberate secondary mirror
- preserve seven fictional rows and required columns
- preserve placeholder URIs and non-activation boundaries
- run `bash scripts/curriculum-builder-foundation-status.sh` after changes
- do not add parsers, importers, or loaders without approval gate crossing

## 14. Recommended Next PR

**PR #142 — Curriculum Builder CSV Static Validation Maintenance** (completed). Next: **PR #143 — Curriculum Builder Markdown/CSV Alignment Proof**.

## 15. PR Handoff Checklist

Before follow-on Curriculum Builder PRs:

- [ ] Start from `docs/curriculum-builder-canonical-planning-index.md`
- [ ] Confirm Markdown remains canonical and CSV remains secondary
- [ ] Complete `docs/curriculum-builder-future-pr-checklist.md`
- [ ] Confirm no app loader or CSV import activation
- [ ] Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL
- [ ] Run `bin/chief-of-staff --dashboard` — no FAIL

## Non-Activation confirmation

This CSV placeholder sample artifact is static documentation only. It does not activate parsers, importers, loaders, runtime validators, live registry behavior, databases, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, network calls, OAuth, or new dependencies.
