# Canvas LLM Frozen Foundation Handoff Snapshot Maintenance

## Purpose

This document defines editing rules for `docs/canvas-llm-frozen-foundation-handoff-snapshot.md`. The snapshot records the frozen handoff state after PR #152. It must not be edited to imply runtime activation.

## Editing Rules

- Keep snapshot planning/status-only.
- Preserve source PR #152 and source commit baseline.
- Preserve freeze boundary language.
- Do not recommend runtime Canvas LLM work as the next default track.
- Do not add active command behavior.

## Required Snapshot Status Language

The snapshot must retain:

- `Snapshot status: recorded`
- `Canvas LLM foundation status: complete for now`
- `Freeze status: frozen for runtime work`
- `Runtime status: not active`
- `Implementation status: not started`
- `Export status: not active`
- `Canvas API status: not active`
- `Google Drive API status: not active`
- `Generation status: not active`
- `Student data status: not active`

## Required Source State

Preserve:

- `Source PR: PR #152 — Canvas LLM Planning Foundation Index and Freeze`
- `Source merge commit: 1c3aa2b654b47ac3d14fc67e9f7beba299b37ff1`
- `Source Teacher App Designer / Canvas LLM status: PASS 519 / WARN 0 / FAIL 0`
- `Source Phase 1 status: PASS 308 / WARN 0 / FAIL 0`
- `Source Curriculum Builder foundation status: PASS 946 / WARN 0 / FAIL 0`

## Required Runtime Freeze Boundary

Preserve language that none of the following is approved:

- no exporter
- no export command
- no package generator
- no bundle assembler
- no Canvas API
- no Google Drive API
- no OAuth
- no network calls
- no browser automation
- no automation/scheduler/background jobs
- no lesson generation
- no student data

## Required Future Prompt Boundary

Preserve:

- What Future Prompts Must Not Start list
- What Future Prompts May Safely Do list
- separate explicit approval before unfreeze

## Required Chief of Staff Boundary

Preserve:

- Chief of Staff may report static Canvas LLM status and show PASS/WARN/FAIL
- Chief of Staff must not generate packages, assemble bundles, export content, publish to Canvas, verify Canvas, resolve Drive links, inspect files, use APIs/OAuth/network, automate browser actions, create generated review notes, or handle student data

## Required Build Queue Boundary

Preserve:

- build queue may reference Canvas LLM as complete/frozen
- build queue must not recommend Canvas LLM runtime work by default
- recommended next focus should be Curriculum Builder foundation

## Required Active Priorities Boundary

Preserve:

- active priorities should show Canvas LLM as frozen
- active priorities should not ask Cursor to continue Canvas LLM runtime/export/API/generation
- active priorities may point to Curriculum Builder foundation

## Required Unfreeze Requirements

Preserve future unfreeze requirements including separate explicit approval, named PR, explicit scope, dry-run behavior, rollback/deletion plan, test plan, safety gates, and no student data confirmation.

## Maintenance Checklist

Before merging snapshot edits:

- [ ] Snapshot remains planning/status-only
- [ ] `Canvas LLM foundation complete for now` preserved
- [ ] `Freeze status: frozen for runtime work` preserved
- [ ] Source PR #152 baseline preserved
- [ ] Runtime freeze boundary preserved
- [ ] Chief of Staff status-only boundary preserved
- [ ] Do not imply Canvas state is software-verified
- [ ] Static status checks updated if new required strings added

## Disallowed Changes Without Separate Approved PR

Do not:

- imply Canvas LLM is implemented
- imply package generation exists
- imply weekly bundle assembly exists
- imply completion tracking exists
- recommend runtime Canvas LLM work as the next default track
- weaken `scripts/teacher-app-designer-canvas-llm-status.sh` checks
- add runtime code, exporters, APIs, OAuth, network calls, or automation

## Related Docs

- Stop marker: `docs/canvas-llm-stop-marker-curriculum-builder-return.md`
- Stop marker maintenance: `docs/canvas-llm-stop-marker-curriculum-builder-return-maintenance.md`
