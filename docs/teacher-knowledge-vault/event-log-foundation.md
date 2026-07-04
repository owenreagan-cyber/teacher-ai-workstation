# Teacher Knowledge Vault — Event Log Foundation (M1)

Last updated: 2026-07-04

```text
Status: fake event log fixtures only — no runtime event store
```

## Event Types in M1 Fixtures

| Event type | Fixture meaning |
| --- | --- |
| discovery_run_planned | Planned only — not executed |
| source_item_found | Catalog fixture item |
| source_item_blocked_do_not_scan | `99_DO_NOT_SCAN` gate |
| fingerprint_calculated | Fake fingerprint set |
| duplicate_candidate_found | Relationship fixture |
| version_candidate_found | Relationship fixture |
| classification_suggested | Rule/evidence — review required |
| teacher_approved | Review approval (fake) |
| teacher_rejected | Review rejection (fake) |
| teacher_edited_suggestion | Manual edit (fake) |
| dry_run_organization_planned | No execute |
| operation_blocked_pending_approval | Gate block |
| ocr_requested_blocked | OCR blocked |
| ai_classification_requested_blocked | AI blocked |
| connector_access_requested_blocked | Connector blocked |
| canvas_publish_requested_blocked | Canvas blocked |

## Rule

Every event has `runtime_executed: false` in M1 fixtures. PASS does not imply real execution.

## Fixture

`assistant/teacher-knowledge-vault/m1/fake-event-log.json`
