# Canvas LLM Planning Foundation Capstone Maintenance

## Purpose

This document defines editing rules for `docs/canvas-llm-planning-foundation-capstone.md`. The capstone is a planning/status-only handoff marker. It must not be edited to imply runtime activation.

## Editing Rules

- Keep capstone planning/status-only.
- Preserve `planning foundation complete for now`.
- Preserve `Activation status: not active`.
- Preserve every doc in the completed planning stack table unless superseded in a future approved PR.
- Add new rows to the table when new Canvas LLM planning docs are added.
- Do not weaken non-activation language.
- Do not add active command behavior.
- Do not add bundle artifacts, package files, or generated content.

## Required Capstone Status Language

The capstone must retain:

- `Status: planning foundation complete for now`
- `Activation status: not active`
- `Runtime status: none`
- `Canvas integration status: none`
- `Google Drive integration status: none`
- `Generation status: none`
- `Student data status: none`

## Required Documentation Map

The capstone must preserve the documentation flow:

```text
overall plan
→ safety and approval contract
→ approval/export states
→ manual package plan/shapes
→ manual review checklist
→ manual completion status placeholders
→ weekly bundle placeholder plan
→ capstone
```

## Required Non-Activation Language

Preserve language that none of the following is active:

- no runtime exporter
- no export command
- no bundle assembler
- no package builder
- no Canvas API
- no Google Drive API
- no OAuth
- no network calls
- no automation
- no scheduler
- no browser automation
- no scanning/indexing/OCR/embeddings/vector database
- no generated lesson drafts
- no generated review notes
- no student data
- no generated package files

## Required Future Approval Gate

Preserve requirement for separate approved PR before:

- package generation
- weekly bundle assembly
- export command
- Canvas publishing
- Canvas API
- Drive API
- OAuth
- browser automation
- review engine
- completion tracker
- real lesson generation
- generated review notes
- student data handling

## Required Chief of Staff Boundary

Preserve:

- Chief of Staff may report static status and confirm docs exist
- Chief of Staff must not generate packages, assemble bundles, export content, publish to Canvas, verify Canvas, resolve Drive links, inspect documents, use APIs, automate browser actions, create review notes, or handle student data

## Required Validation References

The capstone must reference:

- `scripts/teacher-app-designer-canvas-llm-status.sh`
- `bin/chief-of-staff --teacher-app-designer-canvas-llm-status`
- `bash scripts/phase-1-status.sh`
- `bin/chief-of-staff --dashboard`

## Maintenance Checklist

Before merging capstone edits:

- [ ] Capstone remains planning/status-only
- [ ] `planning foundation complete for now` preserved
- [ ] `Activation status: not active` preserved
- [ ] Completed planning stack table is current
- [ ] Non-activation categories complete
- [ ] Manual teacher verification boundary preserved
- [ ] Chief of Staff status-only boundary preserved
- [ ] Separate approved PR gate preserved
- [ ] Static status checks updated if new required strings added

## Related Docs

- Closure audit: `docs/canvas-llm-planning-foundation-closure-audit.md`
- Closure audit maintenance: `docs/canvas-llm-planning-foundation-closure-audit-maintenance.md`
- Planning foundation index: `docs/canvas-llm-planning-foundation-index.md`
- Planning foundation freeze: `docs/canvas-llm-planning-foundation-freeze.md`

## Disallowed Changes Without Separate Approved PR

Do not:

- imply Canvas LLM is implemented
- imply package generation exists
- imply weekly bundle assembly exists
- imply completion tracking exists
- imply Canvas state is software-verified
- Do not imply Canvas state is software-verified when editing related docs
- remove existing status docs from the map unless superseded
- add runtime code, exporters, APIs, OAuth, network calls, or automation
- weaken `scripts/teacher-app-designer-canvas-llm-status.sh` checks
