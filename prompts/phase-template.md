# Phase Planning Template

Use this template when planning a new workstation phase.

This template is designed to prevent scope creep, invisible work, and unsafe automation.

## Phase name

`Phase X: <short name>`

## Goal

Explain what the phase is trying to accomplish in plain language.

## Approval level required

Choose one:

- Review only.
- Approve plan.
- Approve implementation.
- Approve merge.

State what actions are allowed at this approval level.

## Context

Summarize the current state of the workstation, repo, machine, or workflow.

Include relevant prior phases and constraints.

## Approved scope

List exactly what may be added or changed.

Example:

```text
Allowed:
- Add documentation files.
- Add read-only status command.

Not allowed:
- No shell profile changes.
- No account automation.
- No secret access.
```

## Automation labels

For every proposed item, label it as one of:

- Safe to automate.
- Interactive only.
- Human approval required.
- Never automate.
- Later phase.

## Files to add or change

List every file path that may be added or changed.

If a file is not listed, it should not be changed without another review.

## Explicit non-goals

List what this phase must not do.

Examples:

- Do not collect passwords.
- Do not change macOS settings.
- Do not modify bootstrap.
- Do not run setup scripts.
- Do not configure external accounts.

## Safety checks

List safety checks required before implementation.

Examples:

- No secrets in files.
- No write actions during review.
- No app/account state changes unless approved.
- No destructive actions without backup.
- No false verification claims.

## Test plan

Describe how the phase will be verified.

Examples:

- Read docs for consistency.
- Run existing audit script.
- Confirm files exist.
- Confirm no scripts were added if docs-only.
- Confirm optional items remain warnings.

## Acceptance criteria

Define what done means.

Examples:

- All approved files exist.
- No unapproved files changed.
- Owen reviewed the output.
- Pull request matches approved scope.

## Suggested branch name

`phase-x-short-name`

## Suggested commit message

`type: short summary`

Examples:

- `docs: add phase 0e approval and safety docs`
- `feat: add read-only workstation status tool`

## Review-before-action reminder

Before making changes, confirm whether Owen asked for:

- Review only.
- Plan approval.
- Implementation approval.
- Merge approval.

If the request says `review`, do not perform write actions.