# Prompt Pack Reference Index

## Purpose

This document defines a compact prompt pack reference index pass after prompt pack maintenance checklist. It adds a single index for reusable prompt pack references, maintenance guidance, workflow navigation docs, and verification bundle docs without changing behavior.

This PR adds prompt pack reference index guidance only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: prompt pack reference index complete.
```

Prompt pack handoff summary continues reusable prompt stack handoff. See `docs/prompt-pack-handoff-summary.md`.

## Why This Index Exists

After prompt pack maintenance checklist, maintenance rules were documented but reusable prompt references were still spread across multiple workflow docs. This index makes reusable prompt pack references easy to find without weakening lifecycle gates or final local-main proof.

## Reference Index Goals

```text
make reusable prompt references easy to find
make prompt pack maintenance easy to find
make workflow navigation docs easy to find
make verification bundles easy to find
make prompt template rules easy to find
make PR lifecycle guardrails easy to find
make branch hygiene and local-main proof easy to find
keep prompt references current after roadmap changes
preserve every existing command
preserve every existing check
```

## Prompt Pack Start Here

```text
Start with docs/prompt-pack-reference-index.md when looking for reusable prompt references.
Use docs/prompt-pack-maintenance-checklist.md before reusing or updating prompt packs.
Use docs/workflow-docs-navigation-status-summary.md to verify the workflow doc map.
Use docs/testing-checklist-consolidation.md for reusable verification bundles.
Use docs/command-check-bundle-reference-polish.md for the compact bundle picker.
Use docs/cursor-prompt-template.md when drafting a new Cursor prompt.
```

## Maintenance Reference

```text
Prompt pack maintenance checklist: docs/prompt-pack-maintenance-checklist.md
Roadmap update checklist: docs/prompt-pack-maintenance-checklist.md
Dashboard count update checklist: docs/prompt-pack-maintenance-checklist.md
New status command checklist: docs/prompt-pack-maintenance-checklist.md
Prompt reuse review checklist: docs/prompt-pack-maintenance-checklist.md
```

## Workflow Navigation Reference

```text
Workflow docs navigation status summary: docs/workflow-docs-navigation-status-summary.md
Workflow docs cross-link polish: docs/workflow-docs-cross-link-polish.md
Cursor workflow operating system: docs/cursor-workflow-operating-system.md
Cursor prompt template: docs/cursor-prompt-template.md
Cursor PR review checklist: docs/cursor-pr-review-checklist.md
```

## Verification Bundle Reference

```text
Reusable verification bundles: docs/testing-checklist-consolidation.md
Compact command/check bundle picker: docs/command-check-bundle-reference-polish.md
Checklist-driven prompt template tightening: docs/checklist-driven-prompt-template-tightening.md
```

## Prompt Template Reference

```text
Cursor prompt template: docs/cursor-prompt-template.md
Checklist-driven prompt template tightening: docs/checklist-driven-prompt-template-tightening.md
Cursor workflow operating system: docs/cursor-workflow-operating-system.md
```

## PR Lifecycle Reference

```text
PR lifecycle guardrails: docs/pr-lifecycle-guardrail-consolidation.md
Branch hygiene and cleanup: docs/branch-hygiene-cleanup-reference.md
Local main proof report polish: docs/local-main-proof-report-polish.md
```

## Branch and Local Main Reference

```text
Branch hygiene and cleanup: docs/branch-hygiene-cleanup-reference.md
Local main proof report polish: docs/local-main-proof-report-polish.md
PR lifecycle guardrails: docs/pr-lifecycle-guardrail-consolidation.md
```

## Reuse Review Reference

```text
prompt references do not replace PR-specific checks
prompt references do not replace no-commit review
prompt references do not replace PR open/unmerged verification
prompt references do not replace mergedAt non-null verification
prompt references do not replace branch deletion verification
prompt references do not replace final local-main dashboard proof
```

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

- This PR adds prompt pack reference index guidance only.
- This PR preserves all existing commands.
- This PR does not rename commands.
- This PR does not remove commands.
- This PR does not remove checks.
- This PR does not change command behavior.
- This PR preserves dashboard checks.
- This PR preserves PASS/WARN/FAIL semantics.
- This PR does not implement document scanning.
- This PR does not implement file indexing.
- This PR does not generate lesson content.
- This PR does not create real review notes.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Related prompt docs

- Prompt pack stale-reference audit: `docs/prompt-pack-stale-reference-audit.md`
- Prompt pack freshness report: `docs/prompt-pack-freshness-report-polish.md`
- Prompt pack handoff summary: `docs/prompt-pack-handoff-summary.md`
- Prompt pack maintenance: `docs/prompt-pack-maintenance-checklist.md`

## Commands Reference

```bash
bin/chief-of-staff --prompt-pack-reference-index-status
bin/chief-of-staff --prompt-pack-maintenance-status
bin/chief-of-staff --workflow-docs-navigation-status
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --dashboard
bash scripts/prompt-pack-reference-index-status.sh
```
