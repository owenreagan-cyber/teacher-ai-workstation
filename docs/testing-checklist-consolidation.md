# Testing/Checklist Consolidation

## Purpose

This document defines a testing/checklist consolidation pass after project memory cleanup. It groups repeated manual verification commands into reusable bundles so future PR prompts stay shorter without weakening safety.

This PR consolidates testing/checklist guidance only. This pass is about preserving all existing commands, preserving command behavior, and preserving PASS/WARN/FAIL semantics while enforcing no command removals, no command renames, and no check removals.

## Current Status

```text
Current status: testing/checklist consolidation complete.
```

Command/check bundle reference polish adds a compact picker pointing here. See `docs/command-check-bundle-reference-polish.md`. Workflow doc map: `docs/workflow-docs-cross-link-polish.md`.

Checklist-driven prompt template tightening adds lifecycle guardrail rules for bundle use in Cursor prompts. See `docs/checklist-driven-prompt-template-tightening.md`.

Reusable verification bundles are documented for core, documentation/status, teacher planning/review, document indexing safety, Appearance & Vibe safety, pre-commit review, and post-merge verification.

## Why This Consolidation Exists

After project memory cleanup, the roadmap was clearer but PR prompts still repeated long manual check blocks. Consolidating named bundles makes future prompts shorter while preserving every existing check.

## Checklist Consolidation Goals

```text
reduce repeated manual check blocks
make future prompts shorter
preserve every existing check
preserve every existing command
make check bundles reusable
make safety checks easier to reference
make pre-commit review expectations clear
make post-merge verification expectations clear
avoid weakening safety boundaries
avoid hiding failures or warnings
```

## Core Verification Bundle

Run for every PR:

```bash
git status --short
git branch --show-current
bin/chief-of-staff --dashboard
bash scripts/phase-1-status.sh
bash scripts/verify-phase-0e.sh
git diff --check
git diff --stat
git diff --name-only
```

## Documentation/Status PR Bundle

Run for documentation, status, workflow-polish, and memory-cleanup PRs:

```bash
bash -n bin/chief-of-staff
bash -n scripts/chief-of-staff-dashboard.sh
bash -n scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
bash scripts/phase-1-status.sh
```

Each new status script must pass `bash -n`, run directly, and run through its matching `bin/chief-of-staff --*-status` command.

## Teacher Planning and Review Bundle

Run for lesson review, review notes, and teacher planning workflow PRs:

```bash
bin/chief-of-staff --lesson-review-view fractions-review
bin/chief-of-staff --review-notes-template-status
bin/chief-of-staff --lesson-review-workflow-status
bin/chief-of-staff --review-notes-workflow-status
bin/chief-of-staff --teacher-planning-command-status
find assistant/lesson-planning/briefs -maxdepth 1 -type f ! -name "README.md" -print
find assistant/lesson-planning/drafts -maxdepth 1 -type f ! -name "README.md" -print
find assistant/lesson-planning/review-notes -maxdepth 1 -type f ! -name "README.md" -print
```

The `find` commands should return empty output (no generated lesson brief, draft, or review note files).

## Document Indexing Safety Bundle

Run for document indexing plan/follow-up PRs:

```bash
bin/chief-of-staff --document-indexing-plan-status
bin/chief-of-staff --local-document-indexing-follow-up-status
grep -R "document scanning\|folder scanning\|file indexing\|OCR\|embeddings\|vector database" docs assistant/memory README.md scripts bin || true
```

Review grep output as safety-boundary wording only, not implementation.

## Appearance & Vibe Safety Bundle

Run when Appearance & Vibe foundation or safety docs change:

```bash
bin/chief-of-staff --wallpaper-photo-rotation-handoff-safety-status
bin/chief-of-staff --wallpaper-photo-notification-foundation-status
bin/chief-of-staff --wallpaper-photo-scheduler-foundation-status
bin/chief-of-staff --wallpaper-photo-image-processor-foundation-status
```

Appearance & Vibe foundation remains complete for now. Live wallpaper/photo curator implementation is not started.

## Chief of Staff Validation/Proof Bundle

Run for validation/proof infrastructure changes. Dashboard is canonical via `bin/chief-of-staff --dashboard` (not a separate `scripts/dashboard.sh`).

```bash
bash -n tests/chief-of-staff-v1-operating-test.sh
bash -n tests/smoke-chief-of-staff-cli.sh
bash -n scripts/chief-of-staff-validate-all.sh
bash -n scripts/run-workstation-proof.sh
bash -n bin/chief-of-staff

bash tests/chief-of-staff-v1-operating-test.sh
bash scripts/chief-of-staff-validate-all.sh
COS_VALIDATE_INCLUDE_SMOKE=1 bash scripts/chief-of-staff-validate-all.sh
bash scripts/run-workstation-proof.sh
bash tests/smoke-chief-of-staff-cli.sh
bin/chief-of-staff --dashboard
```

Execution model: `validate-all` is fast by default (no smoke). `proof-run` runs validate-all without smoke, then smoke once, then dashboard tail. These paths must never recurse into each other.

## Pre-Commit Review Bundle

Print before every commit:

```text
Changed files review
Unexpected files review
Existing behavior impact review
Command compatibility review
Dashboard count review
Safety review
Generated files review
Final git status review
```

## Post-Merge Verification Bundle

Run after merge on local `main`:

```bash
git switch main
git pull --ff-only
git log --oneline -5
git status --short
bin/chief-of-staff --dashboard
```

## Future Prompt Reuse Rules

```text
future prompts may reference these bundles by name
future prompts must not skip required safety checks
future prompts must still include PR-specific checks
future prompts must still include no-commit review
future prompts must still verify merged PR state
future prompts must still end on local main with clean working tree and dashboard passing
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
```

## Safety Boundaries

```text
no check removals
no command removals
no command renames
no behavior changes
no dashboard count regression
no PASS/WARN/FAIL semantic changes
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

- This PR consolidates testing/checklist guidance only.
- This PR does not implement document scanning.
- This PR does not implement file indexing.
- This PR does not generate lesson content.
- This PR does not create real review notes.
- This PR does not use student data.
- This PR does not add external integrations.
- This PR does not add network calls.
- This PR does not add automation.

## Related workflow docs

- Bundle reference: `docs/command-check-bundle-reference-polish.md`
- Prompt template: `docs/cursor-prompt-template.md`
- Workflow doc map: `docs/workflow-docs-cross-link-polish.md`

## Commands Reference

```bash
bin/chief-of-staff --testing-checklist-status
bin/chief-of-staff --project-memory-cleanup-status
bin/chief-of-staff --dashboard
bash scripts/testing-checklist-consolidation-status.sh
```
