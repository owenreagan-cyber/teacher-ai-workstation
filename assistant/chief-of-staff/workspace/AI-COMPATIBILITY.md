# Phase I Sanitized AI Compatibility View

## Architecture

```text
Internal Chief of Staff Model
        -> fail-closed sanitization
        -> closed metadata allowlist
        -> AI compatibility projection
        -> future reasoning boundary (not connected)
```

The compatibility view is generated, not copied. Phase I operates only on
synthetic in-memory records. It does not read raw host observations, persist a
view, transmit data, invoke a model, or enable an agent.

Phase J adds a deterministic explanation structure upstream of this boundary.
Its validation may pass already-sanitized, fixed-input metadata through the
local projection code to prove contract compatibility. It still does not
persist or transmit a view, include raw observations, or connect a model. A
future AI consumer must receive the explanation-derived compatibility view and
cannot bypass the explanation layer.

## Allowed projection

The view can contain resource types, project and application concepts,
deterministic classifications, bounded relationships, confidence, evidence
summaries, review-only recommendations, and safe metadata fields. Every entity
keeps its identity, authority context, confidence, and review state. Unknown and
unreviewed states are preserved rather than hidden.

Evidence summaries contain source-system labels, counts of evidence references,
claims, confidence, review state, and explicit uncertainty. Raw observation
records and identifiers are not copied into the summary.

## Fail-closed sanitization

Projection rejects inputs containing absolute/home paths, usernames, raw
filenames, file contents, document or extracted text, OCR, embeddings, student
data, credentials, tokens, environment variables, raw observations, private
documents, filesystem handles, and the other local-only fields already prohibited
by the Phase C sanitization policy.

Student-private, restricted, and unknown-sensitivity records fail closed. A
non-empty action-capability list or any non-`none` authority, permission, or action
effect is rejected. The resulting view always declares itself read-only,
metadata-only, non-authoritative, non-executable, and free of raw observations.

## Trust policy

Future AI may summarize, explain relationships, answer metadata questions, and
suggest reviews. It may not modify records, execute actions, change authority,
approve recovery, delete, restore, or move files. Phase I sets
`ai_connection_enabled: false` and exposes no action capabilities.

## Explanation contract

`explain()` operates only on a validated compatibility view. It reports source
systems, evidence claims, confidence, review state, uncertainty, authority
context, and `action_authority: none`. It does not consult a model or retrieve
additional data.

## Deferred

Local and cloud LLM connections, agents, tools, RAG, embeddings, vector search,
autonomous reasoning, filesystem access, raw observation export, recovery
execution, and an action gateway remain unbuilt.

## Phase L readiness consumer

Phase L treats this sanitized projection as the only permitted input to a future
AI context. It adds contracts for deterministic-first routing, prompt envelopes,
output validation, hallucination handling, audit fields, human-only decisions,
and future agent grants. These contracts remain synthetic and disconnected; no
model consumes the compatibility view. See `AI-READINESS.md`.

## Phase L.5D explanation adapter

Phase L.5D reuses this fail-closed policy after the deterministic Phase J
explanation boundary. The adapter selects a closed allowlist from
`explain()`, `related_to()`, and `why()` outputs; it never copies raw observation
records or provenance payloads. Unsafe paths, filenames, student/private data,
credentials, contents, OCR, embeddings, environment data, filesystem handles,
and blocked classifications still fail closed.

The resulting `AIContextPackage` names only `explain` and contains no actions.
Although its request contract identifies the approved local Qwen/Ollama stack,
there is no connector, model invocation, prompt transport, output persistence,
or runtime export. See `AI-CONTEXT-ADAPTER.md`.

## Phase L.5E runtime preservation

The loopback Ollama adapter accepts only a package that has already passed the
Phase I and Phase L.5D checks. It cannot query a registry, observation, source,
application, or filesystem directly. It sends the closed package without paths,
raw observations, private or student data, credentials, or action capabilities.
The model cannot expand that context or request another source. Rejected output
is not treated as evidence and is not persisted.
