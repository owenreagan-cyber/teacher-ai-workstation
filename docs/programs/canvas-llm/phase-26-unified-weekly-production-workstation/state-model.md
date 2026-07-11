# State Model

Phase 26 keeps one local SQLite database at:

`.local/canvas-llm/phase-26-unified-weekly-production/workstation.db`

Tables:

- `settings`
- `week_state`
- `corrections`
- `approvals`
- `revisions`
- `exports`

State behaviors:

- approvals invalidate after edits
- corrections are local and scoped
- restart keeps saved state
- contaminated state is quarantined

