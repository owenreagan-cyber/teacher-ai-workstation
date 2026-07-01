# Canvas LLM Placeholder Schema Maintenance

```text
Status: documentation/status only. This placeholder schema is inert planning text. It does not create runtime schema files, parsers, importers, loaders, validators, database tables, Canvas API clients, Google Drive clients, OAuth flows, network calls, automation, lesson generation, generated lesson drafts, generated review notes, or student-data handling.
```

## 1. Purpose

This guide explains how to maintain Canvas LLM placeholder schema documentation safely. All changes must remain documentation/status only unless a separate explicit approval PR authorizes implementation.

## 2. Canonical Documents

```text
docs/canvas-llm-placeholder-schema.md
docs/canvas-llm-approval-and-export-states.md
docs/canvas-llm-safety-and-approval-contract.md
docs/canvas-llm-local-first-drive-first-architecture.md
docs/teacher-app-designer-canvas-llm-plan.md
```

## 3. Editing Rules

- Keep placeholder schemas in **Markdown only**.
- **Do not create active JSON**, YAML, SQL, or TypeScript schema files.
- **Do not add runtime validators**.
- **Do not add parsers/importers/loaders**.
- Do not introduce API assumptions.
- Do not introduce Canvas publishing.
- Do not introduce Drive resolution.
- Do not use student data.
- **Preserve single-user/local-first/Drive-first** default.
- **Supabase optional/future-only** language must remain.

## 4. Required Placeholder Object Families

These object family names must remain documented:

- `canvas_page_draft`
- `canvas_assignment_draft`
- `canvas_announcement_draft`
- `canvas_module_plan`
- `canvas_file_link_plan`
- `canvas_export_package`

## 5. Required Approval States

- `not_started`
- `drafted`
- `needs_teacher_review`
- `teacher_revised`
- `approved_for_export`
- `exported`
- `blocked`
- `rejected`

## 6. Required Export States

- `not_ready`
- `draft_ready`
- `review_ready`
- `approved`
- `export_ready`
- `exported`
- `blocked`
- `failed`

## 7. Required Safety Flags

- `placeholder_only`
- `documentation_only`
- `no_runtime_behavior`
- `no_canvas_api`
- `no_google_drive_api`
- `no_oauth`
- `no_network_calls`
- `no_automation`
- `no_scanning`
- `no_indexing`
- `no_ocr`
- `no_embeddings`
- `no_vector_database`
- `no_generation`
- `no_student_data`
- `manual_approval_required`
- `export_before_publish`

## 8. Status Script Expectations

`scripts/teacher-app-designer-canvas-llm-status.sh` should only run **static file-presence and fixed-string checks**.

It **must not parse, load, validate, generate, or call APIs**.

## 9. Checklist Before Editing

- [ ] Is the change documentation-only?
- [ ] Does it preserve no-runtime behavior?
- [ ] Does it preserve no Canvas API?
- [ ] Does it preserve no Drive API?
- [ ] Does it preserve no OAuth?
- [ ] Does it preserve no generation?
- [ ] Does it preserve no student data?
- [ ] Does it preserve local-first/Drive-first?
- [ ] Does it avoid new dependencies?
- [ ] Does it avoid new schema files?
- [ ] Does it avoid changing existing command semantics?

## 10. Future Activation Boundary

Moving from placeholder schema docs to active local implementation requires a future explicit PR and approval. Do not add parsers, importers, loaders, runtime validators, databases, or app code without that approval.

## Related Verification Commands

```bash
bash scripts/teacher-app-designer-canvas-llm-status.sh
bin/chief-of-staff --teacher-app-designer-canvas-llm-status
```
