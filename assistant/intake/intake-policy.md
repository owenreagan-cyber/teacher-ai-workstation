# Intake Policy

## Allowed Candidate Material

- sanitized notes
- approved writing samples
- lesson ideas
- project notes
- curriculum references that are safe to use
- public links or citations
- non-sensitive troubleshooting notes
- non-sensitive 3D printing notes
- drafts that Owen wants to review

## Sensitive or Restricted Material

These must not be promoted without careful review:

- student names
- parent names
- grades
- behavior records
- medical information
- accommodations
- discipline records
- private school records
- passwords
- API keys
- tokens
- private emails
- confidential documents
- copyrighted content copied in full
- proprietary school materials not approved for model context

## Review Outcomes

Each item can be:

- approved
- approved after sanitizing
- rejected
- quarantined
- needs more context
- deferred

## Promotion Targets

Approved or sanitized material may be promoted to:

- `assistant/intake/approved-context.md`
- `assistant/training/writing-samples/approved-samples.md`
- `assistant/memory/projects.md`
- `assistant/memory/teaching-context.md`
- `assistant/memory/writing-style-rules.md`
- `assistant/memory/preferences.md`
- `assistant/memory/decisions.md`
- `assistant/memory/active-priorities.md`
- `assistant/memory/knowledge/` (planned — see `docs/teacher-knowledge-vault-m0-foundation.md`; M0 does not populate files)
- a workflow doc

## approved-context.md vs approved-files/

- `approved-context.md` stores safe Markdown summaries and approved excerpts.
- `approved-files/` stores actual reviewed files that may be useful later.
- `approved-files/` is ignored by Git except for `.gitkeep`.
- The CLI never auto-loads `approved-files/`.
- In Phase 1D, the CLI refuses `approved-files/` paths with `--context`; use sanitized Markdown summaries instead.
- A later reviewed-file workflow can add explicit file use if Owen approves it.

## Non-Automation Rule

The system may help review and classify material, but it must not automatically promote, delete, publish, send, or ingest materials.
