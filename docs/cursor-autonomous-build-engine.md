# Cursor Autonomous Build Engine

Last updated: 2026-07-02

```text
Status: documentation/status only
Closure status: complete_autonomous_build_engine_governance
Classification: permanent repo governance — no runtime activation
Complements: docs/cursor-operating-modes-and-approval-gates.md
```

## Purpose

Define **Autonomous Build Engine Mode** so future Cursor missions do not behave like one-off bundles. This document specifies how Cursor operates as builder, tester, validator, reviewer, hardening engineer, analyst, and proposal/roadmap strategist — and when Cursor may continue past named deliverables.

**This document does not authorize implementation by itself.** Prompt-specific scope and `docs/implementation-approval-gate.md` still govern what may be built.

---

## Autonomous Build Engine Mode

When a mission prompt explicitly invokes Autonomous Build Engine Mode (see **Future Prompt Invocation** below), Cursor runs an extended session that:

1. Completes named deliverables.
2. Runs validation and PR lifecycle.
3. Executes the **Autonomous Continuation Loop** until exhaustion or escalation.
4. Produces an **Autonomous Exhaustion Report** before stopping.

Autonomous Build Engine Mode **extends** Maximum Autonomous Execution Mode (`docs/cursor-operating-modes-and-approval-gates.md`) with continuation, exhaustion, and safe-work-class rules. It does not weaken hard boundaries.

---

## Seven Operating Roles

| Role | Responsibility |
| --- | --- |
| **Builder** | Implement approved docs/status/scripts/tests/CLI within scope |
| **Tester** | Add and run meaningful tests; negative assertions for blocked behavior |
| **Validator** | Run dashboard, validate-all, phase-1, smoke, domain status scripts |
| **Reviewer** | Self-review diffs; fix findings before merge |
| **Hardening engineer** | Cross-links, manifest/index coherence, false-PASS risks, boundary clarity |
| **Analyst** | Level 1 scan; classify findings; exhaustion surface inspection |
| **Proposal / roadmap strategist** | Update ledger, roadmap, build queue, priorities when in scope |

---

## Core Continuation Rule

```text
Cursor must not stop merely because the originally named deliverables are complete.

After completing named deliverables, Cursor must run the Autonomous Continuation Loop:

1. Inspect roadmap, build queue, active priorities, capability map, proposal ledger, lane statuses, dashboard, validation surfaces, command surfaces, and recent Level 1/2 findings.
2. Identify the next highest-value safe item that fits the Approved Safe Work Classes in the active prompt.
3. If one exists, scope-lock it, implement it, test it, validate it, PR/merge it, clean branches, and rerun final validation.
4. Repeat until no approved safe item remains or an explicit escalation condition is encountered.

Cursor may stop only if no additional safe approved work remains after required exhaustion checks or a listed escalation condition is hit.

If stopping, Cursor must cite the exact stop reason.
```

---

## Autonomous Continuation Loop

| Step | Action |
| --- | --- |
| 1 | Inspect exhaustion surfaces (see Minimum Exhaustion Rule) |
| 2 | Classify each finding: implement-now / proposal-only / blocked / no action |
| 3 | Scope-lock next highest-value item inside prompt-approved safe work classes |
| 4 | Implement, test, wire dashboard/CLI/manifest if appropriate |
| 5 | Run focused then broad validation |
| 6 | Self-review diff |
| 7 | Commit → push → PR → review → merge |
| 8 | Pull `main`, delete mission branches, prune |
| 9 | Rerun final validation on clean `main` |
| 10 | Run Level 1 discovery again |
| 11 | Repeat or stop with cited reason |

**Scope-lock:** Before each continuation item, Cursor states the single item, files likely touched, and why it fits an approved safe work class. Cursor must not expand into blocked categories mid-loop.

---

## Approved Safe Work Classes

Safe work classes are **not** blanket implementation approval. The active mission prompt may **narrow** but not **widen** repo hard boundaries.

| Class | Meaning |
| --- | --- |
| **Safe Work Class A** | Docs/status/test/CLI/dashboard hardening |
| **Safe Work Class B** | Fake-fixture-only validators and previews |
| **Safe Work Class C** | Proposal ledger, roadmap, build queue, active-priority, capability-map coherence |
| **Safe Work Class D** | Chief of Staff aggregate command surfaces |
| **Safe Work Class E** | Level 1 discovery candidates converted into docs/status-only work |
| **Safe Work Class F** | Level 2 lane review docs/status when lane is `complete_pending_review` and prompt-approved |
| **Safe Work Class G** | Documented expected WARN classification and WARN follow-up tracking |
| **Safe Work Class H** | Proposal folder / idea development system (planning-only docs, templates, indexes; no runtime) |

**Rules:**

- No safe work class overrides student-data, real-curriculum, API/network, production-write, or generation boundaries.
- Production/runtime/API/student-data/real-curriculum work always requires explicit Owen approval.
- Prompt-specific scope controls what Cursor may implement.

---

## Minimum Exhaustion Rule

Cursor may **not** declare “no safe approved work remains” until it inspects and reports on all required exhaustion surfaces:

- `docs/master-build-roadmap.md`
- `docs/build-queue.md`
- `assistant/memory/active-priorities.md`
- `docs/teacher-workstation-capability-map.md`
- `docs/proposals/index.md`
- Program Lane Status table
- Dashboard output
- validate-all output
- phase-1 output
- smoke CLI coverage
- command manifest
- command index
- current WARN-producing checks
- latest Level 1 discovery findings
- latest Level 2 lane review findings
- relevant status scripts for touched domains
- relevant tests for touched domains

For each surface, classify: **implement-now** (inside prompt) · **proposal-only** · **blocked** · **no action**.

---

## No Soft Stop Rule

Cursor must **not** stop for:

- bundle complete
- named deliverables complete
- governance doc complete
- status command complete
- one continuation item complete
- one PR complete
- one merge complete
- “good enough”
- auditability concerns
- elapsed effort
- expected WARNs (if documented per Expected WARN Policy)
- lack of obvious next step **before** inspecting all required exhaustion surfaces

---

## Expected WARN Policy

Cursor may leave WARNs only if **all** are true:

1. WARN is pre-existing or intentionally introduced as non-blocking.
2. WARN is documented in the final report.
3. WARN has a clear reason.
4. WARN has an owner or future follow-up classification.
5. WARN does not hide a FAIL.
6. WARN does not weaken PASS/WARN/FAIL semantics.

**Registered expected WARNs:** `docs/curriculum-builder-registry-expected-warns.md`

Do not hide, downgrade, or reinterpret WARNs as PASS.

---

## Level 1 / Level 2 / Level 3 Discovery Integration

Authority for discovery semantics: `docs/cursor-operating-modes-and-approval-gates.md` § Three-Level Discovery Governance.

### Level 1 — Automatic Every Mission

**When:** After each completed section, PR, or merge (when mission includes Autonomous Build Engine Mode).

**Purpose:** Find 0–3 nearby safe improvements. Classify each:

- implement now (if inside prompt safe work classes)
- backlog idea
- needs Level 2 lane review
- needs Owen approval
- blocked

### Level 2 — Lane-Level Review

**When:** Lane `complete_pending_review` and explicit prompt approval.

**Purpose:** Deep lane review, proposal portfolio, mark `reviewed` if appropriate. Does not authorize runtime/API/generation/write without separate approval.

### Level 3 — Full Product Strategy

**When:** Explicit Owen approval only. **Never automatic** during implementation prompts.

**Purpose:** Full product/architecture strategy across lanes or whole workstation.

---

## Stop Rules and Escalation Conditions

**Valid stop reasons:**

1. `No safe approved work remains after required exhaustion checks` (with completed Autonomous Exhaustion Report)
2. Exact escalation condition from active mission prompt or repo governance

**Escalation examples (stop and report):**

- Production registry writes or active `--write`
- Real curriculum content or student data
- APIs/OAuth/network/Canvas/Drive/NAS/iCloud
- OCR, embeddings, RAG, generation
- PASS/WARN/FAIL semantic change required
- Command removal/rename required
- Broad refactor or Owen product architecture decision
- Validation FAIL outside scope that cannot be safely fixed

---

## PR / Merge / Cleanup Lifecycle

For approved autonomous missions:

1. Feature branch → implement → validate → commit → push → PR
2. Review PR diff → fix → revalidate → merge
3. Pull `main` → delete remote/local mission branch → prune
4. Rerun full validation on clean `main`
5. Verify dashboard health
6. Report final proof with exhaustion report

Auditability through focused PRs — not early stopping.

---

## Run-Approval Expectations

| Requirement | Rule |
| --- | --- |
| Mission prompt | Must explicitly authorize Autonomous Build Engine Mode and safe work classes |
| Implementation | Not approved by governance docs alone |
| Continuation | Limited to prompt-approved safe work classes |
| Level 3 | Requires explicit Owen mission |
| Production writes | Always blocked unless separate explicit mission |

---

## Future Prompt Invocation

```text
Operate under Autonomous Build Engine Mode.

After completing named deliverables, run the Autonomous Continuation Loop.

Continue through approved safe work classes until no safe approved work remains after required exhaustion checks or an escalation condition is encountered.

Do not stop for one commit, one PR, one completed bundle, one completed continuation item, or one validation pass.

Stop only for a listed escalation condition or because no safe approved work remains after required exhaustion checks.

When stopping, cite the exact stop reason.
```

---

## Examples

### Acceptable continuation (Class A/C)

- Missing cross-link from active priorities to new governance doc
- Dashboard/validate-all wiring for new status command
- Document expected WARNs for A4–A7 fixture cross-validation

### Forbidden continuation

- Production registry `--write` implementation
- Real metadata intake
- Canvas/Drive API integration
- Lesson generation
- Broad rename of existing CLI flags

---

## Hard Boundaries (Always)

No student data · no real curriculum content · no production writes · no active `--write` · no APIs/OAuth/network · no scanning/crawling/OCR/embeddings/RAG · no generation · no command/check removal · no PASS/WARN/FAIL semantic changes

---

## Orchestrated Proof

```bash
bin/chief-of-staff --autonomous-build-engine-status
bash scripts/autonomous-build-engine-status.sh
bash tests/autonomous-build-engine-status-test.sh
bin/chief-of-staff --cursor-operating-modes-status
```

## Non-Activation

This document does not activate runtime behavior, automation, or external integrations.
