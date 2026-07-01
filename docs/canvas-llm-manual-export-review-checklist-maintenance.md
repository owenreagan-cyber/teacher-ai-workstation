# Canvas LLM Manual Export Review Checklist Maintenance

```text
Status: documentation/status only. This manual export review checklist is inert planning text. It does not create a checklist runner, review engine, exporter, export command, runtime package builder, Canvas API client, Google Drive client, OAuth flow, parser, importer, loader, validator, database table, schema file, network call, browser automation, lesson generator, generated lesson draft, generated review note, or student-data workflow.
```

## 1. Purpose

This guide explains how to maintain Canvas LLM manual export review checklist documentation safely. All changes must remain documentation/status only unless a separate explicit approval PR authorizes implementation.

## 2. Canonical Documents

- `docs/canvas-llm-manual-export-review-checklist.md`
- `docs/canvas-llm-manual-export-package-plan.md`
- `docs/canvas-llm-manual-export-package-shapes.md`
- `docs/canvas-llm-manual-export-package-maintenance.md`
- `docs/canvas-llm-approval-and-export-states.md`
- `docs/canvas-llm-safety-and-approval-contract.md`
- `docs/canvas-llm-manual-completion-status-placeholder-maintenance.md`

## 3. Editing Rules

- **Keep checklists in Markdown only**.
- **Do not add a checklist runner**.
- **Do not add a review engine**.
- **Do not add an exporter**.
- **Do not add generated package files**.
- **Do not add browser automation**.
- **Do not add Canvas API calls**.
- **Do not add Drive API calls**.
- **Do not resolve links automatically**.
- **Do not upload files**.
- Do not use student data.
- **Preserve manual approval**.
- **Preserve manual completion verification**.
- **Preserve manual copy only**.
- Preserve local-first/Drive-first.
- Preserve Supabase optional/future-only.

## 4. Required Review Gates

- `package_identity_review`
- `approval_state_review`
- `export_state_review`
- `student_facing_safety_review`
- `teacher_only_resource_review`
- `title_and_body_review`
- `resource_link_review`
- `manual_canvas_steps_review`
- `safety_footer_review`
- `blocked_or_rejected_review`
- `completion_status_review`

## 5. Required Package Family Coverage

- `canvas_page_copy_package`
- `canvas_assignment_copy_package`
- `canvas_announcement_copy_package`
- `canvas_module_checklist_package`
- `canvas_file_link_checklist_package`
- `canvas_weekly_export_bundle_placeholder`

## 6. Required Completion Concepts

- `not_copied`
- `copied_to_canvas_manually`
- `teacher_verified_in_canvas`
- `needs_manual_revision`
- `skipped`

## 7. Required Blocked Conditions

- `missing_title`
- `missing_body`
- `teacher_only_resource_in_student_package`
- `unapproved_draft`
- `blocked_approval_state`
- `unsupported_export_format`
- `unresolved_resource_reference`
- `safety_flag_missing`

## 8. Required Safety Concepts

- `placeholder_only`
- `teacher_reviewed_required`
- `manual_copy_only`
- `no_canvas_api`
- `no_google_drive_api`
- `no_oauth`
- `no_network_calls`
- `no_student_data`
- `not_published`

## 9. Status Script Expectations

`scripts/teacher-app-designer-canvas-llm-status.sh` should only use **static file-presence and fixed-string checks**.

It **must not parse checklists**. It **must not execute checklists**. It **must not generate packages**. It **must not write files**. It must not call Canvas, Drive, network, or APIs. It must not inspect folders.

## 10. Checklist Before Editing

- [ ] Is the change documentation-only?
- [ ] Does it preserve manual review only?
- [ ] Does it avoid adding a checklist runner?
- [ ] Does it avoid adding a review engine?
- [ ] Does it avoid adding an exporter?
- [ ] Does it avoid generated package files?
- [ ] Does it avoid Canvas API?
- [ ] Does it avoid Drive API?
- [ ] Does it avoid OAuth?
- [ ] Does it avoid network calls?
- [ ] Does it avoid student data?
- [ ] Does it avoid browser automation?
- [ ] Does it preserve local-first/Drive-first?
- [ ] Does it preserve Supabase optional/future-only?

## 11. Future Activation Boundary

Moving from checklist planning to an active checklist runner **requires a future explicit PR and approval**. A future checklist runner must still begin local-only and export-review-only. A live Canvas connector requires a separate later approval track.

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
