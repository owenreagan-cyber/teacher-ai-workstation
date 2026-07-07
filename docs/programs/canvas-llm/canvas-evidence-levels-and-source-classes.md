# Canvas Evidence Levels And Source Classes

```text
Status: phase_4_static_evidence_model
Classification: docs/status/schema only
Runtime activation: no
Canvas API/OAuth/live reads: blocked
```

## Evidence Levels

| Level | Name | Phase 4 status | Notes |
| --- | --- | --- | --- |
| Level 0 | fake/local fixture evidence | Approved for static fixtures | Repo-owned examples only; no real course, student, or private data. |
| Level 1 | manually prepared redacted packet evidence | Existing manual/redacted planning surface | Must be explicit, redacted, reviewed, and local. No automatic scanning. |
| Level 2 | inactive historical course evidence, approval-gated | Future-only | Includes 2024-2025 and 2025-2026 inactive historical courses. Must be screened for student/private data before any use. |
| Level 3 | sandbox/demo Canvas course evidence | Future-only, preferred for API testing | Preferred later because sandbox/demo Canvas courses can contain no student data and no historical data. |
| Level 4 | current production course evidence | Blocked | Blocked unless separately approved in a later phase. |

No evidence level authorizes Canvas API/OAuth/live reads, Canvas writes/publishing, real curriculum ingestion, student data handling, RAG, embeddings, generation, or runtime storage in Phase 4.

## Source Classes

| Source class | Evidence level | Phase 4 use | Approval state |
| --- | --- | --- | --- |
| `fake_local_fixture` | Level 0 | Static schema/fixture examples | Approved for Phase 4 fixtures only |
| `manual_redacted_packet` | Level 1 | Manual packet concepts and reviewed redacted examples | Approval-gated by packet review |
| `inactive_historical_canvas_course` | Level 2 | Future source class only | Approval-gated and privacy-screened |
| `sandbox_demo_canvas_course` | Level 3 | Future preferred API-test source class | Future approval required |
| `current_production_canvas_course` | Level 4 | None in Phase 4 | Blocked |

## Required Evidence Fields

Every future evidence record should include:

- `evidence_id`
- `source_reference_id`
- `source_class`
- `evidence_level`
- `evidence_kind`
- `redaction_status`
- `contains_student_data`
- `contains_real_curriculum`
- `verification_status`
- `approval_status`
- `confidence_level`
- `created_at`
- `review_notes`

## Verification Status

Use explicit values:

- `fake_local_example`
- `unverified`
- `needs_review`
- `verified_against_source`
- `stale`
- `rejected`

## Approval Status

Use explicit values:

- `fixture_approved`
- `pending_review`
- `approved_for_planning`
- `approved_for_future_ingestion`
- `blocked`
- `rejected`

Phase 4 fixtures may use `fixture_approved` only when they are fake/local examples.
