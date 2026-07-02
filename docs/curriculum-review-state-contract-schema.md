# Curriculum Review State Contract Schema (Program A6)

Last updated: 2026-07-02

```text
Status: documentation/status only — inactive schema draft
Program: A6 — Curriculum Review State Contract
Validator: none
Runtime: not active
Review generation: blocked
```

## Purpose

Define review and approval **metadata** without generating review notes, evaluating real curriculum, or creating lesson drafts.

## Field Definitions

| Field | Type (conceptual) | Purpose |
| --- | --- | --- |
| `review_status` | enum | not_started / in_review / approved_placeholder / deferred / rejected_placeholder |
| `review_scope` | enum | resource_metadata / source_reference / lesson_link / output_contract |
| `teacher_verified` | boolean | Teacher attestation flag (planning only) |
| `student_safe` | boolean | Student-safety planning flag |
| `teacher_only_reason` | string \| null | Placeholder reason when teacher-only |
| `requires_manual_review` | boolean | Must default `true` in inactive samples |
| `last_reviewed_future` | string \| null | Reserved — not populated |
| `review_notes_reference_future` | string \| null | Reserved doc/link ID — no real review notes |

## Fictional Sample (Inactive)

```json
{
  "contract_type": "curriculum_review_state_contract",
  "contract_version": "0.0.0-inactive",
  "metadata_only": true,
  "read_only": true,
  "target_id": "sample-resource-worksheet-001",
  "target_kind": "curriculum_resource",
  "review_status": "approved_placeholder",
  "review_scope": "resource_metadata",
  "teacher_verified": true,
  "student_safe": true,
  "teacher_only_reason": null,
  "requires_manual_review": true,
  "last_reviewed_future": null,
  "review_notes_reference_future": null
}
```

Canonical inactive file: `assistant/curriculum-builder/metadata-contract/v0/samples/sample-review-state-001.json`

## Explicitly Blocked

- Generating review notes
- LLM evaluation of curriculum
- Automated safety scoring from real content
- Student-data lookups

## Non-Activation

Planning metadata only. No review engines or content evaluation.
