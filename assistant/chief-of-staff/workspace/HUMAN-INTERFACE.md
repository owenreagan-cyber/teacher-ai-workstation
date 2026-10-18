# Phase K Human Interface Layer

## Decision

Phase K implements the CLI first. The existing six-command surface already
maps directly to the deterministic Phase J model, works without a service, and
keeps every boundary visible in ordinary terminal output. A local web interface
would add a server lifecycle and another presentation stack without adding new
intelligence, so it is deferred.

The repository-local invocation is:

```bash
python3 chief.py <command>
```

The parser and interface contract name the command `chief`. Phase K does not
install a system-wide executable or change shell configuration.

## Commands

| Command | Human view |
| --- | --- |
| `chief status` | Component health, available systems, known entities, review count, authority, validation, and actions |
| `chief explain <entity>` | Identity, known facts, sources, evidence, relationships, confidence, authority, review state, unknowns, and actions |
| `chief related <entity>` | Related entities, direction, relationship type, evidence, confidence, uncertainty, and no-authority boundary |
| `chief evidence <entity>` | Evidence packages, source/observation labels, provenance, confidence, review, uncertainty, and actions |
| `chief uncertain` | Deterministic human-review queue for conflicts, unknown authority, missing evidence or representations, recovery candidates, and unreviewed relationships |
| `chief recovery <entity>` | Candidate representations, evidence, confidence, risk, next step, and explicit non-execution boundary |

Every command also supports `--json`. Entity commands preserve the Phase J
scopes and restricted-data grant. Relationship and evidence queries keep their
deterministic filters. `chief uncertain --review-state <state>` filters the
presentation without modifying the underlying record.

## Output grammar

Human output uses stable uppercase sections rather than prose inference. The
reusable formatter separates:

- identity and known claims
- sources and evidence
- relationships and provenance
- confidence
- authority
- review state
- unknowns
- recommendations
- actions

An empty section says that no item is known. It never invents a replacement.
Unknown entities remain readable unknown explanations rather than command
failures.

## Status

Status loads the same fixed contracts and inputs as Phase J. It reports health
for Resource Registry, Workspace Model, Relationships, and Recovery. “OK” means
the relevant deterministic contract loaded and the component remains within its
declared boundary; it does not mean that uncertainty has been resolved.

Validation status is the result of constructing and schema-validating the
in-memory interface view. It does not execute another process, scan a source, or
write a validation record.

## Human review queue

The queue consolidates review opportunities from the Phase J uncertainty
explorer and unreviewed Phase G relationships. Items include a reason, evidence
references, confidence, review state, and recommended next step. Recommendations
have `recommendation_state: not_an_action`, `authority_effect: none`, and
`action_authority: none`.

Supported review states are:

- `unreviewed`
- `reviewed`
- `approved`
- `rejected`
- `deferred`

Review state and evidence confidence remain independent. Phase K can represent
and filter these states, but it does not implement transitions, approvals, or
record mutation.

## Security boundary

`registry/interface-policy.json` disables the web interface, persistent
services, natural-language interpretation, AI, source writes, and every action
capability. Restricted records still require the exact Phase J read grant.
The formatter receives already-bounded metadata; it cannot select paths, inspect
new sources, launch applications, or execute recovery.

## Deferred

Web UI, chatbot behavior, natural-language intent handling, LLMs, agents, tool
calling, persistent review state, approval operations, authentication, service
daemons, application launch, file management, recovery execution, and workflow
automation remain unbuilt.

## Phase L boundary

Phase L may consume the same deterministic explanations only after the Phase I
sanitizer creates a closed context projection. The human interface does not send
prompts, route models, display model output, or expose an AI command. Phase K
remains fully usable at trust level 0 with no AI.
