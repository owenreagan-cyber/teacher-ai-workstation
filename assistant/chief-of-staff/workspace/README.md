# Personal Workspace Intelligence — Policy and Observation Contracts

```text
Status: Phase L.5G one separately authorized v2 execution path
Runtime inputs: two static registries plus four fixed Phase D/E/F/G evidence artifacts
Workspace-wide scanning: disabled
Action execution: disabled
```

Personal Workspace Intelligence is the Chief of Staff federation layer. It
describes what may eventually be observed and how existing registries relate;
it is not a file database, cleanup utility, second Resource Registry, or second
Teacher Knowledge Vault.

## Contents

| Path | Purpose |
| --- | --- |
| `AUTHORITY.md` | Ownership, authority, identity, and permanent safety boundaries |
| `registry/` | Static workspace, storage, application, project, classification, and permission policy |
| `schemas/` | Closed JSON contracts for the static registries |
| `OBSERVATION-ARCHITECTURE.md` | Phase C storage, privacy, retention, and security design |
| `validate.py` | Dependency-free Phase B schema and cross-registry validation |
| `validate_observation.py` | Dependency-free Phase C contract and policy validation |
| `sanitization.py` | Pure synthetic-record sanitization helper; performs no I/O |
| `pilot.py` | Bounded metadata-only primitives for the fixed History pilot |
| `run_history_pilot.py` | Executes the single approved source with no scope arguments |
| `validate_pilot.py` | Validates the pilot definition and an explicitly named local run |
| `PROJECT-PILOT.md` | Phase E identity, Git safety, evidence, and local-output boundary |
| `project_pilot.py` | Five-operation read-only Git metadata implementation |
| `run_project_pilot.py` | Executes the fixed History project observation |
| `validate_project_pilot.py` | Validates Phase E policy and one explicit local run |
| `APPLICATION-PILOT.md` | Phase F scope, identity, metadata, and security contract |
| `application_pilot.py` | Exact-path, four-key application metadata implementation |
| `run_application_pilot.py` | Executes the fixed Grade 4 Writing application observation |
| `validate_application_pilot.py` | Validates Phase F policy and one explicit local run |
| `RELATIONSHIP-PILOT.md` | Phase G relationship, evidence, conflict, drift, and security contract |
| `relationship_pilot.py` | Deterministic graph construction from three fixed evidence artifacts |
| `run_relationship_pilot.py` | Executes the non-observing Phase G relationship pilot |
| `validate_relationship_pilot.py` | Validates Phase G policy and one explicit local graph run |
| `RECOVERY-PILOT.md` | Phase H recovery candidate, confidence, authority, and non-action boundary |
| `recovery_pilot.py` | Pure recovery candidate reasoning and four in-memory synthetic scenarios |
| `validate_recovery_pilot.py` | Validates Phase H policy, existing evidence, and synthetic scenarios |
| `evidence_model.py` | Shared evidence package and expected-artifact relationship contracts |
| `AI-COMPATIBILITY.md` | Phase I projection, sanitization, trust, explanation, and deferral boundary |
| `ai_compatibility.py` | Pure fail-closed allowlist projection and explanation implementation |
| `validate_ai_compatibility.py` | Validates the Phase I policy and synthetic in-memory projection |
| `QUERY-LAYER.md` | Phase J query, explanation, scope, security, and CLI contract |
| `query_layer.py` | Deterministic fixed-input entity, relationship, evidence, uncertainty, and recovery queries |
| `chief.py` | Human-readable deterministic CLI; accepts no source or discovery path |
| `validate_query_layer.py` | Validates Phase J policy, fixed inputs, outputs, security, and Phase I compatibility |
| `HUMAN-INTERFACE.md` | Phase K CLI decision, output grammar, review queue, and security boundary |
| `human_interface.py` | Reusable status, explanation, relationship, evidence, review, and recovery formatting |
| `validate_human_interface.py` | Validates Phase K formatting, review states, security, determinism, and performance |
| `AI-READINESS.md` | Phase L capability, trust, routing, context, prompt, validation, audit, approval, and agent architecture |
| `ai_readiness.py` | Pure synthetic contract helpers and fail-closed output checks; no model or network runtime |
| `validate_ai_readiness.py` | Validates all Phase L architecture boundaries with in-memory synthetic records |
| `AI-CONTEXT-ADAPTER.md` | Phase L.5D context package, local-model request, response validation, and audit boundary |
| `ai_context_adapter.py` | Pure explanation-to-context adapter and structured response checks; no model connector |
| `validate_ai_context_adapter.py` | Validates Phase L.5D determinism, sanitization, preservation, and non-execution |
| `OLLAMA-RUNTIME.md` | Phase L.5E loopback policy, prompt, runtime, failure, audit, and live-test boundary |
| `ollama_runtime.py` | One-attempt Ollama transport and existing-response validation adapter |
| `run_controlled_ollama_explain.py` | Fixed Grade 4 Writing entity runner; no arguments or persistence |
| `validate_ollama_runtime.py` | Synthetic-only Phase L.5E endpoint, model, prompt, failure, and safety validation |
| `GROUNDING-CONTRACT.md` | Phase L.5F v1 audit, versioned v2 contract, cardinality, diagnostics, and renderer |
| `grounding_contract.py` | Closed-vocabulary validator, safe diagnostics, and deterministic renderer |
| `validate_grounding_contract.py` | Synthetic-only Phase L.5F round-trip and contract-consistency validation |
| `SECOND-CONTROLLED-EXECUTION.md` | Phase L.5G one-request gates, outcome, audit, and non-persistence boundary |
| `controlled_execution.py` | Deterministic pre-live gate, finalizer, renderer handoff, and safe audit |
| `run_second_controlled_ollama_explain.py` | Fixed no-argument Phase L.5G runner with one execution call site |
| `validate_second_execution.py` | Synthetic-only Phase L.5G gate and outcome validation |
| `tests/fixtures/` | Fictional negative and positive policy cases |
| `tests/test_workspace_policy.py` | Self-contained static-policy tests |
| `tests/test_observation_contracts.py` | Synthetic Phase C contract and sanitization tests |

## Validation

From this directory:

```bash
python3 validate.py
python3 validate_observation.py
python3 validate_pilot.py
python3 validate_project_pilot.py
python3 validate_application_pilot.py
python3 validate_relationship_pilot.py
python3 validate_recovery_pilot.py
python3 validate_ai_compatibility.py
python3 validate_query_layer.py
python3 validate_human_interface.py
python3 validate_ai_readiness.py
python3 validate_ai_context_adapter.py
python3 validate_ollama_runtime.py
python3 -m unittest discover -v -s tests -p 'test_*.py'
```

Validation reads only explicitly named files in this policy directory. It does not
inspect the machine, resolve locator references, connect storage, inspect Git,
or inspect application bundles.

Phase J additionally reads the exact already-created Phase D/E/F/G host-local
artifacts pinned by `registry/query-policy.json`. It cannot select a source,
enumerate a directory, or update an observation.

## Phase C boundary

Phase B registries remain static. Phase C adds contracts for future host-local
observations and uses fictional fixtures only. The proposed runtime root,
`.local/chief-of-staff/workspace/`, is gitignored and was not created by Phase C.
Phase C added no scanner, action gateway, content reader, hashing, network
access, recommendation generation from real data, or background work. Phase D
uses that boundary only for its single approved pilot.

## Phase D pilot

Phase D permits one explicit metadata-only run against
`/Users/owen/Projects/history`. The implementation has no argument for choosing
another source. It skips hidden entries, never follows symlinks, does not read
`.git`, performs no Git command, reads no file contents, and collects no hashes.
Depth is capped at 2, observations at 500, and duration at 60 seconds. Output is
written only beneath the ignored host-local boundary. No recommendation or
action is produced.

## Phase J query layer

Phase J builds an in-memory read-only projection from the two approved static
registries and the exact Phase D/E/F/G artifacts. It supports closed entity,
project, application, resource, relationship, evidence, and recovery-candidate
queries; explicit scope filters; explanations; and uncertainty review. Unknown
remains unknown, restricted data requires a fixed explicit read grant, and all
outputs declare no action authority. It performs no new observation, source
inspection, AI inference, recovery operation, or persistence.

## Phase K human interface

Phase K presents the Phase J model through the six-command `chief` CLI. A
reusable formatter makes known facts, evidence, confidence, uncertainty,
authority, review state, and the no-action boundary explicit. Status adds
component health and available-system summaries. The uncertainty command adds
a deterministic, non-persistent human-review queue with five distinct review
states. Phase K adds no web service, AI, natural-language interpretation,
authentication, source access, review mutation, or action execution.

## Phase L AI readiness

Phase L defines future reasoning capabilities, trust levels 0–4,
deterministic-first model routing, local/cloud policy, context projection,
prompt construction, output validation, hallucination handling, AI interaction
audit fields, human-only decisions, and future agent capability grants. All
examples are synthetic and in memory. Trust level 0 is the only current state;
no model or provider is selected, and AI, network, agents, tools, actions,
exports, approvals, and audit logging remain disabled.

## Phase L.5D local AI context boundary

Phase L.5D turns an existing deterministic entity explanation into a closed,
sanitized `AIContextPackage` by reusing the Phase J query, explanation, and
evidence methods plus the Phase I fail-closed policy. It records the approved
Ollama/Qwen stack as a non-connected request contract and validates structured
synthetic explanation candidates for evidence, confidence, uncertainty,
authority, review state, and action isolation. Only `explain` is represented.
No model invocation, connector, prompt transport, host-local AI data, output
persistence, agent, tool, application access, filesystem access, or action exists.

## Phase L.5E controlled Ollama runtime

Phase L.5E permits one narrow local execution path: the fixed Grade 4 Writing
entity is resolved through existing deterministic APIs, its validated
`AIContextPackage` is sent to `qwen3.5:35b` through loopback-only Ollama, and the
structured response is accepted only after the Phase L.5D validator passes it.
The adapter permits one attempt with a 120-second timeout. It cannot start the
runtime, pull or substitute a model, retry, route to cloud, expose tools or
vision, access sources, persist output or hidden reasoning, or execute actions.

## Phase L.5F grounding contract alignment

Phase L.5F keeps the v1 prose response for compatibility and adds a separately
versioned `local-model-response.v2` contract for future runtime use. The model
selects exact known, evidence, and uncertainty references; relationships and all
action-like fields remain empty. Safe in-memory diagnostics identify structural
violation codes without retaining rejected prose. A deterministic renderer owns
human-readable factual wording. Prompt/schema consistency and a full synthetic
Writing Launcher round trip are validated without contacting Ollama.

## Phase L.5G second controlled execution

Phase L.5G adds a deterministic pre-live gate and safe result finalizer around
the existing v2 runtime path. The gate proves current context, sanitization,
reference cardinality, schema, grounding, renderer, prompt consistency, and
runtime policy before any request. The no-argument runner has one execution call
site. Accepted refs are rendered from deterministic context; rejection exposes
only safe codes. Audit data remains in memory and no response is persisted.

## Phase E pilot

Phase E observes the same fixed History root as a software project. It records
root existence plus five allowlisted Git metadata results: repository detection,
root verification, current branch, HEAD, and a count-only dirty summary. Git
optional locks are disabled. Source contents, README files, manifests,
dependencies, commit messages/history, other branches, and status filenames are
not stored. Project state remains evidence requiring review; no abandonment,
importance, recommendation, relationship authority, or action is inferred.

## Phase F pilot

Phase F observes exactly `/Users/owen/Applications/Grade 4 Writing.app`. It uses
root metadata plus four allowlisted Spotlight attributes: display name,
bundle identifier, version, and content type. It does not enumerate applications
or the bundle, read `Info.plist`, inspect signing, access containers or private
data, launch code, or modify the installed application. Relationship output is
candidate evidence only.

## Phase G pilot

Phase G reads only three explicitly named host-local artifacts already produced
by Phases D, E, and F. It does not scan or observe a source. It constructs eight
evidence-backed nodes, six relationship candidates, and one evidence package per
candidate. All candidates are inferred, high-confidence, unreviewed, and have
no authority, ownership, permission, or action effect. Conflict handling records
competing claims without choosing; drift handling preserves prior relationships.
Outputs remain under ignored `relationships/` and `audit/` folders.

## Phase H architecture

Phase H defines missing/changed signals, recovery candidates, recovery evidence
packages, review recommendations, conflicts, confidence assessment, and recovery
audit events. It reads only the four exact D/E/F/G artifacts during validation and
uses them in four in-memory synthetic scenarios. Live signal detection, live
candidate generation, host-local recovery output, scanning, restoration, and all
file actions are disabled. An insufficient-evidence scenario produces no candidate
and no recommendation.

## Phase H enhancements and Phase I architecture

The Phase H evidence model now normalizes relationship, project, application,
recovery, classification, authority, and availability claims through one shared
contract. Recovery candidates carry risk independently from confidence, a required
explanation, and support `candidate_changed`. Expected-artifact relationships state
what a resource normally produces without claiming the artifact exists.

Phase I adds a synthetic-only AI compatibility projection. It is a generated
allowlist view, not a copy of internal records. It rejects path, filename,
credential, student/private, raw-observation, authority-effect, and action-capability
leakage. Identity, authority, confidence, review state, evidence summaries, and
uncertainty remain visible. No AI service, agent, tool, export, or persisted view
exists.
