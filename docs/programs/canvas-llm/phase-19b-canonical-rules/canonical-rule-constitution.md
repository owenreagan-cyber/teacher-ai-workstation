# Canvas LLM Phase 19B — Canonical Rule Constitution

## Status

Canonical planning specification.

This document converts Phase 19A archaeology findings and owner-approved decisions into durable canonical rules for future Canvas LLM Center work.

This phase does not implement generators, previews, diagnostics, Canvas writes, file operations, migrations, or app behavior.

## Purpose

The Canonical Rule Constitution exists to prevent future implementation from rebuilding accidental legacy behavior.

It defines:

- source authority
- subject prefixes
- assignment title rules
- Study Guide grading
- Reading/Spelling Together rules
- Friday rules
- newsletter rules
- file management policy
- Medical Center diagnostic model
- write gate policy

## Core Principle

```text
Historical evidence is useful.
Historical evidence is not automatic truth.
```

Future Canvas LLM Center work must flow through:

```text
Evidence
  ↓
Classification
  ↓
Canonical rule review
  ↓
Preview
  ↓
Diagnostics
  ↓
Human approval
  ↓
Optional future Canvas write
```

## Source Authority Order

Use this authority order:

```text
1. Safety boundaries
2. Owner-approved canonical rules
3. FPK 2025-2026 Canvas Page Guidelines
4. Current Teacher AI Workstation Canvas LLM governance docs
5. Reviewed deterministic business rules
6. Historical metadata and legacy app evidence
7. AI suggestions
```

## Evidence Classification

Use these labels:

```text
APPROVED_PATTERN
WORKFLOW_EVIDENCE
LEGACY_FORMAT_ONLY
UNKNOWN_NEEDS_REVIEW
```

Rules:

- APPROVED_PATTERN may be used for future specs.
- WORKFLOW_EVIDENCE must be validated before becoming canonical.
- LEGACY_FORMAT_ONLY may be mapped as alias/history but not generated as future output.
- UNKNOWN_NEEDS_REVIEW must not drive implementation.

## Architecture Lock

The future Canvas LLM Center architecture is:

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

The Canvas Write Adapter remains disabled until an explicit future write-gate phase.

## AI Boundary

AI may:

- summarize approved evidence
- suggest wording
- draft preview copy
- explain rules
- suggest organization plans
- identify possible conflicts

AI may not:

- decide whether assignments exist
- invent assignments
- override canonical rules
- override grading settings
- silently publish content
- silently mutate Canvas
- silently rename, move, delete, or upload files
- treat old Canvas content as authoritative

## Current Canonical Rule Modules

This constitution is implemented as these companion specs:

```text
canonical-subject-prefixes.md
canonical-assignment-title-rules.md
canonical-study-guide-grading.md
canonical-reading-spelling-together.md
canonical-friday-rules.md
canonical-newsletter-rules.md
canonical-file-management-policy.md
canonical-source-authority-policy.md
canonical-medical-center-diagnostics.md
canonical-write-gate-policy.md
```

## Implementation Boundary

This phase does not authorize:

- Canvas API calls
- Canvas writes
- live Canvas fetches
- page creation
- assignment creation
- announcement creation
- file movement
- file upload
- publishing
- body ingestion
- student data access
- raw `.local` metadata commits
- school Canvas URL commits
- token exposure
- app behavior implementation
- refactors
- migrations
