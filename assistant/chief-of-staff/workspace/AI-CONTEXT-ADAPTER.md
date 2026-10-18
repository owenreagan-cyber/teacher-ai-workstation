# Phase L.5D Local AI Context Boundary

```text
Status: contract-only; no model invocation
Task: explain only
Model contract: Ollama / qwen3.5:35b / Q4_K_M
Connector: disabled
Execution: disabled
```

## Scope

Phase L.5D creates the controlled data boundary between deterministic Chief of
Staff explanations and a future local reasoning model. It does not connect to
Ollama, invoke Qwen, create an agent, expose tools, persist prompts or outputs,
or grant any action authority.

```text
Chief of Staff
    -> deterministic query layer
    -> deterministic explanation layer
    -> existing evidence layer
    -> Phase I fail-closed sanitization
    -> AIContextPackage
    -> LocalModelRequest contract (not connected)
    -> structured response candidate
    -> deterministic AIResponseValidation
```

The model boundary consumes explanations. It cannot access the workspace,
applications, source repositories, raw observations, or host-local storage.

## Context package

`build_ai_context(entity_id)` calls the existing
`DeterministicQueryLayer.explain()`, `related_to()`, and `why()` methods. It does
not reproduce registry, relationship, evidence, confidence, or authority logic.

`AIContextPackage` contains only:

- stable entity identity, label, type, summary, and safe classification
- bounded relationships with evidence references
- evidence claims and source-system summaries
- confidence for the entity and every evidence summary
- explicit uncertainty
- authority context
- review state
- the explicit `explain` capability
- an empty action list and fixed restrictions

The package uses a fixed contract timestamp and stable identifiers so identical
approved inputs produce an identical package. Context packages exist in memory
only.

## Capability boundary

Phase L.5D implements only `explain`. Summarization, comparison, planning,
agents, tools, and actions remain outside this contract. Every package and
request has:

```json
{
  "capabilities": ["explain"],
  "actions": [],
  "action_authority": "none"
}
```

Restrictions explicitly deny filesystem, application, launch, modification,
restore, deletion, permission, cloud, and tool access. The model cannot infer a
capability from its runtime, model identity, task text, or evidence.

## Sanitization

The adapter inherits `registry/ai-trust-policy.json` and its generated allowlist
projection. Absolute and home paths, usernames, private filenames, content,
OCR, embeddings, credentials, tokens, environment variables, student data, raw
observations, private documents, and filesystem handles fail closed. Restricted,
student-private, and unknown classifications cannot become model context.

Provenance stays at the evidence-summary level. Raw observation records and raw
observation payloads are never copied into the package.

## Local model request contract

`LocalModelRequest` records the owner-approved stack identity:

- runtime: `ollama`
- model: `qwen3.5:35b`
- family: Qwen 3.5 35B MoE
- quantization: `Q4_K_M`
- task: `explain`

Naming that stack does not connect or execute it. Every request is
`connector_state: not_connected`, `execution_state: not_executed`, contains no
prompt transport, and has no actions.

## Structured output validation

The future model response contract is deliberately structured. Claims must be
one of `known`, `evidence`, or `unknown`:

- known claims must exactly match a projected entity summary and cite context evidence
- evidence claims must exactly match one evidence summary and cite that evidence identity
- unknown claims must exactly preserve a projected uncertainty and cannot assert confidence

The response must copy the context confidence, uncertainty, authority, and
review-state arrays exactly. This makes the contract deterministically
checkable without trusting free-form model prose.

Validation rejects unsupported claims, evidence-reference mismatches, invented
authority, invented permissions or access, action instructions, recommendations,
confidence inflation, missing uncertainty, and changed review state. Rejection
produces an in-memory `AIResponseValidation` record only; it does not repair,
retry, execute, or persist the response.

## Audit contract

The local audit contract contains request identity, context identity, model,
task, validation result, and creation time. It is always
`execution_state: not_executed`, `persisted: false`, and
`action_authority: none`. No runtime log or model output file is created.

## Security boundary

Phase L.5D contains no Ollama import or command, network client, provider API,
agent framework, tool-call surface, filesystem locator, application control,
mutation operation, output writer, or background process. It does not alter the
Phase L trust-level router: deterministic Chief of Staff remains the only active
runtime path.

## Deferred

The Ollama connector, model execution service, prompt transport, free-text
rendering, retry policy, runtime audit storage, chatbot, agents, tools, cloud
routing, filesystem integration, application integration, action gateway,
approvals, and autonomous workflows remain unbuilt.

## Phase L.5E runtime consumer

Phase L.5E is a separately approved, narrow runtime consumer of this contract.
It does not weaken or replace the Phase L.5D package, request, or response
validation rules. The fixed Writing entity package may be sent once to
`qwen3.5:35b` through loopback-only Ollama. The runtime adapter cannot build or
expand context, and Qwen cannot request additional context.

The model response remains an untrusted candidate until the existing
`validate_ai_response()` path accepts it. Failed output is withheld. No prompt,
raw response, hidden reasoning, audit record, or model output is persisted. See
`OLLAMA-RUNTIME.md`.

## Phase L.5F response versioning

The Phase L.5D prose-oriented response remains `schema_version: 1` and retains
its original validator. Phase L.5F adds `local-model-response.v2` for future
runtime use. V2 selects stable known, evidence, and uncertainty references and
copies only exact scalar enums. It generates no trusted factual prose. Safe
diagnostics retain codes and structural pointers only, and the deterministic
renderer resolves accepted references back through this validated context.
See `GROUNDING-CONTRACT.md`.
