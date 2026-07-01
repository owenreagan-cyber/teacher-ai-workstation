# Canvas LLM Manual Export Package Shapes

```text
Status: documentation/status only. This manual export package plan is inert planning text. It does not create an exporter, export command, runtime package builder, Canvas API client, Google Drive client, OAuth flow, parser, importer, loader, validator, database table, schema file, network call, automation, lesson generator, generated lesson draft, generated review note, or student-data workflow.
```

## 1. Purpose

This document defines text-only placeholder shapes for future manual copy/export packages. All shapes are Markdown fenced text blocks only — not JSON, YAML, SQL, or TypeScript.

## 2. Shared Package Fields

| Field | Purpose |
| --- | --- |
| `package_placeholder_id` | Planning identifier for the package; not a live key. |
| `package_type` | One of the manual export package family names. |
| `academic_year` | Planning label for school year context. |
| `week_number` | Planning label for weekly context. |
| `subject_key` | Planning label for subject/course context. |
| `source_draft_ids_placeholder` | References source draft placeholder IDs. |
| `approval_state_required` | Required approval state before export (e.g. `approved_for_export`). |
| `export_state_required` | Required export state before package assembly (e.g. `export_ready`). |
| `export_format_placeholder` | Future export format label. |
| `teacher_review_summary_placeholder` | Summary of teacher review; not generated commentary. |
| `copy_ready_blocks_placeholder` | Copy-ready text blocks for manual paste. |
| `resource_link_checklist_placeholder` | Checklist of resource links to verify. |
| `teacher_only_notes_placeholder` | Teacher-only notes; never student data. |
| `manual_canvas_steps_placeholder` | Manual Canvas copy step labels. |
| `post_copy_completion_checklist_placeholder` | Post-copy verification checklist. |
| `safety_footer_placeholder` | Required safety reminder block. |
| `manual_completion_status_placeholder` | Future manual completion status label. |
| `notes` | Freeform planning notes. |

## 3. Canvas Page Copy Package Shape

```text
package_type: canvas_page_copy_package
package_placeholder_id: canvas_page_copy_package_placeholder
source_draft_object_type: canvas_page_draft
approval_state_required: approved_for_export
export_state_required: export_ready
copy_ready_title_block: placeholder_only
copy_ready_body_block: placeholder_only
resource_link_checklist: placeholder_only
manual_canvas_steps: placeholder_only
safety_footer: placeholder_only | manual_copy_only | not_published
```

Future use is copy-ready Canvas page text. No page content is generated here. No page is published here.

## 4. Canvas Assignment Copy Package Shape

```text
package_type: canvas_assignment_copy_package
package_placeholder_id: canvas_assignment_copy_package_placeholder
source_draft_object_type: canvas_assignment_draft
assignment_title_block_placeholder: placeholder_only
assignment_instructions_block_placeholder: placeholder_only
points_block_placeholder: placeholder_only
due_date_block_placeholder: placeholder_only
submission_type_block_placeholder: placeholder_only
resource_link_checklist: placeholder_only
manual_canvas_steps: placeholder_only
safety_footer: placeholder_only | manual_copy_only | not_published
```

Notes:

- `points_block_placeholder` is not a live gradebook action.
- `due_date_block_placeholder` is not live scheduling.
- No assignment is created.

## 5. Canvas Announcement Copy Package Shape

```text
package_type: canvas_announcement_copy_package
package_placeholder_id: canvas_announcement_copy_package_placeholder
source_draft_object_type: canvas_announcement_draft
announcement_title_block_placeholder: placeholder_only
announcement_body_block_placeholder: placeholder_only
publish_timing_note_placeholder: placeholder_only
manual_canvas_steps: placeholder_only
safety_footer: placeholder_only | manual_copy_only | not_published
```

Notes:

- No announcement is sent.
- No audience is resolved.
- No student data is used.

## 6. Canvas Module Checklist Package Shape

```text
package_type: canvas_module_checklist_package
package_placeholder_id: canvas_module_checklist_package_placeholder
module_title_placeholder: placeholder_only
ordered_item_checklist_placeholder: placeholder_only
manual_canvas_steps: placeholder_only
completion_status_placeholder: placeholder_only
safety_footer: placeholder_only | manual_copy_only | not_published
```

Notes:

- This is a checklist concept only.
- No Canvas module is created.
- No module ordering is changed.

## 7. Canvas File-Link Checklist Package Shape

```text
package_type: canvas_file_link_checklist_package
package_placeholder_id: canvas_file_link_checklist_package_placeholder
resource_reference_ids_placeholder: placeholder_only
display_name_placeholder: placeholder_only
source_system_placeholder: placeholder_only
source_uri_placeholder: placeholder_only
student_facing_allowed: placeholder_only
teacher_only: placeholder_only
manual_link_checklist_placeholder: placeholder_only
safety_footer: placeholder_only | manual_copy_only | not_published
```

Notes:

- No Drive link is resolved.
- No Canvas file ID is resolved.
- No file is uploaded.
- No folder is scanned.

## 8. Weekly Export Bundle Placeholder Shape

```text
package_type: canvas_weekly_export_bundle_placeholder
package_placeholder_id: canvas_weekly_export_bundle_placeholder
academic_year: placeholder_only
week_number: placeholder_only
included_package_types: placeholder_only
included_package_ids_placeholder: placeholder_only
teacher_review_summary_placeholder: placeholder_only
manual_copy_order_placeholder: placeholder_only
blocked_items_placeholder: placeholder_only
completion_checklist_placeholder: placeholder_only
safety_footer: placeholder_only | manual_copy_only | not_published
```

Notes:

- This is a future bundle concept only.
- It does not produce an archive.
- It does not create files.
- It does not publish to Canvas.

## 9. Manual Canvas Steps Placeholder

Future manual steps:

```text
open_canvas_course_manually
create_or_open_target_page_manually
copy_title_manually
copy_body_manually
check_links_manually
save_as_draft_or_publish_manually
verify_result_manually
record_completion_status_manually
```

These are teacher checklist labels only. This workflow does not automate a browser. This workflow does not call Canvas.

## 10. Non-Activation Boundary

This shapes document does not add an exporter, generated package files, runtime behavior, Canvas API, Drive API, OAuth, network calls, automation, generation, student data, parser/importer/loader/validator, or database/schema activation.

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
