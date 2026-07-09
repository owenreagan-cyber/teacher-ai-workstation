# Canvas LLM Handoff Regression Rule

## Status

Active governance rule.

## Problem

Canvas LLM phases often update `current-handoff.md` to reflect the newest phase.

That is correct, but it can accidentally remove historical breadcrumbs that older phase status scripts still validate.

Example failure mode:

```text
Phase 19B updates current handoff to PR #301 / f61dae2.
Phase 19A regression still expects PR #300 / 5af1ecd historical baseline.
Phase 19A status fails even though Phase 19B is correct.
```

## Rule

Future phases must preserve historical baseline breadcrumbs required by earlier status scripts.

Do not remove or overwrite older phase markers unless the older status script is intentionally updated in the same PR and regression proof stays clean.

## Required Practice

When updating `docs/programs/canvas-llm/current-handoff.md`:

1. Move the active/current phase forward.
2. Preserve previous phase baselines in a historical baseline section.
3. Keep older PR numbers, commit hashes, and phase labels if any status script checks them.
4. Run current phase status and regression statuses before commit.
5. Fix breadcrumbs rather than weakening regression checks.

## Preferred Pattern

Use this structure:

```text
## Current Production State
Current main / latest merged PR / current commit.

## Latest Completed Phase
Newest completed phase.

## Historical Baselines
Older phase baselines preserved for regression continuity.
```

## Prompt Instruction

Future prompts for Canvas LLM phases should include:

```text
Preserve historical handoff breadcrumbs required by prior phase status scripts.
When updating current-handoff.md, move the current phase forward but do not delete older PR/commit markers that regressions validate.
If a prior status fails because a breadcrumb moved, restore the historical breadcrumb in a dedicated Historical Baselines section rather than weakening the status script.
```

## Validation Requirement

Every phase PR should include regression proof for at least:

```text
current phase status
previous phase status
write/readiness gate status if relevant
```

For Phase 19B specifically:

```text
bin/chief-of-staff --canvas-llm-phase-19b-canonical-rules-status
bin/chief-of-staff --canvas-llm-phase-19a-archaeology-status
bin/chief-of-staff --canvas-llm-phase-18-status
```

## Boundary

This rule is documentation/governance only.

It does not authorize:

- Canvas API calls
- Canvas writes
- live fetches
- student data access
- `.local` metadata commits
- school Canvas URL commits
- tokens
- implementation work
