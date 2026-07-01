# Canvas LLM Manual Export Package Maintenance

```text
Status: documentation/status only. This manual export package plan is inert planning text. It does not create an exporter, export command, runtime package builder, Canvas API client, Google Drive client, OAuth flow, parser, importer, loader, validator, database table, schema file, network call, automation, lesson generator, generated lesson draft, generated review note, or student-data workflow.
```

## 1. Purpose

This guide explains how to maintain Canvas LLM manual export package planning documentation safely. All changes must remain documentation/status only unless a separate explicit approval PR authorizes implementation.

## 2. Canonical Documents

- `docs/canvas-llm-manual-export-package-plan.md`
- `docs/canvas-llm-manual-export-package-shapes.md`
- `docs/canvas-llm-placeholder-schema.md`
- `docs/canvas-llm-approval-and-export-states.md`
- `docs/canvas-llm-safety-and-approval-contract.md`
- `docs/canvas-llm-manual-export-review-checklist-maintenance.md`

## 3. Editing Rules

- **Keep package shapes in Markdown only**.
- **Do not create active export package files**.
- **Do not add an exporter**.
- **Do not add a copy-package generator**.
- **Do not add browser automation**.
- **Do not add Canvas API calls**.
- **Do not add Drive API calls**.
- **Do not resolve links automatically**.
- **Do not upload files**.
- Do not use student data.
- **Preserve manual approval**.
- **Preserve manual copy only**.
- Preserve local-first/Drive-first.
- Preserve Supabase optional/future-only.

## 4. Required Package Families

- `canvas_page_copy_package`
- `canvas_assignment_copy_package`
- `canvas_announcement_copy_package`
- `canvas_module_checklist_package`
- `canvas_file_link_checklist_package`
- `canvas_weekly_export_bundle_placeholder`

## 5. Required Manual Step Labels

- `open_canvas_course_manually`
- `create_or_open_target_page_manually`
- `copy_title_manually`
- `copy_body_manually`
- `check_links_manually`
- `save_as_draft_or_publish_manually`
- `verify_result_manually`
- `record_completion_status_manually`

## 6. Required Completion Status Concepts

- `not_copied`
- `copied_to_canvas_manually`
- `teacher_verified_in_canvas`
- `needs_manual_revision`
- `skipped`

## 7. Required Safety Concepts

- `placeholder_only`
- `teacher_reviewed_required`
- `manual_copy_only`
- `no_canvas_api`
- `no_google_drive_api`
- `no_oauth`
- `no_network_calls`
- `no_student_data`
- `not_published`

## 8. Status Script Expectations

`scripts/teacher-app-designer-canvas-llm-status.sh` should only use **static file-presence and fixed-string checks**.

It **must not parse package shapes**. It **must not generate packages**. It **must not write files**. It must not call Canvas, Drive, network, or APIs. It must not inspect folders.

## 9. Checklist Before Editing

- [ ] Is the change documentation-only?
- [ ] Does it preserve manual copy/export only?
- [ ] Does it avoid adding an exporter?
- [ ] Does it avoid adding generated package files?
- [ ] Does it avoid Canvas API?
- [ ] Does it avoid Drive API?
- [ ] Does it avoid OAuth?
- [ ] Does it avoid network calls?
- [ ] Does it avoid student data?
- [ ] Does it avoid browser automation?
- [ ] Does it preserve local-first/Drive-first?
- [ ] Does it preserve Supabase optional/future-only?

## 10. Future Activation Boundary

Moving from manual export package planning to a real local exporter **requires a future explicit PR and approval**. A future real exporter must still begin local-only and export-only. A live Canvas connector requires a separate later approval track.

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
