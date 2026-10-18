# Phase H Recovery Intelligence Candidate Architecture

## Scope

Phase H answers “what evidence suggests this resource may exist elsewhere?” It
does not detect real missing resources and cannot restore anything. Validation
reads only the exact existing Phase D, E, F, and G artifacts pinned in
`registry/pilots/recovery-intelligence-candidate-architecture.json`. There is no
source-selection argument, directory enumeration, content reading, hashing,
cloud or backup connection, or output-writing path.

## Contracts

`MissingResourceSignal` supports availability changes, relationship changes,
authority conflicts, missing representations, and unavailable sources. Every
Phase H signal is explicitly `synthetic_only` and is interpreted as a review
opportunity rather than a failure.

`RecoveryCandidate` supports:

- `same_resource_candidate`
- `alternate_representation_candidate`
- `backup_candidate`
- `mirror_candidate`
- `archive_candidate`
- `previous_version_candidate`
- `unknown_candidate`

Each candidate references a `RecoveryEvidencePackage`, declares confidence and
authority context, remains unreviewed, and has `action_state: not_an_action` plus
`authority_effect: none`. The recovery package embeds the shared evidence contract
used by relationship, project, application, recovery, classification, authority,
and availability claims.

## Evidence and confidence

Evidence packages explain why a candidate exists, why it may relate to the
subject, and what remains unknown. Deterministic confidence rules are:

- High: representation/backup/mirror relationships, registry or Knowledge Vault
  references, and explicit backup/mirror/archive authority declarations.
- Medium: project, deployment, version, or application observation evidence.
- Low: filename similarity or weak structural evidence alone.
- Unknown: insufficient evidence.

A declared evidence strength cannot override these rules. In particular,
filename similarity marked “high” still assesses as low.

## Risk and explanation

Recovery risk is assessed separately as low, medium, high, or unknown. Its inputs
are authority ambiguity, candidate age, sensitivity, provenance completeness,
relationship conflicts, and scope uncertainty. High confidence never implies low
risk. Student-private/restricted sensitivity, missing provenance, or conflicts
produce high risk; unresolved but non-critical context can produce medium or
unknown risk.

Every candidate explains why it was found, its supporting evidence, what remains
unknown, and that the only next step is review.

## Expected artifacts and drift

`expected_artifact_of` records an expected artifact type, evidence source,
confidence, and review state. Synthetic Math Lesson 27 examples cover presentation
PDF, HTML presentation, and teacher notes. `existence_claim` remains `none`.

The signal model also supports `candidate_changed`. A changed candidate remains a
review opportunity, not a failure, and does not trigger recovery.

## Authority and recommendations

Backup candidates must retain `backup` authority in `backup_recovery` scope.
Mirror and archive candidates retain their roles. `canonical_promotion` is always
false, and timestamp-only canonical claims fail validation.

Recommendations contain only `review_candidate`. They cannot copy, move,
replace, restore, delete, or approve an action. Insufficient evidence produces
neither a candidate nor a recommendation.

## Synthetic scenarios

Four in-memory scenarios validate the architecture:

1. A hypothetical missing representation with an existing Phase G relationship.
2. A fictional explicit backup declaration.
3. Two fictional competing recovery candidates, recorded unresolved.
4. Insufficient evidence, yielding unknown confidence and no recommendation.

Candidate creation, candidate validation, and conflict audit events are generated
for the scenarios. Review events are contracted and tested, but no review event is
fabricated. No host-local Phase H output is created.

## Deferred

Filesystem, Downloads, Documents, Desktop, cloud, NAS, backup, and home-directory
scans remain forbidden. Recovery execution, duplicate comparison, synchronizing,
organizing, cleanup, AI similarity, embeddings, graph databases, background work,
and action agents remain unbuilt.
