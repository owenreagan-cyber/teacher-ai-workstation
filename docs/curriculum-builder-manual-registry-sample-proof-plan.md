# Curriculum Builder Manual Registry Sample Proof Plan

Last verified: 2026-06-30

## 1. Purpose

This document plans how a **future PR** may safely introduce a tiny **fictional manual registry sample proof** for Curriculum Builder. The sample proof will demonstrate schema shape, placeholder source references, safety fields, and review status coverage — without becoming a live registry consumed by app code.

This PR **only plans** the future sample proof. It does not create the sample artifact.

Planning path:

```text
canonical planning index
→ next-stage readiness audit
→ manual registry schema plan
→ manual registry sample proof plan
→ manual registry sample proof (`docs/curriculum-builder-manual-registry-sample-proof.md`)
→ future static sample validation planning
```

## 2. Non-Activation Statement

This document does **not**:

- create the sample registry artifact
- create a live registry
- create a database, SQLite file, Postgres schema, or Supabase schema
- create a schema implementation or parser
- scan files or index folders
- read curriculum documents
- call APIs or use OAuth
- activate Google Drive, NAS, iCloud, Canvas, or any other integration
- generate lesson briefs, lesson drafts, or review notes
- use student data
- use real private curriculum paths or live URLs
- copy raw curriculum files into the repo or app-owned storage

Chief of Staff remains a read-only proof/status/reference surface. It does not own raw curriculum files.

## 3. Relationship to Manual Registry Schema Plan

| Prior doc | Relationship |
| --- | --- |
| `docs/curriculum-builder-manual-registry-schema-plan.md` | Defines required/optional/reserved fields and example placeholder rows in prose |
| This document | Defines rules and expectations for a future standalone sample proof artifact |

The schema plan's example rows are **documentation-only illustrations**. A future sample proof PR may consolidate 5–8 fictional rows into a single static artifact (Markdown table, CSV, JSON, or YAML) for validator planning — still documentation/static data only.

Field names, status values, and safety rules must match the manual registry schema plan unless a future approved PR explicitly revises vocabulary.

## 4. What the Future Sample Proof May Demonstrate

A future approved sample proof PR may demonstrate:

- 5–8 fictional registry rows conforming to the manual schema plan
- placeholder URI schemes for all `source_reference` values
- coverage of multiple `source_system` values (`google_drive`, `nas`, `local_folder`, `icloud`)
- teacher-only and student-facing placeholder examples
- multiple `review_status` and `approval_status` values
- `activation_status: planning_only` on every row
- `created_by_manual_entry: true` on every row
- `local_first_safety_flags` including `no_student_data`, `metadata_only`, `not_indexed`, `not_scanned`, `manual_entry`, `planning_only`
- resource types such as textbook, folder_index, slides, study_guide, canvas_export, test/assessment, practice worksheet

The sample proof helps humans and future validators recognize correct shape before any live registry or app integration exists.

## 5. What the Future Sample Proof Must Not Do

The future sample proof must **not**:

- reference real curriculum files, folders, or document contents
- use `https://drive.google.com`, Canvas web URLs, or other live URLs
- use absolute local user paths (for example `/Users/...`)
- include student names, IDs, grades, or other student-sensitive data
- include copyrighted text excerpts from real materials
- include generated lesson briefs, drafts, or review notes
- be loaded or parsed by runtime app code in the sample-proof PR
- trigger scanning, indexing, OCR, embeddings, APIs, or automation
- imply that Teacher Workstation or Chief of Staff owns raw curriculum files

## 6. Fictional Data Rules

All future sample rows must be **obviously fictional**:

| Rule | Requirement |
| --- | --- |
| IDs | Use planning prefixes like `cr-sm5-...`, `cr-history-...` |
| Titles | Use explicit "Placeholder" in title text |
| Paths | Use placeholder URI schemes only (see section 7) |
| Content | Metadata labels only; no document body text |
| People | No real student or staff names |
| URLs | No `http://` or `https://` source references |
| Activation | `activation_status` must be `planning_only` |
| Entry | `created_by_manual_entry` must be `true` |

If a future row could be mistaken for a real school resource, revise it to be more clearly fictional.

## 7. Placeholder Source Reference Rules

Future sample rows must use **placeholder URI schemes only**:

| Scheme | Example |
| --- | --- |
| `gdrive://placeholder/...` | `gdrive://placeholder/sm5/textbook` |
| `gdrive://placeholder/...` | `gdrive://placeholder/sm5/worksheet-folder` |
| `nas://placeholder/...` | `nas://placeholder/archive/history-slides` |
| `nas://placeholder/...` | `nas://placeholder/archive/science-study-guides` |
| `local://placeholder/...` | `local://placeholder/canvas-export` |
| `local://placeholder/...` | `local://placeholder/teacher-only-assessment` |
| `icloud://placeholder/...` | `icloud://placeholder/student-facing-practice` |

Prohibited in future sample proofs:

- real file paths
- real Google Drive URLs
- real Canvas URLs
- real NAS paths
- real iCloud paths
- `file://` paths to user home directories
- network-resolvable references

## 8. Required Sample Row Coverage

The future sample proof should include **5 to 8 fictional rows** covering at minimum:

| # | Placeholder example | resource_type | source_system | Safety note |
| --- | --- | --- | --- | --- |
| 1 | SM5 textbook placeholder | textbook | google_drive | general metadata |
| 2 | SM5 worksheet folder placeholder | folder_index | google_drive | teacher-only folder index |
| 3 | History unit slides placeholder | slides | nas | archive example |
| 4 | Science study guide placeholder | study_guide | nas | archive example |
| 5 | Canvas export folder placeholder | canvas_export | local_folder | teacher-only export |
| 6 | Teacher-only assessment placeholder | test | local_folder | `teacher_only: true` |
| 7 | Student-facing practice placeholder | worksheet | icloud | `student_facing_allowed: unknown` until reviewed |

An eighth row is optional (for example pacing link placeholder). Rows must collectively exercise required schema fields from the manual registry schema plan.

## 9. Allowed Placeholder Resource Types

Future sample proofs may use these `resource_type` values (non-exhaustive):

- `textbook`
- `folder_index`
- `slides`
- `study_guide`
- `canvas_export`
- `worksheet`
- `test`
- `practice`
- `pacing_link`
- `answer_key` (must pair with `teacher_only: true`)

No resource type may imply live ingestion or automatic classification.

## 10. Safety and Review Status Coverage

Future sample proofs should include multiple values to exercise validation planning:

### `review_status` coverage

- `not_reviewed`
- `metadata_only`
- `teacher_reviewed` (optional in sample)

### `approval_status` coverage

- `not_approved`
- `approved_for_planning` (optional in sample)

### `activation_status` coverage

- `planning_only` (required on all rows)

No sample row may use values that imply live runtime activation.

## 11. Teacher-Only and Student-Facing Coverage

Future sample proofs must include **both**:

- at least one row with `teacher_only: true` and `student_facing_allowed: false` (for example teacher-only assessment, answer key, canvas export)
- at least one row with `teacher_only: false` and `student_facing_allowed: unknown` or `false` (for example textbook or practice placeholder)

Rules (from schema plan; planning only):

- `teacher_only: true` rows must not be treated as student-facing
- answer keys and assessments should default teacher-only
- all rows must include `no_student_data` in `local_first_safety_flags`

## 12. Source System Coverage

Future sample proofs should include at least one row per planned source system where applicable:

| `source_system` | Minimum coverage |
| --- | --- |
| `google_drive` | textbook and/or worksheet folder |
| `nas` | slides and/or study guide |
| `local_folder` | canvas export and/or teacher-only assessment |
| `icloud` | student-facing practice placeholder |

This demonstrates local-first storage diversity without activating connectors.

## 13. Validation Expectations

Current verification (this PR) remains documentation-only:

```bash
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
```

Future sample proof PR validation (not active now) should confirm:

- artifact exists at approved path
- row count is 5–8
- all required schema fields present per row
- all `source_reference` values use placeholder URI schemes
- no live URLs or absolute user paths
- no student data markers in values
- teacher-only and student-facing examples both present
- `activation_status` is `planning_only` on every row
- PASS/WARN/FAIL semantics preserved

## 14. Future File Shape Options

A **later PR** (not this one) may introduce the sample artifact in one of these shapes:

| Option | Path | Notes |
| --- | --- | --- |
| Markdown table only | `docs/curriculum-builder-manual-registry-sample-proof.md` | Easiest to review in GitHub; recommended first |
| CSV placeholder sample | `docs/examples/curriculum-builder-manual-registry-sample.csv` | Good for future CSV validator planning |
| JSON placeholder sample | `docs/examples/curriculum-builder-manual-registry-sample.json` | Good for future JSON schema planning |
| YAML placeholder sample | `docs/examples/curriculum-builder-manual-registry-sample.yaml` | Alternative static format |

**Recommendation:** the next actual proof PR should start with either:

- `docs/curriculum-builder-manual-registry-sample-proof.md` (Markdown table), or
- `docs/examples/curriculum-builder-manual-registry-sample.csv`

The future sample proof must remain **documentation/static data only**. It must not become live input consumed by app code, CLI loaders, or background jobs without a separate explicitly approved implementation PR.

This PR creates **neither** artifact.

## 15. Future Static Proof Checks

A future PR may add read-only static checks to `scripts/curriculum-builder-foundation-status.sh` (or a sibling status script if separately approved). Checks may verify:

- sample proof artifact exists at documented path
- all sample `source_reference` values use `gdrive://placeholder`, `nas://placeholder`, `local://placeholder`, or `icloud://placeholder` schemes
- no `https://drive.google.com` references appear in the artifact
- no real Canvas URL patterns appear (for example `https://*.instructure.com`)
- no absolute local user paths appear (for example `/Users/`)
- no student data marker violations (field names suggesting real student records)
- teacher-only and student-facing examples are both represented
- `review_status` and `approval_status` variety is represented
- `activation_status` remains `planning_only` on all rows
- blocked capabilities remain documented in planning stack

**This PR documents those future checks only.** It does not implement validation against a sample artifact that does not exist yet.

## 16. Blocked Capabilities

Unless explicitly approved through `docs/curriculum-builder-approval-gate.md` and completed decision intake:

- live registry file consumed by app code
- sample registry artifact (blocked until future sample proof PR)
- database schema activation
- no document scanning
- no folder scanning
- file indexing
- OCR
- embeddings
- vector database
- AI parsing or AI summaries
- auto-classification
- real lesson generation
- generated lesson briefs or drafts
- real review notes
- student data handling
- Google Drive API
- Canvas API
- iCloud integration
- NAS crawler
- local folder crawler
- network calls
- OAuth
- background jobs
- scheduler
- automation
- live integrations
- hosted storage requirement for raw files
- new runtime services
- new package dependencies

## 17. Recommended Next PR After This Plan

After the manual registry sample proof (`docs/curriculum-builder-manual-registry-sample-proof.md`) merges, the recommended next Curriculum Builder PR is:

**Static sample validation plan** — document future validation rules (completed in PR #137). Next: **static sample validation checks** — extend read-only grep checks per the validation plan.

Alternative safe paths:

- documentation/status hardening only
- pause and return to another repo priority

Implementation, connectors, validators that read user files, and lesson generation remain blocked.

## 18. PR Handoff Checklist

Before opening the future sample proof PR:

- [ ] Start from `docs/curriculum-builder-canonical-planning-index.md`
- [ ] Read `docs/curriculum-builder-next-stage-readiness-audit.md`
- [ ] Read `docs/curriculum-builder-manual-registry-schema-plan.md`
- [ ] Read this sample proof plan
- [ ] Complete `docs/curriculum-builder-future-pr-checklist.md`
- [ ] Confirm 5–8 fictional rows only
- [ ] Confirm placeholder URI schemes only
- [ ] Confirm no live registry, database, or app loader
- [ ] Confirm no scanning, indexing, OCR, embeddings, APIs, OAuth, automation, or generation
- [ ] Run `bash scripts/curriculum-builder-foundation-status.sh` — no FAIL
- [ ] Run `bin/chief-of-staff --dashboard` — no FAIL
- [ ] Document PASS count changes in PR body

## Non-Activation confirmation

This manual registry sample proof plan does not add a sample registry artifact, active schema files, database tables, migrations, registry data consumed by app code, validators against real files, commands, connectors, APIs, automation, scanning, indexing, OCR, embeddings, lesson generation, student data, or live integrations.
