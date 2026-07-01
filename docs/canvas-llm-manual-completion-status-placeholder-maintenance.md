# Canvas LLM Manual Completion Status Placeholder Maintenance

```text
Status: documentation/status only. This manual completion status plan is inert planning text. It does not create a completion tracker, checklist runner, review engine, exporter, export command, runtime package builder, Canvas API client, Google Drive client, OAuth flow, parser, importer, loader, validator, database table, schema file, network call, browser automation, lesson generator, generated lesson draft, generated review note, or student-data workflow.
```

## 1. Purpose

This guide explains how to maintain Canvas LLM manual completion status planning documentation safely. All changes must remain documentation/status only unless a separate explicit approval PR authorizes implementation.

## 2. Canonical Documents

- `docs/canvas-llm-manual-completion-status-placeholder-plan.md`
- `docs/canvas-llm-manual-export-review-checklist.md`
- `docs/canvas-llm-manual-export-package-plan.md`
- `docs/canvas-llm-approval-and-export-states.md`
- `docs/canvas-llm-safety-and-approval-contract.md`
- `docs/canvas-llm-weekly-export-bundle-placeholder-plan.md`

## 3. Editing Rules

- Keep completion status planning in **Markdown only**.
- **Do not add a completion tracker**.
- **Do not add a checklist runner**.
- **Do not add a review engine**.
- **Do not add an exporter**.
- **Do not add generated package files**.
- **Do not add browser automation**.
- **Do not add Canvas API calls**.
- **Do not add Drive API calls**.
- Do not use student data.
- Preserve manual verification only.
- Preserve local-first/Drive-first.
- Preserve Supabase optional/future-only.

## 4. Required Status Values

These placeholder statuses must remain documented:

- `not_copied`
- `copied_to_canvas_manually`
- `teacher_verified_in_canvas`
- `needs_manual_revision`
- `skipped`
- `blocked`
- `rejected`

## 5. Required Non-Activation Language

Docs must continue to state:

- No Canvas item is read, written, created, updated, deleted, or verified by software.
- Teacher verification is manual and external to the app.
- no Canvas verification is automated.
- Moving to a runtime completion tracker requires a separate approved PR.

## 6. Required Cross-Links

Maintain cross-links from:

- `docs/teacher-app-designer-canvas-llm-plan.md`
- `docs/canvas-llm-approval-and-export-states.md`
- `docs/canvas-llm-manual-export-review-checklist.md`
- `docs/canvas-llm-manual-export-review-checklist-maintenance.md`

## 7. Maintenance Checklist

- [ ] Is the change documentation-only?
- [ ] Are all seven placeholder statuses still documented?
- [ ] Is blocked/rejected carryover still documented?
- [ ] Does it preserve manual-only verification?
- [ ] Does it avoid a completion tracker?
- [ ] Does it avoid Canvas API?
- [ ] Does it avoid Drive API?
- [ ] Does it avoid network calls?
- [ ] Does it avoid student data?
- [ ] Does it preserve non-activation language?

## 8. Future Activation Boundary

Any future runtime completion tracker requires a **separate approved PR**. A future tracker must begin local-only, manual-entry-only, and must not call Canvas API, Drive API, or network endpoints without explicit later approval.

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
