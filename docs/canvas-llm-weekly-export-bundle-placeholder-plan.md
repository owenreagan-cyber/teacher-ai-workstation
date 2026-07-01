# Canvas LLM Weekly Export Bundle Placeholder Plan

```text
Status: documentation/status only. This weekly export bundle plan is inert planning text. It does not create a bundle assembler, package builder, exporter, export command, completion tracker, checklist runner, review engine, Canvas API client, Google Drive client, OAuth flow, parser, importer, loader, validator, database table, schema file, network call, browser automation, lesson generator, generated lesson draft, generated review note, or student-data workflow.
```

## Purpose

This document describes a future weekly bundle concept for organizing Canvas-ready package placeholders for a week of teaching. The weekly bundle is a planning container — not a generated artifact, not an export engine, and not a live Canvas integration.

It ties together existing Canvas LLM planning tracks: page, assignment, announcement, module, and file-link package placeholders; manual export review checklist references; manual completion status references; blocked/rejected carryover; teacher verification boundaries; and Chief of Staff reporting boundaries.

## Current Status

- planning-only
- Markdown-only
- no runtime behavior
- no bundle files are generated
- no Canvas content is read, written, created, updated, deleted, or published

## Non-Activation Boundary

This plan does not add:

- no exporter
- no export command
- no weekly bundle assembler
- no package builder
- no package files
- no generated package files
- no generated lesson drafts
- no generated review notes
- no Canvas API
- no Google Drive API
- no OAuth
- no network calls
- no automation
- no scheduler
- no browser automation
- no parser/importer/loader/runtime validator
- no scanning/indexing/OCR/embeddings/vector database
- no student data
- no new dependencies

## Weekly Bundle Concept

A future weekly bundle is a planning grouping that may eventually reference:

- Canvas pages
- Canvas assignments
- Canvas announcements
- Canvas modules
- file-link package placeholders
- manual review checklist status
- manual completion status
- blocked/rejected carryover
- teacher verification notes

The weekly bundle does not own curriculum files and does not perform exports.

## Bundle Scope

The weekly bundle may eventually organize:

- one week label
- school week date range
- course label
- class/section label
- unit label
- lesson sequence label
- package references
- review status summary
- manual completion status summary
- blocked/rejected item summary
- teacher verification summary

## Out-of-Scope Behavior

The bundle plan does not:

- create Canvas objects
- edit Canvas objects
- publish Canvas objects
- validate Canvas objects
- inspect Canvas objects
- copy anything into Canvas
- upload files
- resolve Drive links
- scan folders
- read student data
- generate real lesson content
- generate package artifacts

## Relationship to Existing Canvas LLM Planning Docs

| Document | Role |
| --- | --- |
| `docs/teacher-app-designer-canvas-llm-plan.md` | Track plan and ownership |
| `docs/canvas-llm-safety-and-approval-contract.md` | Safety prohibitions |
| `docs/canvas-llm-approval-and-export-states.md` | Approval/export states |
| `docs/canvas-llm-manual-export-package-plan.md` | Manual export package workflow |
| `docs/canvas-llm-manual-export-package-shapes.md` | Package shape definitions |
| `docs/canvas-llm-manual-export-review-checklist.md` | Pre-copy review checklist |
| `docs/canvas-llm-manual-completion-status-placeholder-plan.md` | Post-copy completion status |

## Future Bundle Inputs

Planning-only future inputs (not active tool inputs):

- teacher-selected week
- teacher-selected course
- teacher-selected unit/lesson sequence
- teacher-selected package placeholders
- teacher review checklist references
- manual completion status references
- blocked/rejected carryover references
- notes

## Future Bundle Package Types

| Package type | Purpose |
| --- | --- |
| `canvas_page_package` | Page copy package placeholder reference |
| `canvas_assignment_package` | Assignment copy package placeholder reference |
| `canvas_announcement_package` | Announcement copy package placeholder reference |
| `canvas_module_package` | Module checklist package placeholder reference |
| `canvas_file_link_package` | File-link checklist package placeholder reference |
| `teacher_note_placeholder` | Teacher planning note only |
| `manual_followup_placeholder` | Manual follow-up reminder only |

These are planning labels only — not code objects or database tables.

## Future Bundle Status Vocabulary

| Status | Meaning |
| --- | --- |
| `bundle_not_started` | No weekly bundle planning has begun. |
| `bundle_planned` | Bundle structure and item references are drafted locally. |
| `bundle_review_ready` | Bundle is ready for teacher review. |
| `bundle_reviewed` | Teacher has reviewed bundle contents. |
| `bundle_ready_for_manual_copy` | All included items passed review; ready for manual copy workflow. |
| `bundle_partially_copied` | Some items copied manually; others pending. |
| `bundle_copied_to_canvas_manually` | Teacher reports all intended items copied. |
| `bundle_teacher_verified_in_canvas` | Teacher manually verified bundle in Canvas. |
| `bundle_needs_manual_revision` | Teacher found issues requiring revision. |
| `bundle_blocked` | Bundle cannot proceed due to blocked items. |
| `bundle_rejected` | Teacher rejected the bundle. |
| `bundle_skipped` | Teacher chose to skip this week’s bundle. |

## Future Bundle Review Gates

Planning-only review gates (checklist concepts, not runnable gates):

- package presence review
- package type review
- safety boundary review
- blocked/rejected review
- teacher-facing wording review
- Canvas destination label review
- manual copy readiness review
- manual completion status review

## Manual Export Review Relationship

A weekly bundle cannot be considered ready unless referenced package placeholders have completed the manual export review checklist (`docs/canvas-llm-manual-export-review-checklist.md`). Blocked/rejected packages carry into the weekly bundle summary. Review is human/manual. No software verifies content quality.

## Manual Completion Status Relationship

Bundle items may eventually reference completion statuses from `docs/canvas-llm-manual-completion-status-placeholder-plan.md`:

- `not_copied`
- `copied_to_canvas_manually`
- `teacher_verified_in_canvas`
- `needs_manual_revision`
- `skipped`
- `blocked`
- `rejected`

These may appear per bundle item but are not active runtime state in this PR.

## Blocked and Rejected Carryover

- Blocked items remain blocked until teacher resolves the blocker.
- Rejected items must not be copied into Canvas.
- Skipped items are intentionally omitted.
- Weekly bundle summary must preserve blocked/rejected/skipped reasons.
- Nothing silently converts blocked/rejected/skipped into ready.

## Teacher Verification Boundary

- Teacher manually copies content into Canvas.
- Teacher manually checks Canvas.
- Teacher manually verifies Canvas state.
- App does not inspect Canvas.
- App does not prove Canvas state.
- App does not mark anything complete automatically.

## Chief of Staff Reporting Boundary

### Chief of Staff may eventually report

- weekly bundle plan exists
- package placeholders are referenced
- review checklist status is documented
- manual completion status is documented
- blocked/rejected/skipped items are visible
- non-activation boundaries remain in force

### Chief of Staff must not

- assemble bundles
- generate packages
- copy to Canvas
- publish to Canvas
- verify Canvas state
- resolve Drive links
- inspect files
- use student data
- perform API/network/browser automation

## Placeholder Bundle Fields

| Field | Purpose |
| --- | --- |
| `bundle_id` | Planning identifier for the weekly bundle |
| `bundle_label` | Human-readable bundle label |
| `course_label` | Course name label |
| `section_label` | Section/class label |
| `week_start_date` | Week start date label |
| `week_end_date` | Week end date label |
| `unit_label` | Unit label |
| `lesson_sequence_label` | Lesson sequence label |
| `bundle_status` | One of the bundle status vocabulary values |
| `review_checklist_reference` | Link to review checklist completion |
| `manual_completion_summary_reference` | Link to completion status summary |
| `blocked_item_count` | Count of blocked items (planning only) |
| `rejected_item_count` | Count of rejected items (planning only) |
| `skipped_item_count` | Count of skipped items (planning only) |
| `teacher_verification_status` | Manual verification label |
| `created_by` | Teacher identity label |
| `created_at` | Planning timestamp note |
| `updated_at` | Planning update timestamp note |
| `notes` | Freeform planning notes |

## Placeholder Bundle Item Fields

| Field | Purpose |
| --- | --- |
| `bundle_item_id` | Planning item identifier |
| `bundle_id` | Parent bundle reference |
| `package_type` | One of the package type labels |
| `package_label` | Human-readable package label |
| `canvas_destination_label` | Where content would be copied in Canvas |
| `source_package_reference` | Reference to export package placeholder |
| `review_status` | Review checklist status label |
| `completion_status` | Completion status label |
| `blocked_or_rejected_reason` | Carryover reason if blocked/rejected |
| `manual_revision_reason` | Reason if needs revision |
| `teacher_verification_note` | Teacher manual verification note |
| `sort_order` | Display order in bundle |
| `notes` | Freeform item notes |

## Future Folder / Naming Concepts

Future placeholder naming examples only (no folder structure created by this PR):

- `weekly-bundle-placeholder`
- `week-label`
- `course-label`
- `bundle-summary-placeholder`

## Future Audit Trail Expectations

A future approved implementation may record:

- who created the bundle plan
- when items were reviewed
- when items were marked copied or verified manually
- blocked/rejected/skipped reasons at time of review

This PR does not create an audit trail. Audit expectations are planning-only.

## Example Static Bundle Outline

Fictional planning-only example (no real student or course data):

```text
Bundle label: Example Week 01 Placeholder
Course label: Example Course
Week range: 2099-01-05 to 2099-01-09
Status: bundle_planned
Items:
  - canvas_page_package: Example Monday Page Placeholder
  - canvas_assignment_package: Example Practice Assignment Placeholder
  - canvas_announcement_package: Example Weekly Announcement Placeholder
  - canvas_module_package: Example Week Module Placeholder
  - canvas_file_link_package: Example Resource Link Placeholder
```

## Required Human Decisions

These remain manual:

- whether a package is safe
- whether a package is copied
- whether a Canvas destination is correct
- whether content needs revision
- whether blocked/rejected/skipped items should remain excluded
- whether teacher has verified Canvas manually

## Future Activation Requirements

Any future active weekly bundle tool requires a separate approved PR and must define:

- explicit command name
- allowed inputs
- output location
- dry-run behavior
- audit trail
- safety checks
- manual approval gates
- no student data handling
- no network/API behavior unless separately approved
- rollback/deletion behavior if runtime behavior is ever added

## Safety Footer

Documentation/status only. Weekly export bundle placeholder plan is Markdown-only planning text. No runtime behavior, generated package files, weekly bundle files, Canvas API, Google Drive API, OAuth, network calls, automation, browser automation, generation, student data, or Canvas publishing.

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
