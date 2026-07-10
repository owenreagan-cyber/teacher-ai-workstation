# Canvas LLM Current Handoff

## Current Phase

Phase 21 — Codex Autonomous Sandbox Learning Agent

## Current Production State

```text
Repo: ~/Projects/teacher-ai-workstation
Branch: main
Commit: 8275c77
Latest merged PR: #309 — Add Canvas LLM Phase 21 autonomous sandbox learning agent
```

## Current Work

Tighten the Phase 21 autonomous Canvas learning agent framework with the revised owner contract:

- approved runtime Canvas base domain
- reference-only inventory mode
- announcement notification blocking
- handoff and memory continuity

Current Phase 21 directory:

```text
docs/programs/canvas-llm/phase-21-codex-autonomous-sandbox-learning-agent/
```

Current Phase 21 status command:

```text
bin/chief-of-staff --canvas-llm-phase-21-codex-autonomous-sandbox-learning-agent-status
```

Approved runtime Canvas base domain:

```text
https://thalesacademy.instructure.com
```

Future local operator commands:

```bash
export CANVAS_BASE_URL="https://thalesacademy.instructure.com"
# Set CANVAS_TOKEN locally only.
# Use a hidden prompt in Terminal; never paste the token into chat or commit it.
printf "Canvas token: "
stty -echo
IFS= read CANVAS_TOKEN
stty echo
echo
export CANVAS_TOKEN

python3 scripts/canvas-llm/canvas_learning_agent.py --mode inventory
python3 scripts/canvas-llm/canvas_learning_agent.py --mode reference-inventory
python3 scripts/canvas-llm/canvas_learning_agent.py --mode questions
python3 scripts/canvas-llm/canvas_learning_agent.py --mode existing-page-dry-run
python3 scripts/canvas-llm/canvas_learning_agent.py --mode experiment --allow-writes
python3 scripts/canvas-llm/canvas_learning_agent.py --mode cleanup --allow-writes
```

Owner-designated demo sandbox:

```text
course_id: 24399
classification: OWNER_DESIGNATED_DEMO_SANDBOX
```

Sandbox write boundary:

```text
Writes are allowed only in course 24399, only with --allow-writes, and only for approved learning experiments.
Reference courses 21944, 21957, and 21919 remain read-only.
Announcement notification behavior remains blocked unless a later explicit approval names the exact action.
```

## Current Recommendation

Phase 21 live inventory succeeded and should now be followed by Phase 21A doctrine hardening.

Owner clarified:

```text
Q4W10 is the only true normal Week 10 class page currently expected.
Q1W10, Q2W10, and Q3W10 must not be inferred automatically.
Q1END and Q3END may exist as owner-created end-of-track special pages.
```

Owner also clarified calendar disruption behavior:

```text
Snow Day -> In Class: Snow Day.
Snow day homework is removed.
The displaced lesson/homework shifts forward one school day.
Later lessons/homework cascade forward.
Friday lessons shift to Monday.
Friday tests shift to Tuesday.
Changed test dates require parent announcement updates.
Canvas writes require preview and approval.
```

Owner also clarified non-traditional lesson behavior:

```text
Science Lab: Earthquakes
Writing Activity on Expository Writing Unit
```

These exact entries should be preserved as the In Class text.

The app must not auto-pull resources or auto-create assignments unless Owen explicitly adds/approves them in the lesson planner.

Recommended next operational sequence:

```text
1. Preserve the Q4W10 / QxEND / Snow Day / non-traditional lesson doctrine in Phase 21A.
2. Run existing-page-dry-run against sandbox 24399.
3. Review proposed editable-region plan.
4. Only then run sandbox experiment mode with --allow-writes.
5. Promote stable learning into Medical Center rules.
```

## Boundaries

Do not:

- call Canvas APIs
- write to Canvas
- fetch live Canvas data
- move, rename, upload, delete, or publish files
- commit raw `.local` metadata
- commit school Canvas URLs
- expose tokens
- access student data
- enable generation or automation
- implement app behavior
- refactor legacy code

---

## Protected Historical Regression Breadcrumbs

This section preserves historical Canvas LLM handoff breadcrumbs required by regression checks.

### PR Breadcrumbs

- PR #300 — Canvas LLM Phase 19A memory foundation
- PR #301 — Add Canvas LLM Phase 19A archaeology report
- PR #302 — Add Canvas LLM Phase 19B canonical rules
- PR #303 — Add Canvas LLM Phase 19C evidence vault schema
- PR #304 — Add Canvas LLM Phase 19D seed rule catalog
- PR #305 — Add Canvas LLM Phase 19E title cleaner validator
- PR #306 — Add Canvas LLM Phase 19F title cleaner prototype
- PR #307 — Complete Canvas LLM Phase 19 review and write gate design
- PR #308 — Add Canvas LLM Phase 20 demo sandbox approval packet
- PR #310 — Add Canvas LLM Phase 21 autonomous sandbox learning agent

### Phase Directory Breadcrumbs

- docs/programs/canvas-llm/phase-19b-canonical-rules/
- docs/programs/canvas-llm/phase-19c-evidence-vault-rule-catalog/
- docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/
- docs/programs/canvas-llm/phase-19e-title-cleaner-validator-preview/
- docs/programs/canvas-llm/phase-19f-title-cleaner-deterministic-prototype-preview/
- docs/programs/canvas-llm/phase-19g-title-cleaner-review-packet-preview/
- docs/programs/canvas-llm/phase-19h-medical-center-diagnostic-expansion-preview/
- docs/programs/canvas-llm/phase-19i-minimum-write-gate-design-packet/
- docs/programs/canvas-llm/phase-20-demo-sandbox-write-gate-approval-packet/
- docs/programs/canvas-llm/phase-21-codex-autonomous-sandbox-learning-agent/

### Phase Status Breadcrumbs

- Phase 19G-I
- Phase 20
- Phase 21
- Phase 21A

### Regression Rule Breadcrumb

- docs/programs/canvas-llm/handoff-regression-rule.md

### Forward Recommendation Breadcrumbs

- Phase 19A Forward Recommendation Breadcrumb: Phase 19B — Canonical Rule Constitution
- Phase 19G-I Forward Recommendation Breadcrumb: Phase 20 — Canvas LLM Minimum Write Gate Approval Packet
- Phase 20 Forward Recommendation Breadcrumb: Phase 21 — Execute One Approved Demo Sandbox Canvas Write
- Phase 21 Forward Recommendation Breadcrumb: Phase 21A — Calendar, Q/W, Snow Day, and Non-Traditional Lesson Doctrine Hardening

---

## Exact Legacy Status Phrases

These exact phrases are preserved for older Canvas LLM regression scripts.

- PR #300 baseline
- PR #301 baseline
- Phase 19C
- Phase 19D
- Phase 19E
- Phase 19F

### Exact Phase Records

Current handoff references PR #300 baseline.

Current handoff records PR #301 baseline.

Current handoff records Phase 19C.

Current handoff records Phase 19D.

Current handoff records Phase 19E.

Current handoff records Phase 19F.

Current handoff records Phase 19G-I.

### Exact Directory Records

Current handoff records docs/programs/canvas-llm/phase-19c-evidence-vault-rule-catalog/.

Current handoff records docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/.

Current handoff records docs/programs/canvas-llm/phase-19e-title-cleaner-validator-preview/.

Current handoff records docs/programs/canvas-llm/phase-19f-title-cleaner-deterministic-prototype-preview/.

Current handoff records docs/programs/canvas-llm/phase-19g-title-cleaner-review-packet-preview/.

Current handoff records docs/programs/canvas-llm/phase-19h-medical-center-diagnostic-expansion-preview/.

Current handoff records docs/programs/canvas-llm/phase-19i-minimum-write-gate-design-packet/.

---

## Exact Legacy Status Phrases

These exact phrases are preserved for older Canvas LLM regression scripts.

- PR #300 baseline
- PR #301 baseline
- Phase 19C
- Phase 19D
- Phase 19E
- Phase 19F

### Exact Phase Records

Current handoff references PR #300 baseline.

Current handoff records PR #301 baseline.

Current handoff records Phase 19C.

Current handoff records Phase 19D.

Current handoff records Phase 19E.

Current handoff records Phase 19F.

Current handoff records Phase 19G-I.

### Exact Directory Records

Current handoff records docs/programs/canvas-llm/phase-19c-evidence-vault-rule-catalog/.

Current handoff records docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/.

Current handoff records docs/programs/canvas-llm/phase-19e-title-cleaner-validator-preview/.

Current handoff records docs/programs/canvas-llm/phase-19f-title-cleaner-deterministic-prototype-preview/.

Current handoff records docs/programs/canvas-llm/phase-19g-title-cleaner-review-packet-preview/.

Current handoff records docs/programs/canvas-llm/phase-19h-medical-center-diagnostic-expansion-preview/.

Current handoff records docs/programs/canvas-llm/phase-19i-minimum-write-gate-design-packet/.

---

## Machine-Extracted Legacy Handoff Patterns

These exact strings are preserved because older Canvas LLM status scripts grep for them directly.

### handoff records Phase 19B

Source script: `scripts/canvas-llm-phase-19b-canonical-rules-status.sh`

```text
Phase 19B — Canonical Rule Constitution
```

Phase 19B — Canonical Rule Constitution

### handoff records PR #301 baseline

Source script: `scripts/canvas-llm-phase-19b-canonical-rules-status.sh`

```text
f61dae2
```

f61dae2

### handoff records Phase 19B rule directory

Source script: `scripts/canvas-llm-phase-19b-canonical-rules-status.sh`

```text
phase-19b-canonical-rules
```

phase-19b-canonical-rules

### handoff regression rule preserves historical breadcrumbs

Source script: `scripts/canvas-llm-phase-19b-canonical-rules-status.sh`

```text
Preserve historical handoff breadcrumbs
```

Preserve historical handoff breadcrumbs

### handoff regression rule prefers restoring breadcrumbs

Source script: `scripts/canvas-llm-phase-19b-canonical-rules-status.sh`

```text
restore the historical breadcrumb
```

restore the historical breadcrumb

### handoff references handoff regression rule

Source script: `scripts/canvas-llm-phase-19b-canonical-rules-status.sh`

```text
handoff-regression-rule.md
```

handoff-regression-rule.md

### handoff records Phase 19C

Source script: `scripts/canvas-llm-phase-19c-evidence-vault-rule-catalog-status.sh`

```text
Phase 19C — Evidence Vault + Rule Catalog Schema
```

Phase 19C — Evidence Vault + Rule Catalog Schema

### handoff preserves PR #300 breadcrumb

Source script: `scripts/canvas-llm-phase-19c-evidence-vault-rule-catalog-status.sh`

```text
PR #300
```

PR #300

### handoff preserves PR #301 breadcrumb

Source script: `scripts/canvas-llm-phase-19c-evidence-vault-rule-catalog-status.sh`

```text
PR #301
```

PR #301

### handoff preserves PR #302 breadcrumb

Source script: `scripts/canvas-llm-phase-19c-evidence-vault-rule-catalog-status.sh`

```text
PR #302
```

PR #302

### handoff records Phase 19C schema directory

Source script: `scripts/canvas-llm-phase-19c-evidence-vault-rule-catalog-status.sh`

```text
phase-19c-evidence-vault-rule-catalog
```

phase-19c-evidence-vault-rule-catalog

### handoff records Phase 19D

Source script: `scripts/canvas-llm-phase-19d-seed-rule-catalog-title-cleaner-status.sh`

```text
Phase 19D — Machine-Readable Seed Rule Catalog + Title Cleaner Preview
```

Phase 19D — Machine-Readable Seed Rule Catalog + Title Cleaner Preview

### handoff preserves PR #303 breadcrumb

Source script: `scripts/canvas-llm-phase-19d-seed-rule-catalog-title-cleaner-status.sh`

```text
PR #303
```

PR #303

### handoff records Phase 19D directory

Source script: `scripts/canvas-llm-phase-19d-seed-rule-catalog-title-cleaner-status.sh`

```text
phase-19d-seed-rule-catalog-title-cleaner
```

phase-19d-seed-rule-catalog-title-cleaner

### handoff records Phase 19E

Source script: `scripts/canvas-llm-phase-19e-title-cleaner-validator-preview-status.sh`

```text
Phase 19E — Title Cleaner Validator Preview
```

Phase 19E — Title Cleaner Validator Preview

### handoff preserves PR #304 breadcrumb

Source script: `scripts/canvas-llm-phase-19e-title-cleaner-validator-preview-status.sh`

```text
PR #304
```

PR #304

### handoff records Phase 19E directory

Source script: `scripts/canvas-llm-phase-19e-title-cleaner-validator-preview-status.sh`

```text
phase-19e-title-cleaner-validator-preview
```

phase-19e-title-cleaner-validator-preview

### handoff records Phase 19F

Source script: `scripts/canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview-status.sh`

```text
Phase 19F — Title Cleaner Deterministic Prototype Preview
```

Phase 19F — Title Cleaner Deterministic Prototype Preview

### handoff preserves PR #305 breadcrumb

Source script: `scripts/canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview-status.sh`

```text
PR #305
```

PR #305

### handoff records Phase 19F directory

Source script: `scripts/canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview-status.sh`

```text
phase-19f-title-cleaner-deterministic-prototype-preview
```

phase-19f-title-cleaner-deterministic-prototype-preview

### handoff records Phase 19G-I

Source script: `scripts/canvas-llm-phase-19g-19i-completion-status.sh`

```text
Phase 19G-I
```

Phase 19G-I

### handoff preserves PR #306 breadcrumb

Source script: `scripts/canvas-llm-phase-19g-19i-completion-status.sh`

```text
PR #306
```

PR #306

---

## Exact Phase 19A PR #300 Baseline

This exact baseline is preserved for the Phase 19A archaeology status script.

```text
5af1ecd
```

PR #300 baseline: 5af1ecd

Current handoff references PR #300 baseline: 5af1ecd

---

## Exact Phase 19A PR #300 Baseline

This exact baseline is preserved for the Phase 19A archaeology status script.

```text
5af1ecd
```

PR #300 baseline: 5af1ecd

Current handoff references PR #300 baseline: 5af1ecd

---

## Machine-Maintained Handoff Breadcrumb Guardrail

This section is maintained by `scripts/canvas-llm-handoff-breadcrumb-repair.py`.

Do not manually delete this section during phase handoff edits.

### handoff records PR #301 baseline

Source: `manual`

```text
PR #301 baseline: f61dae2
```

PR #301 baseline: f61dae2

### handoff records PR #301 baseline exact phrase

Source: `manual`

```text
Current handoff records PR #301 baseline: f61dae2
```

Current handoff records PR #301 baseline: f61dae2

---

## Phase 21B Existing Page Dry-Run Readiness Update

Phase 21B validates the next safe step after Phase 21A:

```text
Run existing-page dry-run against owner-designated sandbox course 24399 before any --allow-writes experiment.
```

Phase 21B keeps Canvas writes blocked.

Phase 21B adds a dedicated status command:

```bash
bin/chief-of-staff --canvas-llm-phase-21b-existing-page-dry-run-readiness-status
```

Required preflight for future phases:

```bash
python3 scripts/canvas-llm-handoff-breadcrumb-repair.py --repair
python3 scripts/canvas-llm-handoff-breadcrumb-repair.py --check
```

---

## Phase 21B Dry-Run Finding

Observed decision:

```text
EXISTING_PAGE_DRY_RUN_NEEDS_AGENT_HARDENING
```

Reason:

```text
Inventory found sandbox QxWy page candidates in course 24399, but existing-page dry-run returned:
WARN: no sandbox QxWy candidate page found
```

Next step should harden the existing-page dry-run selector before any sandbox write experiment.

Canvas writes remain blocked.
