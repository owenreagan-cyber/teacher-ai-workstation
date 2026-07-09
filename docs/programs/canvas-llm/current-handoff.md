# Canvas LLM Current Handoff

## Current Phase

Phase 19F — Title Cleaner Deterministic Prototype Preview

## Current Production State

```text
Repo: ~/Projects/teacher-ai-workstation
Branch: main
Commit: 375b649
Latest merged PR: #305 — Add Canvas LLM Phase 19E title cleaner validator
```

## Current Work

Create a preview-only deterministic prototype for title cleaning using the committed Phase 19D fixtures and rules.

Current Phase 19F directory:

```text
docs/programs/canvas-llm/phase-19f-title-cleaner-deterministic-prototype-preview/
```

Current Phase 19F outputs:

```text
README.md
title-cleaner-deterministic-prototype-spec.md
title-cleaner-deterministic-prototype-report.md
preview-only-boundary.md
phase-19f-next-step-recommendation.md
scripts/canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview.py
scripts/canvas-llm-phase-19f-title-cleaner-deterministic-prototype-preview-status.sh
```

## Current Recommendation

Do not implement Canvas LLM Center yet.

After Phase 19F, the next safe phase should be preview-only:

```text
Phase 19G — Title Cleaner Review Packet Preview
```

Alternative:

```text
Phase 19G — Medical Center Diagnostic Spec Expansion
```

No Canvas writes are approved.

### Phase 19E Title Cleaner Validator Historical Baseline

```text
Phase 19F — Title Cleaner Deterministic Prototype Preview
PR #305 — Add Canvas LLM Phase 19E title cleaner validator
Commit: 375b649
```

Phase 19E validator directory:

```text
docs/programs/canvas-llm/phase-19e-title-cleaner-validator-preview/
```

This historical marker is preserved for Phase 19E regression status continuity.

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

### Handoff Regression Rule

```text
docs/programs/canvas-llm/handoff-regression-rule.md
```

Preserve historical handoff breadcrumbs required by prior phase status scripts.

### Phase 19A Forward Recommendation Breadcrumb

```text
Phase 19B — Canonical Rule Constitution
```

This preserves the earlier Phase 19A recommendation marker while Phase 19F remains the current active phase.

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
