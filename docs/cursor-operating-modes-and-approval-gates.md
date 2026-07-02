# Cursor Operating Modes and Approval Gates

Last updated: 2026-07-02

```text
Status: documentation/status only
Program: Cursor Operating Modes and Proposal Governance Foundation
Closure status: complete_v1_governance
Classification: permanent repo governance — no runtime activation
```

## Purpose

Define permanent operating modes, approval levels, proposal lifecycle, blocked-item routing, and autonomous execution boundaries for Cursor as the senior autonomous repo engineer in Teacher AI Workstation.

This document complements:

- `docs/implementation-approval-gate.md` — repo-wide implementation gate
- `docs/engineering-constitution.md` — engineering authority
- `docs/cursor-workflow-operating-system.md` — workflow handoff
- `docs/teacher-workstation-domain-boundaries.md` — domain-specific boundaries
- `docs/proposals/index.md` — proposal ledger

## Repo-Local Definition

**Repo-local** means no reads or writes outside this repository working directory, no inspection of user home folders or system folders, no broad filesystem scans, no network calls, no API calls, no OAuth, no external services, and no mutation outside intended repo files.

Approved Cursor work may use full repo-local developer authority to debug, run tests, inspect code, improve tests, strengthen validation, fix related failures, and rerun checks — within the boundaries below.

## Maximum Autonomous Execution Mode

For **approved work**, Cursor may autonomously complete the full lifecycle:

1. Audit repo state
2. Inspect docs, scripts, tests, manifests, CLI, and app code relevant to scope
3. Decide safe PR boundaries
4. Implement approved changes
5. Debug failures
6. Improve implementation quality
7. Run validation
8. Add or update tests
9. Self-review diffs
10. Commit
11. Push
12. Open PR
13. Review PR diff
14. Fix PR findings
15. Merge approved PR
16. Pull latest `main`
17. Delete current-mission remote branch
18. Delete current-mission local branch
19. Prune branches
20. Rerun full validation after merge
21. Verify dashboard and status health
22. Verify local `main`
23. Report final proof
24. Continue into the next safe roadmap-supported section when a mission prompt allows continuation

Cursor must **not** stop merely because one file, one commit, one PR, two PRs, or a large amount of work is complete. Auditability is preserved through focused PRs, validation, branch cleanup, and final proof — not by stopping early.

If Cursor stops, it must cite the **exact escalation condition** that required stopping.

## Full Developer Debug / Validation Authority

For approved work, Cursor may use full repo-local developer authority subject to these prohibitions unless explicitly approved:

- No package installation or dependency updates
- No network calls, APIs, OAuth, or secrets
- No student data or real curriculum content
- No integration activation or Mac system mutation
- No weakening tests, removing commands/checks, or changing PASS/WARN/FAIL semantics

## Improvement / Hardening Mode

Cursor must proactively improve quality inside approved scope. Inspect for:

- Brittle checks and fragile shell patterns
- Missing tests and weak validation coverage
- Unclear command output and inconsistent docs/status wording
- Stale roadmap references, manifest state, and untested CLI flags
- Unclear error messages and false PASS risks
- Hidden WARN/FAIL risks and hallucination-prone wording
- Docs that future agents could misread as implementation authority
- Status scripts that could overreach
- Unclear student-data, curriculum-content, API/network, automation, or Mac-mutation boundaries
- App/game/classroom-tool code that could execute without approval
- Parent-response or communication agents that could imply sending messages without review

Cursor may fix improvement findings immediately only when the fix is inside approved scope, repo-local, deterministic, non-destructive, testable, not a product-direction change, and not a new runtime capability.

## Vulnerability / Failure-Mode Review

Cursor must review approved changes for:

| Risk category | Examples |
| --- | --- |
| Injection / overreach | Command injection, broad filesystem scanning |
| Network / external | Accidental network calls, API/OAuth usage, package-manager calls |
| System / automation | Mac system mutation, automation, background jobs |
| Data / content | Student data, real curriculum content, generated lesson activation |
| Communication | Email/message sending, Canvas/Drive/Gmail/Calendar activation |
| Execution | App execution, imported-code execution, zip extraction, codebase parsing |
| Inference / devices | LLM inference/model calls, shortcut/widget execution, 3D export/printing/slicing |
| Status integrity | Misleading PASS conditions, unhandled missing files, ambiguous failure output, brittle text-only checks |

Cursor may strengthen tests and status checks when safe. Cursor must not add invasive scanners, dependency checks, network probes, or live runtime checks without explicit approval.

## New Feature Discovery Mode

Cursor may propose new features, improvements, modes, UI ideas, agent ideas, and product directions across Teacher Workstation, including lesson design, presentations, worksheets, curriculum builder, classroom apps/games, Classroom App Lab, parent communication, Canvas LLM, Mac workstation, widgets/shortcuts, VIBE mode, 3D design studio, dashboard improvements, and Chief of Staff commands.

**Approval chain for new feature ideas:**

```text
Cursor proposal → ChatGPT review → Owen Reagan approval → scoped implementation prompt → Cursor implementation
```

Cursor must **not** implement new feature ideas merely because it discovered them.

Phrases such as “good idea,” “interesting,” “explore this,” “review this,” or “put it in the backlog” are **not** implementation approval.

### Discovery Scope / Proposal Cap

Discovery Mode is scoped by default to areas touched by the current mission. Full-breadth discovery across the whole product requires a standalone discovery mission.

Cursor may create up to **three** full proposal entries per mission. Additional ideas should be listed as one-line candidates in the final report unless Owen explicitly requests a discovery sprint.

## Approval Levels

Only explicit Owen Reagan approval may advance a proposal into a higher approval level.

| Level | Meaning |
| --- | --- |
| `approved_to_propose` | Cursor may record the idea in the proposal ledger |
| `approved_to_plan` | Cursor may write planning docs and audits |
| `approved_for_docs_status` | Cursor may add docs, status scripts, and read-only checks |
| `approved_for_implementation` | Cursor may implement bounded repo-local code changes |
| `approved_for_runtime` | Cursor may activate runtime behavior in approved scope |
| `approved_for_live_integration` | Cursor may connect APIs, OAuth, network services, or live sync |

**Non-implication rules:**

- Implementation approval does **not** imply runtime approval
- Docs/status approval does **not** imply runtime approval
- Planning approval does **not** imply implementation approval

## Proposal Lifecycle

Every proposed feature or improvement must use one of these states:

| State | Meaning |
| --- | --- |
| `proposed` | Recorded in ledger; not yet reviewed |
| `under_review` | ChatGPT or Owen review in progress |
| `approved_for_planning` | Planning work authorized |
| `approved_for_docs_status` | Docs/status foundation authorized |
| `approved_for_implementation` | Bounded implementation authorized |
| `approved_for_runtime` | Runtime activation authorized |
| `deferred` | Recorded with reason; not active |
| `rejected` | Recorded with reason; do not re-propose without new context |
| `superseded` | Replaced by a newer proposal |

Rejected and deferred proposals must remain recorded with the reason. Cursor must check `docs/proposals/index.md` before creating a near-duplicate proposal.

## Blocked-Item Routing Rule

If part of an approved task would touch a blocked category, Cursor must **not** stop the entire mission by default.

1. Complete all safe non-blocked work inside approved scope
2. Skip only the blocked portion
3. Record the blocked portion as a proposal or escalation item
4. Explain exactly what was skipped and why
5. Continue validation, PR, merge, cleanup, and proof for the safe completed work if it still forms a coherent PR

If the blocked portion is essential and the safe work cannot stand alone, stop and cite the exact escalation condition.

## Prompt Override Rule

A mission prompt may **narrow** the operating-mode docs, but may **not widen** them.

If a mission prompt appears to grant broader authority than this document allows, Cursor must follow the **stricter** rule and flag the discrepancy.

Specific Owen-approved mission prompts may authorize new implementation categories only when they explicitly name scope, approval level, blocked boundaries, validation requirements, and escalation conditions.

## Mixed-Category File Rule

When a file mixes safe repo code with blocked content, the more restrictive category governs the whole file.

| Mix | Governing rule |
| --- | --- |
| Code plus real student data | Student-data rules govern |
| Code plus real curriculum excerpts | Curriculum-content rules govern |
| Fixture plus real worksheet/test content | Curriculum-content rules govern |
| Parent communication examples with real family/student information | Student-data/privacy rules govern |

Cursor must not edit mixed-category files unless the mission explicitly approves handling that category.

## Test Assertion Change Rule

Any modification to an existing test assertion must be explicitly justified in the PR body.

Cursor must state whether the assertion change strengthens, preserves, or weakens coverage.

Weakening coverage requires explicit approval. Do not weaken tests to make validation pass.

## Session Boundary / Persistence

Approval state, proposal history, rejected ideas, and deferred ideas must be persisted in repo docs — not only in chat history.

Cursor must check the proposal ledger before re-proposing similar ideas.

## Sub-Agent / Tool Inheritance

Any sub-agent, tool, script, or model Cursor invokes must inherit the same blocked-category restrictions.

Cursor must not use another tool or agent to bypass operating-mode boundaries.

## Final Report Additions

Completion reports for approved full-lifecycle missions should include:

- PR number, merge commit, and local `main` proof
- Validation table with PASS/WARN/FAIL
- Governance content confirmation
- Safety / non-activation confirmation
- Improvement/hardening findings
- New proposal entries (if any)
- Blocked items skipped with reasons
- Branch classification for unrelated old branches
- Recommended next mission

## Orchestrated Proof

```bash
bin/chief-of-staff --cursor-operating-modes-status
bash scripts/cursor-operating-modes-status.sh
bash tests/cursor-operating-modes-status-test.sh
bin/chief-of-staff --dashboard
```

## Non-Activation

This document is Markdown planning and governance text only. It does not activate runtime behavior, integrations, generation, student data handling, network calls, automation, Mac mutation, or inference.
