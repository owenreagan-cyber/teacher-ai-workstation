# Teacher AI Workstation — Agent Operating Rules

```text
Status: active governance (documentation/status only)
Audience: Cursor, Antigravity, Codex, Claude Code, and future coding agents
Authority: stable entry point — does not replace deeper authority documents
Runtime activation: none
Implementation approval: not granted by this file
```

## What This File Is

`AGENTS.md` is the **repo-wide quick-start for coding agents**. It tells future agents how to work safely in Teacher AI Workstation without re-deriving rules from chat history.

Read this file first. Then follow the linked authority documents for the task at hand.

## What This File Is Not

`AGENTS.md` does **not** replace:

| Document | Role |
| --- | --- |
| `docs/engineering-constitution.md` | Canonical engineering authority |
| `docs/implementation-approval-gate.md` | Repo-wide implementation gate |
| `bin/chief-of-staff` and status scripts | PASS/WARN/FAIL proof surfaces |
| `assistant/memory/active-priorities.md` | Session handoff and active priorities |
| `docs/build-queue.md` | Active build queue and track status |
| `docs/master-build-roadmap.md` | Whole-system roadmap |
| Explicit mission prompts | Scoped approval for a specific task |

If this file and a mission prompt disagree, the **stricter** rule wins unless the mission prompt explicitly narrows scope inside approved boundaries.

## Repo Identity

Teacher AI Workstation is Owen Reagan's **teacher-first**, **local-first**, **reliable**, **auditable**, and **maintainable** engineering environment for planning, organizing, and eventually producing teacher-reviewed instructional work.

Default posture:

- documentation/status work is common and often preferred
- implementation is **not approved by default**
- runtime, integrations, generation, and student-data handling require explicit approval
- local `main` dashboard health is final merge proof

Repo root: `~/Projects/teacher-ai-workstation`

## Authority Stack (Read Order)

1. **Explicit mission prompt** — scoped task approval when present
2. **`docs/engineering-constitution.md`** — engineering philosophy and invariants
3. **`docs/implementation-approval-gate.md`** — planning vs implementation boundary
4. **`docs/cursor-operating-modes-and-approval-gates.md`** — autonomous modes, discovery, proposal lifecycle
5. **`docs/teacher-workstation-domain-boundaries.md`** — domain-specific blocked categories
6. **`docs/cursor-workflow-operating-system.md`** — Owen / ChatGPT / Cursor / GitHub workflow
7. **`.cursor/rules/teacher-ai-workstation-senior-engineer.mdc`** — full lifecycle when explicitly authorized
8. **`docs/proposals/index.md`** — proposal ledger (check before proposing)

Cursor-specific rules also live in `.cursor/rules/teacher-ai-workstation.mdc`.

## Preflight (Before Editing)

Run from repo root:

```bash
cd ~/Projects/teacher-ai-workstation
git switch main
git pull --ff-only origin main
git status --short
git branch --show-current
bin/chief-of-staff --dashboard
```

Preflight requirements:

- on `main` (or create a feature branch from updated `main`)
- understand current uncommitted changes before editing
- do not commit directly to `main`
- stop and report if unexpected files changed outside approved scope

## Default Git Workflow

```text
Preflight on main
  → feature branch
  → implement approved scope only
  → validate
  → self-review
  → commit (when authorized)
  → push + PR (when authorized)
  → merge (when authorized)
  → branch cleanup
  → re-validate clean local main
  → completion report
```

Human gates apply unless a mission prompt explicitly authorizes the full autonomous lifecycle. See `docs/cursor-workflow-operating-system.md` for no-commit review, commit, push/PR, and merge gates.

## Planning vs Implementation

### Allowed without crossing the implementation gate

- planning docs, audits, closeouts, handoffs
- cross-links, indexes, build-queue/active-priorities alignment
- static PASS/WARN/FAIL status checks (file presence and fixed-string grep)
- fictional/static samples explicitly marked planning-only
- read-only CLI and dashboard proof

### Requires explicit approval

- schemas, registry data, validators, parsers, importers, renderers
- commands that read/write curriculum files or external systems
- APIs, OAuth, network calls, secrets
- scanning, indexing, OCR, embeddings, vector DB, RAG
- lesson generation or generated review notes
- automation, schedulers, background jobs
- weakening PASS/WARN/FAIL semantics or removing checks

When unsure, treat work as **implementation** and stop for approval.

## Permanent Hard Boundaries

Unless a mission prompt explicitly approves a bounded exception:

| Category | Rule |
| --- | --- |
| Student data | No real student names, records, or classroom-sensitive content |
| Curriculum content | No real curriculum excerpts in repo artifacts without approval |
| Network / API | No curl/wget/API/OAuth/secrets unless explicitly authorized |
| Scanning / indexing | No folder scans, crawlers, OCR, embeddings, or vector DB |
| Generation | No lesson drafts, review notes, or autonomous instructional output |
| Integrations | No Canvas/Drive/Gmail/Calendar/live sync without approval |
| Communication | No email/message sending or parent-response automation |
| Mac / system | No system mutation, automation, or background jobs |
| Package managers | No npm/brew/pip installs unless explicitly authorized |
| Repo scope | Repo-local only — no reads/writes outside the working tree |

Mixed-category files follow the **most restrictive** rule. See `docs/cursor-operating-modes-and-approval-gates.md` § Mixed-Category File Rule.

## Sub-Agent and Tool Inheritance

Any sub-agent, MCP tool, shell script, or delegated process inherits the same boundaries. Do not use another tool to bypass blocked categories.

## Validation Commands

Minimum proof for docs/status PRs:

```bash
bash -n bin/chief-of-staff
bash scripts/cursor-workflow-status.sh
bin/chief-of-staff --cursor-workflow-status
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

Broader proof when touching governance or whole-system docs:

```bash
scripts/chief-of-staff-validate-all.sh
COS_VALIDATE_INCLUDE_SMOKE=1 COS_VALIDATE_INCLUDE_PHASE1=1 scripts/chief-of-staff-validate-all.sh
bin/chief-of-staff --whole-system-master-roadmap-status
bin/chief-of-staff --whole-system-coherence-status
bin/chief-of-staff --app-ecosystem-inventory-status
```

Status scripts must preserve parseable `PASS:` / `WARN:` / `FAIL:` Summary blocks. Do not weaken tests to make validation pass.

## Escalation Conditions

Stop and report to Owen when:

- work would cross the implementation gate without approval
- runtime, API, generation, or student-data handling is required but not approved
- secrets, OAuth, or external services are needed
- destructive refactors or broad renames are required
- PASS/WARN/FAIL semantics or existing commands would change without approval
- unrelated tests fail and cannot be isolated safely
- multiple architectural paths need owner choice
- mission prompt authority appears broader than governance docs (follow stricter rule and flag discrepancy)

If only part of a mission is blocked, complete safe work, record skipped items, and continue when the safe portion forms a coherent PR. See blocked-item routing in `docs/cursor-operating-modes-and-approval-gates.md`.

## Discovery and New Ideas

Agents may **propose** features during approved discovery scans. Discovery is **never** implementation approval.

```text
Agent proposal → ChatGPT review → Owen Reagan approval → scoped mission → implementation
```

Check `docs/proposals/index.md` before creating near-duplicate proposals.

## Completion Report (Full-Lifecycle Missions)

When a mission authorizes merge and final proof, report:

- branch name, PR number, merge commit, local `main` proof
- validation table with PASS/WARN/FAIL counts
- governance / non-activation confirmation
- improvement or hardening findings (if any)
- blocked items skipped with reasons
- Level 1 discovery table or `No discovery findings this mission`
- recommended next mission

## Chief of Staff

`bin/chief-of-staff` is the local CLI and dashboard orchestrator. It reports health; it does not activate runtime behavior by default.

Quick commands:

```bash
bin/chief-of-staff --dashboard
bin/chief-of-staff --cursor-workflow-status
bin/chief-of-staff --cursor-operating-modes-status
bin/chief-of-staff --help
```

Command index: `docs/chief-of-staff-command-index-v1.md`

## Ecosystem Repos (Related, Separate)

These sibling repos have their own rules and validation. Do not assume Teacher AI Workstation governance transfers automatically:

| Repo | Purpose |
| --- | --- |
| `classroom-command-center` | Vite/React classroom display board |
| `omninote` | iPadOS teaching/presentation app (planning) |
| `reward-maker-studio` | Reward art tooling (parked) |

Cross-repo work requires explicit scope in the mission prompt.

## Non-Activation Confirmation

This file is Markdown governance text only. It does not activate runtime behavior, integrations, generation, student-data handling, network calls, automation, registry writes, or changes to existing command semantics.
