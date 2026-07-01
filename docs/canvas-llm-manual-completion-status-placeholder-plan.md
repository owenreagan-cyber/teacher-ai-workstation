# Canvas LLM Manual Completion Status Placeholder Plan

```text
Status: documentation/status only. This manual completion status plan is inert planning text. It does not create a completion tracker, checklist runner, review engine, exporter, export command, runtime package builder, Canvas API client, Google Drive client, OAuth flow, parser, importer, loader, validator, database table, schema file, network call, browser automation, lesson generator, generated lesson draft, generated review note, or student-data workflow.
```

## 1. Purpose

This document defines future manual completion status tracking for Canvas LLM export packages after a teacher manually copies content into Canvas. The manual completion status concept records what Owen did outside the app — not what software verified in Canvas.

It builds on PR #144–#147 Canvas LLM documentation. This is planning only. No completion tracker runs in this PR.

No Canvas item is read, written, created, updated, deleted, or verified by software. Teacher verification is manual and external to the app.

## 2. Manual Completion Status Concept

After a teacher manually copies an approved export package into Canvas, future workflows may record a planning-only completion status. These statuses are vocabulary labels only — not database values, not API states, and not enforced by code in this PR.

## 3. Placeholder Future Statuses

| Status | Meaning |
| --- | --- |
| `not_copied` | Package approved for export but teacher has not copied content into Canvas yet. |
| `copied_to_canvas_manually` | Teacher reports they copied content into Canvas manually. |
| `teacher_verified_in_canvas` | Teacher manually verified the result in Canvas; not software-verified. |
| `needs_manual_revision` | Teacher found an issue and needs to revise before re-copying. |
| `skipped` | Teacher chose not to copy this package for the week. |
| `blocked` | Carried over from review checklist; item cannot proceed. |
| `rejected` | Carried over from review checklist; teacher rejected the package. |

## 4. Status Transition Rules

Documented future transitions (not enforced in code):

```text
not_copied -> copied_to_canvas_manually
not_copied -> skipped
not_copied -> blocked
not_copied -> rejected
copied_to_canvas_manually -> teacher_verified_in_canvas
copied_to_canvas_manually -> needs_manual_revision
needs_manual_revision -> copied_to_canvas_manually
needs_manual_revision -> skipped
blocked -> not_copied (only after teacher resolves block manually)
rejected -> (terminal; no automatic recovery)
```

Forbidden transitions (documented only):

```text
blocked -> copied_to_canvas_manually (without resolving block)
rejected -> copied_to_canvas_manually
not_copied -> teacher_verified_in_canvas (without copied_to_canvas_manually)
any status -> software-verified (no automated Canvas verification)
```

## 5. Blocked and Rejected Carryover

Blocked and rejected carryover from `docs/canvas-llm-manual-export-review-checklist.md`:

- Items marked `blocked` in review remain blocked until teacher manually resolves the issue.
- Items marked `rejected` in review remain rejected; they must not be copied.
- Blocked/rejected carryover does not trigger automatic repair, regeneration, or background jobs.
- Completion status must not advance past `not_copied` for blocked or rejected packages.

Blocked conditions from review checklist carry over:

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

## 6. Required Future Fields (Planning Only)

Future completion records may use these planning-only fields:

| Field | Purpose |
| --- | --- |
| `package_id` | Reference to the manual export package placeholder ID. |
| `canvas_destination_label` | Human label for where content was copied (e.g. course page name). |
| `completion_status` | One of the placeholder future statuses above. |
| `copied_by` | Teacher identity label; not student data. |
| `copied_at` | Manual timestamp note; not live scheduling. |
| `verified_by` | Teacher who manually verified in Canvas. |
| `verified_at` | Manual verification timestamp note. |
| `revision_reason` | Teacher note when status is `needs_manual_revision`. |
| `blocked_or_rejected_reason` | Carried-over reason from review checklist. |
| `source_review_checklist_reference` | Link to review checklist doc or checklist gate labels. |
| `notes` | Freeform teacher planning notes; not generated review notes. |

These are planning field names only. No database columns, JSON schemas, or runtime validators are created by this PR.

## 7. Manual Verification Expectations

- Teacher opens Canvas manually and verifies the copied content.
- Teacher confirms title, body, links, and module placement manually.
- Teacher records completion status manually in a future approved implementation.
- no Canvas verification is automated.
- No Canvas API is called.
- No browser automation inspects Canvas.
- No software reads Canvas state to confirm success.

## 8. Chief of Staff Future Role

### What Chief of Staff may eventually report

- Whether completion status planning docs exist.
- Whether required status vocabulary is documented.
- Whether safety boundaries and non-activation markers are present.
- PASS/WARN/FAIL from read-only status scripts only.

### What Chief of Staff must not do yet

- Track live completion status.
- Read or write Canvas items.
- Verify teacher copies in Canvas.
- Enforce status transitions.
- Store completion records.
- Call Canvas API, Drive API, or network endpoints.

Chief of Staff remains status and safety verification only.

## 9. Relationship to Existing Canvas LLM Docs

| Document | Role |
| --- | --- |
| `docs/teacher-app-designer-canvas-llm-plan.md` | Track plan |
| `docs/canvas-llm-safety-and-approval-contract.md` | Safety contract |
| `docs/canvas-llm-approval-and-export-states.md` | Approval/export states |
| `docs/canvas-llm-manual-export-package-plan.md` | Export package workflow |
| `docs/canvas-llm-manual-export-review-checklist.md` | Pre-copy review checklist |

## 10. Non-Activation Boundary

This plan does not add:

- No completion tracker
- No checklist runner
- No review engine
- No exporter
- No generated package files
- No runtime behavior
- No Canvas API
- No Google Drive API
- No OAuth
- No network calls
- No browser automation
- No automation or scheduler
- No generation
- No generated review notes
- No student data
- No parser/importer/loader/validator
- No database/schema activation

Moving to a runtime completion tracker requires a separate approved PR.

Weekly bundle planning is documented in `docs/canvas-llm-weekly-export-bundle-placeholder-plan.md`.

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
