# Canvas LLM Stop Marker and Curriculum Builder Return Maintenance

## Purpose

This document defines editing rules for `docs/canvas-llm-stop-marker-curriculum-builder-return.md`. The stop marker blocks default Canvas LLM PR continuation and redirects focus to Curriculum Builder foundation.

## Editing Rules

- Keep stop marker planning/status-only.
- Preserve PR #153 source baseline.
- Preserve stop/frozen/blocked language.
- Do not recommend runtime Canvas LLM work as the next default track.
- Do not add active command behavior.

## Required Stop Marker Language

The stop marker must retain:

- `Stop marker status: active`
- `Canvas LLM foundation status: complete for now`
- `Canvas LLM runtime status: frozen`
- `Default next Canvas LLM PR status: blocked`
- `Recommended next project focus: Curriculum Builder foundation`
- `Runtime/export/API/generation approval status: not approved`

## Required Canvas Complete/Frozen Language

Preserve:

- Canvas LLM docs/status foundation is complete for now
- Canvas LLM runtime status: frozen
- stop marker active

## Required Runtime Block Language

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
- no generated review notes
- no student data

## Required Curriculum Builder Return Language

Preserve:

- Recommended next project focus: Curriculum Builder foundation
- Curriculum Builder foundation remains active as docs/status track
- baseline from PR #153: PASS 946 / WARN 0 / FAIL 0

## Required Future Prompt Boundary

Preserve:

- What Future Prompts Must Not Do list
- What Future Prompts May Do list
- do not continue Canvas LLM PRs by default

## Required Chief of Staff Boundary

Preserve:

- Chief of Staff may report static Canvas LLM status and recommend Curriculum Builder foundation
- Chief of Staff must not generate Canvas packages, assemble bundles, export content, publish to Canvas, verify Canvas, resolve Drive links, inspect files, use APIs/OAuth/network, automate browser actions, create generated review notes, or handle student data

## Required Build Queue Boundary

Preserve:

- build queue may reference Canvas LLM as complete/frozen/stopped
- build queue must not recommend Canvas LLM runtime work by default
- build queue should recommend Curriculum Builder foundation as the next default track

## Required Active Priorities Boundary

Preserve:

- active priorities should show Canvas LLM as complete/frozen/stopped
- active priorities should not ask Cursor to continue Canvas LLM runtime/export/API/generation
- active priorities should point to Curriculum Builder foundation

## Required Reopen Requirements

Preserve future Canvas LLM reopen requirements including separate explicit user approval, named PR, explicit scope, confirmation that stop marker is being intentionally superseded, dry-run behavior, rollback/deletion plan, test plan, safety gates, and no student data confirmation.

## Maintenance Checklist

Before merging stop-marker edits:

- [ ] Stop marker remains planning/status-only
- [ ] `Stop marker status: active` preserved
- [ ] `Canvas LLM foundation complete for now` preserved
- [ ] `Canvas LLM runtime status: frozen` preserved
- [ ] PR #153 baseline preserved
- [ ] Curriculum Builder return handoff preserved
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
