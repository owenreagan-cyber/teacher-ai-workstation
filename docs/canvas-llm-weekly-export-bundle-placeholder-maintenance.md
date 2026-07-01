# Canvas LLM Weekly Export Bundle Placeholder Maintenance

```text
Status: documentation/status only. This weekly export bundle plan is inert planning text. It does not create a bundle assembler, package builder, exporter, export command, completion tracker, checklist runner, review engine, Canvas API client, Google Drive client, OAuth flow, parser, importer, loader, validator, database table, schema file, network call, browser automation, lesson generator, generated lesson draft, generated review note, or student-data workflow.
```

## Purpose

This guide explains how to maintain Canvas LLM weekly export bundle planning documentation safely.

## Editing Rules

- Keep the doc planning-only.
- Preserve every bundle status value unless intentionally superseded in a future approved PR.
- Preserve every package type label.
- Preserve blocked/rejected/skipped carryover.
- Preserve manual verification boundaries.
- Preserve Chief of Staff non-runtime boundary.
- Preserve no Canvas API / no Drive API / no network / no OAuth / no automation language.
- Preserve no scanning/indexing/OCR/embeddings/vector database language.
- Preserve no generated lesson drafts / no generated review notes language.
- Do not add active command behavior.
- Do not add bundle artifacts.
- Do not add runtime validation.
- Do not add generated package files.
- Do not imply Canvas state is software-verified.

## Required Status Values

- `bundle_not_started`
- `bundle_planned`
- `bundle_review_ready`
- `bundle_reviewed`
- `bundle_ready_for_manual_copy`
- `bundle_partially_copied`
- `bundle_copied_to_canvas_manually`
- `bundle_teacher_verified_in_canvas`
- `bundle_needs_manual_revision`
- `bundle_blocked`
- `bundle_rejected`
- `bundle_skipped`

## Required Package Type Labels

- `canvas_page_package`
- `canvas_assignment_package`
- `canvas_announcement_package`
- `canvas_module_package`
- `canvas_file_link_package`
- `teacher_note_placeholder`
- `manual_followup_placeholder`

## Required Non-Activation Language

Docs must continue to state:

- no exporter
- no weekly bundle assembler
- no package builder
- no package files
- no generated package files
- no Canvas API
- no Google Drive API
- no OAuth
- no network calls
- no automation
- no scheduler
- no browser automation
- no student data
- separate approved PR for future activation

## Required Cross-Links

Maintain cross-links from:

- `docs/teacher-app-designer-canvas-llm-plan.md`
- `docs/canvas-llm-approval-and-export-states.md`
- `docs/canvas-llm-manual-export-package-plan.md`
- `docs/canvas-llm-manual-export-package-shapes.md`
- `docs/canvas-llm-manual-export-review-checklist.md`
- `docs/canvas-llm-manual-export-review-checklist-maintenance.md`
- `docs/canvas-llm-manual-completion-status-placeholder-plan.md`
- `docs/canvas-llm-manual-completion-status-placeholder-maintenance.md`

## Maintenance Checklist

- [ ] Is the change documentation-only?
- [ ] Are all bundle statuses still documented?
- [ ] Are all package type labels still documented?
- [ ] Is blocked/rejected/skipped carryover preserved?
- [ ] Is manual verification manual-only?
- [ ] Is Chief of Staff status-only?

## Review Checklist

- [ ] No bundle assembler added?
- [ ] No generated package files added?
- [ ] No Canvas API added?
- [ ] No Drive API added?
- [ ] No network calls added?

## Future Activation Boundary

Any future active weekly bundle tool requires a **separate approved PR**. A future tool must begin local-only and must not call Canvas API, Drive API, or network endpoints without explicit later approval.

## Disallowed Changes Without Separate Approval

- Adding a bundle assembler
- Adding a package builder
- Adding an exporter or export command
- Adding generated weekly bundle files
- Adding runtime validation or completion tracking
- Adding Canvas API, Drive API, OAuth, or network calls
- Adding browser automation or schedulers
- Adding student data handling

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
