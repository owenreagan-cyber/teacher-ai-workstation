# Phase C Host-Local Observation Architecture

## Plane boundary

```text
Policy Plane
    -> Host-Local Observation Plane (Phase C contracts only)
    -> Relationship / Recommendation Plane
    -> Future Action Plane
```

Phase C defines storage and exchange contracts. It neither observes the host
nor instantiates the storage layout.

## Proposed host-local storage

The future runtime root is `.local/chief-of-staff/workspace/`. The repository
ignore rule is exact to this subtree. A future installer must additionally
verify that the root is not synchronized and is protected with host-local
permissions before writing any observation.

| Relative folder | Purpose | Authority status |
| --- | --- | --- |
| `inventory-runs/` | Run envelopes, approvals, limits, and outcomes | Evidence only |
| `observations/` | Metadata-only snapshots from an approved run | Evidence only |
| `relationships/` | Evidence-backed, reviewable relationship candidates | Never authority |
| `recommendations/` | Reviewable proposals derived from evidence | Never an action |
| `audit/` | Append-oriented approvals, validation results, and review events | Audit evidence |
| `cache/` | Regenerable temporary data | Never authority |

The root must be gitignored, excluded from synchronization and cloud-agent
inputs, and never interpreted as source authority. Phase C creates none of
these folders.

## Observation lifecycle

```text
Observation -> Recommendation -> Approval -> Action Plan -> Execution
```

Only the contracts for observations and recommendations exist in Phase C.
Approval, action planning, and execution remain deferred. An observation uses
the physical identity `observation:<run>:<source>:<token>` and does not claim a
permanent resource identity.

## Sanitization and cloud view

Local records may contain approved-source-relative paths and operational audit
details. Absolute paths, private filenames, student data, raw contents,
document text, extracted text, OCR, embeddings, credentials, unrestricted
observations, and filesystem handles are forbidden exports.

A cloud-safe view is a new projection, not a copy of the local record. It may
contain sanitized metadata, classifications, reviewed relationships, and
recommendations. Relative paths are disclosed only when a rule explicitly
allows their segments; otherwise a stable opaque token is used. Every export
requires policy validation, classification, redaction, and an audit event.
Cloud agents receive no filesystem access.

## Retention

Retention is declared in `registry/retention.json`. Runtime enforcement is
disabled. Future enforcement must use reviewed disposition states, preserve
required audit evidence, and never infer authority from age or retention.
Cache is short-lived and regenerable. Reviewed and rejected recommendations
retain their decision history. No deletion is authorized by these contracts.

## Security invariants

- Observation data is evidence, not authority.
- An observation cannot overwrite a registry or create a canonical claim.
- A recommendation cannot authorize or execute an action.
- Missing approval, scope, classification, freshness, or sanitization fails closed.
- Content reads, hashing, symlink traversal, source escape, cloud downloads,
  writes, and unrestricted recursion are prohibited by the run contract.
- Student-private, restricted, and unknown-sensitivity data cannot enter a
  cloud-agent view.

## Compatibility roadmap

- Phase D implements one explicitly approved metadata-only History pilot.
- Phase E implements one explicitly approved History project-metadata pilot.
- Phase F implements one explicitly approved Grade 4 Writing application pilot.
- Phase G derives relationships only from three fixed existing evidence artifacts.
- Phase H defines synthetic-only recovery intelligence without detecting missing
  resources or promoting backups to authority.
- Phase I defines and tests a synthetic sanitized AI compatibility projection;
  AI connection and raw host-data export remain disabled.
- Phase J queries only two static registries and the exact approved Phase D/E/F/G
  artifacts. It makes no new observation, performs no discovery, and persists
  no query result. Its explanation output can be checked by the disconnected
  Phase I sanitizer without invoking an AI model.
- Phase K formats Phase J output in a local CLI and derives a non-persistent
  human-review queue in memory. It adds no observations, review mutations,
  persistent service, source access, or action capability.
- Phase L defines only synthetic contracts above the sanitized explanation
  boundary. Raw observations remain excluded, audit logging is disabled, and no
  model, network, agent, tool, approval, or action runtime is connected.

Each phase needs a separate mission, scoped approval, stop points, validation,
and audit behavior. These contracts do not grant that authority.
