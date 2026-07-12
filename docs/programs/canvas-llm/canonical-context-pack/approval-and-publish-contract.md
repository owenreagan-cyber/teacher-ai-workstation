# Approval and Publish Contract

## Purpose

This contract governs comparison, safety diff, dependency analysis, approval, deployment preparation, transport, verification, rollback planning, and audit history.

It preserves the safety architecture established in Phases 26 and 27.

## Fundamental distinctions

```text
Save is not approval.
Approval is not publish.
Export is not publish.
Preview is not publish.
A successful request is not verified deployment.
```

Local persistence must never be labeled as Canvas publication.

## Current implementation boundary

Phase 27 is:

```text
read-only
preview-only
mutation-blocked
```

Every mutating Canvas transport method must currently fail closed.

No frontend, alternate local service, script, experimental bridge, or future UI may bypass this boundary.

## Artifact lifecycle

Canonical lifecycle:

```text
teacher edit
→ saved local revision
→ generated artifact
→ resource resolution
→ validation
→ Canvas snapshot
→ matching
→ safety diff
→ dependency graph
→ teacher review
→ revision-bound approval
→ controlled transport
→ read-back verification
→ ledger event
```

The controlled mutation stages remain future work until explicitly approved.

## Weekly plan states

Existing weekly-state vocabulary includes:

```text
not_started
in_progress
ready_for_review
approved
scheduled
partially_deployed
deployed
needs_revision
archived
```

A week must not enter `deployed` solely because local generation or export succeeded.

## Comparison status vocabulary

Current Phase 27 comparison states:

```text
CREATE
UPDATE
UNCHANGED
BLOCKED
CONFLICT
OMIT
DELETE_CANDIDATE
```

Older documents may use terms such as `NEW` or `NO_CHANGE`.

The implemented Phase 27 vocabulary above is authoritative for the safety-diff layer.

## CREATE

Meaning:

```text
No matching current Canvas object exists.
```

Required action:

```text
Review new object before approval.
```

A CREATE result does not authorize a write.

## UPDATE

Meaning:

```text
One matching current Canvas object exists and differs from canonical local state.
```

Required action:

```text
Review exact differences before approval.
```

The UI must show the teacher what will change.

## UNCHANGED

Meaning:

```text
A matching object exists and canonical content is equivalent.
```

Required action:

```text
No write.
```

UNCHANGED objects must not be republished merely to make an operation count appear successful.

## BLOCKED

Meaning:

```text
The operation cannot safely proceed.
```

Examples:

- archived target course;
- unresolved assignment due time;
- missing required resource;
- blocked or private resource;
- failed dependency;
- stale snapshot;
- prohibited target;
- missing target metadata;
- preview-only transport.

BLOCKED objects cannot be approved.

## CONFLICT

Meaning:

```text
Matching or intended action is ambiguous.
```

Examples:

- multiple plausible Canvas matches;
- conflicting local identities;
- uncertain target course;
- incompatible revisions;
- uncertain title or route.

No automatic choice is permitted.

CONFLICT objects cannot be approved.

## OMIT

Meaning:

```text
Canonical policy says no operation should occur.
```

Examples:

```text
History assignment generation disabled
Science assignment generation disabled
```

OMIT is not a failure and must not be converted into CREATE.

OMIT objects cannot be approved.

## DELETE_CANDIDATE

Meaning:

```text
A remote object may no longer have a corresponding current local artifact.
```

This status is informational and review-only.

Automatic deletion is prohibited.

DELETE_CANDIDATE objects cannot be approved through the normal publish path.

## Non-approvable statuses

The following statuses are non-approvable:

```text
BLOCKED
CONFLICT
OMIT
DELETE_CANDIDATE
```

`UNCHANGED` requires no mutation approval.

## Canvas snapshot

Every comparison and approval must be based on a specific Canvas snapshot.

Required snapshot fields:

```text
snapshotId
generatedAt
origin
remoteObjects
```

Snapshot metadata must remain local and safe.

## Snapshot freshness

Snapshot freshness must be classified.

Possible conceptual states:

```text
fresh
aging
stale
missing
invalid
```

Blocking freshness states must prevent approval and publication.

A new snapshot invalidates approvals bound to the prior snapshot.

## Safety diff

Each local artifact receives a safety-diff record containing:

```text
objectId
objectType
subject
targetCourse
comparisonStatus
approvalState
blockers
recommendedAction
matchedRemoteObject
dependencies
```

The safety diff must derive from real:

```text
matching
canonical policy
resource state
due-time state
course routing
snapshot freshness
dependency state
```

Fixture-provided readiness fields must never determine production readiness.

## Dependency graph

Dependency edges use:

```text
dependent → dependency
```

Examples:

```text
announcement → verified page
page → verified assignment URL
module item → created page
newsletter announcement → verified newsletter page
```

The graph must detect:

```text
cycles
missing dependencies
duplicate edges
transitive blockers
```

Anything depending on a:

```text
BLOCKED
CONFLICT
OMIT
missing
cyclic
```

object becomes blocked.

## Approval identity

Approval binds to the exact tuple:

```text
objectId
manifestRevision
snapshotId
```

Approval should also preserve:

```text
contentHash
approvedBy
approvedAt
```

A changed revision or snapshot produces no matching active approval.

## Approval scope

Approval is artifact-specific.

Examples:

- approving an assignment does not approve its page;
- approving a page does not approve its announcement;
- approving the newsletter does not approve its update announcement;
- approving one Reading artifact does not approve Spelling;
- approving a combined Reading/Spelling announcement does not approve the underlying assignments.

## Approval invalidation

Approval must be invalidated by:

- teacher edit;
- regenerated content;
- changed title;
- changed body;
- changed resource;
- changed due date;
- changed announcement schedule;
- changed target course;
- changed verified URL;
- changed dependency;
- new manifest revision;
- new Canvas snapshot;
- stale snapshot classification;
- calendar disruption;
- conflict detection;
- failed post-write verification.

## Revoke approval

The teacher must be able to revoke approval manually.

Revocation must:

- be recorded in the ledger;
- preserve prior approval history;
- make the artifact non-approvable until reviewed again;
- not delete the artifact.

## Deployment manifest

The deployment manifest should include:

```text
manifestId
weekCode
revision
status
targetSnapshotId
targetSnapshotGeneratedAt
operations
approvals
dependencies
rollbackPlan
sources
payloadHash
```

Manifest status must remain blocked when:

- snapshot freshness blocks readiness;
- safety-diff failures exist;
- dependency failures exist;
- required approvals are absent;
- due-time blockers remain;
- transport is unavailable.

## Manifest revision behavior

Every material artifact or operation change must create a new manifest revision.

Older manifest approvals must not transfer automatically.

The ledger must reject attempts to act on an older revision when a newer revision exists.

## Idempotency

Every planned mutation must have a stable idempotency identity derived from:

```text
local object ID
target course
object type
manifest revision
canonical payload hash
```

Retries must not create duplicate assignments, pages, announcements, or module items.

## Current transport classes

Current Phase 27 transport concepts include:

```text
DisabledCanvasTransport
SnapshotCanvasTransport
InMemoryCanvasTransport
gated live read-only transport
```

All mutating methods remain rejected.

## Prohibited current operations

Current blocked mutation methods include conceptual operations such as:

```text
create_assignment
update_assignment
create_page
update_page
publish_page
set_front_page
create_announcement
update_announcement
publish_announcement
delete_object
```

No alternative write path may be added without a separately approved phase.

## Future controlled write transport

A future mutation-capable transport must require:

```text
explicit enablement
correct environment
current target verification
fresh snapshot
valid manifest revision
valid artifact approval
resolved dependencies
idempotency key
ledger recording
post-write verification
fail-closed behavior
```

It must expose only narrowly approved operations.

## Deployment ledger

The canonical local ledger is SQLite under ignored `.local/...`.

It records:

```text
snapshot imports
manifest revisions
approvals
approval revocations
approval invalidations
deployment attempts
verification events
health events
ledger events
```

## Ledger location

The ledger path must be anchored to the repository root.

It must not depend on the current shell working directory.

This prevents accidentally reading or writing a different stale ledger.

## Append-only event history

Ledger event history must be append-only.

Existing events must not be updated or deleted.

Corrections must be represented by later events such as:

```text
approval-revoked
approval-invalidated
deployment-failed
verification-failed
manual-review-required
```

## Sensitive data boundary

The ledger must not store:

- Canvas API tokens;
- raw secrets;
- committed school Canvas base URLs;
- student data;
- grades;
- submissions;
- full sensitive API responses.

## Optimistic concurrency

The ledger must reject an attempt to record or act on an older manifest revision when a newer revision already exists.

This prevents stale approval and stale deployment.

## Deployment attempt record

A future mutation attempt should record:

```text
eventId
objectId
operation
manifestRevision
snapshotId
idempotencyKey
attemptedAt
result
responseReference
error
```

Error messages must not expose tokens or secret headers.

## Read-back verification

After a future approved write:

1. fetch the object again;
2. normalize the remote representation;
3. compare it with intended canonical state;
4. record the verification result;
5. mark the artifact deployed only when verification passes.

A successful HTTP response alone is insufficient.

## Verification states

Suggested verification states:

```text
VERIFIED
PARTIALLY_VERIFIED
FAILED
RETRY_ELIGIBLE
MANUAL_REVIEW_REQUIRED
```

## Deployed state

An artifact may be marked `deployed` only when:

```text
write succeeded
and
read-back verification passed
```

A partially verified operation must not be reported as fully deployed.

## Health status vocabulary

Current health statuses:

```text
PASS
WARN
FAIL
BLOCKED
NOT_APPLICABLE
```

Warnings must not be converted to passes merely to improve readiness.

## Current health checks

Current Phase 27 health checks include:

```text
snapshot schema
snapshot freshness
archived-course blocking
resource state
unresolved due time
dependency cycles
missing dependencies
History assignment omission
Science assignment omission
ledger integrity
```

## Due-time blocker

Canvas assignment due-time convention remains unresolved.

Affected assignments must remain:

```text
BLOCKED
```

until an owner-approved due-time contract is recorded.

The system must not guess:

```text
12:00 AM
end of day
class start
class end
11:59 PM
```

## Archived targets

Any operation targeting an archived course must be:

```text
BLOCKED
```

Archived mappings remain read-only evidence.

## History and Science assignments

Current canonical policy:

```text
History assignment → OMIT
Science assignment → OMIT
```

Agenda-page generation remains allowed.

The safety diff must not turn these into CREATE operations.

## Rollback planning

Every future mutation-capable manifest must include a rollback plan.

Possible rollback actions:

```text
restore prior title
restore prior body
restore prior publish state
restore prior schedule
remove newly created module item
restore prior front page
archive newly created object
manual intervention
```

Rollback planning does not authorize automatic deletion.

## Delete behavior

`DELETE_CANDIDATE` is informational only.

The system must never automatically delete a Canvas object because it lacks a current local counterpart.

Deletion requires a separate explicit review and approval workflow.

## UI terminology

Use exact action labels such as:

```text
Save Draft
Generate Preview
Compare with Canvas
Approve
Revoke Approval
Prepare Publish
Publish to Canvas
Verify
```

Do not label any of the following as Publish:

```text
local save
preview generation
packet generation
manifest creation
export package creation
file export
```

## Export behavior

An export package may contain:

```text
manifest
safety diff
snapshot reference
dependency graph
ledger export
rollback plan
transport readiness
```

Exporting these files does not change Canvas.

## Publish blockers

Publishing is blocked when any of the following apply:

- transport remains preview-only;
- snapshot is stale or invalid;
- target is archived;
- comparison is BLOCKED;
- comparison is CONFLICT;
- comparison is OMIT;
- comparison is DELETE_CANDIDATE;
- required dependency is unresolved;
- dependency cycle exists;
- required resource is missing or blocked;
- due time is unresolved;
- approval is missing;
- approval belongs to another revision;
- approval belongs to another snapshot;
- content changed after approval;
- idempotency identity is missing;
- health check fails;
- target environment is ambiguous;
- target course verification fails.

## Validation requirements

The validator must confirm:

- current transport rejects all mutations;
- comparison status vocabulary is exact;
- non-approvable states are enforced;
- UNCHANGED causes no write;
- approval binds to object, revision, and snapshot;
- revision changes invalidate approval;
- snapshot changes invalidate approval;
- blockers propagate through dependencies;
- cycles are detected;
- missing dependencies are detected;
- archived targets are blocked;
- History assignments are omitted;
- Science assignments are omitted;
- unresolved due-time assignments remain blocked;
- ledger integrity passes;
- ledger events are append-only;
- idempotency identity exists;
- automatic deletion is prohibited;
- export is never labeled publish;
- deployed state requires read-back verification.
