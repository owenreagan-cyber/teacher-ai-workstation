# Proposals

Last updated: 2026-07-02

## Purpose

Persistent proposal ledger for Teacher Workstation feature and improvement ideas. Chat history is not the source of truth — `docs/proposals/index.md` is.

## Workflow

```text
Cursor proposal → ChatGPT review → Owen Reagan approval → scoped implementation prompt → Cursor implementation
```

## States

See `docs/cursor-operating-modes-and-approval-gates.md` for lifecycle states and approval levels.

## Adding a Proposal

1. Check `index.md` for near-duplicates
2. Add a row to the ledger table in `index.md`
3. Optionally add a detail file under `docs/proposals/<slug>.md` when the idea needs more than one table row
4. Do not implement until approval level reaches `approved_for_implementation` or higher as required

## File Layout

| Path | Purpose |
| --- | --- |
| `docs/proposals/index.md` | Canonical ledger table |
| `docs/proposals/<slug>.md` | Optional detail files |
