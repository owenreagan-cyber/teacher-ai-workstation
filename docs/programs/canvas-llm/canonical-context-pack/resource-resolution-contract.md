# Resource Resolution Contract

## Purpose

This contract defines how curriculum resources are identified, matched, reviewed, linked, blocked, and audited.

Resource resolution must remain:

```text
deterministic
source-backed
privacy-safe
teacher-reviewable
local-first
```

## Canonical implementation references

```text
scripts/canvas_llm_phase25/models.py
scripts/canvas_llm_phase25/requirements.py
scripts/canvas_llm_phase25/resolver.py
scripts/canvas_llm_phase25/registry.py
scripts/canvas_llm_phase25/correction_memory.py
scripts/canvas_llm_phase25/integration.py
```

## Storage boundary

Large source files may remain in:

```text
Google Drive
NAS
iCloud
local folders
Canvas
```

The workstation stores:

```text
metadata
stable resource identity
source references
hashes
visibility
verification state
deployment policy
relationships
teacher corrections
review history
```

It does not require duplicate hosted storage for every curriculum file.

## Canonical resource identity

A resource record may include:

```text
resource_id
canonical_name
original_name
subject
curriculum
resource_type
variant
audience
visibility
sensitivity
verification_status
availability_status
deployment_policy
lesson_ref
lesson_number
assessment_number
content_hash
sha256
local_path
canvas_references
metadata
revision
created_at
updated_at
updated_by
```

## Resource requirement identity

A generated requirement should include:

```text
required_resource_class
subject
event_id
week_code
day
lesson_ref
lesson_number
assessment_number
required_visibility
preferred_verification_status
title_hint
```

## Known resource classes

Current rule surfaces include classes such as:

```text
written-test
fact-test
teacher-answer-key
secure-assessment
teacher-guide
study-guide-blank
study-guide-completed
power-up-practice
reader
workbook
checkout-passage
spelling-word-list
```

The subject and artifact contracts determine whether each resource is:

```text
required
optional
teacher-only
student-facing
secure
prohibited
```

## Visibility classes

Canonical visibility and sensitivity concepts:

```text
student-facing
teacher-only
answer-key
assessment-secure
```

A student-facing requirement must never be satisfied by:

```text
teacher-only
answer-key
assessment-secure
```

## Verification states

Supported verification states include:

```text
verified
owner-approved
unverified
rejected
```

Only resources marked:

```text
verified
owner-approved
```

may be treated as final production resolutions.

## Availability states

Suggested canonical values:

```text
available
missing
archived
unreachable
unknown
```

A resource that exists only as metadata but cannot currently be accessed must not be treated as production-ready.

## Deployment policy

Suggested canonical values:

```text
approved-for-canvas-link
local-reference-only
teacher-only
blocked
```

A student-facing Canvas link requires all of:

```text
visibility: student-facing
verification_status: verified or owner-approved
availability_status: available
deployment_policy: approved-for-canvas-link
```

## Resolution states

Canonical review states:

```text
resolved
needs_review
missing
blocked
```

Resolution methods may include:

```text
exact
owner-correction
verified-alias
reused-canonical
candidate
unresolved
```

## Matching precedence

Canonical precedence:

1. explicit owner correction;
2. exact stable resource identity;
3. exact subject/type/lesson or assessment match;
4. verified canonical alias;
5. approved reusable resource with matching content identity;
6. ranked candidate requiring review;
7. unresolved.

A lower-precedence candidate must never override a higher-precedence owner decision.

## Exact-match criteria

Exact matching should consider:

```text
subject
resource_type
lesson_ref
lesson_number
assessment_number
visibility
verification_status
availability_status
deployment_policy
```

Title similarity alone is insufficient for production resolution.

## Candidate handling

When multiple plausible resources exist, the result must be:

```text
needs_review
```

The review UI should show:

```text
candidate title
canonical name
source location
subject
resource type
lesson or assessment identity
visibility
verification state
deployment policy
content hash
why the candidate matched
differences between candidates
```

The resolver must not silently choose based only on filename ordering.

## Deterministic tie-breaking

When multiple resources are already proven equivalent and verified, deterministic ordering may use:

1. highest revision;
2. stable resource ID.

This is allowed only after equivalence has been established.

## Blocked resource behavior

A resource requirement becomes blocked when:

- a student-facing requirement resolves to teacher-only material;
- an answer key would appear in student output;
- a secure assessment would be exposed;
- deployment policy is blocked;
- a required resource is rejected;
- the resource belongs to an incompatible subject or type;
- the link is unsafe;
- the resource is stale or unavailable in a way that prevents safe use.

Blocked resources must:

- remain visible in teacher review;
- show a plain-language reason;
- remain out of student-facing HTML;
- block dependent publication when required.

## Missing resource behavior

A required missing resource must:

- remain visible;
- create a blocker;
- preserve its requirement identity;
- never be replaced with a fake link;
- never be silently omitted.

An optional missing resource may produce a warning only when the governing artifact contract permits omission.

## Student-facing link gate

A resource may be linked into student-facing HTML only when all are true:

```text
verification_status is verified or owner-approved
visibility is student-facing
availability_status is available
deployment_policy is approved-for-canvas-link
subject and type match the requirement
relationship is verified
safe URL exists
```

## Local path handling

Local filesystem paths are internal only.

They must never appear in:

```text
Canvas pages
Canvas assignments
announcements
newsletters
student-facing exports
```

## Canvas references

A resource may carry verified Canvas metadata such as:

```text
canvas_file_id
canvas_folder_id
canvas_url
course_id
module_id
module_item_id
```

Live numeric IDs and URLs must come from:

- current approved read-only metadata;
- or verified post-write read-back.

They must never be guessed.

## Correction memory

A teacher correction should preserve:

```text
subject
week_code
day
required_resource_class
predicted_resource_id
approved_resource_id
scope
reason
revision
created_at
created_by
```

Possible correction scopes:

```text
this occurrence
this lesson
this assessment type
this subject
future matching cases
```

Broad reuse requires an explicit teacher choice.

## Correction precedence

Teacher corrections outrank prediction but do not override hard safety rules.

For example:

- a teacher may choose a different verified workbook;
- a teacher may not approve an answer key for student-facing output;
- a teacher may mark a resource teacher-only;
- a teacher may leave a requirement unresolved.

## Content hashes

Hashes may support:

```text
duplicate detection
changed-file detection
idempotency
revision comparison
canonical reuse
```

A matching hash does not override:

```text
visibility
sensitivity
verification status
deployment policy
subject compatibility
```

## Secure assessment handling

Secure assessments and answer materials must:

- remain teacher-only;
- stay out of student-facing previews;
- stay out of Canvas pages;
- stay out of announcements;
- stay out of newsletters;
- stay out of student-facing assignment bodies;
- remain visible to the teacher as private or blocked resources.

## Resource review queue

The teacher review queue should show:

```text
requirement
resolution state
selected resource
candidate resources
visibility
verification status
availability
deployment policy
explanation
blocked reason
suggested teacher action
```

Suggested actions:

```text
Approve match
Choose another resource
Mark missing
Mark teacher-only
Reject candidate
Add verified alias
Remember correction
Leave unresolved
```

## Artifact dependencies

Assignments, pages, announcements, and newsletters must reference stable resource IDs.

A resource edit or replacement must:

- update the dependent artifact hash;
- mark comparison stale;
- invalidate affected approval;
- require renewed review.

## Reading-specific behavior

Reading resource resolution may involve:

```text
Reader volume
comprehension page
workbook
Checkout passage
teacher guide
assessment notice resource
```

Reading Test 14 must not request or resolve a Checkout 14 resource.

## Spelling-specific behavior

Spelling resource resolution may involve:

```text
cumulative word list
focus-word list
practice material
assessment reminder material
```

The current canonical source supports Tests 1–24 only.

No Test 25 resource may be treated as canonical without owner-approved source data.

## Math-specific behavior

Math resource resolution may involve:

```text
Student Book lesson
Power Up practice
homework worksheet
Fact Test practice
Study Guide blank
Study Guide completed
written test
teacher answer key
secure assessment
```

Student-facing output may include only the approved safe resource classes.

## Failure behavior

Resolution must fail closed when:

- required identity is incomplete;
- multiple conflicting verified resources exist;
- visibility is incompatible;
- deployment policy is blocked;
- required resource is missing;
- source location is unsafe;
- verification state is insufficient.

## Validation requirements

The validator must confirm:

- known resource classes are recognized;
- exact matching uses subject/type/lesson or assessment identity;
- title similarity alone cannot finalize a match;
- only verified or owner-approved resources resolve finally;
- teacher-only resources stay out of student-facing HTML;
- answer keys remain private;
- assessment-secure resources remain blocked;
- fake links are prohibited;
- unresolved required resources block publication;
- local paths do not leak;
- correction memory preserves provenance;
- resource changes invalidate dependent approvals;
- Reading Test 14 requests no Checkout 14 resource;
- Spelling Test 25 remains unresolved until approved.
