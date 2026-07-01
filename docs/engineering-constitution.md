# Teacher AI Workstation Engineering Constitution

```text
Constitution status: active
Phase: Phase 2 transition (engineering governance)
Documentation status: documentation/status only
Implementation approval status: not approved by default
Authority: canonical engineering document for this repository
```

## Purpose of This Document

This Engineering Constitution is the **single authoritative engineering document** for Teacher AI Workstation. It describes how the repository is designed, how implementation proceeds, and how future contributors — human or AI — are expected to work.

Future prompts should reference this document instead of repeating engineering philosophy.

documentation/status only — this constitution does not activate runtime behavior.

---

## 1. Mission

Teacher AI Workstation exists to give Owen a **teacher-first**, **local-first**, **reliable**, **auditable**, and **maintainable** engineering environment for planning, organizing, and eventually producing teacher-reviewed instructional work.

The workstation prioritizes:

- **Teacher-first:** workflows serve classroom planning and review, not autonomous student-facing output by default.
- **Local-first:** the Mac and repo are the primary control plane; cloud systems are references or future connectors only unless explicitly approved.
- **Reliable:** status scripts, dashboard health, and deterministic validation are first-class product surfaces.
- **Auditable:** planning boundaries, approval gates, and PASS/WARN/FAIL proofs make state inspectable.
- **Maintainable:** small PRs, preserved invariants, explicit contracts, and clear ownership reduce drift.

---

## 2. Core Principles

| Principle | Meaning |
| --- | --- |
| Local-first architecture | Raw curriculum files stay in Drive/NAS/iCloud/local folders; the repo stores metadata, planning, and tooling — not unapproved duplicates of sensitive curriculum corpora. |
| Human approval before implementation tracks | Planning completion does not approve implementation. Explicit intake and gate crossing are required. |
| Documentation before implementation | Contracts, boundaries, and status checks precede runtime code. |
| Explicit contracts | Registry fields, output contracts, and approval states are named and versioned in docs before activation. |
| Single source of truth | Each concern has one canonical doc (this constitution, canonical indexes, section completion audits, approval gates). |
| Renderer neutrality | Output contracts describe artifact shapes; renderers are separate and must not leak into registry or planning layers by default. |
| Composition over duplication | Extend existing scripts, indexes, and rules; do not fork parallel governance docs. |
| Preserve existing behavior | Commands, checks, and semantics change only with explicit approval. |
| Small auditable changes | Prefer focused PRs with validation proof over broad refactors. |
| Deterministic outputs whenever possible | Status scripts use static file-presence and fixed-string checks; avoid dynamic parsing in proof surfaces unless separately approved. |

Additional permanent boundaries:

- No student data in repo artifacts unless explicitly approved and governed.
- No network calls, APIs, OAuth, or secrets in unapproved work.
- No lesson generation, scanning, indexing, OCR, embeddings, or vector database activation without explicit approval.

---

## 3. Architectural Layers

Intended architecture (top to bottom). **Current status:** upper layers exist as planning/status foundation; lower layers are approval-gated and largely not active.

```text
Chief of Staff
    ↓
Curriculum Registry
    ↓
Output Contracts
    ↓
Renderers
    ↓
Canvas Package Builder
    ↓
Local Retrieval
    ↓
Lesson Generation
    ↓
Automation
```

### Chief of Staff

| | |
| --- | --- |
| **Purpose** | Local CLI, dashboard, memory, intake, and read-only status orchestration. |
| **Responsibilities** | Report PASS/WARN/FAIL; route to status scripts; preserve workflow guardrails. |
| **Dependencies** | Shell scripts, repo docs, project memory. |
| **Non-responsibilities** | Lesson generation; cloud API calls; student data handling; autonomous merges without authorization. |

### Curriculum Registry

| | |
| --- | --- |
| **Purpose** | Metadata/reference catalog of curriculum sources and relationships. |
| **Responsibilities** | Hold approved registry records pointing at source storage; support teacher review states. |
| **Dependencies** | Chief of Staff status surfaces; source storage strategy; approval gate. |
| **Non-responsibilities** | Copying raw files into repo; scanning folders; resolving Drive/NAS/iCloud paths without approval. |

### Output Contracts

| | |
| --- | --- |
| **Purpose** | Named shapes for teacher-facing artifact types (slide deck, worksheet, review game, teacher script, Canvas package reference). |
| **Responsibilities** | Define contract vocabulary and planning boundaries. |
| **Dependencies** | Curriculum Registry planning; Curriculum Builder foundation docs. |
| **Non-responsibilities** | Rendering content; generating drafts; activating schema files without approval. |

### Renderers

| | |
| --- | --- |
| **Purpose** | Transform approved contract inputs into reviewable teacher artifacts. |
| **Responsibilities** | Produce deterministic, human-reviewable outputs when explicitly approved. |
| **Dependencies** | Output contracts; validators; explicit implementation intake. |
| **Non-responsibilities** | Registry ingestion; RAG; network fetches; student-facing publication without review. |

### Canvas Package Builder

| | |
| --- | --- |
| **Purpose** | Assemble Canvas-ready export packages from approved artifacts. |
| **Responsibilities** | Package planning and bounded export workflows when approved. |
| **Dependencies** | Canvas LLM planning foundation (frozen); output contracts; renderers. |
| **Non-responsibilities** | Canvas API calls; OAuth; live publishing; unfreezing Canvas track by default. |

### Local Retrieval

| | |
| --- | --- |
| **Purpose** | Local-first search and retrieval over approved indexes and references. |
| **Responsibilities** | Support teacher lookup without cloud dependency when approved. |
| **Dependencies** | Registry; explicit indexing policy; no student data. |
| **Non-responsibilities** | Vector database; embeddings; OCR; crawling; RAG pipelines without approval. |

### Lesson Generation

| | |
| --- | --- |
| **Purpose** | Assisted drafting of lesson briefs, activities, and review materials under teacher control. |
| **Responsibilities** | Generate drafts for human review when explicitly approved. |
| **Dependencies** | Contracts; retrieval; Chief of Staff safety layer. |
| **Non-responsibilities** | Autonomous classroom-ready production; gitignored drafts promoted without review. |

### Automation

| | |
| --- | --- |
| **Purpose** | Schedulers, background jobs, and recurring workflows. |
| **Responsibilities** | Run only with explicit approval, dry-run defaults, and rollback plans. |
| **Dependencies** | All upstream layers stable and approved. |
| **Non-responsibilities** | Unattended network calls; launch agents; cron without approval. |

---

## 4. Repository Invariants

These invariants are permanent unless Owen explicitly approves a coordinated change:

- **Existing commands preserved** — `bin/chief-of-staff` subcommands remain stable.
- **PASS/WARN/FAIL semantics preserved** — status scripts keep parseable Summary blocks.
- **Status scripts remain authoritative** — dashboard captures script output; scripts do not abort early on `set -e` in wrappers.
- **Dashboard remains authoritative** — local `main` dashboard health is final merge proof.
- **Full PR lifecycle** — feature branch, validation, PR, merge, cleanup, re-validation on `main`.
- **Branch cleanup verification** — remote and local feature branches deleted after merge.
- **Local main verification** — clean working tree, up to date with `origin/main`, post-merge validation.
- **Never commit directly to `main`.**
- **No student-sensitive data by default.**

---

## 5. Engineering Workflow

Reference: `.cursor/rules/teacher-ai-workstation-senior-engineer.mdc`, `docs/cursor-workflow-operating-system.md`.

Autonomous lifecycle for approved tasks:

```text
Review → Plan → Implement → Validate → Debug → Retest → Self-review
    → Commit → Push → PR → Review → Merge → Cleanup → Final proof
```

Preflight before editing:

1. Pull latest `main`.
2. Verify clean working tree and dashboard when feasible.
3. Create a feature branch.
4. Inspect only files in approved scope.

---

## 6. Approval Gates

Reference: `docs/implementation-approval-gate.md`.

| Stage | Description | Default status |
| --- | --- | --- |
| **Planning** | Docs, indexes, audits, fictional samples | Allowed when bounded |
| **Documentation** | Cross-links, status checks, governance | Allowed when bounded |
| **Implementation** | Schema, registry, validators, renderers, commands that read/write | **Blocked** without intake |
| **Runtime** | APIs, connectors, resolution, generation, automation | **Blocked** without intake |
| **Production** | Student-facing, deployed, or unattended behavior | **Blocked** without explicit approval |

Track-specific gates add requirements:

- Curriculum Builder: `docs/curriculum-builder-approval-gate.md`
- Canvas LLM: freeze + stop marker (`docs/canvas-llm-section-completion-audit.md`)

---

## 7. Cursor Responsibilities

Cursor is the local **senior engineer** and **repository maintainer**.

Roles:

- builder
- debugger
- reviewer
- tester
- documentation maintainer
- PR owner
- validation owner
- cleanup owner
- proof provider

Cursor should continue autonomously until:

- the mission is complete, **or**
- an escalation condition is encountered (Section 8).

Rules: `.cursor/rules/teacher-ai-workstation.mdc`, `.cursor/rules/teacher-ai-workstation-senior-engineer.mdc`.

---

## 8. Escalation Conditions

Cursor must stop and ask Owen when:

- hard repo boundaries would be violated
- runtime/app/API/generation is required but not approved
- secrets, credentials, OAuth, network services, or external APIs are needed
- student data or real curriculum content would be touched
- destructive refactors, broad renames, or deletions are needed
- existing commands, checks, or PASS/WARN/FAIL semantics would need to change without approval
- unrelated tests fail and cannot be safely isolated
- WARN/FAIL cannot be fixed without changing approved behavior
- multiple architectural paths are equally valid and require owner choice

Full list: `.cursor/rules/teacher-ai-workstation-senior-engineer.mdc` — Escalation Conditions.

---

## 9. Definition of Done

Every **approved implementation** track PR should satisfy:

- [ ] Architecture reviewed against this constitution and relevant section audits
- [ ] Documentation updated (indexes, handoffs, cross-links)
- [ ] Status scripts updated when doc or wiring changes require it
- [ ] Validation passing (track scripts + dashboard + smoke tests)
- [ ] Dashboard clean on local `main` after merge
- [ ] Smoke tests passing
- [ ] PR merged via feature branch
- [ ] Branches removed (local and remote)
- [ ] Local `main` verified clean and up to date
- [ ] Completion report produced (PR, commits, check deltas, non-activation)

Documentation/status PRs follow the same validation and cleanup discipline without crossing implementation gates.

---

## 10. Version 1.0 Definition

**Version 1.0** describes engineering goals — not a delivery date. A future 1.0 release means the following systems exist as **approved, teacher-reviewed, locally operable capabilities** with validation proof:

| System | 1.0 engineering goal |
| --- | --- |
| Chief of Staff | Stable CLI, dashboard, memory, intake, and status orchestration |
| Curriculum Registry | Approved manual/static registry with metadata references (no unapproved scanning) |
| Output Contracts | Active contract definitions wired to registry and review workflow |
| Renderers | At least one teacher-reviewed renderer per primary contract type |
| Canvas Package Builder | Bounded export path from approved artifacts (Canvas API only if separately approved) |
| Local Retrieval | Approved local lookup over registry/index without cloud dependency |
| Lesson Generation | Human-reviewed draft generation under explicit safety boundaries |
| Validation suite | PASS/WARN/FAIL scripts and dashboard cover all active tracks |
| Dashboard | Single local health surface proving repo state on `main` |

**Not required for 1.0 by default:** unattended automation, student-facing publication, cloud-first ingestion, RAG/vector search, or school-system integrations.

Current phase: **Phase 2 transition** — engineering governance and planning foundations complete; implementation tracks approval-gated.

---

## 11. Future Track Model

Future work proceeds as **implementation tracks**, not ad hoc PRs.

Each track:

1. Starts from section completion audit and this constitution.
2. Completes track intake (`docs/implementation-approval-gate.md`).
3. Crosses track-specific approval gate when applicable.
4. Lands in small, validated PRs with preserved invariants.
5. Ends with section or track completion audit and dashboard proof.

Expected progression (approval-gated at each step):

```text
Governance & planning foundations (current)
    → Curriculum Registry (manual-first)
    → Output contract activation
    → Validators & renderers (bounded)
    → Canvas package builder (frozen Canvas track unfreeze if approved)
    → Local retrieval (no RAG by default)
    → Lesson generation (human-reviewed)
    → Automation (last; explicit approval only)
```

Isolated PRs that skip intake or weaken invariants are out of constitution compliance.

---

## Canonical References

| Document | Role |
| --- | --- |
| `docs/engineering-constitution.md` | This document — canonical engineering authority |
| `docs/implementation-approval-gate.md` | Repo-wide implementation gate |
| `docs/curriculum-builder-canonical-planning-index.md` | Curriculum Builder entry point |
| `docs/curriculum-builder-section-completion-audit.md` | Curriculum Builder planning complete |
| `docs/canvas-llm-section-completion-audit.md` | Canvas LLM frozen/stopped |
| `docs/cursor-workflow-operating-system.md` | Owen/ChatGPT/Cursor/GitHub workflow |
| `.cursor/rules/teacher-ai-workstation-senior-engineer.mdc` | Cursor autonomous workflow |
| `docs/build-queue.md` | Active priorities and track status |
| `assistant/memory/active-priorities.md` | Session handoff memory |

---

## Validation Expectations

```bash
bash scripts/cursor-workflow-status.sh
bin/chief-of-staff --cursor-workflow-status
bash scripts/curriculum-builder-foundation-status.sh
bin/chief-of-staff --curriculum-builder-foundation-status
bash scripts/phase-1-status.sh
bin/chief-of-staff --dashboard
bash tests/smoke-chief-of-staff-cli.sh
```

---

## Non-Activation Confirmation

Documentation/status only. Engineering Constitution is Markdown-only governance text. No runtime implementation, schemas, validators, renderers, registry activation, ingestion, scanning, indexing, OCR, embeddings, vector database, APIs, OAuth, automation, lesson generation, generated lesson drafts, generated review notes, student data, or changes to existing commands or PASS/WARN/FAIL semantics. Constitution status: active. Implementation approval status: not approved by default.
