# Architecture

Phase 26 uses a thin orchestration layer over the existing phase modules.

## Data flow

1. Select a canonical instructional week from Phase 22.
2. Load the Phase 24 synthetic pacing source and build prediction data.
3. Feed the prediction into Phase 25 resource resolution.
4. Load the Phase 23 production packet.
5. Combine the outputs into a workstation packet with approvals, revisions, diff, readiness, export preview, and deployment-manifest preview.

## Persistence

SQLite stores:

- week selection
- teacher corrections
- subject approvals
- revision history
- export history

Contaminated state is quarantined and replaced with a fresh database.

