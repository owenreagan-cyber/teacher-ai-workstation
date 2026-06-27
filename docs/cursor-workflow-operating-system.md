# Cursor Workflow Operating System

## Purpose

This document defines how Owen, ChatGPT, Cursor, GitHub, and the local dashboard work together in the Teacher AI Workstation repo. It makes future Cursor workflow faster, smoother, more coordinated, and more verifiable without changing lesson-generation behavior.

## Roles

```text
Owen: owner/operator
ChatGPT: architect, prompt writer, PR reviewer, merge advisor
Cursor: local implementation agent and terminal runner
GitHub: PR and history source of truth
Dashboard: local final health check
```

## Standard Fast Workflow

```text
ChatGPT writes Cursor prompt
Cursor preflights
Cursor creates feature branch
Cursor implements
Cursor runs tests
Cursor gives no-commit review
Owen approves commit
Cursor commits
Cursor pushes and creates PR
ChatGPT reviews PR through GitHub
Owen approves merge
Cursor or Terminal merges
Cursor verifies local main dashboard
```

## Cursor Agent Rules

- Follow repo rules in `.cursor/rules/teacher-ai-workstation.mdc`.
- Default mode is safe, local-first, human-reviewed.
- Never commit directly to `main`.
- Always run preflight before editing.
- Always work on a feature branch.
- Always show no-commit review before committing unless Owen explicitly says to commit after review.
- Never merge without explicit Owen approval.
- Never add student-sensitive data or real student names.
- Never add Gmail, Drive, Calendar, APIs, OAuth, secrets, or school-system integrations without a separate approved PR.
- Never create network calls unless the prompt explicitly authorizes them.
- Keep generated lesson files in `assistant/lesson-planning/briefs/` and `assistant/lesson-planning/drafts/` local and gitignored unless explicitly instructed otherwise.
- If unexpected file changes appear, stop and explain before committing.
- If any command fails, stop and report exact output.

## Terminal Command Rules

- Use the repo root: `~/Projects/teacher-ai-workstation`.
- Prefer read-only status commands before writes.
- Capture output from status scripts in dashboard wrappers so `set -euo pipefail` does not abort early.
- Do not push, merge, or create PRs without explicit Owen approval at the matching gate.
- Report exact command output on failure.

## No-Commit Review Gate

Before any commit, Cursor must produce a no-commit review that includes:

- Current branch
- Changed files
- Unexpected changed files (or none)
- Existing behavior impact
- Status/dashboard review
- Generated test files (or none)
- Cursor workflow review
- Test summary
- Final git status
- Required file checklist

Stop after the no-commit review unless Owen explicitly approves commit.

## Commit Gate

Only after Owen approves the no-commit review:

- Stage only intended files
- Commit with the approved message
- Report commit hash, branch, and clean status
- Do not push yet

## Push and PR Gate

Only after Owen approves push/PR:

- Push the feature branch
- Create the PR with the approved title and body
- Report PR URL
- Do not merge yet

## ChatGPT PR Review Gate

ChatGPT reviews the PR on GitHub using `docs/cursor-pr-review-checklist.md`.

Outcomes may include:

- APPROVE TO COMMIT (if commit was deferred)
- APPROVE TO PUSH/PR
- APPROVE TO MERGE
- REQUEST CHANGES
- BLOCKED

## Merge Gate

Only merge after Owen explicitly approves merge.

Before merge, verify the feature branch is clean and passing:

```bash
bin/chief-of-staff --cursor-workflow-status
bin/chief-of-staff --dashboard
bash scripts/phase-1-status.sh
```

Merge verification rule:

```text
mergedAt: null means not merged
non-null mergedAt means merged
```

## Post-Merge Main Verification

After merge:

```bash
git switch main
git pull --ff-only
bin/chief-of-staff --dashboard
```

Local `main` dashboard is the final source of truth. Only call the work complete when local `main` has the merge and dashboard passes.

## Handling Unexpected Changes

If `git status --short` or `git diff --name-only` shows files outside the required add/update list:

1. Stop immediately.
2. Explain each unexpected file.
3. Do not commit until Owen resolves or explicitly approves inclusion.

## Handling Failed Tests

If any required syntax check, status script, dashboard check, or phase verifier fails:

1. Stop immediately.
2. Report exact command and output.
3. Fix only what is needed for the current PR scope.
4. Re-run required tests before presenting another no-commit review.

## Handling Cursor Credit or Approval Blocks

If Cursor blocks a command, needs approval, or runs out of credits:

1. Stop and report the block reason exactly.
2. Do not guess that work succeeded.
3. Resume only after Owen clears the block or approves an alternate path.

## Safety Boundaries

This workflow PR type must not add:

- Student-sensitive data
- Real student names
- Gmail, Google Drive, Google Calendar, APIs, OAuth, secrets, or school-system integrations
- Deployment, databases, or unauthorized network calls
- LLM lesson drafting or automatic lesson generation

Generated lesson files stay local and gitignored unless Owen explicitly instructs otherwise.

## Commands Reference

Preflight:

```bash
cd ~/Projects/teacher-ai-workstation
git status --short
git branch --show-current
git fetch origin
git switch main
git pull --ff-only
bin/chief-of-staff --dashboard
```

Cursor workflow status:

```bash
bin/chief-of-staff --cursor-workflow-status
```

Dashboard:

```bash
bin/chief-of-staff --dashboard
```

Phase checks:

```bash
bash scripts/phase-1-status.sh
bash scripts/verify-phase-0e.sh
```

Merge verification:

```bash
gh pr view PR_NUMBER --json state,mergedAt,url,mergeCommit
```

Related docs:

- `docs/cursor-prompt-template.md`
- `docs/cursor-pr-review-checklist.md`
- `.cursor/rules/teacher-ai-workstation.mdc`
