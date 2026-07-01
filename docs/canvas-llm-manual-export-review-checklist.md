# Canvas LLM Manual Export Review Checklist

```text
Status: documentation/status only. This manual export review checklist is inert planning text. It does not create a checklist runner, review engine, exporter, export command, runtime package builder, Canvas API client, Google Drive client, OAuth flow, parser, importer, loader, validator, database table, schema file, network call, browser automation, lesson generator, generated lesson draft, generated review note, or student-data workflow.
```

## 1. Purpose

This document defines future teacher review checklists for manual Canvas copy/export packages. The manual export review checklist exists to keep copy-ready Canvas packages safe before Owen manually uses them in Canvas.

It builds on the PR #144 foundation, PR #145 placeholder schema/state vocabulary, and PR #146 manual export package plan. This is planning only. No checklist is executed by code in this PR.

## 2. Review Philosophy

- Manual review comes before manual copy.
- Teacher approval is required before export.
- Export does not mean publish.
- Manual copy does not imply automated Canvas action.
- The checklist should catch blocked states, missing titles/bodies, teacher-only resources, unresolved links, and safety footer issues.
- Local-first/Drive-first remains the default.
- Supabase remains optional/future only, not default.

## 3. Relationship to Existing Canvas LLM Docs

| Document | Role |
| --- | --- |
| `docs/teacher-app-designer-canvas-llm-plan.md` | Track plan and ownership split |
| `docs/canvas-llm-safety-and-approval-contract.md` | Safety prohibitions and approval gates |
| `docs/canvas-llm-approval-and-export-states.md` | Approval and export state vocabulary |
| `docs/canvas-llm-placeholder-schema.md` | Draft object vocabulary |
| `docs/canvas-llm-manual-export-package-plan.md` | Manual export package workflow |
| `docs/canvas-llm-manual-export-package-shapes.md` | Text-only package shapes |
| `docs/canvas-llm-manual-export-package-maintenance.md` | Package maintenance rules |

Placeholder schema defines future draft/package vocabulary. Approval/export states define status vocabulary. Manual export package plan defines package families. This checklist defines review steps only. No implementation is activated.

## 4. Required Review Gates

Future review gates (planning labels only):

```text
package_identity_review
approval_state_review
export_state_review
student_facing_safety_review
teacher_only_resource_review
title_and_body_review
resource_link_review
manual_canvas_steps_review
safety_footer_review
blocked_or_rejected_review
completion_status_review
```

These are planning labels only. They are not executable gates. They do not enforce workflow. They do not publish anything.

## 5. Universal Manual Export Review Checklist

Markdown checklist for all future packages (documentation only; not executed by the repo):

```text
[ ] Confirm package_placeholder_id is present.
[ ] Confirm package_type is one of the allowed manual export package families.
[ ] Confirm approval_state_required is approved_for_export.
[ ] Confirm export_state_required is export_ready.
[ ] Confirm no blocked safety issue is listed.
[ ] Confirm no rejected item is included.
[ ] Confirm student-facing package does not include teacher-only resources.
[ ] Confirm title block is present where required.
[ ] Confirm body/instructions block is present where required.
[ ] Confirm resource links are placeholders or manually reviewed references.
[ ] Confirm no student data appears.
[ ] Confirm no generated review note is treated as real review.
[ ] Confirm manual_canvas_steps are present.
[ ] Confirm safety_footer is present.
[ ] Confirm package is manual_copy_only and not_published.
```

The checklist is documentation only. It is not executed by the repo. It does not validate files.

## 6. Canvas Page Copy Package Review

- [ ] Page title present
- [ ] Page body present
- [ ] Student-facing status reviewed
- [ ] Resource links reviewed manually
- [ ] Teacher-only notes excluded from student-facing content
- [ ] Safety footer present
- [ ] No Canvas page is created by this checklist

## 7. Canvas Assignment Copy Package Review

- [ ] Assignment title present
- [ ] Instructions present
- [ ] Points reviewed as placeholder/manual value only
- [ ] Due date reviewed as placeholder/manual value only
- [ ] Submission type reviewed as placeholder/manual value only
- [ ] Resources reviewed
- [ ] No gradebook action occurs
- [ ] No assignment is created

## 8. Canvas Announcement Copy Package Review

- [ ] Announcement title present
- [ ] Announcement body present
- [ ] Publish timing reviewed manually
- [ ] Audience not resolved automatically
- [ ] No student data
- [ ] No announcement is sent

## 9. Canvas Module Checklist Package Review

- [ ] Module title present
- [ ] Ordered item checklist reviewed
- [ ] Manual order confirmed
- [ ] Completion status reviewed manually
- [ ] No module is created
- [ ] No Canvas module is reordered

## 10. Canvas File-Link Checklist Package Review

- [ ] Resource reference ID present
- [ ] Display name reviewed
- [ ] Source system reviewed
- [ ] Source URI remains placeholder/manual reference
- [ ] `student_facing_allowed` reviewed
- [ ] `teacher_only` reviewed
- [ ] No Drive link resolved
- [ ] No Canvas file ID resolved
- [ ] No file uploaded
- [ ] No folder scanned

## 11. Weekly Export Bundle Review

- [ ] Week number present
- [ ] Included package types reviewed
- [ ] Included package IDs reviewed
- [ ] Teacher review summary present
- [ ] Manual copy order reviewed
- [ ] Blocked items reviewed
- [ ] Completion checklist present
- [ ] no archive is produced
- [ ] no files are generated
- [ ] no Canvas publish occurs

## 12. Safety Footer Review

Required safety footer concepts:

```text
placeholder_only
teacher_reviewed_required
manual_copy_only
no_canvas_api
no_google_drive_api
no_oauth
no_network_calls
no_student_data
not_published
```

Checklist:

- [ ] Safety footer is present
- [ ] Safety footer includes `manual_copy_only`
- [ ] Safety footer includes `not_published`
- [ ] Safety footer does not imply Canvas publish
- [ ] Safety footer does not imply automated verification

## 13. Blocked and Rejected Handling Review

Blocked conditions:

```text
missing_title
missing_body
teacher_only_resource_in_student_package
unapproved_draft
blocked_approval_state
unsupported_export_format
unresolved_resource_reference
safety_flag_missing
```

- Blocked items should not be copied.
- Rejected items should not be copied.
- No automatic repair occurs.
- No automatic regeneration occurs.
- No background job is triggered.

## 14. Manual Completion Verification

Manual completion concepts:

```text
not_copied
copied_to_canvas_manually
teacher_verified_in_canvas
needs_manual_revision
skipped
```

Checklist:

- [ ] Teacher manually confirms if copied
- [ ] Teacher manually verifies result in Canvas
- [ ] Teacher records completion status manually
- [ ] no Canvas verification is automated
- [ ] No Canvas API is called

## 15. Non-Activation Boundary

This checklist does not add:

- No checklist runner
- No review engine
- No exporter
- No generated package files
- No runtime behavior
- No Canvas API
- No Drive API
- No OAuth
- No network
- No automation
- No browser automation
- No generation
- No generated review notes
- No student data
- No parser/importer/loader/validator
- No database/schema activation

See `docs/canvas-llm-manual-completion-status-placeholder-plan.md` for manual completion status planning after teacher copy.

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
