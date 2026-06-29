# Workflow Docs Cross-Link Polish

## Purpose

This document defines a workflow docs cross-link polish pass after local main proof report polish. It adds cross-links among checklist, prompt template, lifecycle guardrail, branch hygiene, and local-main proof docs so future prompts can navigate the process quickly without duplicating full instructions.

This PR adds workflow docs cross-link polish only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: workflow docs cross-link polish complete.
```

Workflow docs navigation status summary verifies the navigation path. See `docs/workflow-docs-navigation-status-summary.md`. Prompt pack maintenance checklist keeps reusable prompts current. See `docs/prompt-pack-maintenance-checklist.md`.

## Why Cross-Links Exist

After local main proof report polish, lifecycle, branch hygiene, and final report rules were complete but spread across many docs. Cross-links make navigation obvious without weakening PR-specific checks, no-commit review, or final local-main dashboard proof.

## Cross-Link Goals

```text
make workflow docs easier to navigate
avoid duplicating full instructions in every doc
make start-here guidance obvious
connect verification bundle docs to prompt template docs
connect lifecycle guardrails to branch hygiene
connect branch hygiene to local-main proof reporting
preserve every existing command
preserve every existing check
```

## Workflow Doc Map

```text
Cursor workflow operating system: docs/cursor-workflow-operating-system.md
Cursor prompt template: docs/cursor-prompt-template.md
Cursor PR review checklist: docs/cursor-pr-review-checklist.md
Testing/checklist consolidation: docs/testing-checklist-consolidation.md
Command/check bundle reference: docs/command-check-bundle-reference-polish.md
Checklist-driven prompt template tightening: docs/checklist-driven-prompt-template-tightening.md
PR lifecycle guardrail consolidation: docs/pr-lifecycle-guardrail-consolidation.md
Branch hygiene and cleanup reference: docs/branch-hygiene-cleanup-reference.md
Local main proof report polish: docs/local-main-proof-report-polish.md
```

Use `docs/workflow-docs-cross-link-polish.md` as the map for workflow docs.

## Start Here Links

```text
For daily workflow orientation, start with docs/cursor-workflow-operating-system.md.
For writing a new Cursor prompt, start with docs/cursor-prompt-template.md.
For reviewing before merge, use docs/cursor-pr-review-checklist.md.
For reusable verification bundles, use docs/testing-checklist-consolidation.md and docs/command-check-bundle-reference-polish.md.
For lifecycle gates, use docs/pr-lifecycle-guardrail-consolidation.md.
For branch cleanup, use docs/branch-hygiene-cleanup-reference.md.
For final completion reports, use docs/local-main-proof-report-polish.md.
```

## Verification Bundle Links

- Full bundle commands: `docs/testing-checklist-consolidation.md`
- Compact bundle picker: `docs/command-check-bundle-reference-polish.md`
- Bundle reference in prompts: `docs/checklist-driven-prompt-template-tightening.md`

## Prompt Template Links

- Operating system overview: `docs/cursor-workflow-operating-system.md`
- Reusable prompt body: `docs/cursor-prompt-template.md`
- Pre-merge review checklist: `docs/cursor-pr-review-checklist.md`

## PR Lifecycle Links

- Lifecycle guardrails: `docs/pr-lifecycle-guardrail-consolidation.md`
- Prompt template tightening: `docs/checklist-driven-prompt-template-tightening.md`
- Branch hygiene (after lifecycle): `docs/branch-hygiene-cleanup-reference.md`

## Branch Hygiene Links

- Lifecycle guardrails (before branch): `docs/pr-lifecycle-guardrail-consolidation.md`
- Branch hygiene reference: `docs/branch-hygiene-cleanup-reference.md`
- Final report (after branch cleanup): `docs/local-main-proof-report-polish.md`

## Local Main Proof Links

- Branch hygiene (before final proof): `docs/branch-hygiene-cleanup-reference.md`
- Local main proof and final report: `docs/local-main-proof-report-polish.md`
- Workflow doc map: `docs/workflow-docs-cross-link-polish.md`

## Future Prompt Navigation Rules

```text
future prompts may reference this doc map
future prompts must still include PR-specific checks
future prompts must still include no-commit review
future prompts must still verify PR open/unmerged state
future prompts must still verify mergedAt after merge
future prompts must still verify branch deletion when available
future prompts must still verify final local main
future prompts must still include dashboard proof
cross-links must not replace lifecycle guardrails
```

Cross-links help navigation but do not replace PR-specific checks, no-commit review, PR open/unmerged verification, mergedAt non-null verification, branch deletion verification, or final local-main dashboard proof.

## Backward Compatibility Rules

```text
do not remove existing commands
do not rename existing commands
do not remove existing checks
do not change command behavior
do not change dashboard summary format
do not change PASS/WARN/FAIL semantics
do not change merge verification expectations
do not weaken branch deletion proof
do not weaken final local-main proof
```

## Safety Boundaries

```text
no check removals
no command removals
no command renames
no behavior changes
no dashboard count regression
no PASS/WARN/FAIL semantic changes
no weakened PR lifecycle
no skipped PR-specific checks
no skipped no-commit review
no skipped PR open/unmerged verification
no skipped merged-state verification
no skipped branch deletion verification
no skipped final local-main proof
no document scanning
no folder scanning
no file indexing
no content parsing
no OCR
no embeddings
no vector database
no lesson generation changes
no new lesson briefs
no new lesson drafts
no real review notes
no student data
no student-sensitive data
no live integrations
no network calls
no APIs
no OAuth
no secrets
no automation
no scheduler implementation
no notifications
no image processing
no wallpaper/photo curator implementation
```

## What This PR Does Not Implement

- This PR adds workflow docs cross-link polish only.
- This PR does not implement document scanning.
- This PR does not implement file indexing.
- This PR does not generate lesson content.
- This PR does not create real review notes.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Related workflow docs

- Navigation status: `docs/workflow-docs-navigation-status-summary.md`
- Prompt pack maintenance: `docs/prompt-pack-maintenance-checklist.md`
- Local main proof: `docs/local-main-proof-report-polish.md`
- PR lifecycle: `docs/pr-lifecycle-guardrail-consolidation.md`

## Commands Reference

```bash
bin/chief-of-staff --workflow-docs-cross-link-status
bin/chief-of-staff --local-main-proof-report-status
bin/chief-of-staff --branch-hygiene-cleanup-status
bin/chief-of-staff --pr-lifecycle-guardrail-status
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --dashboard
bash scripts/workflow-docs-cross-link-status.sh
```
