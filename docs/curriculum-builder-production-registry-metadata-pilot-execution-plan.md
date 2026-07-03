# Production Registry Metadata Pilot Execution Plan

Last updated: 2026-07-02

```text
Status: metadata_pilot_execution_plan_complete
Classification: one-record pilot protocol — planning only, no execution
Proof: --curriculum-production-registry-metadata-pilot-plan-status
```

## Non-Activation Statement

```text
This plan does not execute the metadata pilot.
This plan does not add a record.
This plan does not authorize --write.
This plan does not authorize writer scripts.
This plan does not authorize sentinel removal.
This plan does not authorize real curriculum file reads.
This plan does not authorize source auto-resolution.
```

## Purpose

Define the **exact protocol** for the first future governed single-record write to the production registry. The pilot is **one-record-only** so Owen can validate manual metadata entry, review gates, snapshot/diff/restore proof, and rollback before any broader write missions.

## Why One Record Only

| Reason | Detail |
| --- | --- |
| Smallest blast radius | One `resource-*` ID proves the full write path |
| Manual-only posture | Owen types every field; no parsers or integrations |
| Rollback proof | Restore to empty shell baseline is auditable |
| Gate discipline | Review state, acceptance criteria, and go/no-go before scale |

## Approved Surface

| Field | Value |
| --- | --- |
| Production path | `assistant/curriculum-builder/registry/v0-2/production-registry.json` |
| Namespace | `resource-*` |
| Empty-file baseline | `records: []` — see `docs/curriculum-builder-production-registry-empty-file.md` |
| Sentinel | `BLOCKED-NO-WRITES.sentinel` remains until separate write mission |

## Manual-Only Data Entry Rules

1. Owen fills `docs/curriculum-builder-production-registry-first-record-owen-entry-worksheet.md` by hand.
2. No curriculum file reads, folder scans, Drive/Canvas/NAS/iCloud access, or APIs.
3. `source_reference` fields are **non-resolving labels** only (see source-reference contract).
4. No copied curriculum content, worksheet text, answer keys, or student data.
5. No AI auto-fill of production fields.

## Allowed Fields

Per `docs/curriculum-builder-production-registry-manual-metadata-field-contract.md`:

- `id`, `title`, `subject`, `grade_band`, `unit_label`, `lesson_label`, `resource_type`, `audience`, `review_state`, `manual_tags`, `notes`, `source_reference`, `created_by`, `created_at`, `updated_at`

## Blocked Fields

Per `docs/curriculum-builder-production-registry-blocked-field-guardrails.md`:

- Student identifiers, rosters, grades tied to individuals
- Resolvable paths, file IDs, URLs, API endpoints, OAuth tokens
- Integration activation fields, embeddings, OCR output, RAG payloads
- Copied curriculum body text in any field

## Source-Reference Rules

Per `docs/curriculum-builder-production-registry-source-reference-contract.md`:

- `display_label`, `source_type`, `location_note`, `citation_note` — Owen-typed labels only
- No auto-fetch, file open, or path resolution

## Review-State Rules

Per `docs/curriculum-builder-production-registry-review-state-model.md`:

- First record write requires `review_state: approved` before mutation
- Draft or pending states block production write

## Snapshot-Before-Write Plan

See `docs/curriculum-builder-production-registry-first-record-snapshot-diff-restore-plan.md`.

1. Capture pre-write snapshot of empty shell (`records: []`).
2. Confirm validator PASS on baseline.
3. No mutation without snapshot artifact plan documented in future write mission.

## Diff-After-Write Plan

1. Expected diff: `records` length `0` → `1`.
2. Single new `resource-*` ID only.
3. Human-readable diff summary to stdout in future write mission.
4. Post-write validator PASS required.

## Restore / Rollback Proof Plan

1. On validation FAIL after write: restore byte-identical empty shell.
2. Post-restore validator PASS.
3. Diff shows zero net change from pre-write baseline.
4. Audit log records rollback reason (future write mission).

## Go / No-Go Checklist (Future Execution Mission)

| # | Gate | Required |
| ---: | --- | --- |
| 1 | Empty shell exists and validates | yes |
| 2 | Metadata pilot execution plan complete | yes |
| 3 | Owen worksheet completed with placeholders replaced by Owen-approved values | yes |
| 4 | Acceptance criteria reviewed | yes |
| 5 | Snapshot/diff/restore plan acknowledged | yes |
| 6 | `review_state: approved` on worksheet | yes |
| 7 | ChatGPT review recommended | yes |
| 8 | Separate explicit governed single-record write prompt issued | yes |
| 9 | Sentinel handling explicit in write prompt | yes |
| 10 | No integration, scan, or curriculum file access | yes |

**No-go if any gate fails.** Abort; do not write.

## Human Review Checklist (Owen)

- [ ] Exactly one `resource-*` ID chosen
- [ ] All fields manual; no pasted curriculum excerpts
- [ ] Source reference is label-only; no resolvable path/URL
- [ ] No student data in any field
- [ ] Audience and review_state valid
- [ ] Worksheet values match acceptance criteria
- [ ] Comfortable with snapshot/restore proof plan

## Stop Conditions

Stop and escalate if the future write mission would require:

- More than one record in the first write
- Removing `BLOCKED-NO-WRITES.sentinel` without explicit approval
- Reading real curriculum files or copying content
- Source auto-resolution or any integration
- Batch import or writer scripts before single-record proof

## Future Prompt Required Before Execution

A **separate explicit prompt** for **governed single-record write** must authorize:

- The one record mutation only
- Sentinel handling per that mission
- Snapshot capture and post-write validation
- No bulk write, no `--write` unless that mission explicitly approves a minimal handler

Planning appendix outline only — not executable:

```text
Mission: Governed Single-Record Production Registry Write
Prerequisites: metadata_pilot_execution_plan_complete, Owen worksheet filled, go/no-go PASS
Scope: append exactly one record to production-registry.json
Out of scope: second record, writer automation, integrations, file reads
Proof commands: empty-file validator, metadata boundary validator, snapshot diff report
```

## Related Documents

| Document | Role |
| --- | --- |
| `docs/curriculum-builder-production-registry-first-record-owen-entry-worksheet.md` | Manual entry template |
| `docs/curriculum-builder-production-registry-first-record-acceptance-criteria.md` | Pass/fail criteria |
| `docs/curriculum-builder-production-registry-first-record-snapshot-diff-restore-plan.md` | Audit proof steps |
| `docs/curriculum-builder-metadata-pilot-planning-boundary.md` | Pilot scope boundary |
| `docs/proposals/backlog/production-registry-write-mission.md` | Write mission backlog |

## Non-Activation

This document is planning authority only. It does not execute the metadata pilot or authorize registry mutation.
