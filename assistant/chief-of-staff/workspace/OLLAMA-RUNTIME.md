# Phase L.5E Ollama Runtime Adapter

```text
Status: one controlled local explanation route
Endpoint: http://127.0.0.1:11434
Runtime: Ollama
Model: qwen3.5:35b
Task: explain
Attempts: one
Timeout: 120 seconds
```

## Scope

Phase L.5E is the first narrowly approved model-execution phase. It sends one
already-validated `AIContextPackage` and its `LocalModelRequest` to the exact
approved local model through loopback-only Ollama. The returned JSON is trusted
only if deterministic response validation accepts it. Phase L.5D retains the
original prose-oriented v1 validator; Phase L.5F aligns future runtime output to
the separately versioned closed-reference v2 validator.

The runtime adapter does not build context, query Chief of Staff, choose an
entity, inspect a source, start Ollama, pull a model, retry, select a fallback,
expose tools, execute actions, or persist model data.

## Runtime policy

`registry/local-model-runtime.json` permits only:

- HTTP over `127.0.0.1` or canonicalized `localhost`
- port `11434`
- model `qwen3.5:35b`
- task `explain`
- one attempt
- a 120-second timeout
- a 1,000,000-byte response ceiling

LAN IPs, remote hostnames, alternate ports, alternate models, alternate tasks,
cloud routing, model fallback, retry, automatic pull, and automatic startup fail
closed. The transport disables environment proxy use and canonicalizes
`localhost` to `127.0.0.1` before connecting.

The 120-second ceiling allows a bounded cold load of the approved 35B MoE model
on the approved Mac while preventing an indefinite wait. Phase L.5E does not
optimize or benchmark the setting.

## Runtime lifecycle

Preflight calls the fixed Ollama model-inventory endpoint. It confirms that the
runtime responds and that `qwen3.5:35b` is present exactly. If Ollama is stopped,
the result is `runtime_unavailable` and asks the human to start it. If the model
is absent, the result is `model_missing`; the adapter never pulls it.

The adapter never launches Ollama.app, runs `ollama serve`, controls Homebrew,
changes a LaunchAgent, or alters login items.

## Prompt boundary

The system instructions are a fixed constant. They state that the local model:

- receives approved sanitized context only
- has no filesystem, application, network, shell, tool, recovery, mutation,
  deletion, restore, or authority-changing capability
- cannot infer permissions or authority
- cannot paraphrase or create factual sentences
- must select only supplied identifiers and exact state enums
- must return only JSON with no explanation outside it

The user message contains only the validated request, the serialized sanitized
context package, the derived allowed response vocabulary, and fixed output
rules. The Ollama payload has no tools or images and sets streaming and thinking
output to false. Phase L.5F pins future requests to the separately versioned
closed-reference v2 response schema.

## Response boundary

Only `message.content` is decoded. Any Ollama thinking field is discarded and
never exposed, treated as evidence, or persisted. The final content must be one
JSON object conforming to `local-model-response.v2`.

The v2 validator must then preserve and ground:

- every supplied known reference
- every supplied evidence reference
- every supplied uncertainty reference
- exact confidence, authority, and review-state enums
- empty action, recommendation, permission, and access arrays

Relationships are excluded from the response. Trusted prose is rendered later
from the validated context, never copied from model output. Rejections carry
safe structural diagnostic codes but no rejected prose.

Malformed JSON, extra fields, missing uncertainty, invented evidence,
confidence inflation, authority changes, access claims, recommendations, and
action instructions fail closed. Rejected raw output is never returned as a
trusted explanation.

## Controlled failures

The adapter returns one of:

- `runtime_unavailable`
- `model_missing`
- `request_timeout`
- `connection_failure`
- `malformed_response`
- `schema_validation_failed`
- `grounding_validation_failed`
- `authority_violation`
- `capability_violation`

A failure contains no rejected model response. There is no automatic retry,
provider change, alternate model, cloud fallback, repair prompt, or second
generation attempt.

## Audit and persistence

The runtime result records safe timing and token-count metadata reported by
Ollama. The in-memory audit contract records request, context, runtime, model,
task, start/end time, duration, validation result, failure code, and no-action
state.

Phase L.5D does not authorize audit or output persistence, so Phase L.5E writes
neither. Raw model content and hidden reasoning are not saved beneath the repo
or the ignored host-local boundary.

## First controlled entity

`run_controlled_ollama_explain.py` has no entity or endpoint arguments. It is
fixed to `application:grade-4-writing-launcher`, builds context through existing
deterministic APIs, prints only a sanitized semantic context summary, performs
preflight, makes at most one generation request, validates the result, emits a
safe in-memory audit representation, and stops.

## Deferred

Chat, conversational memory, summarize, planning, agents, function or tool
calling, MCP, filesystem or application tools, model routing, fallback models,
cloud models, recovery execution, file organization, action gateways,
background workers, persistent queues, runtime service management, automatic
startup, and autonomous AI remain unbuilt.
