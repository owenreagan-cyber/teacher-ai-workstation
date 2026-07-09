# Canvas LLM Current Handoff

## Current Phase

Phase 19D — Machine-Readable Seed Rule Catalog + Title Cleaner Preview

## Current Production State

```text
Repo: ~/Projects/teacher-ai-workstation
Branch: main
Commit: 3e04771
Latest merged PR: #303 — Add Canvas LLM Phase 19C evidence vault schema
```

## Current Work

Create preview-only machine-readable seed data for the Evidence Vault, Rule Catalog, source links, and Canonical Title Cleaner.

Current Phase 19D directory:

```text
docs/programs/canvas-llm/phase-19d-seed-rule-catalog-title-cleaner/
```

Current Phase 19D preview data/specs:

```text
README.md
evidence.json
rules.json
links.json
title-normalization-rules.json
title-normalization-fixtures.md
preview-only-boundary.md
phase-19d-next-step-recommendation.md
```

## Current Recommendation

Do not implement Canvas LLM Center yet.

After Phase 19D, the next safe phase should be preview-only:

```text
Phase 19E — Title Cleaner Validator Preview
```

Alternative:

```text
Phase 19E — Medical Center Diagnostic Spec Expansion
```

No Canvas writes are approved.

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

Phase 19C — Evidence Vault + Rule Catalog Schema

```text
Phase 19D — Machine-Readable Seed Rule Catalog + Title Cleaner Preview
PR #303 — Add Canvas LLM Phase 19C evidence vault schema
Commit: 3e04771
```

Phase 19C schema directory:

```text
docs/programs/canvas-llm/phase-19c-evidence-vault-rule-catalog/
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

This preserves the earlier Phase 19A recommendation marker while Phase 19D remains the current active phase.

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
