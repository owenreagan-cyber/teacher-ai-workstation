# Canvas LLM Phase 21B — Existing Page Dry-Run Readiness

## Purpose

Phase 21B validates that the Canvas LLM autonomous sandbox learning agent can safely prepare an existing-page update preview before any sandbox write experiment.

This phase follows Phase 21A, which hardened:

- Q/W page doctrine
- Q4W10 true Week 10 behavior
- Q1END/Q3END end-of-track special page behavior
- Snow Day Protocol
- non-traditional lesson exact-text behavior
- handoff breadcrumb auto-repair guardrail

## Scope

Phase 21B is a dry-run/readiness phase.

It may:

- run the handoff breadcrumb guardrail
- refresh live inventory for owner-approved sandbox course `24399`
- refresh read-only reference inventory for courses `21919`, `21944`, and `21957`
- regenerate question backlog
- run existing-page dry-run mode
- inspect sanitized local learning outputs
- document readiness for a future sandbox write experiment

It must not:

- run `--mode experiment`
- pass `--allow-writes`
- create Canvas pages
- update Canvas pages
- publish Canvas pages
- set Canvas front page
- create announcements
- notify parents
- mutate files/modules/assignments
- access grades, people, submissions, gradebook, analytics, or student data

## Safety Boundary

Phase 21B keeps all generated live-learning artifacts under ignored local paths:

```text
.local/canvas-llm/sandbox-learning-runs/phase-21/
```

These files are runtime evidence and must not be committed.

## Expected Decision

The Phase 21B observed decision is:

```text
EXISTING_PAGE_DRY_RUN_NEEDS_AGENT_HARDENING
```

Reason:

```text
Inventory found sandbox QxWy page candidates in course 24399, but existing-page dry-run returned:
WARN: no sandbox QxWy candidate page found
```

This means Canvas access is working, but the dry-run selector needs hardening before any sandbox write experiment.

No Canvas write is approved by this phase.
