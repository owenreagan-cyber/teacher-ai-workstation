# Canvas Validation Tiers

```text
Status: PHASE_0_DOCS_ONLY
Classification: validation planning
Runtime validator: blocked
```

## Tier 0 - Docs Presence

Checks that standards, boundaries, templates, and fake fixture guidance exist. Approved in Phase 0.

## Tier 1 - Fake/Local Consistency

Checks fake/local example structure against the evidence schema. Approved only as static fixture validation, not live Canvas validation.

Current implementation: `scripts/canvas-llm-fake-local-validator.sh` validates only fixed fixtures under `fixtures/canvas-llm/`.

## Tier 2 - Manual Review Readiness

Human-reviewed reports summarize candidate standards and blocked gaps. Planned only.

Current scaffold: `evidence/canvas-llm/` defines a manual/exported redacted intake location and `bin/chief-of-staff --canvas-llm-phase-2-status` verifies the scaffold and committed redacted examples. This is not automatic scanning or live Canvas validation.

## Tier 3 - Runtime Validation

Runtime validation of Canvas content is blocked. It would require separate approval, defined inputs, safe outputs, rollback/deletion expectations, and explicit Canvas/API/OAuth decisions.

## Tier 4 - Self-Healing

Self-healing is blocked. Future work may begin with recommendation-only, dry-run reports after approval. Automated repair and Canvas writes are not approved.
