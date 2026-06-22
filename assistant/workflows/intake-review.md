# Intake Review Workflow

## Purpose

Review candidate material before it becomes approved Chief of Staff context, memory, writing samples, workflow guidance, or future knowledge files.

This workflow recommends decisions. Owen makes the final decision.

## Inputs

- Intake item ID
- Source type
- Source location or safe summary
- Intended use
- Sensitivity notes
- Suggested promotion target
- Relevant checklist status

## Review Steps

1. Confirm what the material is and where it came from.
2. Check whether the source is appropriate for model context.
3. Check for student, parent, credential, confidential, copyrighted, or proprietary content.
4. Decide whether a sanitized summary is safer than raw material.
5. Recommend one review decision category.
6. Recommend one promotion target, if any.
7. Identify the next human action.

## Decision Categories

- approved
- approved after sanitizing
- rejected
- quarantined
- needs more context
- deferred

## Promotion Targets

- `assistant/intake/approved-context.md`
- `assistant/training/writing-samples/approved-samples.md`
- `assistant/memory/projects.md`
- `assistant/memory/teaching-context.md`
- `assistant/memory/writing-style-rules.md`
- `assistant/memory/preferences.md`
- `assistant/memory/decisions.md`
- `assistant/memory/active-priorities.md`
- a workflow doc
- a future knowledge file

## Sensitivity Checks

- student private data
- parent private data
- credentials, passwords, API keys, or tokens
- confidential school records
- medical, behavior, accommodation, or discipline details
- full copyrighted text copied without permission
- unclear source, license, permission, or intended use

## Source Checks

- Prefer sanitized summaries over raw material.
- Do not automatically move files or edit memory.
- Do not treat rejected or quarantined material as approved context.
- If a source is unclear, recommend `needs more context` or `quarantined`.

## Output Format

- Intake item reviewed
- Decision
- Sensitive data concerns
- Sanitization needed
- Recommended promotion target
- Human approval required
- Next action

## Required Footer

- Intake item reviewed
- Decision
- Sensitive data concerns
- Sanitization needed
- Recommended promotion target
- Human approval required
- Next action
