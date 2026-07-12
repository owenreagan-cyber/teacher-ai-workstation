# Legacy Application Comparison Oracle

## Purpose

This document defines how legacy applications, historical repositories, ignored reference copies, screenshots, reports, and recovered source code may be used during the Teacher AI Workstation recovery.

A comparison oracle is evidence.

It is not automatically:

```text
canonical truth
the implementation home
approved architecture
approved curriculum data
approved deployment behavior
```

## Core rule

```text
Inspect legacy behavior.
Measure it.
Compare it.
Extract evidence.
Do not copy it blindly.
```

## Reference-app boundary

Ignored reference applications may exist under:

```text
.local/reference-apps/
```

Known examples include reference copies associated with:

```text
thales-academic-os
thales-academic-os-v2
```

Other historical repositories may include projects such as:

```text
pacing-sync-pilot
Thalescanvasgemini
```

Exact local names may vary.

All remain reference evidence unless explicitly promoted through tracked review.

## Git boundary

`.local/reference-apps/...` must remain ignored.

Rules:

- do not commit reference repositories;
- do not make feature changes there as canonical work;
- do not report ignored changes as completed canonical implementation;
- do not open a PR whose primary implementation exists only there;
- do not copy secrets or school URLs from them;
- do not treat their current runtime as the recovered product.

## Canonical implementation location

Accepted implementation homes are tracked repository paths such as:

```text
apps/
scripts/
config/
tests/
docs/
fixtures/
```

The exact final frontend path must be explicitly selected and documented before implementation begins.

## Evidence classes

Legacy evidence may be classified as:

```text
CANONICAL_CANDIDATE
WORKFLOW_EVIDENCE
VISUAL_EVIDENCE
DATA_CANDIDATE
CONFLICTING_EVIDENCE
REJECTED_BEHAVIOR
UNKNOWN
```

## CANONICAL_CANDIDATE

A legacy behavior may become canonical only when:

- its source is known;
- its meaning is understood;
- it does not conflict with current owner decisions;
- it is compatible with the target architecture;
- it has validation evidence;
- it is recorded in tracked canonical configuration or contracts.

## WORKFLOW_EVIDENCE

Workflow evidence may inform:

```text
teacher task order
form grouping
review steps
resource selection
week navigation
assignment preparation
newsletter preparation
```

The workflow concept may survive even when the legacy code should not.

## VISUAL_EVIDENCE

Visual evidence may inform:

```text
layout
density
hierarchy
labeling
page previews
navigation
teacher ergonomics
```

A visually useful screen does not authorize its data model or backend.

## DATA_CANDIDATE

Legacy maps and curriculum values must be treated as candidates until reconciled.

Examples:

```text
Power Up mappings
Fact Test mappings
Reading pages
Spelling lists
course IDs
assignment groups
module relationships
```

Conflicting sources must be surfaced rather than merged silently.

## CONFLICTING_EVIDENCE

When two legacy sources disagree:

1. preserve both values;
2. identify source and scope;
3. compare against current config;
4. seek owner confirmation where needed;
5. record the decision;
6. update the validator;
7. retain the rejected value as evidence where useful.

Do not choose based on which app appears newer or more polished.

## REJECTED_BEHAVIOR

A legacy behavior must be rejected when it conflicts with current requirements.

Examples include:

```text
browser-only persistence
Supabase/Firebase dependency
silent fixture substitution
unsafe direct Canvas writes
unreviewed title conventions
automatic deletion
student-data assumptions
false publish labels
```

Rejected behavior may still be documented to prevent regression.

## Architecture evidence

Legacy cloud architectures may demonstrate:

```text
schemas
relationship ideas
resolver concepts
idempotency patterns
deduplication approaches
workflow screens
```

They must not force the recovered architecture to use:

```text
Supabase
Firebase
hosted multi-user authentication
cloud database subscriptions
edge functions
```

The target remains local-first.

## Curriculum-map evidence

Legacy curriculum maps must be compared against committed canonical maps.

Current examples of previously conflicting evidence include:

```text
lesson-based Power Up mappings
test-based Power Up mappings
different Reading mappings
different Spelling conventions
different title prefixes
```

The committed validator-backed maps remain authoritative unless the owner explicitly changes them.

## Course-routing evidence

Historical course IDs may help identify:

```text
subject relationships
shared Reading/Spelling courses
Homeroom newsletter patterns
module structures
folder structures
assignment-group names
```

Archived course IDs remain read-only.

They must never become current write targets automatically.

## Newsletter evidence

Historical Homeroom courses may be used to study:

```text
page counts
module relationships
section ordering
layout evolution
page naming
announcement/page patterns
```

Current approved references include:

```text
19424 → primary historical newsletter structure reference
22254 → supporting historical reference
26427 → current target shell
```

Historical body content must not be copied without a separate approved review gate.

## UI comparison

A legacy UI comparison should record:

```text
screen or workflow
useful behavior
problematic behavior
canonical requirement
keep/rewrite/reject decision
validation method
```

Recommended table:

| Area | Legacy evidence | Decision | Canonical target | Proof |
|---|---|---|---|---|
| Week selector | observed behavior | keep/rewrite/reject | target rule | test or screenshot |
| Daily editor | observed behavior | keep/rewrite/reject | target rule | interaction proof |
| Resources | observed behavior | keep/rewrite/reject | target rule | validator |
| Publish flow | observed behavior | keep/rewrite/reject | target rule | safety test |

## Functional comparison

Comparison should measure concrete outcomes.

Examples:

```text
Does a teacher edit survive reload?
Does week selection survive restart?
Does a blank week stay blank?
Does changing Reading invalidate only dependent artifacts?
Does Friday homework remain when manually entered?
Does Reading Test 14 avoid Checkout 14?
Does the UI distinguish Save from Publish?
```

Avoid vague conclusions such as:

```text
looks modern
seems complete
mission ready
close to production
```

## Measurement principle

Prefer measurable evidence:

```text
database row
content hash
validator result
HTTP response
browser interaction proof
screenshot
generated HTML
diff
ledger event
```

Visual inspection alone is insufficient for data and safety claims.

## Feature-survival decisions

Every legacy feature should receive one decision:

```text
KEEP
REWRITE
DEFER
BLOCK
OWNER_REVIEW_REQUIRED
```

## KEEP

Use only when the legacy implementation already fits:

- canonical rules;
- target architecture;
- privacy boundary;
- validation requirements;
- repository structure.

This will be uncommon.

## REWRITE

Use when the behavior is valuable but implementation is incompatible.

Likely rewrite candidates:

```text
weekly planning workflow
resource suggestions
title normalization
newsletter workflow
assignment preview
file classification suggestions
```

## DEFER

Use when useful but not required for the first vertical slice.

Examples:

```text
local AI drafting
Google Drive integration
email delivery
advanced analytics
cross-device sync
```

## BLOCK

Use when unsafe or contrary to the current product.

Examples:

```text
unapproved production writes
automatic deletion
teacher-only resource exposure
implicit Test 25 generation
direct browser Canvas token usage
```

## OWNER_REVIEW_REQUIRED

Use when behavior depends on a teacher-specific preference or unresolved curriculum fact.

Examples:

```text
Spelling student-facing prefix
Spelling Test 25
exact newsletter title
assignment due-time convention
final announcement templates
```

## Copilot/Codex/agent rules

Any coding agent working with legacy apps must:

1. inspect the canonical repository first;
2. identify tracked implementation paths;
3. treat `.local/reference-apps` as read-only;
4. state which legacy evidence is being used;
5. state which behavior is being rejected;
6. preserve owner decisions;
7. run canonical validators;
8. show tracked `git diff`;
9. avoid claiming ignored changes are canonical work.

## Promotion procedure

To promote a legacy fact or behavior:

1. cite its legacy source;
2. describe its meaning;
3. compare it with current canonical sources;
4. record conflicts;
5. obtain owner approval when needed;
6. add or update tracked config/contract;
7. add validation;
8. implement in the canonical path;
9. prove behavior;
10. leave the legacy source unchanged.

## Prohibited promotion shortcuts

Do not promote a behavior merely because:

- it appears in multiple legacy files;
- it exists in a database migration;
- it is used by a polished UI;
- it was generated by Lovable, Copilot, Cursor, or another agent;
- it has newer timestamps;
- it appears in a current-looking reference app;
- it produces a successful demo.

## Current legacy-derived concepts worth preserving

Reviewed concepts that may survive through canonical rewrites include:

```text
weekly subject planning
course routing
assignment title normalization
resource relationship intelligence
page-first newsletter behavior
idempotency
duplicate prevention
read-only file classification suggestions
historical course structure comparison
```

## Current legacy-derived architecture to reject

Do not require:

```text
Supabase
Firebase
multi-tenant user accounts
cloud-first database state
edge-function deployment
browser-direct persistence
browser-direct Canvas writes
```

## Comparison oracle output

A future automated comparison report should produce:

```text
legacySource
canonicalTarget
feature
observedLegacyBehavior
canonicalExpectedBehavior
matchStatus
risk
recommendedDecision
evidence
ownerDecisionRequired
```

Suggested match statuses:

```text
MATCH
PARTIAL_MATCH
CONFLICT
MISSING_CANONICAL
MISSING_LEGACY
REJECTED
UNKNOWN
```

## Runtime prohibition

The production application must not import or execute the ignored reference app as a runtime dependency.

Reference apps are not plugins.

They are evidence repositories.

## Test-fixture distinction

Legacy data and synthetic fixtures serve different purposes:

```text
legacy evidence → explains prior behavior
synthetic fixture → proves deterministic tests
canonical config → defines approved facts
SQLite weekly model → stores current teacher work
```

These categories must remain distinguishable.

## Current recovery use

During recovery, the comparison oracle should help answer:

```text
What did the legacy app do?
Was that behavior intentional?
Does it conflict with current owner decisions?
Should the concept survive?
Where should it be rewritten?
How will the rewritten behavior be proven?
```

## Validation requirements

The context-pack validator must confirm:

- reference apps are labeled evidence only;
- ignored reference directories are not implementation homes;
- Supabase/Firebase are not canonical requirements;
- legacy maps cannot override validated config silently;
- every promotion requires tracked config or contract;
- archived courses remain read-only;
- rejected behavior is preserved as regression guidance;
- agents must show tracked diffs;
- production does not depend on ignored reference code;
- measurable proof is required for claims.
