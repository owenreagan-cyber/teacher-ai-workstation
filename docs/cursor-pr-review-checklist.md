# Cursor PR Review Checklist

Use this checklist before approving a Cursor PR. ChatGPT and Owen may both use it.

## 1. PR Metadata

- [ ] PR title matches intended scope
- [ ] PR body lists adds, updates, safety boundaries, and tests
- [ ] PR is workflow/process only unless explicitly scoped otherwise

## 2. Branch and Commit

- [ ] Feature branch name matches the prompt
- [ ] No commits directly on `main`
- [ ] Commit message matches approved message
- [ ] Commit contains only intended files

## 3. Scope Match

- [ ] Changes match stated GOAL and SCOPE
- [ ] No lesson-generation behavior changes unless explicitly requested
- [ ] No unrelated refactors or drive-by edits

## 4. Safety Boundaries

- [ ] No student-sensitive data
- [ ] No real student names
- [ ] No Gmail, Drive, Calendar, APIs, OAuth, secrets, or school-system integrations
- [ ] No unauthorized network calls
- [ ] No LLM lesson drafting or automatic lesson generation added

## 5. Required Files

- [ ] All required add files present
- [ ] All required update files present
- [ ] No required file skipped

## 6. Unexpected Files

- [ ] `git diff --name-only` matches intended file list
- [ ] Any unexpected file is explained and approved

## 7. Existing Behavior Impact

- [ ] Each updated existing file has a clear impact summary
- [ ] Existing CLI commands still work
- [ ] Dashboard and phase checks still behave as expected

## 8. Status Script Behavior

- [ ] New or updated status scripts use `set -euo pipefail`
- [ ] Status scripts print parseable `PASS:` / `WARN:` / `FAIL:` summary
- [ ] Exit nonzero only when `FAIL > 0` (unless script documents otherwise)

## 9. Dashboard Behavior

- [ ] Dashboard captures subprocess output safely
- [ ] New dashboard section parses summary correctly
- [ ] Expected dashboard health achieved locally on the feature branch

## 10. Generated Files

- [ ] No generated lesson brief files committed unintentionally
- [ ] No generated lesson draft files committed unintentionally
- [ ] Local gitignored lesson artifacts remain local only

## 11. GitHub Merge State

- [ ] PR is open and reviewable
- [ ] CI/check expectations documented if applicable
- [ ] Merge state verified with `gh pr view`:

```text
mergedAt: null means not merged
non-null mergedAt means merged
```

## 12. Local Main Verification

After merge (not before):

- [ ] Local `main` fast-forwarded from origin
- [ ] `bin/chief-of-staff --dashboard` passes on local `main`
- [ ] Phase checks pass on local `main`

## 13. Approval Decision

Choose one outcome:

```text
APPROVE TO COMMIT
APPROVE TO PUSH/PR
APPROVE TO MERGE
REQUEST CHANGES
BLOCKED
```

Notes:

- Use **APPROVE TO COMMIT** when no-commit review passed but commit is not yet made.
- Use **APPROVE TO PUSH/PR** after commit when push/PR is the next gate.
- Use **APPROVE TO MERGE** only after PR review and Owen approval.
- Use **REQUEST CHANGES** when fixes are needed but work can continue.
- Use **BLOCKED** for safety, scope, or verification failures that must stop work.
