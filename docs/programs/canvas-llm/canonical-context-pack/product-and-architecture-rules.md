# Product and Architecture Rules

## Purpose

This document defines the canonical product boundary and target implementation architecture for the Teacher AI Workstation Canvas LLM builder.

It distinguishes:

- durable production architecture;
- current preview implementations;
- test fixtures;
- historical evidence;
- prohibited architectural regressions.

## Product identity

The product is:

```text
a single-user, local-first Teacher AI Workstation
for one teacher's planning, curriculum, Canvas preparation,
resource resolution, review, approval, and controlled publishing
```

It is not:

```text
a multi-tenant SaaS platform
a district-wide administration system
a student information system
a hosted curriculum marketplace
a Supabase application
a Firebase application
an autonomous live Canvas bot
```

## Primary user

The primary user is one teacher.

The architecture should optimize for:

```text
fast local startup
durable teacher edits
clear weekly planning
low operating cost
no surprise API billing
simple backup and recovery
teacher-controlled approvals
safe Canvas interaction
```

Multi-user collaboration is not a current architectural requirement.

## Privacy scope

The current product should avoid student data unless a later explicitly approved feature requires it.

Current production planning should not need:

```text
student names
grades
submissions
accommodations
behavior records
enrollment data
private family data
```

Synthetic fixtures must declare:

```text
containsStudentData: false
```

## Canonical high-level architecture

Target architecture:

```text
browser UI
    ↓ localhost HTTP/JSON
local Python application service
    ↓
SQLite + local files + committed canonical configuration
    ↓
controlled connectors
    ├── Canvas read-only metadata
    ├── future approval-gated Canvas write transport
    ├── resource locations
    ├── optional local model/Ollama
    └── optional future email/daily-brief delivery
```

## Frontend boundary

The frontend may be implemented with:

```text
static HTML/CSS/JavaScript
or
React + Vite + TypeScript
```

The exact UI framework is not the product architecture.

Regardless of framework, the frontend must:

- call the localhost service;
- use the service as the persistence authority;
- avoid direct Canvas secrets;
- avoid direct database access;
- avoid browser-only production persistence;
- expose save/conflict/approval state honestly;
- preserve accessibility and keyboard use.

## Browser restrictions

The browser must not:

- open SQLite directly through unsupported browser APIs;
- contain Canvas API tokens;
- perform uncontrolled Canvas writes;
- treat `localStorage` as the canonical weekly model;
- recreate Phase 27 safety logic independently;
- bypass service-side validation;
- label local export as Canvas publication.

Browser cache may support transient convenience only.

## Local service

The canonical service layer is a local Python application bound by default to:

```text
127.0.0.1
```

The service owns:

```text
database access
schema migrations
weekly-plan CRUD
autosave conflict checks
curriculum resolution
resource resolution
generation
validation
revision history
approval state
comparison
deployment preparation
audit records
```

## Network exposure

Default host:

```text
127.0.0.1
```

The service must not bind to all interfaces by default.

External device access requires a separately reviewed local-network design with authentication and privacy controls.

## SQLite authority

Canonical teacher work lives in SQLite.

SQLite should store:

```text
weekly plans
subject weekly plans
daily entries
teacher corrections
generated artifacts
resource registry metadata
revisions
approvals
exports
settings
deployment preparation state
```

SQLite must use:

```text
foreign keys
WAL mode
busy timeout
schema migrations
transactional writes
backup support
optimistic concurrency where appropriate
```

## Database location

Runtime databases belong under ignored:

```text
.local/canvas-llm/
```

The default path must be anchored to the repository root.

It must not depend on the shell's current working directory.

## Source-of-truth hierarchy

Production authority order:

1. current owner decisions recorded in this context pack;
2. committed canonical configuration and maps;
3. persisted teacher edits in the active SQLite weekly model;
4. current approved read-only Canvas metadata;
5. approved historical evidence;
6. legacy source evidence;
7. synthetic fixtures and prototype behavior.

A lower-authority source must not silently override a higher one.

## Editable weekly model

The production weekly model must support:

```text
blank/new weeks
Monday-Friday
all supported subjects
teacher-entered In Class text
teacher-entered At Home text
lessons
tests
resources
notes
calendar disruptions
newsletter inclusion
revisions
approval invalidation
```

The selected week must drive all generated artifacts.

## New-week behavior

A teacher must be able to create or open a week without synthetic curriculum being inserted automatically.

Production behavior:

```text
new week → blank or explicitly imported teacher-owned state
```

Test behavior may seed fixtures only when the command or test explicitly requests fixture mode.

## Fixture prohibition

Synthetic fixtures are valid for:

```text
unit tests
integration tests
browser proofs
validator demonstrations
deterministic regression tests
```

Synthetic fixtures are prohibited as the implicit production source.

In particular:

```text
fixtures/canvas-llm/phase-23/synthetic-weekly-content.json
```

must not remain the source for ordinary production page, assignment, reminder, or resource generation.

## Phase 22 status

Phase 22 proves useful durable foundations:

```text
SQLite schema and migrations
local HTTP service
JSON API
autosave
revision restore
backups
resource metadata
weekly-plan UI
agenda preview
preview-only safety
```

However, current automatic fixture seeding must not define final production startup behavior.

The recovery implementation must separate:

```text
production initialization
test/demo fixture seeding
```

## Phase 23 status

Phase 23 contains useful generation logic for:

```text
pages
assignments
resources
assessment reminders
packet validation
Canvas-compatible HTML
```

Current limitation:

```text
build_packet() loads the synthetic Phase 23 fixture
```

Required convergence:

- accept the real persisted weekly model as input;
- preserve deterministic generation;
- retain test fixture adapters;
- remove Q1W5 as an implicit production assumption;
- retain provenance;
- keep preview-only behavior until write approval.

## Phase 24 status

Phase 24 contains deterministic prediction and Teacher Brain rules.

Prediction must remain:

```text
suggestion
not silent overwrite
```

Teacher edits outrank predictions.

Predictions should operate on real weekly/pacing state, with fixtures limited to tests.

## Phase 25 status

Phase 25 contains the canonical resource-resolution foundation.

Preserve:

```text
resource identity
visibility
verification
secure-resource blocking
correction memory
review queue
explanations
```

Production resource resolution must consume the real weekly model and real local registry metadata, not fixture files by default.

## Phase 26 status

Phase 26 contains useful unification concepts:

```text
selected week
correction persistence
revision history
approval invalidation
export history
subject snapshots
readiness
```

Current limitation:

```text
parts of the pipeline still use Phase 24 and Phase 25 fixture inputs
```

Required convergence:

- use the active SQLite weekly model;
- use the active local resource registry;
- use real teacher corrections;
- generate one coherent production packet;
- keep fixture-driven pipeline execution as test-only.

## Phase 27 status

Phase 27 contains the strongest current Canvas safety foundation.

Preserve:

```text
Canvas snapshot schema
snapshot freshness
matching
Safety Diff
comparison statuses
dependency graph
revision-bound approval
append-only deployment ledger
health checks
rollback planning
idempotency
read-only transport boundary
read-back verification design
```

Do not replace Phase 27 with an unreviewed direct deployment bridge.

## One canonical pipeline

The recovered product must converge on one production path:

```text
SQLite weekly model
→ curriculum resolution
→ resource resolution
→ artifact generation
→ validation
→ Canvas comparison
→ dependency analysis
→ approval
→ controlled future transport
→ read-back verification
```

Parallel incompatible generation/deployment paths are prohibited.

## Canvas connector boundary

Canvas access must occur through a controlled service-side connector.

The browser must not call Canvas directly.

Current authorized behavior:

```text
approved read-only metadata fetches
local ignored snapshot imports
preview-only comparison
```

Current unauthorized behavior:

```text
production Canvas mutation
unapproved token usage
broad course enumeration
student-data fetches
body ingestion outside approved scope
```

## Canvas secrets

Canvas credentials must remain local.

Allowed local environment variables may include:

```text
CANVAS_BASE_URL
CANVAS_API_TOKEN
```

Rules:

- never print tokens;
- never commit tokens;
- never write tokens into SQLite;
- never place tokens in browser code;
- never commit school Canvas URLs unless explicitly approved;
- redact secret-bearing errors and logs.

## Read-only metadata

Approved read-only metadata may support:

```text
courses
folders
files metadata
modules
module items
pages metadata
announcements metadata
constrained assignment metadata
```

Current restrictions remain defined by the relevant approved fetch contracts.

## Write transport

A mutation-capable Canvas transport is future work.

It must not be created as an alternate shortcut around Phase 27.

A future transport must enforce:

```text
explicit enablement
approved current target
fresh snapshot
valid manifest revision
valid artifact approval
resolved dependencies
idempotency
ledger record
post-write read-back
fail-closed behavior
```

## Resource storage

Resources may remain in their existing storage systems.

The workstation should store references and metadata instead of forcing duplication.

Supported future resource locations may include:

```text
local filesystem
NAS
Google Drive
iCloud
Canvas files
```

External integrations require separate approval and secure credential handling.

## Ollama and local models

Ollama or another local model may be added later as an optional helper.

Appropriate uses:

```text
draft wording
summarization
classification suggestions
resource suggestions
teacher-facing explanations
```

Local AI must not become the authority for:

```text
course routing
assessment dates
curriculum maps
resource safety
approval
publication
student facts
```

Deterministic rules and owner decisions remain authoritative.

## Cloud AI

Cloud AI may be optional.

The core workstation must remain usable without recurring per-request cloud API charges.

Any cloud integration must:

- be opt-in;
- show which data is sent;
- avoid student data by default;
- fail gracefully;
- preserve local deterministic operation.

## Email boundary

Current email sending is not authorized.

Daily brief and newsletter-email concepts may remain preview-only until a separate delivery contract exists.

Canvas announcement and email are distinct channels.

## Backups

SQLite backups must be supported before risky migrations or major changes.

Backups belong under ignored `.local/...`.

A backup must not be treated as an export to Canvas.

## Exports

Local exports may include:

```text
JSON packets
HTML previews
manifests
safety diffs
dependency graphs
rollback plans
ledger exports
```

Export is not publication.

## Logging

Logs should be local, bounded, and redacted.

Logs must not expose:

```text
tokens
authorization headers
student data
secure assessment content
private local paths in student-facing output
```

## Error behavior

The application should fail closed for:

```text
missing canonical mappings
ambiguous resource matches
stale approval
stale Canvas snapshot
unresolved due time
archived course target
blocked dependencies
unsafe resource visibility
transport gate failure
```

## UI truthfulness

The UI must clearly distinguish:

```text
Unsaved
Saving
Saved
Conflict
Preview
Needs Review
Approved
Approval Stale
Blocked
Ready to Prepare
Published to Canvas
Verified
```

`Published to Canvas` may appear only after an actual approved mutation and successful read-back verification.

## Repository implementation home

Canonical implementation must live in tracked paths under:

```text
apps/
scripts/
config/
docs/
tests/
fixtures/
```

Ignored reference directories are not implementation homes.

## Prohibited architecture regressions

Do not:

- move canonical implementation into `.local/reference-apps`;
- reintroduce Supabase or Firebase as required infrastructure;
- create a second uncontrolled deployment service;
- make the browser authoritative for weekly state;
- seed production automatically from Q1W5 fixtures;
- duplicate Phase 27 approval logic in frontend-only code;
- perform direct mutation before approval;
- store secrets in tracked files;
- claim preview output is deployed;
- call local export Publish.

## Target recovery sequence

Recommended convergence sequence:

1. finish and validate the canonical context pack;
2. build context-pack validator and status command;
3. audit Phase 22–27 convergence gaps;
4. select tracked canonical app/service locations;
5. separate production startup from fixture seeding;
6. implement blank/new editable weeks;
7. adapt Phase 23 generation to the real weekly model;
8. connect Phase 25 resolution to real registry state;
9. connect Phase 26 review to the unified packet;
10. preserve Phase 27 safety boundary;
11. prove one no-write Math vertical slice;
12. expand subjects only after vertical-slice proof.

## First vertical slice

The first production convergence slice should be:

```text
one selected Math week
→ editable daily entries
→ deterministic Math resolution
→ resource requirements
→ assignment/page preview
→ Safety Diff
→ approval proof
→ no Canvas write
```

Success requires real SQLite input, not the Phase 23 fixture.

## Validation requirements

The context-pack validator must confirm:

- product mode is single-user and local-first;
- SQLite is the teacher-work authority;
- localhost service is the application boundary;
- browser-only persistence is prohibited;
- production startup does not require fixture seeding;
- Phase 23 fixture is test-only;
- Phase 25 safety is preserved;
- Phase 27 safety is preserved;
- Supabase/Firebase are not required;
- reference apps are evidence only;
- no alternate write bridge is authorized;
- export is not publish;
- secrets remain local;
- student data is excluded by default.
