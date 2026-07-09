# Canvas LLM Current Handoff

## Current Phase

Phase 20 — Demo Sandbox Write Gate Approval Packet

## Current Production State

```text
Repo: ~/Projects/teacher-ai-workstation
Branch: main
Commit: 375b649
Latest merged PR: #305 — Add Canvas LLM Phase 19E title cleaner validator
```

## Current Work

Prepare the Phase 20 demo sandbox write gate approval packet.

Current Phase 20 directory:

```text
docs/programs/canvas-llm/phase-20-demo-sandbox-write-gate-approval-packet/
```

Current Phase 20 status command:

```text
bin/chief-of-staff --canvas-llm-phase-20-demo-sandbox-write-gate-approval-packet-status
```

Owner-designated demo sandbox:

```text
course_id: 24399
classification: OWNER_DESIGNATED_DEMO_SANDBOX
```

Approved requested operation, recorded but not executed in Phase 20:

```text
create one unpublished Canvas page titled Math Automation Sandbox
```

## Current Recommendation

Phase 20 prepares the approval packet but does not execute the write.

Recommended next phase:

```text
Phase 21 — Execute One Approved Demo Sandbox Canvas Write
```

Phase 21 must execute only the approved operation:

```text
Create one unpublished Canvas page in course 24399 titled Math Automation Sandbox.
```

No Canvas write is executed in Phase 20.

## Historical Baselines Required For Regression Status

These breadcrumbs must remain in current handoff so older phase status scripts continue to pass.

### Phase 19A Memory Foundation Historical Baseline

```text
PR #300 — Canvas LLM Phase 19A memory foundation
Commit: 5af1ecd
```

### Phase 19A Archaeology Historical Baseline

```text
PR #301 — Add Canvas LLM Phase 19A archaeology report
Commit: f61dae2
```

### Phase 19B Canonical Rules Historical Baseline

```text
Phase 19B — Canonical Rule Constitution
PR #302 — Add Canvas LLM Phase 19B canonical rules
Commit: f2d99a9
```

Phase 19B canonical rules directory:

```text
docs/programs/canvas-llm/phase-19b-canonical-rules/
```

### Phase 19C Evidence Vault Historical Baseline

```text
Phase 19C — Evidence Vault + Rule Catalog Schema
PR #303 — Add Canvas LLM Phase 19C evidence vault schema
Commit: 3e04771
```

Phase 19C schema directory:

```text
docs/programs/canvas-llm/phase-19c-evidence-vault-rule-catalog/
```

### Phase 19D Seed Rule Catalog Historical Baseline

```text
Phase 19D — Machine-Readable Seed Rule Catalog + Title Cleaner Preview
PR #304 — Add Canvas LLM Phase 19D seed rule catalog
Commit: ed52100
```

Phase 19D seed catalog directory:

```text
docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/
```

### Phase 19E Title Cleaner Validator Historical Baseline

```text
Phase 19E — Title Cleaner Validator Preview
PR #305 — Add Canvas LLM Phase 19E title cleaner validator
Commit: 375b649
```

Phase 19E validator directory:

```text
docs/programs/canvas-llm/phase-19e-title-cleaner-validator-preview/
```

### Phase 19F Title Cleaner Prototype Historical Baseline

```text
Phase 19F — Title Cleaner Deterministic Prototype Preview
PR #306 — Add Canvas LLM Phase 19F title cleaner prototype
Commit: 004aa88
```

Phase 19F prototype directory:

```text
docs/programs/canvas-llm/phase-19f-title-cleaner-deterministic-prototype-preview/
```

### Phase 19G-I Completion Historical Baseline

```text
Phase 19G-I — Review Packet, Medical Center Diagnostics, and Minimum Write Gate Design
PR #307 — Complete Canvas LLM Phase 19 review and write gate design
Commit: 42d4077
```

Phase 19G-I directories:

```text
docs/programs/canvas-llm/phase-19g-title-cleaner-review-packet-preview/
docs/programs/canvas-llm/phase-19h-medical-center-diagnostic-expansion-preview/
docs/programs/canvas-llm/phase-19i-minimum-write-gate-design-packet/
```

### Handoff Regression Rule

```text
docs/programs/canvas-llm/handoff-regression-rule.md
```

Preserve historical handoff breadcrumbs required by prior phase status scripts.

### Phase 19A Forward Recommendation Breadcrumb

```text
Phase 19B — Canonical Rule Constitution
```

This preserves the earlier Phase 19A recommendation marker while Phase 20 remains the current active phase.

### Phase 19G-I Forward Recommendation Breadcrumb

```text
Phase 20 — Canvas LLM Minimum Write Gate Approval Packet
```

This preserves the Phase 19 closure recommendation marker while Phase 20 uses the owner-designated demo sandbox approval packet.

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
