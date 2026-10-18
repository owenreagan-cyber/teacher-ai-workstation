# Phase L AI Readiness Architecture

## Boundary

Phase L defines how a future AI could receive Chief of Staff evidence. It does
not install, select, connect, or call a model. It adds no agent framework, tool
runtime, network path, filesystem handle, prompt transmission, action gateway,
or persistent AI audit log.

AI is a non-authoritative reasoning layer above deterministic evidence and
explanation:

```text
Chief of Staff model
    -> evidence
    -> deterministic explanation
    -> sanitized AI context projection
    -> bounded prompt envelope
    -> future approved model (not connected)
    -> output validation
    -> human review
```

AI never routes directly to the filesystem, authority system, permissions,
recovery, or actions.

## Capability model

Potential reasoning capabilities are `summarize`, `explain`, `compare`,
`prioritize`, `draft`, `plan`, and `identify_patterns`.

The restricted set is `modify`, `delete`, `restore`, `move`, `replace`,
`approve_authority`, and `change_permissions`. Listing a restricted capability
defines the boundary; it does not grant it. These operations remain outside AI
authority and require future scoped capability, approval, audit, and execution
architectures.

## Trust levels

| Level | Name | Phase L state | Boundary |
| --- | --- | --- | --- |
| 0 | No AI | Current | Deterministic Chief of Staff only |
| 1 | Explanation Assistance | Planned | Summarize, explain, or compare approved context; no state or authority change |
| 2 | Planning Assistance | Planned | Evidence-grounded drafts, plans, prioritization, and pattern identification; human review required |
| 3 | Scoped Agent Assistance | Future only | Requires a grant, target scope, duration, approval, rollback, and audit |
| 4 | Autonomous Operations | Prohibited | Requires separate architecture and explicit future approval |

Only Level 0 is current. Levels 1 and 2 are contracts, not enabled services.
Levels 3 and 4 grant no capability in Phase L.

## Deterministic-first routing

```text
User request
    -> Chief of Staff
    -> deterministic answer available?
       -> yes: return deterministic explanation
       -> no: require trust level above 0
              -> require approved context projection
              -> require approved model route
              -> future model
              -> output validation
              -> human review
```

The Phase L router can return `deterministic_explanation`,
`ai_unavailable`, `context_projection_required`, or `ai_runtime_disabled`.
It cannot return a model invocation. The approved model list is empty and the
provider is `unselected`.

## Local and cloud policy

Local AI is architecture-only. Future uses may include sensitive metadata
reasoning, private workspace assistance, and offline work, but require local
permission, bounded resources, context projection, output validation, and
audit.

Cloud AI is architecture-only. Future use is limited to sanitized reasoning,
general planning, and non-sensitive analysis. It additionally requires human
cloud-export approval, the sanitized AI view, no raw paths, no private records,
and no student data.

No model or provider is selected for either route.

## Context projection

`AIContextProjection` is built only from the Phase I sanitized compatibility
view. It contains:

- identity and safe labels
- source-system references
- evidence summaries and provenance
- bounded relationships
- confidence
- explicit uncertainty
- authority state
- review state
- deterministic classification

It excludes credentials, secrets, unrestricted paths, private documents,
student data, raw observations, and action capabilities. Its nested entity,
evidence, and relationship objects are closed schemas. Absolute paths and
blocked classifications fail closed before projection.

## Prompt boundary

`AIPromptEnvelope` has four explicit sections:

1. System context: non-authoritative role, restrictions, and authority boundary
2. Evidence context: projected facts, provenance, confidence, and uncertainty
3. User request: the actual bounded request
4. Required output: claim-type separation, citations, uncertainty, and no unsupported assumptions

The envelope grants only reasoning capabilities allowed by its planned trust
level. It has `runtime_state: not_connected` and `action_authority: none`.
Unsafe paths or restricted action capabilities fail validation.

## Output validation and hallucination handling

Every future output candidate must label each claim as `known`, `evidence`,
`inference`, `unknown`, or `recommendation`. Non-unknown claims require valid
evidence citations. A claim cannot report stronger confidence than its weakest
cited evidence.

Validation rejects unsupported claims, uncited known claims, authority changes,
hidden action language, confidence inflation, and missing uncertainty. An
inference never becomes a fact merely because a model stated it. Missing
evidence becomes `unknown`; unsupported claims are rejected.

The validator produces errors only. It neither repairs a response nor executes
a recommendation.

## Audit contract

`AIInteractionAudit` defines the future record fields: request identity, model,
context projection, trust level, granted capabilities, input classification,
output-validation result, and human-review result.

Phase L creates only an in-memory synthetic record with model `unselected`,
`execution_state: not_executed`, and `persisted: false`. Audit logging remains
disabled.

## Human approval boundary

These decisions always remain human:

- authority changes
- canonical replacement
- restore and delete
- movement of canonical resources
- permission changes
- cloud export approval

AI may eventually assist with summaries, explanations, prioritization, drafts,
and planning. Phase L has no approval runtime.

## Future agent permission contract

The future sequence is:

```text
Agent -> Capability Grant -> Scope -> Approval -> Execution -> Audit
```

`AgentCapabilityGrant` requires an allowed action, exact target scope, bounded
duration, human approval state, rollback plan, and audit requirement. The Phase
L form is always `architecture_only`, non-autonomous, non-executable, and has no
action authority. It cannot be used as an operational grant.

## Deferred

Model selection, model installation, local or cloud inference, provider APIs,
network access, agents, tools, RAG, embeddings, vector stores, prompt sending,
audit persistence, filesystem access, recovery execution, and autonomous
operations remain unbuilt.

## Phase L.5D context boundary

Phase L.5D adds a contract-only local route beneath this architecture without
activating the Phase L router. `build_ai_context(entity_id)` consumes the
existing deterministic query, explanation, relationship, and evidence outputs,
then applies the Phase I compatibility policy to create a closed
`AIContextPackage`. Identical fixed inputs produce an identical package.

The owner-approved Ollama/Qwen stack is named in `LocalModelRequest`, but its
connector and execution fields remain disabled. Only `explain` is represented;
capabilities are explicit, actions are empty, and the model has no workspace,
application, filesystem, launch, permission, or mutation access.

Structured response candidates must preserve confidence, uncertainty,
authority, and review state exactly. Deterministic validation rejects unsupported
claims, action language, invented access or authority, and confidence inflation.
Validation and audit records remain synthetic, in memory, unexecuted, and
unpersisted. See `AI-CONTEXT-ADAPTER.md`.

## Phase L.5E narrow runtime exception

Phase L.5E does not activate the general Phase L router, cloud policy, planned
trust levels, agent architecture, or action architecture. It authorizes one
separate fixed path for the Grade 4 Writing application explanation using the
already-approved `AIContextPackage`, loopback-only Ollama, `qwen3.5:35b`, and the
existing structured response validator.

The runtime has one task, one model, one endpoint policy, one attempt, and no
fallback. It provides no tools, vision, source access, additional retrieval,
permission, action, approval, or persistence. General model selection and all
other AI routing remain unbuilt. See `OLLAMA-RUNTIME.md`.

## Phase L.5F deterministic grounding alignment

Phase L.5F narrows future model output from exact prose regeneration to closed
reference selection. Authority, confidence, review state, uncertainty coverage,
and empty action fields remain deterministically enforced. Human-readable text
is rendered only from the validated context after reference validation. This
phase performs no local or cloud inference and does not change the trust level.
