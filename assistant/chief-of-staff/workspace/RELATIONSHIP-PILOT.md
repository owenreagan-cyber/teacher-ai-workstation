# Phase G Relationship Intelligence Pilot

## Scope

The pilot answers “what belongs together?” from only these existing host-local
artifacts:

- Phase D History metadata observations and relationship-preparation evidence
- Phase E History project observation
- Phase F Grade 4 Writing application observation

Their run IDs and relative artifact paths are fixed in
`registry/pilots/relationship-intelligence-pilot.json`. The runner has no source
path, discovery, or scanning argument. It never re-observes History, Writing, an
application, or the filesystem.

## Contract

The static policy declares exactly 12 supported node types, 10 supported
relationship types, and four assertion types. The live pilot uses eight nodes:
two Projects, two Representations, one ApplicationConcept, one
ApplicationInstance, and two RegistryEntries.

Each relationship candidate must resolve both endpoints, match the explicit
node-type matrix, reference a valid EvidencePackage, declare confidence and
review state, and set authority, ownership, permission, and action effects to
`none`. Owner assertions require `owner-evidence:` evidence; registry assertions
require `registry-evidence:` evidence.

The Phase F evidence uses the phrase `Application used_by_project Project`, but
`used_by_project` is not in the approved Phase G relationship-type list. Phase G
therefore records the supported inverse:

```text
Project used_by_application ApplicationConcept
```

The normalization is stated in that candidate’s evidence package. It creates no
new authority or semantic claim.

## Conflict and drift behavior

Candidates with the same source and relationship type but different targets
produce an unresolved `relationship_conflict`. The pilot never selects a winner.
When the current target differs from a prior target, it records
`relationship_changed` and keeps the prior relationship. Synthetic tests exercise
both paths; the approved live evidence currently produces neither a conflict nor
drift event.

## Output and audit

The graph is written beneath ignored
`.local/chief-of-staff/workspace/relationships/`. Audit output is written beneath
the sibling `audit/` directory. Each accepted live candidate generates
`relationship_created` and `relationship_validated`. Conflict and review event
types are contracted but emitted only when those events actually occur.

No recommendation, cleanup, recovery, duplicate merge, graph database, vector
database, embedding, AI reasoning, background processing, source-system write,
or action execution exists in Phase G.
