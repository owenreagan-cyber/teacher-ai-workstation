# Canvas LLM Phase Plan

```text
Status: planned/frozen for runtime
Classification: documentation/status only
```

## Phase 0 - Standards Foundation

Status: complete as docs/status/fake-local scaffold.

Keep existing Canvas LLM planning foundation frozen for runtime. Confirm no Canvas API, OAuth, live reads/writes, generation, deployment, or student data. Maintain standards, evidence schema, safe data boundaries, authority/conflict policy, validation tiers, report templates, and fake/local fixture guidance.

## Phase 1 - Canvas Knowledge Sweep

Status: fake/local validator complete; live knowledge sweep not started.

Collect and summarize Canvas standards, export expectations, review states, and safety requirements as local planning docs only. No live Canvas access.

Phase 1 currently validates fake/local fixture evidence only through `scripts/canvas-llm-fake-local-validator.sh` and `bin/chief-of-staff --canvas-llm-phase-1-status`.

## Phase 2 - Manual Evidence Intake

Status: manual/exported redacted evidence intake scaffold complete; no live Canvas access.

Define manual review and export concepts using fake/local examples and Owen-provided redacted evidence only. No package generator, exporter, automatic scanner, live Canvas read, or Canvas write path. Current implementation: `evidence/canvas-llm/`, `docs/programs/canvas-llm/canvas-phase-2-manual-evidence-intake.md`, and `bin/chief-of-staff --canvas-llm-phase-2-status`.

## Phase 3 - Self-Healing Planning

Document possible self-healing checks as a future approval-gated track. No automated repair, live read, live write, or scheduler.

## Phase 4 - Reopen Gate

Any runtime phase requires an explicit Owen approval statement, named scope, allowed inputs/outputs, rollback plan, test plan, and API/OAuth/network approval if applicable.
