# Workflow Docs Navigation Status Summary

## Purpose

This document defines a workflow docs navigation status summary pass after workflow docs cross-link polish. It adds a compact status summary that verifies the workflow documentation map, cross-links, and navigation path remain intact without changing behavior.

This PR adds workflow docs navigation status summary only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: workflow docs navigation status summary complete.
```

Prompt pack freshness report polish continues reusable prompt freshness summaries. See `docs/prompt-pack-freshness-report-polish.md`.

## Why This Summary Exists

After workflow docs cross-link polish, cross-links were present but there was no single command to verify the full navigation path remained intact. This summary makes workflow documentation status easy to verify without weakening lifecycle gates or final local-main proof.

## Navigation Summary Goals

```text
make workflow documentation status easy to verify
make the start-here path easy to find
make verification bundle docs easy to find
make prompt template docs easy to find
make PR lifecycle docs easy to find
make branch hygiene docs easy to find
make local-main proof docs easy to find
preserve every existing command
preserve every existing check
```

## Workflow Navigation Status

```text
Start here: docs/cursor-workflow-operating-system.md
Prompt template: docs/cursor-prompt-template.md
PR review checklist: docs/cursor-pr-review-checklist.md
Verification bundles: docs/testing-checklist-consolidation.md
Compact bundle picker: docs/command-check-bundle-reference-polish.md
Prompt template tightening: docs/checklist-driven-prompt-template-tightening.md
PR lifecycle guardrails: docs/pr-lifecycle-guardrail-consolidation.md
Branch hygiene: docs/branch-hygiene-cleanup-reference.md
Local main proof: docs/local-main-proof-report-polish.md
Cross-link map: docs/workflow-docs-cross-link-polish.md
Navigation status summary: docs/workflow-docs-navigation-status-summary.md
```

Use `docs/workflow-docs-navigation-status-summary.md` to verify the workflow doc map remains intact.

## Start-Here Path

```text
1. Read docs/cursor-workflow-operating-system.md.
2. Use docs/cursor-prompt-template.md to draft a prompt.
3. Use docs/testing-checklist-consolidation.md and docs/command-check-bundle-reference-polish.md for reusable check bundles.
4. Use docs/pr-lifecycle-guardrail-consolidation.md for lifecycle gates.
5. Use docs/branch-hygiene-cleanup-reference.md for branch cleanup.
6. Use docs/local-main-proof-report-polish.md for final reporting.
```

## Verification Bundle Path

- Full bundles: `docs/testing-checklist-consolidation.md`
- Compact picker: `docs/command-check-bundle-reference-polish.md`
- Prompt template tightening: `docs/checklist-driven-prompt-template-tightening.md`

## Prompt Template Path

- Operating system: `docs/cursor-workflow-operating-system.md`
- Prompt template: `docs/cursor-prompt-template.md`
- PR review checklist: `docs/cursor-pr-review-checklist.md`
- Navigation status: `docs/workflow-docs-navigation-status-summary.md`

## PR Lifecycle Path

- Lifecycle guardrails: `docs/pr-lifecycle-guardrail-consolidation.md`
- Branch hygiene (next): `docs/branch-hygiene-cleanup-reference.md`
- Cross-link map: `docs/workflow-docs-cross-link-polish.md`

## Branch Hygiene Path

- PR lifecycle (before): `docs/pr-lifecycle-guardrail-consolidation.md`
- Branch hygiene: `docs/branch-hygiene-cleanup-reference.md`
- Local main proof (after): `docs/local-main-proof-report-polish.md`

## Local Main Proof Path

- Branch hygiene (before): `docs/branch-hygiene-cleanup-reference.md`
- Local main proof: `docs/local-main-proof-report-polish.md`
- Navigation status: `docs/workflow-docs-navigation-status-summary.md`

## Navigation Rules

```text
navigation links help people find the right doc
navigation links do not replace PR-specific checks
navigation links do not replace no-commit review
navigation links do not replace PR open/unmerged verification
navigation links do not replace mergedAt non-null verification
navigation links do not replace branch deletion verification
navigation links do not replace final local-main dashboard proof
```

Navigation summaries help people find the right process doc. Navigation summaries do not replace PR-specific checks, no-commit review, PR open/unmerged verification, mergedAt non-null verification, branch deletion verification, or final local-main dashboard proof.

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

- This PR adds workflow docs navigation status summary only.
- This PR does not implement document scanning.
- This PR does not implement file indexing.
- This PR does not generate lesson content.
- This PR does not create real review notes.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Related workflow docs

- Prompt pack maintenance: `docs/prompt-pack-maintenance-checklist.md`
- Prompt pack reference index: `docs/prompt-pack-reference-index.md`
- Prompt pack stale-reference audit: `docs/prompt-pack-stale-reference-audit.md`
- Prompt pack freshness report: `docs/prompt-pack-freshness-report-polish.md`
- Cross-link map: `docs/workflow-docs-cross-link-polish.md`

## Commands Reference

```bash
bin/chief-of-staff --workflow-docs-navigation-status
bin/chief-of-staff --workflow-docs-cross-link-status
bin/chief-of-staff --local-main-proof-report-status
bin/chief-of-staff --branch-hygiene-cleanup-status
bin/chief-of-staff --pr-lifecycle-guardrail-status
bin/chief-of-staff --dashboard
bash scripts/workflow-docs-navigation-status-summary.sh
```
