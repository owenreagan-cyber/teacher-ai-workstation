# Artifact Registry Contract

## Purpose

The artifact registry is a **derived, read-only, non-authoritative metadata view** over existing Canvas LLM C0-series artifacts.

It does not replace generator ownership. Existing generators remain authoritative for:

- assignments
- assessment announcements
- Homeroom newsletters
- newsletter update announcements
- Daily Teacher Briefs

C0Q adds a unified normalization and health-reporting layer only.

## Artifact sources

All supported artifacts are read from the existing Phase 22 `drafts` table.

| Logical artifact | `drafts.kind` | Nested payload key | `artifactKind` |
| --- | --- | --- | --- |
| Assignment draft | `assignment` | `metadata` and due metadata | — |
| Assessment announcement | `announcement` | `announcementDraft` | — |
| Homeroom newsletter page | `page` | `newsletterDraft` | `newsletter` |
| Newsletter update announcement | `announcement` | `announcementDraft` | `newsletter_update` |
| Daily Teacher Brief | `daily_brief` | `dailyBriefDraft` | `daily_brief` |

No second artifact storage table is created by this contract.

## Normalization rules

The registry adapter:

- reads existing draft rows
- resolves logical artifact kind from `kind`, `payload.artifactKind`, and nested draft objects
- maps common approval, preview, deployment, warning, and blocker fields into `ArtifactRegistryRecord`
- leaves missing values explicit (`None`, `false`, `[]`, `{}`) according to field meaning
- ignores unsupported draft kinds such as academic agenda pages

The adapter does not duplicate artifact ownership or regenerate content.

## Read-only behavior

The registry is metadata only.

It must not:

- modify artifacts
- approve artifacts
- deploy artifacts
- regenerate artifacts
- change approval state
- create a competing storage table

Health reporting is observation only.

## Approval model

Approval remains teacher-bound and revision-bound.

Canonical lifecycle:

```text
Artifact
↓
Validation
↓
Approval
↓
Deployment Plan
↓
Future Connector
```

Current C0-series artifacts are expected to remain:

- `approval_state`: Draft
- `teacher_approval_required`: true
- `preview_only`: true
- `approved`: false

Save is not approval. Approval is not publish.

## Deployment boundary

Deployment remains preview-only and blocked by default.

Registry health rules treat these as safety findings:

| Finding | Meaning |
| --- | --- |
| PASS | Draft artifact in preview-only posture with teacher approval required |
| WARN | Artifact needs review or has warnings |
| BLOCK | Approved artifact still has blockers |
| BLOCK | Deployment status indicates active deployment while Canvas writes are disallowed |

Examples:

- Homeroom newsletter update remains blocked without a verified page
- Daily Teacher Brief delivery remains disabled in preview mode

## Safety rules

The registry command and status surfaces must not print:

- emails
- URLs
- secrets
- local private paths
- database paths

Health output is category-level and metadata-only.

## Future transport boundary

Future transport remains explicitly blocked unless separately approved:

- Canvas API
- email transport
- external integrations
- automatic publishing

The registry may report readiness. It must not activate transport.

## Explicitly blocked

- Canvas API calls
- email transport
- external integrations
- automatic publishing
- artifact mutation
- duplicate artifact storage

## Command surface

Read-only health command:

```bash
bin/chief-of-staff --canvas-llm-artifact-health-status
```

Purpose: read-only artifact readiness and safety summary.

Not in scope:

- approve command
- deploy command
- publish command
- send command

## Non-activation

This contract documents a read model only. It does not activate runtime behavior, Canvas writes, email delivery, or external integrations.
