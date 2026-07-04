# Teacher Knowledge Vault — Organization Review Queue Model

Last updated: 2026-07-04

```text
Status: review queue states — fake fixtures only
```

## Organization Review States

| State | Meaning |
| --- | --- |
| `organization_requested` | Operation requested from suggestion |
| `dry_run_ready` | Preview generated |
| `conflict_detected` | Blocked or needs review |
| `teacher_approval_required` | Awaiting teacher |
| `approved_pending_execution` | Approved but not executed in M5 |
| `execution_blocked` | M5 blocks all execution |
| `executed` | future only |
| `rollback_available` | future only |
| `rollback_requested` | future only |
| `restored` | future only |
| `rejected` | Teacher rejected |
| `archived` | Archived candidate |

## Example Scenarios (Fake)

- Smart rename promoted to operation request
- Duplicate merge requested but blocked
- Version canonical selection requested
- Teacher-only destination conflict
- Student-facing leakage conflict
- `99_DO_NOT_SCAN` destination blocked
- Cloud placeholder source blocked
- No-overwrite conflict
- Rollback unavailable conflict

Fixture: `assistant/teacher-knowledge-vault/m5/fake-organization-review-queue.json`
