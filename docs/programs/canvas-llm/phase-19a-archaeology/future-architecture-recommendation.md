# Canvas LLM Phase 19A Future Architecture Recommendation

## Status

Analysis-only architecture recommendation.

## Core Decision

The Canvas LLM Center should not start as a Canvas writer.

Recommended order:

```text
Evidence Vault
  ↓
Rule Catalog
  ↓
Relationship / Pattern Catalog
  ↓
Preview Builders
  ↓
Diagnostics / Medical Center
  ↓
Human Approval Gates
  ↓
Canvas Write Adapter
```

The Canvas Write Adapter remains disabled until explicitly approved in a later write-gate phase.

## Why

Legacy repositories contain valuable intelligence, but also risky mutation paths.

The safe path is:

```text
recover intelligence
classify evidence
promote approved rules
preview output
diagnose risks
require human approval
only then consider writes
```

## Layer 1 — Evidence Vault

Purpose:

```text
Here is what we know and where it came from.
```

Stores:

- course metadata references
- page metadata references
- assignment metadata references
- file/folder metadata references
- legacy source evidence
- rule documents
- owner decisions
- teacher memory patterns
- resource relationships

Every object should track:

- source
- classification
- confidence
- approval status
- review state
- student-facing vs teacher-only status
- generated vs human-authored status

## Layer 2 — Rule Catalog

Purpose:

```text
Deterministic business rules live in reviewed tables, not prompts.
```

Initial tables:

- subject prefixes
- assignment title formats
- assignment group routing
- grading/exclude-from-final settings
- Math Test triple expansion
- Math Fact Test map
- Math Power Up map
- Reading/Spelling Together Logic
- Spelling word bank/focus rules
- Friday rules
- newsletter model
- file operation policy
- diagnostic definitions

## Layer 3 — Relationship / Pattern Catalog

Purpose:

```text
Map relationships without mutating source systems.
```

Examples:

- lesson to resource
- assignment to resource
- subject to course role
- historical template to current target
- Reading to Spelling paired rows
- Math Test to Fact Test and Study Guide
- file aliases and duplicates
- newsletter to Homeroom page

## Layer 4 — Preview Builders

Purpose:

```text
Build previews before writes.
```

Preview types:

- agenda page preview
- assignment preview
- newsletter preview
- announcement preview
- resource map preview
- file organization preview
- Canvas setup action preview

Preview builders may use AI for wording, but only after deterministic rules decide structure.

## Layer 5 — Diagnostics / Medical Center

Purpose:

```text
Answer what could go wrong before Canvas is touched.
```

Recommended panels:

- Page Standard Check
- Assignment Gatekeeper
- Resource Integrity
- Reading/Spelling Integrity
- Math Test Integrity
- Newsletter Boundary
- Teacher Memory Confidence
- Canvas Brain Confidence
- Course ID Drift
- File Operation Risk
- Write Gate Readiness

Diagnostic levels:

```text
PASS
WARN
FAIL
BLOCKED
```

## Layer 6 — Human Approval Gates

Purpose:

```text
No external mutation without explicit approval.
```

Approval gates should require:

- exact target
- exact operation
- exact preview
- validation result
- rollback/cleanup expectation
- stop conditions
- approval phrase

## Layer 7 — Canvas Write Adapter

Purpose:

```text
Small, locked, auditable Canvas mutation layer.
```

Disabled until approved.

When eventually enabled:

- no historical-course mutation
- no publish by default
- no student data access
- no file body ingestion unless approved
- no page body ingestion unless approved
- no silent rename/move/delete/upload
- every operation is logged
- every operation has post-action validation
- every operation has human approval evidence

## Implementation Recommendation

Do not implement app behavior yet.

Next phase should be:

```text
Phase 19B — Canonical Rule Constitution
```

Deliverables:

- canonical subject prefix table
- canonical assignment title table
- canonical Study Guide grading rule
- Reading/Spelling Together rule table
- Friday rule table
- newsletter rule table
- file operation policy
- source authority policy
- Medical Center diagnostic spec
- write gate policy

Only after Phase 19B should implementation planning begin.

## Rejected Architecture

Do not rebuild:

```text
AI → Canvas API → Create pages/assignments
```

Do not inherit:

- direct deploy buttons as first-class workflow
- hardcoded course IDs
- prompt-only logic
- automatic file organization
- unreviewed memory updates
- old page body templates
- standalone Spelling announcement path

## Recommended Architecture Summary

```text
Teacher evidence
  ↓
Canonical rules
  ↓
Resource/curriculum relationships
  ↓
Teacher memory
  ↓
AI suggestions
  ↓
Preview
  ↓
Medical Center
  ↓
Human approval
  ↓
Optional future Canvas write
```
