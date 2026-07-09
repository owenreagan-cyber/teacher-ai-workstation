# Canvas LLM Current Handoff

## Current Phase

Phase 19C — Evidence Vault + Rule Catalog Schema

## Current Production State

```text
Repo: ~/Projects/teacher-ai-workstation
Branch: main
Commit: f2d99a9
Latest merged PR: #302 — Add Canvas LLM Phase 19B canonical rules
```

## Current Working Branch

```text
canvas-llm-phase-19c-evidence-vault-rule-catalog-schema
```

## Handoff Regression Rule

Future phases must preserve historical handoff breadcrumbs required by prior phase status scripts.

Rule file:

```text
docs/programs/canvas-llm/handoff-regression-rule.md
```

When updating current handoff, move the current phase forward but keep older PR/commit markers in a historical baseline section if regressions validate them.

## Current Rule

Use repo-tracked memory files as the active handoff source.

Do not rely on archived chats, temporary Codex folders, assistant memory, or pasted inventories unless the contents have been converted into a repo-tracked memory or rule file.

## Active Memory File

```text
docs/programs/canvas-llm/memory/phase-19a-memory.md
```

## Latest Completed Phase

```text
Phase 19B — Canonical Rule Constitution
PR #302
Status: merged
```

## Phase 19A Historical Baseline

Phase 19A archaeology originally used this baseline:

```text
PR #300 — Canvas LLM Phase 19A memory foundation
Commit: 5af1ecd
```

This historical marker is preserved for Phase 19A regression status continuity.

## Phase 19A Archaeology Historical Baseline

Phase 19A archaeology report used this merged PR baseline:

```text
PR #301 — Add Canvas LLM Phase 19A archaeology report
Commit: f61dae2
```

This historical marker is preserved for Phase 19B regression status continuity.

## Phase 19B Rule Directory Historical Breadcrumb

Phase 19B canonical rules directory:

```text
docs/programs/canvas-llm/phase-19b-canonical-rules/
```

This historical marker is preserved for Phase 19B regression status continuity.

## Phase 19B Historical Baseline

Phase 19B canonical rules used this baseline:

```text
PR #302 — Add Canvas LLM Phase 19B canonical rules
Commit: f2d99a9
```

This historical marker is preserved for Phase 19B regression status continuity.


## Current Work

Define preview-only Evidence Vault and Rule Catalog schemas before implementation.

Current schema directory:

```text
docs/programs/canvas-llm/phase-19c-evidence-vault-rule-catalog/
```

Current Phase 19C schema specs:

```text
evidence-vault-schema.md
evidence-classification-schema.md
rule-catalog-schema.md
rule-review-workflow.md
rule-source-linking-schema.md
diagnostic-readiness-schema.md
preview-only-boundary.md
phase-19c-next-step-recommendation.md
```

## Current Recommendation

Do not implement Canvas LLM Center yet.

After Phase 19C, the next safe phase should be preview-only:

```text
Phase 19D — Machine-Readable Seed Rule Catalog Preview
```

Alternative:

```text
Phase 19D — Medical Center Diagnostic Spec Expansion
```

No Canvas writes are approved.

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
