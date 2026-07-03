# Autonomous Build Engine — Sprint Queue Template

Last updated: 2026-07-02

```text
Status: planning-only template
Classification: docs/status — no automatic execution
Runtime activation: no
```

## Purpose

Template for planning safe autonomous sprints. **Queue entries do not authorize implementation.** Owen approval and scoped mission prompts remain required for runtime work.

## Sprint Queue Row Template

| ID | Lane | Safe work class | Scope summary | Blocked boundaries | Validation plan | Status |
| --- | --- | --- | --- | --- | --- | --- |
| SQ-001 | [lane] | A–H per ABE governance | [docs/status/tests only] | no writes/API/network/runtime | dashboard + targeted tests | proposed |

## Rules

- Discovery findings go to proposal ledger or lane review — not straight to implementation
- Exhaustion surfaces must be checked before sprint close
- Expected WARNs must remain documented — do not weaken checks
- Production registry writes, metadata intake, integrations remain blocked unless Owen approves separately

## Related

- `docs/cursor-autonomous-build-engine.md`
- `docs/proposals/README.md`
- `docs/proposals/backlog/`
- `docs/proposals/blocked/`

## Non-Activation

This template does not start sprints, execute queues, or bypass approval gates.
