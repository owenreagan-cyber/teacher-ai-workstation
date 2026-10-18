# Phase J Deterministic Query and Explanation Layer

## Boundary

Phase J answers “What do you know?” and “Why do you know it?” from a closed
set of approved records. It reads only `registry/projects.json`,
`registry/applications.json`, and the exact Phase D/E/F/G artifacts pinned in
`registry/query-policy.json`. It does not enumerate a directory or inspect a
new source.

The layer is a projection, not a new source of truth. It never changes source
authority, converts uncertainty into fact, or exposes an action capability.
Live recovery candidate generation and AI connections are disabled.

## Query contract

`schemas/query.schema.json` defines seven query types:

- `entity_lookup`
- `relationship_lookup`
- `evidence_lookup`
- `recovery_candidate_lookup`
- `project_lookup`
- `application_lookup`
- `resource_lookup`

The supported scopes are `active`, `classroom_ready`, `teacher_only`,
`student_safe`, `restricted`, `superseded`, `all`, `unreviewed`, and
`conflicts`. Scope is a filter only; it never grants authority. Restricted
scope or a restricted entity requires the explicit
`workspace.restricted.read` grant. Unknown classification does not satisfy a
teacher-only, student-safe, or restricted filter.

Optional filters are relationship type, confidence, review state, and data
classification. Ordering is stable by entity, relationship, evidence-package,
or uncertainty identity as applicable.

## Explanation contract

`schemas/explanation.schema.json` requires:

- subject identity and type
- deterministic summary
- source labels and evidence-package references
- relationship references
- confidence and review state
- one or more explicit uncertainties
- scoped authority context
- `action_authority: none`

An unknown entity returns a valid explanation with unknown identity,
confidence, and authority. It is not an exception or failed observation.

## Relationship and evidence explorers

`related_to(entity)` returns direction, relationship type, related identity,
evidence package, provenance, confidence, and review state. It preserves the
Phase G relationship assertion and adds no ownership, permission, or action
effect.

`why(entity)` returns the fixed registry, observation, and relationship
evidence packages linked to the entity. Evidence reports provenance,
confidence, and review state. Missing evidence remains an uncertainty.

`uncertain()` exposes unknown authority, unresolved conflicts, missing
representations, unreviewed recovery candidates, and missing evidence. Every
item is a `review_opportunity_not_failure` with no action authority.

## Recovery explanations

`recovery_candidates(resource)` can display a candidate identity, evidence,
confidence, risk, review state, and next step. It has no copy, restore, replace,
move, or delete operation. The approved live model contains no candidates
because Phase H live detection and candidate generation remain disabled.
Synthetic tests exercise the explanation shape only.

## CLI

Run from this directory:

```bash
python3 chief.py explain application:grade-4-writing-launcher
python3 chief.py related project:history
python3 chief.py evidence resource:writing
python3 chief.py uncertain
python3 chief.py recovery resource:writing
python3 chief.py status
```

All commands support `--json`; entity commands also support `--scope`. The
relationship and evidence commands accept deterministic filters. Restricted
queries require `--allow-restricted`, which supplies only the fixed read grant.
The CLI does not accept source paths or discovery roots.

## Future AI compatibility

`ai_compatibility_input()` translates a validated explanation into the internal
shape accepted by the Phase I sanitizer. It does not invoke or connect an AI
model. Phase J validation passes this structure through the local fail-closed
projection solely to prove that identity, evidence, uncertainty, review state,
authority, and the no-action boundary survive. AI cannot bypass explanation.

## Deferred

Chat, natural-language inference, LLMs, agents, tool calling, RAG, embeddings,
vector storage, graph databases, caches, background workers, indexing daemons,
filesystem controls, recovery execution, organizing, cleanup, and workflow
automation remain unbuilt.

## Phase K consumer

Phase K consumes these deterministic structures through `human_interface.py`.
It adds reusable formatting, status health, and a non-persistent review queue,
but does not change Phase J evidence, confidence, authority, query scope, or
action boundaries. See `HUMAN-INTERFACE.md`.
