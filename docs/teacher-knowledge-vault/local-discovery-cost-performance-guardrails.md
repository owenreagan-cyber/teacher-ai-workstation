# Teacher Knowledge Vault — Local Discovery Cost and Performance Guardrails

Last updated: 2026-07-04

```text
Status: guardrail documentation — M2 approval packet
API cost estimate: $0.00
```

## Cost Rules (M2 and Future M2b)

| Cost type | M2 / default |
| --- | --- |
| API cost estimate | `api_cost_estimate_usd` must remain `$0.00` |
| OCR cost | `$0.00` — blocked |
| AI classification cost | `$0.00` — blocked |
| Connector cost | `$0.00` — blocked |
| Background file watch (chokidar) | Not approved |
| Recursive Drive/iCloud/NAS root scans | Blocked |

## Performance Rules (Required Before Future Implementation)

- `max_file_count` limit per discovery run
- `max_depth` limit under approved root
- Progress reporting with cancel/stop behavior
- No background bulk discovery
- No repeated metadata reads without change detection

Fixture: `assistant/teacher-knowledge-vault/m2/fake-cost-performance-metrics.json`
