# Change Approval Process

This repository uses approval gates so planning, implementation, and machine changes do not happen by accident.

## Command words

### Review

When Owen says `review`, the assistant must only analyze, audit, and recommend.

During review, the assistant must not perform write actions.

Allowed during review:

- Read files and inspect existing state.
- Summarize risks, gaps, and recommendations.
- Propose an implementation order.
- Identify what should be added, removed, deferred, or enhanced.
- Present a final recommendation and wait for approval.

Not allowed during review:

- Creating, editing, closing, or commenting on GitHub issues.
- Creating branches or pull requests.
- Creating, editing, deleting, or committing files.
- Running scripts that change the local machine.
- Changing account, app, credential, or repository state.

### Approve plan

When Owen says `approve` after a review, the assistant may perform only the planning actions that were recommended and approved.

Typical allowed actions:

- Close or comment on superseded planning issues if explicitly included in the approved recommendation.
- Create or update the approved planning issue.

This does not automatically approve file edits or implementation work unless Owen explicitly approves implementation.

### Approve implementation

When Owen says `approve implementation`, the assistant may create branches, add or edit files, and open pull requests only within the approved scope.

Implementation must stay inside the approved issue, phase, and file list. If a new idea appears, it must be brought back for review before being added.

### Approve merge

When Owen says `approve merge`, the assistant may merge the approved pull request if merge access is available and checks are acceptable.

## What counts as a write action

A write action includes any action that changes repository, machine, account, app, or credential state.

Examples:

- GitHub issue creation, update, close, label, assignment, or comment.
- GitHub pull request creation, update, close, comment, review, or merge.
- Branch creation, update, or deletion.
- File creation, edit, deletion, or commit.
- Running a script that changes the local machine.
- Changing macOS settings, app settings, Dock layout, shell profiles, or installed tools.
- Changing account state, app sign-in state, OAuth state, or permissions.
- Accessing, creating, storing, retrieving, rotating, or exposing secrets.

## Required flow

Use this flow unless Owen explicitly instructs otherwise:

1. Review.
2. Recommendation.
3. Approval.
4. Planning issue.
5. Branch.
6. Pull request.
7. Test or verification.
8. Merge approval.
9. Merge.

## No invisible work

Every action must be one of these:

- Review-only and clearly non-mutating.
- Explicitly approved before it happens.
- Reported after completion with a clear summary of what changed.

The assistant must not do background work or make silent changes.

## Scope discipline

An approved phase is a hard boundary. If the implementation reveals a tempting extra improvement, the assistant should document it as a follow-up rather than include it without approval.

## Phase 0E-A rule

Phase 0E-A is documentation only. It must not add setup scripts, modify shell profiles, change bootstrap behavior, automate accounts, configure apps, retrieve secrets, or alter the local machine.