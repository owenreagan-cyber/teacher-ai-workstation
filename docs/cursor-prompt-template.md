# Cursor Prompt Template

Reusable template for future Cursor PR tasks in the Teacher AI Workstation repo. Replace placeholders before sending to Cursor.

## Placeholders

```text
PR_TITLE
FEATURE_BRANCH
GOAL
SCOPE
REQUIRED_FILES_TO_ADD
REQUIRED_FILES_TO_UPDATE
DO_NOT_ADD
REQUIRED_TESTS
EXPECTED_DASHBOARD_HEALTH
COMMIT_MESSAGE
PR_BODY
```

---

## Prompt Body

You are working in this local repo:

`~/Projects/teacher-ai-workstation`

Repository:

`owenreagan-cyber/teacher-ai-workstation`

Goal:

**PR_TITLE**

FEATURE_BRANCH: `FEATURE_BRANCH`

GOAL:

GOAL

SCOPE:

SCOPE

DO NOT ADD:

DO_NOT_ADD

# Mandatory Git Workflow Contract

You may use Cursor Agent and Cursor terminal to run commands, but you must follow this workflow exactly.

## 1. Preflight

Run:

```bash
cd ~/Projects/teacher-ai-workstation
git status --short
git branch --show-current
git fetch origin
git switch main
git pull --ff-only
git status --short
bin/chief-of-staff --dashboard
```

Required starting state:

* branch is `main`
* `git status --short` is empty
* local `main` is up to date with `origin/main`
* dashboard passes on local `main`

If any of these are false, stop and report. Do not edit.

## 2. Create a feature branch

Create and switch to:

```bash
git switch -c FEATURE_BRANCH
```

Verify:

```bash
git branch --show-current
```

Required:

```text
FEATURE_BRANCH
```

If the branch is `main`, stop immediately.

# Feature Scope

REQUIRED_FILES_TO_ADD

REQUIRED_FILES_TO_UPDATE

Do not skip any required file.

Do not modify unrelated files.

# Required file checklist

Before no-commit review, confirm every required add/update file is present and intentional.

# Unexpected changed files gate

Before committing:

```bash
git diff --name-only
git status --short
```

If any file outside the required list changed, stop and explain. Do not commit until resolved or Owen explicitly approves inclusion.

# Existing behavior impact review

For each updated file, summarize whether existing behavior changes. Workflow/process PRs should not change lesson-generation behavior unless explicitly scoped.

# Dashboard/status parse review

Status scripts must print parseable Summary blocks:

```text
Summary
----------------------------------------
PASS: X
WARN: Y
FAIL: Z
```

Dashboard scripts must capture status output so `set -euo pipefail` does not abort early.

# Generated file cleanup review

Verify no generated lesson brief or draft files remain unless explicitly intended:

```bash
find assistant/lesson-planning/briefs -maxdepth 1 -type f ! -name "README.md" -print
find assistant/lesson-planning/drafts -maxdepth 1 -type f ! -name "README.md" -print
```

# Required tests

REQUIRED_TESTS

Expected dashboard health:

EXPECTED_DASHBOARD_HEALTH

# Mandatory Self-Review Gates

Before committing, produce this exact no-commit review:

```text
NO-COMMIT REVIEW

Branch:
<git branch --show-current>

Changed files:
<git diff --name-only plus untracked expected files>

Unexpected changed files:
<none OR list with explanation>

Existing behavior impact:
<summary of each existing file changed>

Status/dashboard review:
<summary>

Generated test files:
<none OR list>

Cursor workflow review:
<confirm required workflow artifacts and integrations>

Test summary:
<commands and results>

Final status:
<git status --short>

Checklist:
Added:
<REQUIRED_FILES_TO_ADD>

Updated:
<REQUIRED_FILES_TO_UPDATE>
```

Stop there unless Owen has already explicitly approved commit.

# Commit approval gate

Only after Owen approves the no-commit review:

```bash
git add <intended files>
git commit -m "COMMIT_MESSAGE"
```

Do not push until Owen approves.

# Push/PR approval gate

Only after Owen approves push/PR:

```bash
git push -u origin FEATURE_BRANCH
gh pr create --base main --head FEATURE_BRANCH --title "PR_TITLE" --body "<PR_BODY>"
```

Do not merge until Owen explicitly approves merge.

# Merge verification gate

Before merge:

```bash
git switch FEATURE_BRANCH
git status
bin/chief-of-staff --dashboard
bash scripts/phase-1-status.sh
```

Verify merge state:

```bash
gh pr view PR_NUMBER --json state,mergedAt,url,mergeCommit
```

```text
mergedAt: null means not merged
non-null mergedAt means merged
```

# Post-merge local main dashboard gate

After merge:

```bash
git switch main
git pull --ff-only
bin/chief-of-staff --dashboard
```

Only call complete when local `main` has the merge and dashboard passes.

---

## Reusable verification bundles

Prompt packs must be checked after roadmap changes.
Prompt packs must be checked after dashboard count changes.
Prompt packs must be checked after new status commands are added.
Prompt pack references do not replace PR-specific checks.
Prompt pack references do not replace no-commit review.
Prompt pack references do not replace PR open/unmerged verification.
Prompt pack references do not replace mergedAt non-null verification.
Prompt pack references do not replace branch deletion verification.
Prompt pack references do not replace final local-main dashboard proof.

Use `docs/workflow-docs-cross-link-polish.md` as the map for workflow docs.
Use `docs/workflow-docs-navigation-status-summary.md` to verify the workflow doc map remains intact.
Use `docs/prompt-pack-stack-completion-marker.md` to confirm the reusable prompt pack documentation stack is complete for now.
The next safe return point is Core Teacher Workstation planning cleanup.
Use `docs/prompt-pack-handoff-summary.md` to understand the current reusable prompt pack stack.
The handoff summary points to maintenance, freshness, stale-reference audit, reference index, workflow navigation, verification bundles, and lifecycle guardrails.
Use `docs/prompt-pack-reference-index.md` to find reusable prompt pack references.
Use `docs/prompt-pack-maintenance-checklist.md` before reusing or updating prompt packs.
Use `docs/prompt-pack-stale-reference-audit.md` to review reusable prompt docs for stale roadmap labels, dashboard counts, status commands, branch examples, and next recommended PR references.
Use `docs/prompt-pack-freshness-report-polish.md` to summarize whether reusable prompt docs are current.

Prompt pack completion markers do not replace PR-specific checks.
Prompt pack completion markers do not replace no-commit review.
Prompt pack completion markers do not replace PR open/unmerged verification.
Prompt pack completion markers do not replace mergedAt non-null verification.
Prompt pack completion markers do not replace branch deletion verification.
Prompt pack completion markers do not replace final local-main dashboard proof.

Handoff summaries do not replace PR-specific checks.
Handoff summaries do not replace no-commit review.
Handoff summaries do not replace PR open/unmerged verification.
Handoff summaries do not replace mergedAt non-null verification.
Handoff summaries do not replace branch deletion verification.
Handoff summaries do not replace final local-main dashboard proof.

Freshness reports should cover roadmap labels, dashboard counts, status commands, verification bundles, lifecycle guardrails, and safety boundaries.
Freshness reports do not replace PR-specific checks.
Freshness reports do not replace no-commit review.
Freshness reports do not replace PR open/unmerged verification.
Freshness reports do not replace mergedAt non-null verification.
Freshness reports do not replace branch deletion verification.
Freshness reports do not replace final local-main dashboard proof.

Lifecycle guardrails: `docs/pr-lifecycle-guardrail-consolidation.md`

Branch hygiene: `docs/branch-hygiene-cleanup-reference.md`

Local main proof: `docs/local-main-proof-report-polish.md`

Template tightening: `docs/checklist-driven-prompt-template-tightening.md`

Compact bundle picker: `docs/command-check-bundle-reference-polish.md`

Full bundle commands: `docs/testing-checklist-consolidation.md`

```bash
bin/chief-of-staff --local-main-proof-report-status
bin/chief-of-staff --branch-hygiene-cleanup-status
bin/chief-of-staff --pr-lifecycle-guardrail-status
bin/chief-of-staff --checklist-driven-prompt-template-status
bin/chief-of-staff --command-check-bundle-reference-status
bin/chief-of-staff --testing-checklist-status
```

Every PR completion must prove local main.
Every PR completion must report the local main commit.
Every PR completion must report dashboard PASS/WARN/FAIL and health count.
Every PR completion must report next recommended PR.
Every PR completion must report branch deletion status.
Every PR completion must end with final status: on main, clean working tree, dashboard passing.
Final report polish does not replace merge verification or branch hygiene checks.

Navigation summaries help people find the right process doc.
Navigation summaries do not replace PR-specific checks.
Navigation summaries do not replace no-commit review.
Navigation summaries do not replace PR open/unmerged verification.
Navigation summaries do not replace mergedAt non-null verification.
Navigation summaries do not replace branch deletion verification.
Navigation summaries do not replace final local-main dashboard proof.

Cross-links help navigation but do not replace PR-specific checks.
Cross-links do not replace no-commit review.
Cross-links do not replace PR open/unmerged verification.
Cross-links do not replace mergedAt non-null verification.
Cross-links do not replace branch deletion verification.
Cross-links do not replace final local-main dashboard proof.

Every PR prompt must name the expected branch.
Every PR prompt must verify the current branch before work and before commit.
Every PR prompt must verify PR headRefName and baseRefName before merge.
Every PR prompt must verify remote branch deletion after merge when available.
Every PR prompt must return to local main after merge.
Every PR prompt must end with clean working tree and dashboard passing.
Branch cleanup guidance does not replace no-commit review or merge verification.

Every PR prompt must verify preflight on main.
Every PR prompt must verify the feature branch.
Every PR prompt must include no-commit review.
Every PR prompt must verify PR state is OPEN and mergedAt is null before merge.
Every PR prompt must verify merged state is MERGED and mergedAt is non-null after merge.
Every PR prompt must verify local main is synced after merge.
Every PR prompt must end with clean working tree and dashboard passing.
Reusable bundles do not replace these lifecycle guardrails.

Reusable verification bundles may shorten future prompts.

Reusable verification bundles do **not** replace PR-specific checks.

Reusable verification bundles do **not** replace no-commit review.

Reusable verification bundles do **not** replace PR open/unmerged verification.

Reusable verification bundles do **not** replace mergedAt non-null verification.

Reusable verification bundles do **not** replace final local-main dashboard proof.

Every PR must still end on local `main`, clean working tree, and dashboard passing.

---

See also:

- `docs/cursor-workflow-operating-system.md`
- `docs/cursor-pr-review-checklist.md`
- `docs/testing-checklist-consolidation.md`
- `docs/command-check-bundle-reference-polish.md`
- `docs/checklist-driven-prompt-template-tightening.md`
- `docs/pr-lifecycle-guardrail-consolidation.md`
- `docs/branch-hygiene-cleanup-reference.md`
- `docs/local-main-proof-report-polish.md`
- `docs/workflow-docs-cross-link-polish.md`
- `.cursor/rules/teacher-ai-workstation.mdc`
