# Canvas LLM Placeholder Schema

```text
Status: documentation/status only. This placeholder schema is inert planning text. It does not create runtime schema files, parsers, importers, loaders, validators, database tables, Canvas API clients, Google Drive clients, OAuth flows, network calls, automation, lesson generation, generated lesson drafts, generated review notes, or student-data handling.
```

## 1. Purpose

This document defines placeholder object shapes for future Canvas LLM draft and export workflows inside Teacher Workstation. These are planning schemas only — not active implementation schemas, not code objects, not database tables, and not runtime validators.

The placeholder vocabulary makes future Canvas LLM work safer by naming object families, shared fields, and safety concepts before any implementation PR is approved.

## 2. Relationship to PR #144 Foundation

This document builds on the PR #144 foundation by defining object vocabulary only. It does not activate runtime behavior.

| Foundation doc | Role |
| --- | --- |
| `docs/teacher-app-designer-canvas-llm-plan.md` | Track plan, ownership split, fast school-year path |
| `docs/canvas-llm-safety-and-approval-contract.md` | Safety prohibitions and approval gates |
| `docs/canvas-llm-local-first-drive-first-architecture.md` | Local-first / Drive-first architecture |
| `docs/canvas-llm-approval-and-export-states.md` | Approval and export state vocabulary |
| `docs/canvas-llm-placeholder-schema-maintenance.md` | Maintenance rules for this schema layer |
| `docs/canvas-llm-manual-export-package-plan.md` | Manual copy/export package workflow plan |

## 3. Design Principles

- **Single-user/Owen-focused** — built for one teacher, not enterprise multi-tenant use.
- **Local-first** — drafts and exports stay on local disk until explicitly approved otherwise.
- **Drive-first** — curriculum source references point to Google Drive, NAS, iCloud, or local folders.
- **Export-before-publish** — export to local/manual packages before any future Canvas connector.
- **Human approval before export** — teacher must approve before export; export does not imply publish.
- **No silent publishing** — nothing reaches Canvas without explicit approval and a separate connector PR.
- **No student data** — placeholders must never include real student names, IDs, or grades.
- **No live APIs during foundation** — no Canvas API, Google Drive API, or OAuth.
- **No runtime behavior during foundation** — this doc is inert planning text only.
- **Metadata/reference-first, not raw-file-hosting-first** — reference Curriculum Builder metadata; do not duplicate all raw files into hosted storage.

## 4. Placeholder Object Families

### Main Canvas object families

```text
canvas_page_draft
canvas_assignment_draft
canvas_announcement_draft
canvas_module_plan
canvas_file_link_plan
```

### Supporting objects

```text
canvas_export_package
canvas_review_note_placeholder
canvas_idempotency_fingerprint
canvas_source_reference
```

These are names for planning only. They are not code objects, database tables, JSON schemas, TypeScript interfaces, or validators.

## 5. Shared Placeholder Fields

Future Canvas draft objects may share these planning fields:

| Field | Purpose |
| --- | --- |
| `placeholder_id` | Planning identifier only; not a live database key. |
| `object_type` | One of the placeholder object family names. |
| `academic_year` | Planning label for school year context. |
| `week_number` | Planning label for weekly pacing context. |
| `day_of_week` | Planning label for daily pacing context. |
| `subject_key` | Planning label for subject/course context. |
| `source_reference` | Points to manual or placeholder sources only; not live Drive resolution. |
| `title_placeholder` | Planning title text; not generated content. |
| `body_placeholder` | Planning body text; not generated content. |
| `resource_reference_ids` | References future Curriculum Builder metadata/reference records, not raw hosted files. |
| `teacher_only_notes_placeholder` | Teacher planning notes only; must never imply student data. |
| `student_facing_allowed` | Safety concept flag only; not a live permission grant. |
| `approval_state` | Vocabulary from `docs/canvas-llm-approval-and-export-states.md`. |
| `export_state` | Vocabulary from `docs/canvas-llm-approval-and-export-states.md`. |
| `safety_flags` | Required safety marker list (see section 14). |
| `created_from` | Planning label for how the placeholder was authored. |
| `revision_label` | Planning label for revision tracking. |
| `idempotency_fingerprint_placeholder` | Future idempotency concept; not computed in this PR. |
| `notes` | Freeform planning notes; not generated review comments. |

## 6. Canvas Page Draft Placeholder

Text-only shape (not JSON/YAML):

```text
object_type: canvas_page_draft
placeholder_id: canvas_page_draft_placeholder
academic_year: placeholder_only
week_number: placeholder_only
day_of_week: placeholder_only
subject_key: placeholder_only
title_placeholder: placeholder_only
body_placeholder: placeholder_only
resource_reference_ids: placeholder_only
student_facing_allowed: placeholder_only
approval_state: not_started
export_state: not_ready
safety_flags: placeholder_only | no_canvas_api | no_generation | no_student_data
```

Intended future use:

- Draft Canvas page title and body locally.
- Preview locally for teacher review.
- Teacher approves for export.
- Future manual copy or optional approved connector.

Explicit boundaries:

- No page is generated here.
- No page is exported here.
- No page is published here.

## 7. Canvas Assignment Draft Placeholder

Fields:

```text
object_type
placeholder_id
academic_year
week_number
day_of_week
subject_key
lesson_code_placeholder
assignment_title_placeholder
instructions_placeholder
points_placeholder
due_date_placeholder
submission_type_placeholder
resource_reference_ids
approval_state
export_state
safety_flags
```

Notes:

- `points_placeholder` is not gradebook data.
- `due_date_placeholder` is not live Canvas scheduling.
- `submission_type_placeholder` is a planning label only.
- No real assignment is created.

## 8. Canvas Announcement Draft Placeholder

Fields:

```text
object_type
placeholder_id
academic_year
week_number
audience_placeholder
announcement_title_placeholder
announcement_body_placeholder
publish_timing_placeholder
approval_state
export_state
safety_flags
```

Notes:

- No announcement is sent.
- No audience is resolved.
- No students are referenced.
- No Canvas API is called.

## 9. Canvas Module Plan Placeholder

Fields:

```text
object_type
placeholder_id
academic_year
week_number
module_title_placeholder
ordered_item_placeholders
approval_state
export_state
safety_flags
```

Notes:

- This is a local planning outline only.
- It does not create Canvas modules.
- It does not reorder Canvas modules.
- It does not inspect existing Canvas modules.

## 10. Canvas File-Link Plan Placeholder

Fields:

```text
object_type
placeholder_id
resource_reference_id
source_system_placeholder
source_uri_placeholder
display_name_placeholder
teacher_only
student_facing_allowed
link_status_placeholder
approval_state
export_state
safety_flags
```

Notes:

- This references future Curriculum Builder metadata records.
- It does not upload files.
- It does not resolve Drive links.
- It does not resolve Canvas file IDs.
- It does not scan folders.

## 11. Canvas Export Package Placeholder

Fields:

```text
object_type
placeholder_id
academic_year
week_number
included_subjects_placeholder
included_draft_ids_placeholder
approved_count_placeholder
export_format_placeholder
export_state
safety_flags
notes
```

Allowed future export formats:

```text
markdown
html
csv
manual_copy_package
future_canvas_api_payload
```

Notes:

- `future_canvas_api_payload` is a label only.
- It is not generated in this PR.
- It is not executable.
- It does not activate Canvas.

## 12. Review Note Placeholder

Fields:

```text
object_type
placeholder_id
related_draft_id
review_note_placeholder
review_source
teacher_action_needed
approval_state
safety_flags
```

Important:

- This must not create real review notes.
- This must not analyze real student data.
- This must not generate real lesson review comments.
- This is only a placeholder for future teacher-facing draft review workflow.

## 13. Idempotency Fingerprint Placeholder

Future idempotency may use:

```text
academic_year
week_number
day_of_week
subject_key
object_type
title_placeholder
body_placeholder
resource_reference_ids
revision_label
```

State:

- No hash is computed in this PR.
- No idempotency engine is added.
- No duplicate detection is active.
- This is a future design placeholder only.

## 14. Safety Flags

Required safety flags for future placeholder examples:

```text
placeholder_only
documentation_only
no_runtime_behavior
no_canvas_api
no_google_drive_api
no_oauth
no_network_calls
no_automation
no_scanning
no_indexing
no_ocr
no_embeddings
no_vector_database
no_generation
no_student_data
manual_approval_required
export_before_publish
```

Future placeholder examples should include these safety concepts where relevant.

## 15. Non-Activation Boundary

This placeholder schema does not add:

- parser
- importer
- loader
- runtime validator
- database
- app code
- Canvas integration
- Drive integration
- generation
- student data

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
