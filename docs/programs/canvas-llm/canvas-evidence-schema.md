# Canvas Evidence Schema

```text
Status: PHASE_0_DOCS_ONLY
Classification: fake/local schema guidance
Runtime activation: no
```

## Purpose

This schema describes how future Canvas Knowledge Sweep evidence should be classified before it can influence Canvas LLM behavior. It is not a parser, database schema, API contract, or runtime validator.

## Evidence Record Shape

| Field | Required | Allowed Phase 0 value |
| --- | --- | --- |
| `evidence_id` | yes | fake stable ID |
| `source_type` | yes | `fake_page`, `fake_module`, `fake_assignment`, `policy_note`, `manual_observation_template` |
| `authority_level` | yes | `repo_authority`, `fake_local_example`, `candidate`, `blocked_live_source` |
| `canvas_area` | yes | `page`, `module`, `assignment`, `navigation`, `accessibility`, `publishing`, `self_healing` |
| `claim` | yes | short standards claim |
| `evidence_summary` | yes | concise summary, no real Canvas content |
| `student_data_status` | yes | `blocked` |
| `live_canvas_status` | yes | `blocked` |
| `review_status` | yes | `draft`, `needs_owen_review`, `approved_for_docs`, `rejected` |
| `safe_next_step` | yes | docs/status-only next step |

## Authority Levels

- `repo_authority`: committed repo docs approved as planning/status authority.
- `fake_local_example`: fabricated example used to shape fixtures safely.
- `candidate`: idea needs repo evidence or Owen decision.
- `blocked_live_source`: source would require Canvas/API/OAuth/live access and must not be used in Phase 0.

## Explicit Non-Use

This schema must not be used to ingest real Canvas content, student data, live course data, real curriculum, or external source material.
