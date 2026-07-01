# Canvas LLM Planning Foundation Closure Audit Maintenance

## Purpose

This document defines editing rules for `docs/canvas-llm-planning-foundation-closure-audit.md`. The closure audit verifies the capstone endpoint and stale-reference hygiene. It must not be edited to imply runtime activation.

## Editing Rules

- Keep closure audit planning/status-only.
- Preserve capstone as canonical endpoint.
- Preserve `Canvas LLM foundation complete for now` language.
- Do not weaken non-activation language.
- Do not recommend runtime Canvas LLM work as the next default track.
- Do not add active command behavior.

## Required Closure Language

The closure audit must retain:

- `Audit status: complete`
- `Canvas LLM foundation status: complete for now`
- `Runtime status: not active`
- `Implementation status: not started`
- Canvas LLM foundation complete for now

## Required Canonical Endpoint Language

- `docs/canvas-llm-planning-foundation-capstone.md` is the canonical endpoint
- Closure audit does not supersede the capstone

## Required Non-Activation Language

Preserve language that none of the following is active:

- no Canvas API
- no Google Drive API
- no OAuth
- no network calls
- no browser automation
- no automation
- no scheduler
- no background jobs
- no scanning/indexing/OCR/embeddings/vector database
- no lesson generation
- no generated lesson drafts
- no generated review notes
- no student data

## Required Runtime Stop Line

Preserve:

- Runtime activation requires a separate explicitly approved PR
- separate explicit approval before runtime work
- API/OAuth/network behavior must be separately approved
- Canvas/Drive behavior must be separately approved

## Required Chief of Staff Boundary

Preserve:

- Chief of Staff may report Canvas LLM status and show PASS/WARN/FAIL results
- Chief of Staff must not generate packages, assemble bundles, export content, publish to Canvas, verify Canvas, resolve Drive links, inspect files, use APIs, use OAuth, use network calls, automate browser actions, create generated review notes, or handle student data

## Required Safe Future Work Language

Preserve safe tracks such as:

- pause Canvas LLM and return to Curriculum Builder foundation
- docs/status-only stale-reference audit
- Recommended next focus is outside Canvas LLM runtime work

## Required Blocked Future Work Language

Preserve blocked tracks:

- runtime bundle assembler
- exporter
- package generator
- Canvas API integration
- Drive API integration
- OAuth
- review engine
- completion tracker

## Maintenance Checklist

Before merging closure audit edits:

- [ ] Closure audit remains planning/status-only
- [ ] `Canvas LLM foundation complete for now` preserved
- [ ] Capstone remains canonical endpoint
- [ ] Runtime stop line preserved
- [ ] Chief of Staff status-only boundary preserved
- [ ] No implication that Canvas LLM is implemented
- [ ] Do not imply Canvas state is software-verified
- [ ] Static status checks updated if new required strings added

## Disallowed Changes Without Separate Approved PR

Do not:

- imply package generation exists
- imply weekly bundle assembly exists
- imply completion tracking exists
- recommend runtime Canvas LLM work as the default next track
- remove capstone from canonical endpoint role
- add runtime code, exporters, APIs, OAuth, network calls, or automation
- weaken `scripts/teacher-app-designer-canvas-llm-status.sh` checks
